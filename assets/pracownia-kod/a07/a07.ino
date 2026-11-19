// A07 Pokrętło i odczyt: potencjometr na A0, wynik 0–1023
void setup() {
  Serial.begin(9600);
}

void loop() {
  int pozycja = analogRead(A0);       // 0 = jeden koniec, 1023 = drugi
  Serial.print("Pokrętło: ");
  Serial.println(pozycja);
  delay(200);
}
