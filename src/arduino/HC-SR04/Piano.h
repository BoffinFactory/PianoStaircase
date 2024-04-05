int states[sizeof(stepPitches) / sizeof(stepPitches[0])];

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

// A function that stops a particular note
// Args:
//  note (int): integer value of a note from PitchToNote.h
//
// Outputs:
//  Uses USBMIDI to stop provided note
void stopNote(int note) {
  Serial.print("Stopping Note: ");
  Serial.print(note);
  Serial.println();
  noteOff(0, note, 64);
  MidiUSB.flush();
}

// A function that starts a particular note
// Args:
//  note (int): integer value of a note from PitchToNote.h
//
// Outputs:
//  Uses USBMIDI to start provided note
void startNote(int note) {
  Serial.print("Starting Note: ");
  Serial.print(note);
  Serial.println();
  noteOn(0, note, 64);
  MidiUSB.flush();
}

// A function that converts an note integer value to a key reference value
// Args:
//  note (int): integer value of a note from PitchToNote.h
//
//  Outputs:
//  key (int): key value of provided note
int getNoteKeyValue(int note) {
  for(int i = 0; i < sizeof(stepPitches) / sizeof(stepPitches[0]); i++) {
    if(note == stepPitches[i]) {
      return i;
    }
  }
}

// A function that changes the state of a particular note
// Args:
//  note (int): integer value of a note from PitchToNote.h
//
// Outputs:
//  Change state of note through USBMIDI and set state
void changeState(int note, bool state) {
  int noteKeyValue = getNoteKeyValue(note);

  if(states[noteKeyValue] == 0 && state == 1) {
    startNote(note);
    states[noteKeyValue] = 1;
  }

  else if(states[noteKeyValue] == 1 && state == 0) {
    stopNote(note);
    states[noteKeyValue] = 0;
  }
}