#define COUNT_NOTES 14

const int green_led = 7;
const int yellow_led = 5;
const int red_led = 2;

const int ringhton = 12;

int  frequences[COUNT_NOTES] = {329, 392, 392, 329, 440, 392, 440, 392, 440, 392, 440, 392, 440, 493};
int  durations[COUNT_NOTES]  = {300, 600, 300, 600, 300, 300, 300, 300, 300, 300, 300, 300, 300, 600 };
int  delays[COUNT_NOTES]  = {300, 1200, 300, 1200, 300, 300, 300, 300, 300, 300, 300, 300, 300, 600 };


void setup() {
  pinMode(green_led, OUTPUT);
  pinMode(yellow_led, OUTPUT);
  pinMode(red_led, OUTPUT);
  pinMode(ringhton, OUTPUT);
  Serial.begin(9600);
  while (!Serial) {
    ; // Ожидаем подключения Serial
  }
  Serial.println("System started. Ready for commands.");
}

void logAction(const String& action) {
  Serial.print("[LOG] ");
  Serial.print(millis());
  Serial.print("ms: ");
  Serial.println(action);
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "green_on") {
      logAction("Turning green LED solid ON");
      digitalWrite(green_led, HIGH);
    }
    else if (command == "green_off") {
      logAction("Turning green LED solid OFF");
      digitalWrite(green_led, LOW);
    }
    else if (command == "red_on") {
      logAction("Turning red LED solid ON");
      digitalWrite(red_led, HIGH);
    }
    else if (command == "red_off") {
      logAction("Turning red LED solid OFF");
      digitalWrite(red_led, LOW);
    }
    else if (command == "yellow_on") {
      logAction("Turning yellow LED solid ON");
      digitalWrite(yellow_led, HIGH);
    }
    else if (command == "yellow_off") {
      logAction("Turning yellow LED solid OFF");
      digitalWrite(yellow_led, LOW);
    }
    else if (command == "all_on") {
      logAction("Turning all LEDs OFF");
      digitalWrite(green_led, HIGH);
      digitalWrite(red_led, HIGH);
      digitalWrite(yellow_led, HIGH);
    }
    else if (command == "all_off") {
      logAction("Turning all LEDs OFF");
      digitalWrite(green_led, LOW);
      digitalWrite(red_led, LOW);
      digitalWrite(yellow_led, LOW);
    }
    else if (command == "led_notify") {
      logAction("LED notify");
      for (int i = 0; i < 20; i++) {
        digitalWrite(red_led, HIGH);
        delay(100);
        digitalWrite(red_led, LOW);
        digitalWrite(yellow_led, HIGH);
        delay(100);
        digitalWrite(yellow_led, LOW);
        digitalWrite(green_led, HIGH);
        delay(100);
        digitalWrite(green_led, LOW);
        delay(100);
      }
    }
    else if (command == "ringhton") {
      logAction("Play ringhtone");
      for (int i=0; i<COUNT_NOTES; i++) {
          digitalWrite(yellow_led, HIGH);
          tone(ringhton, frequences[i], durations[i]);
          digitalWrite(yellow_led, LOW);
          delay(delays[i]/2);
      }
    }
    else if (command == "sound_notify") {
      logAction("Play sound nnotify");
      tone(ringhton, 500, 1500);
    }
    else {
      logAction("Unknown command: " + command);
    }
    
    // Отправляем подтверждение выполнения
    Serial.println("CMD_DONE:" + command);
  }
}