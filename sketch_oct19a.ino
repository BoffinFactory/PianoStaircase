#include "pitches.h"

// defines pins numbers
const int trigPin = 9;
const int echoPin = 10;
const int buzzer = 8;
const int redLED = 13;
const int greenLED = 12;
const int yellowLED = 11;

// change this to make the song slower or faster
int tempo = 180;

// notes of the moledy followed by the duration.
// a 4 means a quarter note, 8 an eighteenth , 16 sixteenth, so on
// !!negative numbers are used to represent dotted notes,
// so -4 means a dotted quarter note, that is, a quarter plus an eighteenth!!
int melody[] = {

  // Nokia Ringtone 
  // Score available at https://musescore.com/user/29944637/scores/5266155
  
  NOTE_E5, 8, NOTE_D5, 8, NOTE_FS4, 4, NOTE_GS4, 4, 
  NOTE_CS5, 8, NOTE_B4, 8, NOTE_D4, 4, NOTE_E4, 4, 
  NOTE_B4, 8, NOTE_A4, 8, NOTE_CS4, 4, NOTE_E4, 4,
  NOTE_A4, 2, 
};

// defines variables
long duration;
int distance;
int safetyDistance;

// sizeof gives the number of bytes, each int value is composed of two bytes (16 bits)
// there are two values per note (pitch and duration), so for each note there are four bytes
int notes = sizeof(melody) / sizeof(melody[0]) / 2;

// this calculates the duration of a whole note in ms
int wholenote = (60000 * 4) / tempo;

int divider = 0, noteDuration = 0;


void setup() {
pinMode(trigPin, OUTPUT); // Sets the trigPin as an Output
pinMode(echoPin, INPUT); // Sets the echoPin as an Input
pinMode(buzzer, OUTPUT);
pinMode(redLED, OUTPUT);
pinMode(yellowLED, OUTPUT);
pinMode(greenLED, OUTPUT);
Serial.begin(9600); // Starts the serial communication
}


void loop() {
// Clears the trigPin
digitalWrite(trigPin, LOW);
delayMicroseconds(2);

// Sets the trigPin on HIGH state for 10 micro seconds
digitalWrite(trigPin, HIGH);
delayMicroseconds(10);
digitalWrite(trigPin, LOW);

// Reads the echoPin, returns the sound wave travel time in microseconds
duration = pulseIn(echoPin, HIGH);

// Calculating the distance
distance= duration*0.034/2;

safetyDistance = distance;
if (safetyDistance < 10){
  
  tone(buzzer, NOTE_A5, 0.01);
  digitalWrite(redLED, HIGH);
  delay(200);
  noTone(buzzer);
  delay(200);
  digitalWrite(redLED, LOW);
}
if(safetyDistance < 20 && safetyDistance >= 10){
  tone(buzzer, NOTE_D5, 0.01);
  digitalWrite(yellowLED, HIGH);
  delay(200);
  noTone(buzzer);
  delay(200);
  digitalWrite(yellowLED, LOW);

}
if(safetyDistance < 30 && safetyDistance >= 20){
  tone(buzzer, NOTE_C5, 0.01);
  digitalWrite(greenLED, HIGH);
  delay(200);
  noTone(buzzer);
  delay(200);
  digitalWrite(greenLED, LOW);

}

else{
  digitalWrite(buzzer, LOW);
  digitalWrite(greenLED, LOW);
  digitalWrite(yellowLED, LOW);
  digitalWrite(redLED, LOW);
  
}

// Prints the distance on the Serial Monitor
Serial.print("Distance: ");
Serial.println(distance);
}
