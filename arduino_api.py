from fastapi import FastAPI, HTTPException
import serial
import serial.tools.list_ports
from time import sleep

app = FastAPI()

valid_commands = {
    "green_on", "green_off",
    "yellow_on", "yellow_off",
    "red_on", "red_off",
    "all_on", "all_off",
    "led_notify", "sound_notify",
    "ringhton"
}

def find_arduino_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "Arduino" in port.description or "CH340" in port.description:
            return port.device
    return None

# Подключение к Arduino
arduino_port = find_arduino_port()
if arduino_port:
    arduino = serial.Serial(arduino_port, 9600, timeout=2)
    print(f"Connected to Arduino on {arduino_port}")
    # Даем Arduino время на инициализацию
    sleep(2)
    arduino.reset_input_buffer()
else:
    raise Exception("Arduino not found!")

def send_command(command: str) -> dict:
    """Отправляет команду в Arduino и возвращает результат"""
    try:
        # Отправляем команду
        arduino.write(f"{command}\n".encode())
        
        # Ждем подтверждения от Arduino
        while True:
            response = arduino.readline().decode().strip()
            if not response:
                continue
                
            if response.startswith("CMD_DONE:"):
                executed_command = response.split(":")[1]
                if executed_command == command:
                    return {
                        "status": "success",
                        "command": command,
                        "message": f"Command '{command}' executed successfully"
                    }
                else:
                    return {
                        "status": "error",
                        "command": command,
                        "message": f"Arduino executed wrong command: {executed_command}"
                    }
            
            # Выводим логи Arduino в консоль сервера
            print(f"Arduino log: {response}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/control/{command}")
async def control_leds(command: str):
    
    if command not in valid_commands:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid command. Valid commands are: {', '.join(valid_commands)}"
        )

    return send_command(command)

@app.on_event("shutdown")
def shutdown_event():
    if arduino and arduino.is_open:
        arduino.close()
    print("Arduino connection closed")

@app.get("/")
async def root():
    return {
        "message": "LED Control API",
        "endpoints": {
            "/control/{command}": "Control LEDs " + ", ".join(valid_commands)
        }
    }