# Demo 2 Software Architecture

Demo 2 separates reusable application code from diagnostic scripts.

The current structure is:

```text
src/demo2/
├── piano_staircase_demo/
│   ├── __init__.py
│   ├── audio.py
│   └── lighting.py
├── scripts/
│   ├── setup.sh
│   ├── test_audio.py
│   ├── test_led_channel.py
│   ├── test_led_channels.py
│   └── test_vl53l0x.py
├── pyproject.toml
└── requirements.txt
```

## Reusable Code vs. Diagnostic Scripts

The `piano_staircase_demo` package contains code intended to be reused by the complete
demonstration.

For example:

```python
from piano_staircase_demo.lighting import LightingSystem
```

allows another part of the program to control the lights without needing to know the underlying GPIO
or PWM implementation.

Similarly:

```python
from piano_staircase_demo.audio import AudioSystem
```

allows the application to generate and play musical sequences without needing to know which physical
audio device is being used.

The `scripts` directory contains small diagnostic programs.

Diagnostics are intentionally kept separate from the reusable application code so that individual
hardware and software subsystems can be tested independently.

Conceptually:

```text
diagnostic or application
          |
          v
piano_staircase_demo
          |
          v
hardware or system libraries
          |
          v
Raspberry Pi hardware / operating system
```

## The Lighting Abstraction

`lighting.py` provides two main classes.

### `LightingChannel`

A `LightingChannel` represents one physical lighting channel.

It handles:

- PWM configuration;
- brightness percentages;
- fading;
- turning the channel off; and
- releasing its GPIO resource.

Instead of application code manipulating raw PWM duty-cycle values:

```python
pwm.duty_cycle = 49151
```

it can use:

```python
lights.green.set_brightness(75)
```

This keeps hardware-specific details out of higher-level application logic.

### `LightingSystem`

`LightingSystem` represents the three lighting channels used by Demo 2:

```text
green  -> GPIO17 / physical pin 11
yellow -> GPIO27 / physical pin 13
blue   -> GPIO22 / physical pin 15
```

It provides named access to the channels:

```python
lights.green
lights.yellow
lights.blue
```

and operations that apply to the complete lighting system.

## The Audio Abstraction

`audio.py` provides reusable audio generation and playback without depending on a particular
physical audio output.

Application code does not need to know whether audio is being sent through HDMI, USB/3.5 mm, or
Bluetooth. Audio is sent to the current PipeWire default sink.

### `AudioClip`

An `AudioClip` represents generated audio that is ready for playback.

It stores:

- the path to the generated WAV file; and
- the approximate duration of the clip.

Separating clip generation from playback allows the complete demonstration to generate commonly used
sounds during startup and reuse them whenever the sensor is triggered.

This avoids unnecessarily regenerating the same audio during every interaction.

### `AudioSystem`

`AudioSystem` generates musical sequences and plays them through PipeWire.

For example:

```python
with AudioSystem() as audio:
    sequence = audio.create_sequence(("C4", "E4", "G4"))
    audio.play(sequence)
```

A complete sequence is generated as one continuous WAV file rather than launching a separate
playback stream for every note.

This simplifies playback and also avoids creating and destroying multiple PipeWire streams during a
single musical sequence.

`AudioSystem` supports both blocking and non-blocking playback.

Blocking playback waits until the clip finishes:

```python
audio.play(sequence)
```

Non-blocking playback returns immediately:

```python
audio.play(sequence, blocking=False)
```

This allows lighting or other application behavior to run while audio is playing.

The application can later use:

```python
audio.wait()
```

to wait for playback to finish, or:

```python
audio.stop()
```

to stop it early.

This non-blocking behavior will be important when the lighting and audio subsystems are
synchronized.

## Resource Cleanup

GPIO, PWM, audio playback processes, and temporary files should be cleaned up when the program
exits.

`LightingSystem` can therefore be used as a Python context manager:

```python
with LightingSystem() as lights:
    lights.green.set_brightness(100)
```

When the `with` block ends, the lighting system turns the channels off and releases their PWM
resources.

`AudioSystem` provides the same pattern:

```python
with AudioSystem() as audio:
    sequence = audio.create_sequence(("C4", "E4", "G4"))
    audio.play(sequence)
```

When the block ends, active playback is stopped if necessary and generated temporary audio files are
removed.

Context managers also provide cleanup when an exception causes a block to exit unexpectedly.

## Python Package

The reusable code is stored in the Python package:

```text
piano_staircase_demo
```

The package is described by `pyproject.toml`.

During development, `setup.sh` installs the package into the project's virtual environment in
**editable mode**:

```bash
python -m pip install -e .
```

An editable installation lets Python import the package normally while still using the source files
directly from the repository.

This means changes to files such as:

```text
piano_staircase_demo/lighting.py
piano_staircase_demo/audio.py
```

take effect without reinstalling the package after every edit.

## Current Subsystem Boundaries

The current reusable package contains lighting and audio abstractions.

Conceptually:

```text
test_led_channels.py
        |
        v
LightingSystem
        |
        v
PWM / GPIO
        |
        v
lighting circuit
```

and:

```text
test_audio.py
      |
      v
AudioSystem
      |
      v
PipeWire
      |
      v
default audio output
```

The diagnostic scripts know how to exercise each subsystem.

The reusable modules know how to control each subsystem.

The future complete demonstration will decide **when and why** those subsystems should operate.

For example:

```text
sensor detects visitor
        |
        v
demo application
   |           |
   v           v
lighting      audio
system        system
```

This keeps interaction logic separate from low-level hardware and operating-system details.

## Future Sensor Abstraction

The VL53L0X distance sensor has already been independently validated, but reusable sensor behavior
has not yet been moved into the `piano_staircase_demo` package.

During Phase 1, the sensor was connected directly to the Raspberry Pi header so that it could be
tested independently.

During integrated assembly, the sensor will instead be incorporated into the organized breadboard
wiring alongside the lighting circuitry.

After that integrated hardware arrangement has been assembled and validated, reusable sensor
behavior can be moved into a module such as:

```text
piano_staircase_demo/sensor.py
```

The exact integrated breadboard layout should be documented only after the physical wiring has been
built and tested.

## Why Use This Structure?

The goal is to keep different responsibilities separate:

```text
lighting.py
    knows how the lighting hardware works

audio.py
    knows how audio clips are generated and played

test_led_channels.py
    knows how to test the lighting subsystem

test_audio.py
    knows how to test the audio subsystem

future demo application
    knows when and why the subsystems should operate
```

As additional subsystems are developed, the package may grow to include modules such as:

```text
piano_staircase_demo/
├── audio.py
├── lighting.py
├── sensor.py
└── ...
```

The current audio and lighting modules provide reusable abstractions for subsystems that have
already been independently validated.

Each subsystem should first be independently testable before it is integrated into the complete
demonstration.
