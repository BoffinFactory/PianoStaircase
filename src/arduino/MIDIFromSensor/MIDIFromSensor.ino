/*
 * The IR break beam is very fickle and current implementation is unreliable.
 * Adjust if(reading == 0) for new sensors. Code inside if statement sends MIDI
*/

#include "MIDIUSB.h"
#include "PitchToNote.h" //Variables defined in PitchToNote.h may have different names when downloading library

const int sensorPin = 4;
const int sens2Pin = 5;
bool isPlaying = false;

//Send MIDI note
void noteOn(byte channel, byte pitch, byte velocity) {
  midiEventPacket_t noteOn = {0x09, 0x90 | channel, pitch, velocity};
  MidiUSB.sendMIDI(noteOn);
}

//Send MIDI off for note
void noteOff(byte channel, byte pitch, byte velocity) {
  midiEventPacket_t noteOff = {0x08, 0x80 | channel, pitch, velocity};
  MidiUSB.sendMIDI(noteOff);
}

//I don't know what this method is
void controlChange(byte channel, byte control, byte value) {
  midiEventPacket_t event = {0x0B, 0xB0 | channel, control, value};
  MidiUSB.sendMIDI(event);
}

void setup() {
  pinMode(sensorPin, INPUT);
  pinMode(sens2Pin, INPUT);
  Serial.begin(9600);
}

void loop() {
  int reading = digitalRead(sensorPin);
  int reading2 = digitalRead(sens2Pin);

  //When IR break beam is broken, arduino reads digital 0;
  if (reading == 0) {
    if (!isPlaying) {
      Serial.println("Sending note on: C3");
      noteOn(0, C3, 90);   // Channel 0, note, normal velocity
      MidiUSB.flush();
      isPlaying = true;
      delay(50);
    }
  }
  else {
    Serial.println("Sending note off: C3");
    noteOff(0, C3, 90);  // Channel 0, note, normal velocity
    MidiUSB.flush();
    isPlaying = false;
    delay(50);
  }

  if (reading2 == 0) {
    if (!isPlaying) {
      Serial.println("Sending note on: D3");
      noteOn(0, D3, 90);   // Channel 0, note, normal velocity
      MidiUSB.flush();
      isPlaying = true;
      delay(50);
    }
  }
  else {
    Serial.println("Sending note off: D3");
    noteOff(0, D3, 90);  // Channel 0, note, normal velocity
    MidiUSB.flush();
    isPlaying = false;
    delay(50);
  }

}