# Piano Staircase Demo 2

This directory contains the second Piano Staircase demonstration system.

Unlike the original proof of concept in `src/demo1/`, this version is being built as a reproducible
example that future students should be able to install, test, understand, and modify.

The demo is being developed in phases. Each phase adds one working subsystem and includes
documentation and diagnostic tools before the next subsystem is added.

## Current Status

### Phase 1 — Raspberry Pi and Distance Sensor — Complete

Phase 1 established the basic Raspberry Pi development environment and validated the VL53L0X
time-of-flight distance sensor.

This phase included:

- preparing Raspberry Pi OS Lite for the demo;
- enabling and testing I2C;
- creating the Python virtual environment;
- installing the Raspberry Pi GPIO and Adafruit sensor libraries;
- wiring the VL53L0X sensor; and
- validating live distance measurements from Python.

The VL53L0X is connected over I2C and normally appears at address `0x29`.

See:

- [Phase 1: Raspberry Pi and VL53L0X Setup](docs/phase-1-sensor.md)
- [Raspberry Pi Hardware Safety](docs/hardware-safety.md)
- [Breadboard Wiring Conventions](docs/breadboard-wiring.md)

### Phase 2 — Single-Channel Lighting — Complete

Phase 2 established the basic lighting circuit used by the tabletop staircase.

A Raspberry Pi GPIO pin controls an LED through a transistor rather than driving the LED load
directly. The circuit includes:

- a 2N2222 NPN transistor used as a low-side switch;
- a resistor limiting LED current;
- a resistor limiting transistor base current;
- a base pull-down resistor to keep the channel off when the GPIO is not actively driven; and
- PWM brightness control from Python.

The completed circuit demonstrated reliable GPIO switching, brightness control, and fades.

See:

- [Single LED Lighting Channel](docs/led-channel.md)
- [Raspberry Pi Hardware Safety](docs/hardware-safety.md)
- [Breadboard Wiring Conventions](docs/breadboard-wiring.md)

### Phase 3 — Three-Channel Lighting — Complete

Phase 3 expanded the single lighting circuit into three independently controlled channels:

- green — GPIO17 / physical pin 11;
- yellow — GPIO27 / physical pin 13;
- blue — GPIO22 / physical pin 15.

Each channel uses the transistor-controlled circuit developed during Phase 2.

All three channels have been independently tested and successfully operated together using PWM.

The lighting subsystem is implemented as reusable Python package code and has been validated against
the complete three-channel breadboard circuit.

See:

- [Three-Channel Lighting System](docs/three-channel-lighting.md)
- [Software Architecture](docs/software-architecture.md)

### Phase 4 — Audio — In Progress

Phase 4 adds musical audio output to the tabletop demonstration and will eventually synchronize
audio with the three lighting channels.

Basic C4-E4-G4 tone generation and PipeWire playback have been successfully tested.

The following output methods have been evaluated:

- HDMI audio through the portable display;
- USB audio through a Framework Audio Expansion Card and 3.5 mm connection; and
- Bluetooth audio through an Anker SoundCore 2.

The application uses the current PipeWire default audio sink rather than depending on a particular
physical audio device.

HDMI playback is clean but the portable display speakers are too quiet for the tabletop
demonstration. The wired USB/3.5 mm path provides sufficient volume but requires additional cabling.
Bluetooth provides sufficient volume and is currently convenient for development.

An intermittent startup crackling problem has been observed with Bluetooth audio on the Raspberry Pi
Zero 2 W. Testing indicates that the problem is specific to the Bluetooth path rather than the
generated audio or general PipeWire playback. Cycling Wi-Fi off and back on cleared the problem
during one test, after which Bluetooth audio continued to work normally with Wi-Fi enabled. The
behavior will be investigated further before the final demonstration audio transport is selected.

See:

- [Audio System](docs/audio.md)
- [Software Architecture](docs/software-architecture.md)

