import os
import logging
import sqlite3

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

from api import send_count, send_notification
from db import init_db, is_admin, get_unread_messages_count, register_user

ADMIN_ID = os.getenv('ADMIN_ID')
API_TOKEN = os.getenv('API_TOKEN')
LOCALHOST = os.getenv('LOCALHOST')
PORT = os.getenv('PORT')


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

init_db()

# Состояния для FSM
class AdminStates(StatesGroup):
    waiting_for_reply = State()

# Клавиатура для пользователя
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Написать сообщение')],
        [KeyboardButton(text='Мои сообщения')]
    ],
    resize_keyboard=True
)

# Клавиатура для администратора
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Непрочитанные сообщения')],
        [KeyboardButton(text='Все сообщения')]
    ],
    resize_keyboard=True
)

# Добавление администратора (вручную в БД или через команду)
@dp.message(Command('add_admin'))
async def add_admin_command(message: types.Message):
    if message.from_user.id == ADMIN_ID:  # Замените на ваш ID
        conn = sqlite3.connect('support_bot.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO admins VALUES (?, ?, ?, ?)', 
                      (message.from_user.id, message.from_user.username, 
                       message.from_user.first_name, message.from_user.last_name))
        conn.commit()
        conn.close()
        await message.answer("Вы добавлены как администратор!", reply_markup=admin_keyboard)
    else:
        await message.answer("У вас нет прав для этой команды.")

# Обработчик команды /start
@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    register_user(message.from_user)
    
    if is_admin(message.from_user.id):
        await message.answer("Добро пожаловать, администратор!", reply_markup=admin_keyboard)
    else:
        await message.answer("Добро пожаловать! Напишите нам свое сообщение, и мы скоро ответим.", 
                            reply_markup=user_keyboard)

# Обработчик кнопки "Написать сообщение"
@dp.message(F.text == 'Написать сообщение')
async def start_message(message: types.Message):
    await message.answer("Напишите ваше сообщение, и администратор ответит вам как можно скорее:")


