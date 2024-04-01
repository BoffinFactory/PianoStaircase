# `./src/`

This folder has a bunch of random demo code from various places (I did not actually write any of this code).

In no particular order: 

### Linux pre-requisite programs

* `fluidsynth/` has some scripts that ended up being useless.  Just install `fluidsynth` and be done with it.
  * Seems to also come with `qsynth`

### Examples

* `midi-7button-example/` has an example Arduino midi USB library with 7 buttons (not tested fully with the above yet)
* `picopi-midi-example/` has an example Raspberry Pi Pico setup with all required libraries.  Requires a specific 
  pi-pico hat with a 4x4 key matrix (working with the above setup)

### Setup

1. `sudo apt install fluidsynth qjackctl` for Linux, or `brew install fluidsynth qjackctl` for Mac OS
2. Run `test-boot.sh`
    - `./test-boot.sh`
3. Power cycle Pico/[Whatever it will end up being].
4. If no output, run `test-boot.sh` again
