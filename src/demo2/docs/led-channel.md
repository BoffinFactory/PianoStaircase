# Single LED Lighting Channel

This phase introduces the basic lighting circuit used by Demo 2.

The goal is not only to make an LED light. It is to create a lighting channel that the Raspberry Pi
can safely switch and control in brightness.

The tested circuit uses:

- Raspberry Pi GPIO17 / physical pin 11;
- one 2N2222 NPN transistor;
- one green LED;
- one 330 Ω LED resistor;
- one 1 kΩ transistor base resistor;
- one 10 kΩ base pulldown resistor;
- the Raspberry Pi's 5 V supply for the test load.

## Circuit Overview

The lighting channel is:

```text
                       +5 V
                         |
                       330 Ω
                         |
                    LED anode (+)
                    LED cathode (-)
                         |
                      Collector
                         C
                         |
GPIO17 ── 1 kΩ ──┬──── Base
                 |       B
               10 kΩ     |
                 |       E
                GND    Emitter
                         |
                        GND
```

The transistor allows a small GPIO signal from the Raspberry Pi to control a separate LED current
path.

## GPIO

**GPIO** stands for **General-Purpose Input/Output**.

GPIO pins allow software to interact with external electronics.

A GPIO can commonly be configured as:

- an **input**, where software reads a digital signal; or
- an **output**, where software drives the pin high or low.

For this circuit we use:

```text
GPIO17 / physical pin 11
```

When GPIO17 is high, it outputs approximately 3.3 V.

When GPIO17 is low, it outputs approximately 0 V.

The GPIO does **not** directly power the LED. Instead, it controls the transistor.

## Why Use a Transistor?

A transistor can act as an electronically controlled switch.

The 2N2222 used here is an **NPN bipolar junction transistor (BJT)**.

It has three terminals:

```text
Collector
Base
Emitter
```

For this circuit:

```text
GPIO17
   |
   v
 Base

Collector
   |
   v
LED current

Emitter
   |
   v
Ground
```

A small current into the **base** allows a larger current to flow from the **collector** to the
**emitter**.

This lets the Raspberry Pi control a load without requiring the GPIO pin itself to supply all of the
load current.

## Transistor Orientation

A transistor's three leads must be identified correctly.

Do **not** assume that every component labeled `2N2222` uses the same physical lead order.

For the BOJACK 2N2222 transistors tested for Demo 2, the pinout was verified with a multimeter's
transistor tester.

With the **flat face toward the viewer**, the tested parts were:

```text
LEFT      CENTER      RIGHT
Emitter    Base      Collector
   E        B            C
```

The transistor tester measured approximately:

```text
E-B-C orientation: hFE ≈ 304
C-B-E orientation: hFE ≈ 23
```

This strongly confirmed the E-B-C orientation for the tested parts.

Future builders should verify the pinout of unfamiliar transistors rather than relying only on
package shape.

## LED Polarity

LED stands for **Light-Emitting Diode**.

Unlike an ordinary resistor, an LED has polarity. It is intended to conduct current primarily in one
direction.

The two leads are:

```text
Anode   = positive side
Cathode = negative side
```

For a typical through-hole LED:

```text
long lead  = anode (+)
short lead = cathode (-)
```

The flat edge on the LED body also normally marks the cathode.

In this circuit:

```text
+5 V
 |
resistor
 |
anode
 LED
cathode
 |
transistor
 |
GND
```

If the LED is installed backward, it normally will not light.

## Why the LED Needs a Resistor

An LED does not naturally limit its own current.

Once its forward voltage is reached, allowing too much current through the LED can damage it.

The **330 Ω resistor** limits the LED current:

```text
+5 V ── 330 Ω ── LED ── transistor ── GND
```

The resistor converts some of the available voltage into a controlled voltage drop and therefore
limits current through the LED.

For this prototype, 330 Ω produces a bright but reasonable test current.

Each conventional LED should have its **own current-limiting resistor** when multiple LEDs are later
connected in parallel.

## Why the Base Needs a 1 kΩ Resistor

GPIO17 does not connect directly to the transistor base.

Instead:

```text
GPIO17 ── 1 kΩ ── Base
```

The transistor's base-emitter junction behaves somewhat like a diode. Connecting it directly to the
GPIO could allow excessive base current.

The 1 kΩ resistor limits that current.

With approximately 3.3 V from the GPIO and roughly 0.7 V across the base-emitter junction:

