import sqlite3
from datetime import datetime


# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('support_bot.db')
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        registration_date TEXT
    )
    ''')
    
    # Таблица сообщений
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        admin_id INTEGER,
        message_text TEXT,
        is_answered INTEGER DEFAULT 0,
        timestamp TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    # Таблица администраторов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        admin_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

# Проверка, является ли пользователь администратором
def is_admin(user_id):
    conn = sqlite3.connect('support_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT admin_id FROM admins WHERE admin_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# Регистрация пользователя
def register_user(user):
    conn = sqlite3.connect('support_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user.id,))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?)', 
                      (user.id, user.username, user.first_name, 
                       user.last_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    
    conn.close()

# Получение количества непрочитанных сообщений
def get_unread_messages_count():
    conn = sqlite3.connect('support_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM messages WHERE is_answered = 0')
    count = cursor.fetchone()[0]
    conn.close()
    return count