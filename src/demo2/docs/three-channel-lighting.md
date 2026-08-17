# Three-Channel Lighting System

Demo 2 uses three independently controlled lighting channels to represent the three steps of the
tabletop staircase.

Each channel is based on the single-transistor circuit described in
[Single LED Lighting Channel](led-channel.md).

The three channels are:

| Channel | GPIO | Physical Pin |
| --- | --- | ---: |
| Green | GPIO17 | 11 |
| Yellow | GPIO27 | 13 |
| Blue | GPIO22 | 15 |

The GPIO pins are intentionally adjacent on the same side of the Raspberry Pi header, which keeps
the prototype wiring easy to identify and trace.

For an official Raspberry Pi GPIO pinout and description, see:

<https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio>

## Repeated Channel Design

Each lighting channel uses the same basic circuit:

```text
+5 V
 |
330 Ω
 |
LED
 |
Collector
 |
2N2222
 |
Emitter
 |
GND

GPIO
 |
1 kΩ
 |
Base
 |
10 kΩ
 |
GND
```

The green, yellow, and blue channels therefore differ primarily in:

* LED color;
* GPIO assignment;
* signal-wire color.

Using repeated circuits makes the prototype easier to understand and debug.

If one channel behaves differently from the others, its wiring can be compared directly against a
known-good channel.

## GPIO Assignments

The three GPIO outputs are:

```text
GPIO17 / physical pin 11 -> green
GPIO27 / physical pin 13 -> yellow
GPIO22 / physical pin 15 -> blue
```

Physical pin numbers and GPIO numbers describe different things.

* **Physical pin numbers** identify positions on the Raspberry Pi's 40-pin connector.
* **GPIO numbers** identify digital signals provided by the Raspberry Pi processor.

For example:

```text
GPIO17 = physical pin 11
```

The software controls `GPIO17`, while a person wiring the circuit connects the jumper to physical
pin 11.

Documentation in this project gives both numbers where practical.

## Breadboard Layout

The three lighting circuits are arranged as repeated functional blocks.

Conceptually:

```text
          GREEN          YELLOW          BLUE

+5 V      330 Ω           330 Ω          330 Ω
            |               |              |
           LED             LED            LED
            |               |              |
            C               C              C
         2N2222          2N2222         2N2222
            E               E              E
            |               |              |
           GND             GND            GND

GPIO17 -- 1 kΩ -- B
                    \
                    10 kΩ
                      |
                     GND

GPIO27 -- 1 kΩ -- B
                    \
                    10 kΩ
                      |
                     GND

GPIO22 -- 1 kΩ -- B
                    \
                    10 kΩ
                      |
                     GND
```

The physical breadboard layout follows the same repeated pattern for all three channels.

This is intentional: the circuit should be understandable by looking at it, rather than requiring
every connection to be traced individually.

## Shared Power

The three prototype LEDs share the Raspberry Pi's:

```text
+5 V supply
GND
```

Each LED still has its **own 330 Ω current-limiting resistor**.

Do not replace the three resistors with one shared resistor.

The three base pulldown resistors also connect to the common ground rail.

The current required by three individual indicator LEDs is small enough for this prototype. The
larger LED banks used to illuminate the physical mock staircase will later require a separate power
design.

## Safe Default State

Each transistor base has a 10 kΩ pulldown resistor.

This means that a channel remains off when its GPIO control wire is disconnected or the GPIO is not
actively driving the transistor:

```text
GPIO inactive
      |
10 kΩ pulls base toward GND
      |
transistor OFF
      |
LED OFF
```

This allowed the three channels to be constructed together and tested one at a time without removing
their +5 V connections.

## PWM Control

All three channels support pulse-width modulation (PWM).

PWM lets the program independently control the apparent brightness of each step.

This makes effects possible such as:

```text
green -> yellow -> blue
```

or:

```text
green fades out
       yellow fades in
              blue fades in
```

as well as simultaneous effects:

```text
green  \
yellow  } fade together
blue   /
```

See [Single LED Lighting Channel](led-channel.md) for an introduction to PWM, duty cycle, and
transistor operation.

## Diagnostic Testing

Before the three channels were connected simultaneously, each was tested independently:

```text
Green   GPIO17 / pin 11   PASS
Yellow  GPIO27 / pin 13   PASS
Blue    GPIO22 / pin 15   PASS
```

The complete three-channel circuit was then tested with:

```bash
./scripts/test_led_channels.py
```

The diagnostic verifies:

1. each channel independently at several PWM brightness levels;
2. green-yellow-blue sequencing;
3. independent fades;
4. simultaneous PWM control of all three channels;
5. safe shutdown with all LEDs off.

The tested circuit completed all diagnostic operations successfully.

## What This Phase Demonstrates

The lighting subsystem now consists of three independently controllable outputs:

```text
             Raspberry Pi

GPIO17 --------> green channel
GPIO27 --------> yellow channel
GPIO22 --------> blue channel
```

Each channel separates the software control signal from the LED load using a transistor.

This gives Demo 2 a reusable lighting subsystem that can next be incorporated into higher-level
software and eventually connected to the illuminated physical staircase.
