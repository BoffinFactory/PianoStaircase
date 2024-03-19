# `./src/`

This folder has a bunch of random demo code from various places (I did not actually write any of this code).

In no particular order: 

### Linux pre-requisite programs

* `fluidsynth/` has some scripts that ended up being useless.  Just install `fluidsynth` and be done with it.
  * Seems to also come with `qsynth`
* `qjackctl/` has the configuration image for the required `qjackctl` program.  May require more setup to get
  the right inputs and outputs shown...

### Examples

* `midi-7button-example/` has an example Arduino midi USB library with 7 buttons (not tested fully with the above yet)
* `picopi-midi-example/` has an example Raspberry Pi Pico setup with all required libraries.  Requires a specific 
  pi-pico hat with a 4x4 key matrix (working with the above setup)

### Setup

1. `sudo apt install fluidsynth qjackctl` for Linux, or `brew install fluidsynth qjackctl` for Mac OS
2. Start and config qjackctl per below (might need fluidsynth running first)
  ![qjackctl](./qjackctl/qjackctl.png)
    * may need to restart qjackctl
3. Start fluidsynth and configure a sound
4. Make sure to have a soundfont installed
5. Run `qsynth`
6. Open `setup`
    * Enable MIDI output
    * Set MIDI driver to be `jack`
7. Switch to `Audio` tab
    * Set audio driver to be `jack`
8. Go to Soundfonts tab
    * Click `Open` and select your soundfont
9. Click `Okay` and then `Yes` 
10. Open `qjackctl`
    * Click `Graph`
11. You should see `Midi-Bridge` and `qsynth` blocks with red bubbles
12. Drag from the red `pico-2` bubble on the `Midi-Bridge` block to the midi_00 bubble in the `qsynth` one
