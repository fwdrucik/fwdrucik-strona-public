// A08 Dźwięk jako sygnał: dwa krótkie piski = „czekam”
const int BRZECZYK = 8;      // brzęczyk pasywny

void setup() {}

void loop() {
  for (int i = 0; i < 2; i++) {
    tone(BRZECZYK, 880, 150);  // ton 880 Hz przez 150 ms
    delay(300);
  }
  delay(2000);
}
