const int trigPinOne = 2;
const int trigPinTwo = 5;
const int echoPinOne = 3;
const int echoPinTwo = 6;

float duration, distance;

void setup() {
  pinMode(trigPinOne, OUTPUT);
  pinMode(trigPinTwo, OUTPUT);

  pinMode(echoPinOne, INPUT);
  pinMode(echoPinTwo, INPUT);
  Serial.begin(9600);
}

void loop() {
  showDistance(1, trigPinOne, echoPinOne);
  showDistance(2, trigPinTwo, echoPinTwo);
  Serial.println();
  delay(1000);
}

void showDistance(int num, int trigPin, int echoPin) {
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