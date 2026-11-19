// A02 Wejście i wyjście: przycisk na D2 włącza diodę na D13
const int PRZYCISK = 2;      // drugi styk przycisku do GND
const int LED = 13;

void setup() {
  pinMode(PRZYCISK, INPUT_PULLUP);  // otwarty = HIGH, wciśnięty = LOW
  pinMode(LED, OUTPUT);
}

void loop() {
  if (digitalRead(PRZYCISK) == LOW) {
    digitalWrite(LED, HIGH);
  } else {
    digitalWrite(LED, LOW);
  }
}
