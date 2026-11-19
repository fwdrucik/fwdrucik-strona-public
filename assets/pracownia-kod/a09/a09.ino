// A09 Zapis obserwacji: log zmian przycisku w monitorze portu
const int PRZYCISK = 2;
int poprzedni = HIGH;

void setup() {
  pinMode(PRZYCISK, INPUT_PULLUP);
  Serial.begin(9600);
  Serial.println("czas_ms;stan");
}

void loop() {
  int teraz = digitalRead(PRZYCISK);
  if (teraz != poprzedni) {
    Serial.print(millis());
    Serial.print(";");
    Serial.println(teraz == LOW ? "wcisniety" : "puszczony");
    poprzedni = teraz;
    delay(30);               // przeczekanie drgań styków
  }
}
