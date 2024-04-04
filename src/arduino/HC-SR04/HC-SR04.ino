#include "PitchToNote.h"
#include "MIDIUSB.h"

const int trigPin = 2;

const int echoPins[] = {
  3,
  4,
};

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

void noteOn(byte channel, byte pitch, byte velocity) {
  midiEventPacket_t noteOn = {0x09, 0x90 | channel, pitch, velocity};
  MidiUSB.sendMIDI(noteOn);
}

void noteOff(byte channel, byte pitch, byte velocity) {
  midiEventPacket_t noteOff = {0x08, 0x80 | channel, pitch, velocity};
  MidiUSB.sendMIDI(noteOff);
}

void controlChange(byte channel, byte control, byte value) {
  midiEventPacket_t event = {0x0B, 0xB0 | channel, control, value};
  MidiUSB.sendMIDI(event);
}

void sendNoteFromStep(int note) {
  Serial.println("Sending note on");
  noteOn(0, stepPitches[note], 64);   // Channel 0, middle C, normal velocity
  MidiUSB.flush();
  delay(500);
  Serial.println("Sending note off");
  noteOff(0, stepPitches[note], 64);  // Channel 0, middle C, normal velocity
  MidiUSB.flush();
  delay(100);
}

void setup() {
  pinMode(trigPin, OUTPUT);

  for(int i = 0; i < sizeof(echoPins) / sizeof(echoPins[0]); i++) {
    pinMode(echoPins[i], INPUT);
  }

  Serial.begin(115200);
}

void loop() {
  float distance;
  for(int i = 0; i < sizeof(echoPins) / sizeof(echoPins[0]); i++) {
    distance = showDistance(i + 1, echoPins[i]);

    if(distance < 30) {
      sendNoteFromStep(i);
    } 
    Serial.println();
  }
  Serial.println();
  Serial.println();
  delay(100);
}

float showDistance(int num, int echoPin) {
  float duration, distance;

  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);
  distance = (duration*.0343)/2;
  delay(100);

  return distance;
}