```text
I ≈ (3.3 V - 0.7 V) / 1000 Ω
```

which is approximately:

```text
2.6 mA
```

The exact value is not important for understanding this circuit. The important idea is:

> **The resistor prevents the GPIO from supplying excessive current to the transistor base.**

## Why There Is a 10 kΩ Pulldown Resistor

The base also connects to ground through a 10 kΩ resistor:

```text
          Base
           |
GPIO ──────+
           |
         10 kΩ
           |
          GND
```

This is called a **pulldown resistor**.

During startup, shutdown, or before software configures GPIO17, the GPIO may not be actively driving
a clear high or low signal.

Without the pulldown, the transistor base could **float**, meaning its voltage is not well defined.

The 10 kΩ resistor gently pulls the base toward ground when nothing else is driving it.

That gives the circuit a safe default state:

```text
GPIO inactive
      |
Base pulled low
      |
Transistor OFF
      |
LED OFF
```

When GPIO17 goes high, the GPIO easily overcomes the weak 10 kΩ pulldown and turns the transistor
on.

## Switching the LED

The simplest software control is digital:

```text
GPIO LOW  -> transistor off -> LED off
GPIO HIGH -> transistor on  -> LED on
```

That is enough for blinking.

Demo 2 also needs smooth lighting effects, so we use **pulse-width modulation**.

## Pulse-Width Modulation (PWM)

PWM is a way to control the apparent power delivered to a device by switching it on and off very
rapidly.

Instead of attempting to output a continuously adjustable voltage, the GPIO still produces only:

```text
HIGH
```

or:

```text
LOW
```

The difference is how long it spends in each state.

### Duty Cycle

The percentage of each cycle that the signal remains high is called the **duty cycle**.

For example:

```text
25% duty cycle:

HIGH  ┌─┐   ┌─┐   ┌─┐
      │ │   │ │   │ │
LOW ──┘ └───┘ └───┘ └───
```

The LED is on about 25% of the time.

```text
50% duty cycle:

HIGH  ┌──┐  ┌──┐  ┌──┐
      │  │  │  │  │  │
LOW ──┘  └──┘  └──┘  └──
```

The LED is on about half the time.

```text
75% duty cycle:

HIGH  ┌───┐ ┌───┐ ┌───┐
      │   │ │   │ │   │
LOW ──┘   └─┘   └─┘   └─
```

The LED is on about 75% of the time.

At a sufficiently high switching frequency, the eye does not normally perceive the individual
flashes. Instead, the LED appears to have a different brightness.

## PWM Frequency

The **frequency** describes how many PWM cycles occur each second.

The Demo 2 diagnostic currently uses:

```text
500 Hz
```

which means approximately:

```text
500 cycles per second
```

For this application, that is fast enough that the LED appears continuously illuminated rather than
intentionally blinking.

Frequency and duty cycle describe different things:

```text
frequency  = how quickly cycles repeat
duty cycle = how much of each cycle is ON
```

## Why PWM Is Useful for the Piano Staircase

Simple ON/OFF control would allow:

```text
step dark
step bright
```

PWM allows effects such as:

```text
fade in
fade out
pulse
cross-fade
different brightness levels
```

For example:

```text
0%   -> 25% -> 50% -> 75% -> 100%
```

can create a smooth fade instead of an abrupt transition.

This will allow the staircase lighting to visually follow musical notes and animations.

## Brightness Is Not Perfectly Linear

A 50% PWM duty cycle does not necessarily **look** exactly half as bright as a 100% duty cycle.

Human vision does not perceive brightness linearly.

For the diagnostic, this is not a problem. The goal is simply to verify that PWM provides repeatable
brightness control.

Later animation code can compensate for human brightness perception if necessary.

## Diagnostic

The lighting channel can be tested with:

```bash
source ~/.venv/piano-demo/bin/activate
python scripts/test_led_channel.py
```

The diagnostic tests:

1. several fixed brightness levels;
2. LED off;
3. repeated fade-in and fade-out cycles.

The tested circuit produced the expected behavior.

## What This Phase Demonstrates

This small circuit introduces several concepts that will be reused throughout the Piano Staircase:

```text
GPIO
  |
control signal
  |
transistor
  |
load
```

along with:

- current limiting;
- defined default states;
- LED polarity;
- transistor switching;
- PWM brightness control.

The later three-step lighting system will mostly repeat this same pattern for additional lighting
channels.