## Hardware Documentation

Before modifying hardware, read:

- [Raspberry Pi Hardware Safety](docs/hardware-safety.md)
- [Breadboard Wiring Conventions](docs/breadboard-wiring.md)

Sensor and integrated hardware documentation:

- [Phase 1: Raspberry Pi and VL53L0X Setup](docs/phase-1-sensor.md)
- [Demo 2 Integrated Breadboard Wiring](docs/integrated-breadboard.md)

Lighting documentation:

- [Single LED Lighting Channel](docs/led-channel.md)
- [Three-Channel Lighting System](docs/three-channel-lighting.md)

## Software Documentation

- [Software Architecture](docs/software-architecture.md)
- [Audio System](docs/audio.md)

Reusable application code is located in the `piano_staircase_demo` Python package. Diagnostic and
setup utilities are kept separately in `scripts/`.

## Quick Start

The current setup was tested on:

- Raspberry Pi Zero 2 W
- Raspberry Pi OS Lite 64-bit
- Debian 13 (Trixie)
- Python 3.13

After installing Raspberry Pi OS, enable I2C:

```bash
sudo raspi-config
```

Choose:

```text
Interface Options -> I2C -> Enable
```

Then, from this directory, run:

```bash
./scripts/setup.sh
```

Activate the Python environment with:

```bash
source ~/.venv/piano-demo/bin/activate
```

### Test the Distance Sensor

After wiring the VL53L0X sensor, check that the Raspberry Pi can see it:

```bash
i2cdetect -y 1
```

A working sensor should appear at I2C address `0x29`.

Test live ranging with:

```bash
./scripts/test_vl53l0x.py
```

Move an object toward and away from the sensor. The displayed distance should change.

Press `Ctrl+C` to stop the diagnostic.

### Test the Lighting System

After assembling the documented three-channel lighting circuit, run:

```bash
./scripts/test_led_channels.py
```

The diagnostic exercises each lighting channel independently and then demonstrates coordinated
brightness changes and fades.

See [Three-Channel Lighting System](docs/three-channel-lighting.md) for wiring and GPIO assignments.

### Test Audio

To test musical audio through the current PipeWire default output:

```bash
./scripts/test_audio.py
```

The diagnostic generates and plays a repeating C4-E4-G4 sequence.

Use:

```bash
wpctl status
```

to inspect the available PipeWire audio sinks and identify the current default output.

To change the default output:

```bash
wpctl set-default <sink-id>
```

PipeWire sink IDs may change between boots or device reconnections and should not be hard-coded into
the application.

See [Audio System](docs/audio.md) for tested output methods, PipeWire configuration, Bluetooth
setup, and current limitations.

## Development Approach

Each subsystem should be developed using the same process:

```text
build -> test -> document -> automate -> integrate
```

A subsystem should have a simple diagnostic test before it is incorporated into the complete demo.

This approach makes hardware and software problems easier to isolate and gives future students
small, working examples they can study independently.

Reusable application behavior belongs in the `piano_staircase_demo` package. Hardware diagnostics,
installation utilities, and other development tools belong in `scripts/`.

## AI-Assisted Development

The code and documentation for Demo 2 were developed with assistance from OpenAI ChatGPT under the
direction of project contributors.

ChatGPT was used to help draft code, documentation, explanations, and development procedures.
Project contributors reviewed the generated material, made implementation decisions, assembled and
inspected the hardware, and validated hardware-facing code on the intended Raspberry Pi system
before considering each subsystem complete.

AI-generated output should not be assumed correct solely because it appears in this repository. The
project's build-test-document-automate-integrate process is intended to ensure that generated
material is reviewed and validated before it becomes part of the completed demonstration.

## License

Unless otherwise noted, the code and documentation in `src/demo2/` are licensed under the MIT
License. See [LICENSE](LICENSE).

Third-party dependencies remain subject to their respective licenses.
