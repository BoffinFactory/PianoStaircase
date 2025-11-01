// Reads an analog signal from the A0 pin
// Outputs it as a Serial on baud 9600 in plain text

const int sensorPin = A0;  // Analog input pin
int sensorValue = 0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  sensorValue = analogRead(sensorPin);
  Serial.println(sensorValue);
  delay(100);
}