# Обработчик кнопки "Непрочитанные сообщения" для администратора
@dp.message(F.text == 'Непрочитанные сообщения')
async def show_unread_messages(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для этой команды.")
        return
    
    conn = sqlite3.connect('support_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT m.message_id, m.user_id, m.message_text, m.timestamp, u.username, u.first_name, u.last_name
    FROM messages m
    JOIN users u ON m.user_id = u.user_id
    WHERE m.is_answered = 0
    ORDER BY m.timestamp
    ''')
    
    messages = cursor.fetchall()
    conn.close()
    
    if not messages:
        await message.answer("Нет непрочитанных сообщений.")
        return
    
    for msg in messages:
        message_id, user_id, message_text, timestamp, username, first_name, last_name = msg
        user_info = f"@{username}" if username else f"{first_name} {last_name}"
        
        await message.answer(
            f"📩 Сообщение от {user_info} (ID: {user_id})\n"
            f"🕒 {timestamp}\n"
            f"✉️ {message_text}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="Ответить", 
                    callback_data=f"reply_{user_id}_{message_id}"
                )]
            ])
        )

# Обработчик кнопки "Все сообщения" для администратора
@dp.message(F.text == 'Все сообщения')
async def show_unread_messages(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для этой команды.")
        return
    
    conn = sqlite3.connect('support_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT m.message_id, m.user_id, m.message_text, m.timestamp, u.username, u.first_name, u.last_name
    FROM messages m
    JOIN users u ON m.user_id = u.user_id
    ORDER BY m.timestamp
    ''')
    
    messages = cursor.fetchall()
    conn.close()
    
    if not messages:
        await message.answer("Нет сообщений.")
        return
    
    for msg in messages:
        message_id, user_id, message_text, timestamp, username, first_name, last_name = msg
        user_info = f"@{username}" if username else f"{first_name} {last_name}"
        
        await message.answer(
            f"📩 Сообщение от {user_info} (ID: {user_id})\n"
            f"🕒 {timestamp}\n"
            f"✉️ {message_text}"
        )

# Обработчик callback для кнопки "Ответить"
@dp.callback_query(F.data.startswith('reply_'))
async def process_reply_callback(callback_query: types.CallbackQuery, state: FSMContext):
    _, user_id, message_id = callback_query.data.split('_')
    
    await callback_query.answer()
    
    await state.update_data(
        recipient_id=user_id,
        original_message_id=message_id
    )
    
    await state.set_state(AdminStates.waiting_for_reply)
    await callback_query.message.answer(
        "Введите ваш ответ:"
    )

# Обработчик ответа администратора
@dp.message(AdminStates.waiting_for_reply)
async def process_admin_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['recipient_id']
    original_message_id = data['original_message_id']
    
    try:
        # Отправляем ответ пользователю
        await bot.send_message(
            user_id,
            f"🔵 Ответ администратора:\n{message.text}"
        )
        
        # Помечаем сообщение как отвеченное в БД
        conn = sqlite3.connect('support_bot.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE messages SET is_answered = 1, admin_id = ? WHERE message_id = ?',
                      (message.from_user.id, original_message_id))
        conn.commit()
        conn.close()
        
        send_count(LOCALHOST, PORT)

        await message.answer("Ответ отправлен пользователю!", reply_markup=admin_keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа пользователю: {e}")
        await message.answer("Не удалось отправить ответ. Пользователь, возможно, заблокировал бота.")
    
    await state.clear()

# Обработчик кнопки "Мои сообщения" для пользователя
@dp.message(F.text == 'Мои сообщения')
async def show_user_messages(message: types.Message):
    conn = sqlite3.connect('support_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT m.message_text, m.timestamp, m.is_answered, a.first_name, a.last_name
    FROM messages m
    LEFT JOIN admins a ON m.admin_id = a.admin_id
    WHERE m.user_id = ?
    ORDER BY m.timestamp DESC
    LIMIT 10
    ''', (message.from_user.id,))
    
    messages = cursor.fetchall()
    conn.close()
    
    print(messages)


    if not messages:
        await message.answer("У вас пока нет сообщений.")
        return

    response = "Ваши последние сообщения:\n\n"
    for msg in messages:
        message_text, timestamp, is_answered, admin_first_name, admin_last_name = msg
        status = "🔵 Ответ получен" if is_answered else "🟡 Ожидает ответа"
        admin_info = f" от {admin_first_name} {admin_last_name}" if is_answered else ""
        
        response += (
            f"📅 {timestamp}\n"
            f"✉️ {message_text}\n"
            f"🔄 {status}{admin_info}\n\n"
        )
    
    await message.answer(response)

# Сохранение сообщения от пользователя
@dp.message(F.text)
async def save_user_message(message: types.Message):
    if is_admin(message.from_user.id):
        return
    
    register_user(message.from_user)
    
    conn = sqlite3.connect('support_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('INSERT INTO messages (user_id, message_text, timestamp) VALUES (?, ?, ?)',
                  (message.from_user.id, message.text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    
    # Получаем список администраторов для уведомления
    cursor.execute('SELECT admin_id FROM admins')
    admins = cursor.fetchall()
    
    conn.close()
    
    # Уведомляем администраторов о новом сообщении
    for admin in admins:
        try:
            unread_count = get_unread_messages_count()
            await bot.send_message(
                admin[0],
                f"📨 Новое сообщение от пользователя!\n"
                f"👤 Пользователь: @{message.from_user.username or 'нет username'}\n"
                f"✉️ Сообщение: {message.text}\n\n"
                f"Всего непрочитанных: {unread_count}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="Ответить", 
                        callback_data=f"reply_{message.from_user.id}_{cursor.lastrowid}"
                    )]
                ])
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления администратору {admin[0]}: {e}")
    
    send_notification(LOCALHOST, PORT)
    send_count(LOCALHOST, PORT)

    await message.answer("Ваше сообщение отправлено администратору. Ожидайте ответа.", reply_markup=user_keyboard)


async def on_startup():
    print("Бот запущен")

if __name__ == '__main__':
    dp.startup.register(on_startup)
    dp.run_polling(bot)