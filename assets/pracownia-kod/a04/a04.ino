// A04 Polecenie STOP: przycisk zatrzymuje silnik do restartu
const int SILNIK = 5;        // sterowanie przez tranzystor lub moduł L298N
const int STOP = 2;          // przycisk do GND
bool zatrzymany = false;

void setup() {
  pinMode(SILNIK, OUTPUT);
  pinMode(STOP, INPUT_PULLUP);
}

void loop() {
  if (digitalRead(STOP) == LOW) {
    zatrzymany = true;       // STOP zostaje zapamiętany
  }
  digitalWrite(SILNIK, zatrzymany ? LOW : HIGH);
}
