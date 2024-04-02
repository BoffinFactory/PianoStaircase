const int trigPin = 2;

const int echoPins[] = {
  6,
  3,
  4,
  5,
};

float duration, distance;

void setup() {
  pinMode(trigPin, OUTPUT);

  for(int i = 0; i < sizeof(echoPins) / sizeof(echoPins[0]); i++) {
    pinMode(echoPins[i], INPUT);
  }

  Serial.begin(9600);
}

void loop() {
  for(int i = 0; i < sizeof(echoPins) / sizeof(echoPins[0]); i++) {
    showDistance(i + 1, echoPins[i]);
    Serial.println();
  }
  Serial.println();
  Serial.println();
  delay(1000);
}

void showDistance(int num, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);
  distance = (duration*.0343)/2;
  Serial.print(num);
  Serial.print(" Distance: ");
  Serial.println(distance);
  delay(100);
}