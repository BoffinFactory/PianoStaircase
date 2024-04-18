# [Piano Staircase](https://boffinfactory.github.io/PianoStaircase/)

The Build Boffin Back Better project.

Table of contents:

* [Intent](README.md#intent)
* [Outline](README.md#outline)
* [Getting Involved](README.md#getting-involved)
* [Student Impact](README.md#student-impact)
* 

## Intent

For starters, the intent of this `Intent` section is to give you some starter bragging verbage
for what any standard Boffin project is all about.

The Build Boffin Back Better Project, sponsored by the Wright State Foundation Student First Fund, 
was awarded to restart the “Boffin Factory” - an informal student learning space that fosters 
creativity and communication by providing students with a room of tools to tackle extensions of 
themes learned in their coursework and personal projects that allow them to expression their 
passion for topics in their engineering field.

Building a piano staircase with peers offers a multifaceted learning experience for students in 
engineering and computer science. Firstly, it provides a hands-on application of engineering 
principles as they design the device to the conforms of the Russ Engineering staircase, 
incorporating elements such as safety, physical implementation and mounting of sensors, and 
mechanical engineering aspects of measurement and layout design. 

Additionally, integrating sensors and programming to transform steps into musical notes involves 
electrical and computer science concepts like sensor technology, data processing, and software development. 
Collaboration with peers fosters communication and teamwork skills essential in professional 
environments. Troubleshooting challenges throughout the project cultivates problem-solving 
abilities and adaptability, crucial traits in both engineering and computer science careers. 
Overall, this project amalgamates practical skills with theoretical knowledge, preparing 
students for the interdisciplinary demands of the modern workforce.

## Outline

The goal of this project is very simple, we will detect a footstep on a stair and play a corresponding musical note.

End result, a piano staircase (whee)!

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/ExmJZJlXsKg/0.jpg)](https://www.youtube.com/watch?v=ExmJZJlXsKg)

In order to play the note like in the video above we are using the following logical flow:

1. Sensor (? 2 options here) detects foot step -> 
2. Arduino reads the sensor footstep trigger and sends a MIDI event via USB cable -> 
3. Raspberry Pi recieves the MIDI event and sends it to a software synthesizer (via `a2jmidi`) -> 
4. `fluidsynth` recieves the event and plays the corresponding note

Hardware we will be using include the following:

* [Arduino](src/arduino)
* [Raspberry Pi](src/raspi/README.md)
* [Ultrasonic Distance Sensor: HC-SR04]() low cost /  option 1, not the best though interference and accuracy wise
* [Time of Flight (ToF) sensor: VL53L0X]() higher cost  / option 2, needs I2C knowledge and uses lots of arduino resources
* Various audio amplification and speaker equipment
* Breadboards! and wires! and all other cool electrcial things that Boffin has to offer!

Software we will using include the following:

* [Arduino IDE](https://www.arduino.cc/en/software) for developing for the arduino
  * [Arduino MIDI-USB library](https://www.arduino.cc/reference/en/libraries/midiusb/) for creating MIDI events on the arduino
  * [Arduino Adafruit_VL53L0x library](https://github.com/adafruit/Adafruit_VL53L0X) for interacting with the Time of Flight sensors
* Raspberry Pi OS (debian/ubuntu based linux distro for Pi), a great low-cost linux computer
  * [`fluidsynth`](https://github.com/FluidSynth/fluidsynth/wiki/FluidFeatures) for taking in MIDI events and making sounds
  * [`a2jmidi`](https://github.com/jackaudio/a2jmidid) for bridging our MIDI-USB arduino to our `fluidsynth` software synthesizer

## Getting Involved

In order to get involved you just need to check two things:

1. Check out our [`CONTRIBUTING.md`](./CONTRIBUTING.md) file to figure out how to 
  interact with the project and what our current focus points are.
2. Check out the [Issues page](https://github.com/BoffinFactory/PianoStaircase/issues)

Thats really it.  We have a ton of example source code and installation / config scripts in `./src/`
and there should be a few example setups floating around on the Boffin desk (table with record player).



