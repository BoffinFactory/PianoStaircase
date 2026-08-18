# Demo 2 Integrated Breadboard Wiring

Demo 2 uses a VL53L0X time-of-flight distance sensor connected to the Raspberry Pi Zero 2 W over
I2C.

The sensor was initially tested as an independent subsystem during Phase 1. It has now been
incorporated into the complete Demo 2 breadboard alongside the three-channel lighting system.

For the original sensor setup and software installation procedure, see [Phase 1: Raspberry Pi and
VL53L0X Setup](phase-1-sensor.md).

For general wiring practices, see [Breadboard Wiring Conventions](breadboard-wiring.md).

## Raspberry Pi Connections

The integrated sensor uses the same Raspberry Pi connections validated during Phase 1:

| Function      | Raspberry Pi | Physical Pin | Wire Color |
| ------------- | ------------ | -----------: | ---------- |
| Sensor power  | 3.3 V        |            1 | Orange     |
| SDA           | GPIO2 / SDA1 |            3 | Purple     |
| SCL           | GPIO3 / SCL1 |            5 | White      |
| Common ground | GND          |            6 | Black      |

The Raspberry Pi also provides the following connections for the lighting subsystem:

| Function       | Raspberry Pi | Physical Pin | Wire Color |
| -------------- | ------------ | -----------: | ---------- |
| Lighting power | +5 V         |            2 | Red        |
| Green channel  | GPIO17       |           11 | Green      |
| Yellow channel | GPIO27       |           13 | Yellow     |
| Blue channel   | GPIO22       |           15 | Blue       |

The sensor, lighting circuitry, and Raspberry Pi share a common ground.

## Sensor Connections

At the VL53L0X breakout board:

```text
VL53L0X             Connection

VIN   <--- orange --- +3.3 V
GND   <--- blue   --- common ground
SCL   <--- white  --- GPIO3 / SCL1
SDA   <--- purple --- GPIO2 / SDA1
```

The blue wire at the sensor is a local breadboard ground jumper. The Raspberry Pi ground connection
to the breadboard remains black, following the project's normal ground-wire convention.

The unused VL53L0X pins are not required for the current Demo 2 configuration.

These include:

```text
GPIO1
XSHUT
```

## Breadboard Power

The integrated breadboard contains separate supply voltages for the sensor and lighting circuitry.

```text
+3.3 V rail
    |
    +---- VL53L0X VIN

+5 V rail
    |
    +---- green lighting channel
    +---- yellow lighting channel
    +---- blue lighting channel
```

The +3.3 V and +5 V rails must remain distinct.

The VL53L0X used by this prototype is powered from the Raspberry Pi's 3.3 V supply.

The three prototype lighting channels use the Raspberry Pi's +5 V supply.

## I2C Communication

The VL53L0X communicates with the Raspberry Pi using I2C:

```text
Raspberry Pi                    VL53L0X

GPIO2 / SDA1  ----------------> SDA
GPIO3 / SCL1  ----------------> SCL
```

The sensor normally appears at I2C address:

```text
0x29
```

The connection can be checked with:

```bash
i2cdetect -y 1
```

A working sensor should show `29` in the I2C device table.

## Integrated Validation

The complete breadboard has been operated with the sensor and all three lighting channels connected
simultaneously.

The integrated configuration successfully supports:

* VL53L0X initialization;
* continuous distance measurements;
* green-channel PWM control;
* yellow-channel PWM control; and
* blue-channel PWM control.

This configuration is therefore the known-good integrated hardware arrangement for the next Demo 2
development stage.

## Future Connector Harness

The current prototype uses individual jumper connections between the Raspberry Pi and breadboard.

Once the hardware design and pin assignments are finalized, these connections may be replaced with a
keyed wiring harness or multi-pin connector.

A harness would provide several advantages:

* faster connection and disconnection;
* reduced strain on individual jumper wires;
* lower risk of connecting a wire to the wrong Raspberry Pi pin;
* lower risk of shifting a group of connections by one pin; and
* easier transport and assembly of the tabletop demonstration.

The connector type and final pin arrangement should not be selected until the prototype wiring has
stabilized.
