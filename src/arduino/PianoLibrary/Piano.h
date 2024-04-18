// Integer array that holds values of current states
int states[sizeof(stepPitches) / sizeof(stepPitches[0])];

// A function to turn a MIDI note on with a USB event packet
// Args:
//  channel (byte): the channel to modify (default is usually zero)
//  pitch (byte): the pitch (note) to modify
//  velocity (byte): the velocity of the pitch (default is usually 64 for on)
//
// Outputs:
//  Sends a MIDI USB event with provided details
void noteOn(byte channel, byte pitch, byte velocity) {
  midiEventPacket_t noteOn = {0x09, 0x90 | channel, pitch, velocity};
  MidiUSB.sendMIDI(noteOn);
}

// A function to turn a MIDI note off with a USB event packet
// Args:
//  channel (byte): the channel to modify (default is usually zero)
//  pitch (byte): the pitch (note) to modify
//  velocity (byte): the velocity of the pitch (default is usually 0 for off)
//
// Outputs:
//  Sends a MIDI USB event with provided details
void noteOff(byte channel, byte pitch, byte velocity) {
  midiEventPacket_t noteOff = {0x08, 0x80 | channel, pitch, velocity};
  MidiUSB.sendMIDI(noteOff);
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