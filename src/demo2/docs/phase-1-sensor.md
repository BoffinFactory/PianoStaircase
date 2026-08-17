# Phase 1: Raspberry Pi and VL53L0X Setup

This phase sets up the Raspberry Pi software environment and connects a VL53L0X time-of-flight
distance sensor.

The goal is to reach a known-good starting point before adding lights, audio, or other hardware.

## What You Are Building

The VL53L0X is a small distance sensor. It measures approximately how far away an object is by
emitting infrared light and measuring its return.

The Raspberry Pi communicates with the sensor using **I2C**, a common protocol for connecting small
electronic devices to a computer or microcontroller.

For this demo, the connection is:

```text
Raspberry Pi Zero 2 W
        |
        | I2C
        |
     VL53L0X
        |
        +---- distance measurement
```

The sensor normally appears on the I2C bus at address:

```text
0x29
```

## Hardware Used

This setup was tested with:

- Raspberry Pi Zero 2 W
- Raspberry Pi OS Lite 64-bit
- VL53L0X time-of-flight sensor
- breadboard and jumper wires

The same software should work with many other Raspberry Pi models.

## Wiring

Connect the sensor as follows:

| Raspberry Pi | Physical Pin | VL53L0X |
| --- | ---: | --- |
| 3.3 V | Pin 1 | VIN / VCC |
| Ground | Pin 6 | GND |
| GPIO2 / SDA1 | Pin 3 | SDA |
| GPIO3 / SCL1 | Pin 5 | SCL |

The two important I2C signals are:

**SDA** — carries data between the Raspberry Pi and sensor.

**SCL** — carries the clock signal that coordinates communication.

For this setup, power the sensor from the Raspberry Pi's 3.3 V supply.

## Install Raspberry Pi OS

Install the current 64-bit Raspberry Pi OS Lite image using Raspberry Pi Imager.

Raspberry Pi OS Lite does not include a graphical desktop. That keeps the installation small and
leaves more system resources available for the demo.

When configuring the image, it is useful to set:

- a hostname;
- username and password;
- Wi-Fi credentials;
- SSH access;
- the correct country and time zone.

After the Raspberry Pi starts, connect to it through SSH.

Update the operating system:

```bash
sudo apt update
sudo apt full-upgrade -y
```

Reboot if necessary:

```bash
sudo reboot
```

## Enable I2C

I2C must be enabled before Linux can communicate with the sensor.

Run:

```bash
sudo raspi-config
```

Choose:

```text
Interface Options -> I2C -> Enable
```

Exit `raspi-config` and reboot if requested.

You can check that Linux created the I2C device with:

```bash
ls /dev/i2c-*
```

The expected result is:

```text
/dev/i2c-1
```

## Run the Setup Script

From `src/demo2`:

```bash
./scripts/setup.sh
```

The script installs the Linux and Python packages needed for this phase and creates a Python virtual
environment.

## What Is a Python Virtual Environment?

A Python **virtual environment**, commonly shortened to **venv**, is an isolated place where a
project can install its Python packages.

Without a virtual environment, installing a Python library can modify packages used by the entire
operating system.

For example, the Piano Staircase requires libraries from Adafruit for communicating with hardware.
Another project on the same Raspberry Pi might require different versions of those libraries.

A virtual environment keeps the Piano Staircase dependencies separate:

```text
Raspberry Pi OS Python
│
├── operating-system Python packages
│
└── ~/.venv/piano-demo/
    ├── Adafruit Blinka
    ├── VL53L0X library
    └── other Piano Staircase dependencies
```

The environment used by this project is:

```text
~/.venv/piano-demo
```

Activate it with:

```bash
source ~/.venv/piano-demo/bin/activate
```

Your shell prompt will normally change to include:

```text
(piano-demo)
```

To leave the environment later, run:

```bash
deactivate
```

## Why `--system-site-packages` Is Used

Most Python packages for this project live inside the virtual environment.

One exception is `lgpio`.

`lgpio` provides low-level access to Raspberry Pi GPIO hardware. Raspberry Pi OS provides a
compatible version as the Linux package:

```text
python3-lgpio
```

The project therefore creates its virtual environment with:

```bash
python3 -m venv --system-site-packages ~/.venv/piano-demo
```

The `--system-site-packages` option allows the virtual environment to use Python modules installed
by Raspberry Pi OS in addition to its own packages.

This avoids compiling `lgpio` manually and worked reliably on the tested Raspberry Pi OS Trixie /
Python 3.13 installation.

## Python Libraries

The setup installs two main Python packages for the sensor:

### Adafruit Blinka

```text
adafruit-blinka
```

Blinka provides CircuitPython-style hardware APIs on Linux computers such as the Raspberry Pi.

It allows Python programs to use familiar modules such as:

```python
import board
import busio
```

### VL53L0X CircuitPython Library

```text
adafruit-circuitpython-vl53l0x
```

This library contains the Python driver used to communicate with the VL53L0X.

It allows the demo to create a sensor object and read distances using code such as:

```python
sensor.range
```

## Check the I2C Connection

After wiring the sensor, run:

```bash
i2cdetect -y 1
```

A working VL53L0X should appear as `29`:

```text
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- 29 -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- --
```

If `29` does not appear, check the wiring before debugging the Python code.

In particular, verify:

```text
3.3 V -> VIN
GND   -> GND
SDA   -> SDA
SCL   -> SCL
```

## Test Distance Measurements

Activate the virtual environment:

```bash
source ~/.venv/piano-demo/bin/activate
```

Then run:

```bash
python scripts/test_vl53l0x.py
```

You should see output similar to:

```text
=== VL53L0X Range Diagnostic ===
Sensor initialized successfully.

 842 mm
 611 mm
 393 mm
 215 mm
```

Move your hand or another object toward and away from the sensor.

The values should change accordingly.

Press:

```text
Ctrl+C
```

to stop.

## Expected Range

In the default configuration, the VL53L0X is intended primarily for relatively short-range
measurements.

During testing for this demo, readings stopped increasing at approximately:

```text
1250 mm
```

or about:

```text
1.25 meters
```

This is sufficient for the current demonstration.

Longer-range configurations are possible, but they are not needed for Phase 1.

## Phase 1 Is Complete When

Phase 1 has been successfully reproduced when:

```text
/dev/i2c-1 exists
        ↓
i2cdetect reports 0x29
        ↓
Python hardware libraries import successfully
        ↓
test_vl53l0x.py reports changing distances
```

Once all four checks pass, the sensor hardware and basic Raspberry Pi software environment can be
considered working.
