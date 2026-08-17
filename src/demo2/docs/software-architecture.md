# Demo 2 Software Architecture

Demo 2 separates reusable application code from diagnostic scripts.

The current structure is:

```text
src/demo2/
├── piano_staircase_demo/
│   ├── __init__.py
│   └── lighting.py
├── scripts/
│   ├── setup.sh
│   ├── test_led_channel.py
│   ├── test_led_channels.py
│   └── test_vl53l0x.py
├── pyproject.toml
└── requirements.txt
````

## Reusable Code vs. Diagnostic Scripts

The `piano_staircase_demo` package contains code intended to be reused by the complete
demonstration.

For example:

```python
from piano_staircase_demo.lighting import LightingSystem
```

allows another part of the program to control the lights without needing to know the underlying GPIO
or PWM implementation.

The `scripts` directory contains small diagnostic programs.

Diagnostics are intentionally kept separate from the application code so that individual hardware
subsystems can be tested independently.

Conceptually:

```text
diagnostic or application
          |
          v
piano_staircase_demo
          |
          v
hardware libraries
          |
          v
Raspberry Pi GPIO
```

## The Lighting Abstraction

`lighting.py` provides two main classes.

### `LightingChannel`

A `LightingChannel` represents one physical lighting channel.

It handles:

* PWM configuration;
* brightness percentages;
* fading;
* turning the channel off;
* releasing its GPIO resource.

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

## Resource Cleanup

GPIO and PWM resources should be released when the program exits.

`LightingSystem` can therefore be used as a Python context manager:

```python
with LightingSystem() as lights:
    lights.green.set_brightness(100)
```

When the `with` block ends, the lighting system turns the channels off and releases their PWM
resources.

This also occurs if an exception causes the block to exit unexpectedly.

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
```

take effect without reinstalling the package after every edit.

## Why Use This Structure?

The goal is to keep different responsibilities separate:

```text
lighting.py
    knows how the lighting hardware works

test_led_channels.py
    knows how to test the lighting hardware

future demo application
    knows when and why the lights should animate
```

As additional subsystems are developed, the package may grow to include modules such as:

```text
piano_staircase_demo/
├── lighting.py
├── sensor.py
├── audio.py
└── ...
```

Each subsystem should first be independently testable before it is integrated into the complete
demonstration.
