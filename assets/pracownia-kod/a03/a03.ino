// A03 Serwo pozycyjne: ramię odwiedza trzy położenia
#include <Servo.h>
Servo ramie;                 // sygnał serwa na D9

void setup() {
  ramie.attach(9);
}

void loop() {
  ramie.write(0);            // kąt 0°
  delay(1000);
  ramie.write(90);           // kąt 90°
  delay(1000);
  ramie.write(180);          // kąt 180°
  delay(1000);
}
