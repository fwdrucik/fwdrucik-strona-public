// A01 Pętla i rytm: dioda świeci 1 s i gaśnie na 1 s
const int LED = 13;          // wbudowana dioda UNO R3

void setup() {
  pinMode(LED, OUTPUT);
}

void loop() {
  digitalWrite(LED, HIGH);   // świeci
  delay(1000);               // czeka 1000 ms
  digitalWrite(LED, LOW);    // gaśnie
  delay(1000);
}
