# Piano Staircase Demo 2

This directory contains the second Piano Staircase demonstration system.

Unlike the original proof of concept in `src/demo1/`, this version is being built as a reproducible
example that future students should be able to install, test, understand, and modify.

The demo is being developed in phases. Each phase adds one working subsystem and includes
documentation and diagnostic tools before the next subsystem is added.

## Current Phase

### Phase 3 — Three-Channel Lighting

Phase 1 established the Raspberry Pi software environment and VL53L0X distance sensing.

Phase 2 established a transistor-controlled LED channel and PWM brightness control.

Phase 3 expands the lighting system into three independently controlled channels:

- green — GPIO17 / physical pin 11;
- yellow — GPIO27 / physical pin 13;
- blue — GPIO22 / physical pin 15.

All three channels have been independently tested and successfully operated together using PWM.

See:

- [Phase 1: Raspberry Pi and VL53L0X Setup](docs/phase-1-sensor.md)
- [Single LED Lighting Channel](docs/led-channel.md)
- [Three-Channel Lighting System](docs/three-channel-lighting.md)

## Hardware Documentation

Before modifying hardware, read:

- [Raspberry Pi Hardware Safety](docs/hardware-safety.md)
- [Breadboard Wiring Conventions](docs/breadboard-wiring.md)

Lighting documentation:

- [Single LED Lighting Channel](docs/led-channel.md)

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

After wiring the VL53L0X sensor, check that the Raspberry Pi can see it:

```bash
i2cdetect -y 1
```

A working sensor should appear at I2C address `0x29`.

Finally, test live ranging:

```bash
source ~/.venv/piano-demo/bin/activate
python scripts/test_vl53l0x.py
```

Move an object toward and away from the sensor. The displayed distance should change.

Press `Ctrl+C` to stop the diagnostic.

## Development Approach

Each subsystem should be developed using the same process:

```text
build -> test -> document -> automate -> integrate
```

A subsystem should have a simple diagnostic test before it is incorporated into the complete demo.
This makes hardware problems easier to isolate and gives future students small working examples they
can study independently.
