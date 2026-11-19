// A10 Warunek: „jest wciśnięty” kontra „właśnie został wciśnięty”
const int PRZYCISK = 2;
const int LED = 13;
const int BRZECZYK = 8;
int poprzedni = HIGH;

void setup() {
  pinMode(PRZYCISK, INPUT_PULLUP);
  pinMode(LED, OUTPUT);
}

void loop() {
  int teraz = digitalRead(PRZYCISK);
  digitalWrite(LED, teraz == LOW);           // świeci, dopóki trzymasz
  if (poprzedni == HIGH && teraz == LOW) {   // tylko w chwili wciśnięcia
    tone(BRZECZYK, 1000, 100);               // jeden pisk na wciśnięcie
  }
  poprzedni = teraz;
  delay(20);
}
