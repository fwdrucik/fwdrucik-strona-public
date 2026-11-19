// A05 Czas bez zatrzymywania programu: millis() zamiast delay()
const int LED = 13;
const int PRZYCISK = 2;
unsigned long ostatnio = 0;
bool stan = false;

void setup() {
  pinMode(LED, OUTPUT);
  pinMode(PRZYCISK, INPUT_PULLUP);
  pinMode(12, OUTPUT);       // druga dioda reaguje na przycisk
}

void loop() {
  if (millis() - ostatnio >= 500) {   // co 500 ms zmiana diody
    ostatnio = millis();
    stan = !stan;
    digitalWrite(LED, stan);
  }
  digitalWrite(12, digitalRead(PRZYCISK) == LOW);  // przycisk działa cały czas
}
