#include "MIDIUSB.h"

const int sensorPin = 4;
bool isPlaying = false;

float duration, distance;

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

void setup() {
  pinMode(sensorPin, INPUT);
  Serial.begin(9600);
}

void loop() {
  int reading = digitalRead(sensorPin);

  // duration = pulseIn(echoPin, HIGH);
  // distance = (duration*.0343)/2;

  Serial.println("" + reading);
  if (reading == 0) {
    if (!isPlaying) {
      Serial.println("Sending note on");
      noteOn(0, 48, 64);   // Channel 0, middle C, normal velocity
      MidiUSB.flush();
      isPlaying = true;
      delay(50);
    }
  }
  else {
    Serial.println("Sending note off");
    noteOff(0, 48, 64);  // Channel 0, middle C, normal velocity
    MidiUSB.flush();
    isPlaying = false;
    delay(50);
  }

  // Serial.print("Distance: ");
  // Serial.println(distance);
  // delay(100);
}