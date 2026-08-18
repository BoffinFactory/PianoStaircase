# Demo 2 Software Architecture

Demo 2 separates reusable application code from diagnostic scripts.

The current structure is:

```text
src/demo2/
├── piano_staircase_demo/
│   ├── __init__.py
│   ├── audio.py
│   ├── interaction.py
│   ├── lighting.py
│   ├── sensor.py
│   └── trigger.py
├── scripts/
│   ├── setup.sh
│   ├── test_audio.py
│   ├── test_audio_lighting.py
│   ├── test_interaction_gate.py
│   ├── test_led_channel.py
│   ├── test_led_channels.py
│   ├── test_sensor_interaction.py
│   ├── test_sensor_trigger.py
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

This allows lighting, sensing, or other application behavior to continue while audio is playing.

The application can later use:

```python
audio.wait()
```

to wait for playback to finish, or:

```python
audio.stop()
```

to stop it early.

`AudioSystem` also reports whether non-blocking playback is currently active:

```python
audio.is_playing
```

This allows higher-level application code to avoid starting overlapping playback operations.

## The Distance Sensor Abstraction

`sensor.py` provides `DistanceSensor`, which hides the I2C and VL53L0X implementation details from
higher-level application code.

Application code reads:

```python
distance_mm = sensor.distance_mm
```

rather than communicating directly with the Adafruit VL53L0X driver.

A valid measurement is returned as an integer number of millimeters.

Sensor readings that are not usable by the application are returned as:

```python
None
```

This keeps sensor-specific behavior at the hardware abstraction boundary instead of requiring every
application or diagnostic to understand individual VL53L0X result values.

For example:

```python
distance_mm = sensor.distance_mm

if distance_mm is None:
    # Ignore this sample.
    ...
```

`DistanceSensor` also manages the I2C interface used by the sensor and releases that interface when
the sensor is closed.

## The Distance Trigger Abstraction

`trigger.py` provides `DistanceTrigger`.

`DistanceTrigger` converts distance measurements into one-shot proximity events.

It contains no Raspberry Pi, I2C, or VL53L0X-specific code. This allows the trigger behavior to be
tested independently from the physical sensor.

The trigger uses:

- a trigger-distance threshold;
- a separate rearm-distance threshold;
- a configurable number of consecutive trigger samples; and
- a configurable number of consecutive rearm samples.

Using separate trigger and rearm thresholds provides hysteresis.

Conceptually:

```text
ARMED
  |
  | confirmed close measurement
  v
TRIGGER
  |
  v
DISARMED
  |
  | confirmed clear measurement
  v
ARMED
```

While armed, measurements at or below the trigger threshold count toward a trigger.

After a confirmed trigger, the object must move beyond the higher rearm threshold before another
trigger can occur.

This prevents small distance fluctuations near a single boundary from repeatedly activating the
demonstration.

The consecutive-sample counts allow additional filtering when needed. A value of one provides the
fastest response, while larger values can reject brief or noisy measurements.

## The Interaction Gate

`interaction.py` provides `CooldownGate`.

The sensor and trigger logic are intentionally allowed to remain responsive even when users interact
very rapidly.

The cooldown gate independently limits how often detected physical interactions may become
application actions.

Conceptually:

```text
sensor measurement
       |
       v
DistanceTrigger
       |
       v
physical interaction
       |
       v
CooldownGate
   |       |
   v       v
ACCEPT    DROP
```

An accepted interaction records the current monotonic time.

Additional interactions that arrive before the configured minimum interval has elapsed are rejected.

This places an upper bound on downstream work without deliberately slowing sensor detection.

The distinction is important:

```text
DistanceTrigger
    asks:
    "Did a physical interaction occur?"

CooldownGate
    asks:
    "Should the application act on it right now?"
```

For example, a user may wave a hand through the sensor rapidly enough to create several valid
physical interactions. The sensor should continue detecting those interactions promptly even if the
application deliberately drops some of them to protect audio playback or other resources.

## Resource Cleanup

GPIO, PWM, I2C interfaces, audio playback processes, and temporary files should be cleaned up when
the program exits.

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

`DistanceSensor` is also a context manager:

```python
with DistanceSensor() as sensor:
    distance_mm = sensor.distance_mm
```

When the block ends, the I2C interface used by the sensor is released.

Context managers also provide cleanup when an exception causes a block to exit unexpectedly.

Hardware-facing programs should prefer graceful shutdown between sensor operations rather than
interrupting an I2C transaction in progress.

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
piano_staircase_demo/audio.py
piano_staircase_demo/interaction.py
piano_staircase_demo/lighting.py
piano_staircase_demo/sensor.py
piano_staircase_demo/trigger.py
```

take effect without reinstalling the package after every edit.

## Current Subsystem Boundaries

The reusable package currently separates five major responsibilities.

### Lighting

```text
application or diagnostic
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

### Audio

```text
application or diagnostic
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

### Distance Measurement

```text
application or diagnostic
          |
          v
DistanceSensor
          |
          v
Adafruit VL53L0X library
          |
          v
I2C
          |
          v
VL53L0X sensor
```

### Trigger Detection

```text
distance measurement
          |
          v
DistanceTrigger
          |
          v
one-shot physical interaction
```

### Interaction Rate Control

```text
physical interaction
          |
          v
CooldownGate
     |         |
     v         v
  ACCEPT      DROP
```

The diagnostic scripts know how to exercise these subsystems.

The reusable modules know how to perform their individual responsibilities.

The complete demonstration will decide how accepted interactions should coordinate the lighting and
audio systems.

## Integrated Interaction Path

The sensor-side interaction path has now been assembled and independently validated.

Conceptually:

```text
VL53L0X
   |
   v
DistanceSensor
   |
   v
DistanceTrigger
   |
   v
CooldownGate
   |
   v
accepted interaction
   |
   +----------------+
   |                |
   v                v
lighting           audio
```

Each layer has a separate responsibility:

```text
sensor.py
    knows how to obtain a usable distance measurement

trigger.py
    knows when distance measurements represent one physical interaction

interaction.py
    knows whether an interaction should be accepted at the current rate

lighting.py
    knows how to control the lighting hardware

audio.py
    knows how to generate and play audio

demo application
    decides which light and sound response an accepted interaction should produce
```

The current sensor-interaction diagnostic validates the path through `CooldownGate` without starting
lighting or audio.

This allows sensing, trigger behavior, and rate limiting to be tested without introducing additional
hardware or operating-system variables.

The next integration stage can use the same accepted interaction events to drive synchronized light
and sound responses.

## Why Use This Structure?

The goal is to keep different responsibilities separate.

A low-level hardware module should not need to know the rules of the complete demonstration.

Likewise, higher-level application logic should not need to manipulate GPIO registers, I2C
transactions, PWM duty cycles, or PipeWire subprocesses directly.

Conceptually:

```text
sensor.py
    knows how the distance sensor works

trigger.py
    knows how distance becomes a one-shot interaction

interaction.py
    knows how frequently actions may occur

lighting.py
    knows how the lighting hardware works

audio.py
    knows how audio clips are generated and played

diagnostic scripts
    know how to test individual pieces

demo application
    knows when and why those pieces should operate together
```

This structure provides several advantages:

- individual subsystems can be tested independently;
- hardware-specific behavior remains localized;
- interaction policies can be tested without Raspberry Pi hardware;
- failures are easier to isolate;
- future students can study smaller working examples before reading the complete application; and
- hardware or behavior can be changed without unnecessarily rewriting unrelated subsystems.

Each subsystem should first be independently testable before it is integrated into the complete
demonstration.
