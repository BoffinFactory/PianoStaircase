#include "PitchToNote.h"

// Pitches for each sensor (key value of element matches key value of echoPins; IE: stepPitch[i] = pitch sound of echoPin[i])
const int stepPitches[] = {
  C4,
  D4,
  E4,
  F4,
  G4,
  A4,
  B4,
  C5,
};

#include "MIDIUSB.h"
#include "Piano.h"

// Distance to trigger note at
const int triggerDistance = 65;

// Trigger pin to be used for all sensors
const int trigPin = 2;

// Echo pins for each sensor
const int echoPins[] = {
  3,
  4,
};

// Initalizes all pins
// Sets trigger pin as output
// Sets all echo pins as input
// Sets baud rate
void setup() {
  // Set trigger pin to output
  pinMode(trigPin, OUTPUT);

  // Loop through all echo pins and set input
  for(int i = 0; i < sizeof(echoPins) / sizeof(echoPins[0]); i++) {
    pinMode(echoPins[i], INPUT);
  }

  // Set baud rate
  Serial.begin(115200);
}

// Loops through all sensors looking
// to trigger once trigger distance
// is satisifed.
void loop() {
  // Distance of object from sensor
  float distance;

  // Loop through each echo pin
  for(int i = 0; i < sizeof(echoPins) / sizeof(echoPins[0]); i++) {
    // Get distance of object from sensor
    distance = showDistance(i + 1, echoPins[i]);

    // If distance is close enough and the currentState of pitch for sensor is 0, turn on note
    if(distance <= triggerDistance) {
      changeState(stepPitches[i], true);
    } 

    // If sound is on and distance is too far away, turn off note  
    else {
      changeState(stepPitches[i], false);
    }

    // Print line for pretty console
    Serial.println();
  }

  // Print line for pretty console
  Serial.println();
  delay(25);
}

// A function to calculate distance of object from sensor
// Args:
//  num (int): number of note (coincides with step number)
//  echoPin (int): step to check
//
// Outputs:
//  distance (float): distance of object from sensor in cm
float showDistance(int num, int echoPin) {
  // Get duration and distance
  float duration, distance;

  // Stop sending any trigger
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  // Send trigger
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);

  // Stop sending any trigger
  digitalWrite(trigPin, LOW);

  // Calculate distance away from sensor
  duration = pulseIn(echoPin, HIGH);
  distance = (duration*.0343)/2;
  delay(25);

  // Return distance
  return distance;
}
