#include "PitchToNote.h"
#include "MIDIUSB.h"

// Distance to trigger note at
const int triggerDistance = 50;

// Trigger pin to be used for all sensors
const int trigPin = 2;

// Echo pins for each sensor
const int echoPins[] = {
  3,
  4,
};

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

// State of the pitch output for each sensor
int currentState[sizeof(echoPins) / sizeof(echoPins[0])];

// Turn note on
void noteOn(byte channel, byte pitch, byte velocity) {
  midiEventPacket_t noteOn = {0x09, 0x90 | channel, pitch, velocity};
  MidiUSB.sendMIDI(noteOn);
}

// Turn note off
void noteOff(byte channel, byte pitch, byte velocity) {
  midiEventPacket_t noteOff = {0x08, 0x80 | channel, pitch, velocity};
  MidiUSB.sendMIDI(noteOff);
}

// Change control
void controlChange(byte channel, byte control, byte value) {
  midiEventPacket_t event = {0x0B, 0xB0 | channel, control, value};
  MidiUSB.sendMIDI(event);
}

// Start provided note
void startNote(int note) {
  Serial.print("Starting Note: ");
  Serial.print(stepPitches[note]);
  Serial.println();
  noteOn(0, stepPitches[note], 64);
  MidiUSB.flush();
}

// Stop provided note
void stopNote(int note) {
  Serial.print("Stopping Note: ");
  Serial.print(stepPitches[note]);
  Serial.println();
  noteOff(0, stepPitches[note], 64);
  MidiUSB.flush();
}

// Setup GPIO pins
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

void loop() {
  // Distance of object from sensor
  float distance;

  // Loop through each echo pin
  for(int i = 0; i < sizeof(echoPins) / sizeof(echoPins[0]); i++) {
    // Get distance of object from sensor
    distance = showDistance(i + 1, echoPins[i]);

    // If distance is close enough and the currentState of pitch for sensor is 0, turn on note
    if(distance <= triggerDistance && currentState[i] == 0) {
      // Start note
      startNote(i);

      // Set state
      currentState[i] = 1;
    } 

    // If sound is on and distance is too far away, turn off note  
    else if(currentState[i] == 1 && distance > triggerDistance) {
      // Start note
      stopNote(i);

      // Set state
      currentState[i] = 0;
    }

    // Print line for pretty console
    Serial.println();
  }

  // Print line for pretty console
  Serial.println();
  delay(25);
}

// Given number of sensor and pin, check distance
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
