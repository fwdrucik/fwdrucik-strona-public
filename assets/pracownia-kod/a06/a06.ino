// A06 Kolory RGB: czerwony + zielony = żółty (dioda ze wspólną katodą)
const int R = 9, G = 10, B = 11;   // wyjścia PWM przez rezystory 220 Ω

void kolor(int r, int g, int b) {
  analogWrite(R, r);
  analogWrite(G, g);
  analogWrite(B, b);
}

void setup() {}

void loop() {
  kolor(255, 0, 0);   delay(1000);  // czerwony
  kolor(0, 255, 0);   delay(1000);  // zielony
  kolor(255, 255, 0); delay(1000);  // żółty
  kolor(0, 0, 255);   delay(1000);  // niebieski
}
