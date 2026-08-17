# Breadboard Wiring Conventions

This project uses breadboards for prototyping circuits before they are moved to more permanent
hardware.

A breadboard circuit can be electrically correct and still be difficult to understand or debug. Good
wiring practices make the circuit easier to inspect, modify, explain, and reproduce.

Before working with Raspberry Pi GPIO hardware, read [Hardware Safety](hardware-safety.md).

## Breadboard Basics

Most breadboards contain two different types of connections:

- **terminal strips** in the center, where groups of holes are electrically connected;
- **power rails** along the edges, normally marked `+` and `-`.

On a typical breadboard, five holes in the same numbered column are connected:

```text
A20 ─┐
B20  │
C20  ├── electrically connected
D20  │
E20 ─┘
```

The two sides of the center gap are separate.

Power rails may also be **split in the middle**. Do not assume that a rail is continuous end-to-end.
Check the breadboard markings or use a multimeter's continuity mode before relying on it.

## Wire Types

Use the type of wire that fits the job.

### Raspberry Pi to breadboard

Use flexible female-to-male jumper wires:

```text
Raspberry Pi GPIO pin
        |
   female connector
        |
    flexible wire
        |
      male pin
        |
    breadboard
```

These are convenient because the Raspberry Pi uses exposed header pins.

### Connections within the breadboard

Prefer short solid-core jumpers.

Solid wire stays where it is placed and can be routed neatly along the surface of the breadboard.

Avoid long loops when a shorter wire will work.

## Wire Colors

Wire color does not change how electricity behaves, but consistent colors make a circuit much easier
to understand.

For Piano Staircase prototypes, use:

| Color | Meaning |
| --- | --- |
| Red | +5 V |
| Black | Ground |
| Orange | +3.3 V, when available |
| Other colors | Signals |

Do not use red or black for unrelated signals simply because the wire is convenient.

When practical, signal colors should also describe their function. For example:

- green for the green lighting channel;
- yellow for the yellow lighting channel;
- blue for the blue lighting channel.

The exact signal colors are less important than using them consistently.

## Power Rails

Clearly identify which rails contain which voltages.

A prototype may eventually contain both:

```text
+5 V
+3.3 V
GND
```

These are not interchangeable.

In particular:

> **Raspberry Pi GPIO signals use 3.3 V logic. Never connect +5 V directly to a GPIO pin.**

If both 3.3 V and 5 V are present, label the rails if there is any possibility of confusion.

Small pieces of masking tape marked `5V`, `3V3`, and `GND` are sufficient.

## Organize by Function

Components that work together should generally be placed together.

For example, a lighting channel can be arranged conceptually as:

```text
GPIO control
     |
base resistor
     |
 transistor
     |
 LED load
     |
 power
```

Keeping these parts near one another makes the circuit easier to trace.

As the Demo 2 breadboard grows, try to keep separate functional areas for:

- sensor connections;
- GPIO control circuitry;
- transistor drivers;
- LED loads;
- power distribution.

Do not pack components together simply to save breadboard space. Leaving several unused rows between
functional sections often makes debugging easier.

## Route Wires Clearly

When practical, route wires horizontally or vertically rather than diagonally across unrelated
components.

Prefer:

```text
────────────┐
            |
            └──────
```

over a large collection of crossing wires.

This is not an electrical requirement. It is a readability and maintenance practice.

Also avoid running wires directly over components when a route around them is practical.

## Keep Exposed Leads Reasonably Short

Resistors, LEDs, and other through-hole components often have long leads.

Long exposed leads work electrically, but they can:

- bend into nearby connections;
- accidentally short another component;
- make the circuit difficult to inspect.

Trim or bend leads to reasonable lengths when the circuit becomes more permanent.

During early experimentation, leaving some extra lead length is acceptable if the conductors remain
safely separated.

## Physical Pin Numbers vs. GPIO Numbers

Raspberry Pi pins have more than one naming system.

For example:

```text
physical pin 11 = GPIO17
```

`11` describes where the pin is physically located on the 40-pin header.

`GPIO17` is the Broadcom GPIO signal name used by software.

Documentation for this project should normally include both when first introducing a connection:

```text
GPIO17 / physical pin 11
```

This helps prevent confusing a physical pin number with a GPIO number.

## Common Ground

Circuits controlled by the Raspberry Pi need a shared electrical reference.

For example, when the Raspberry Pi controls an externally powered LED circuit:

```text
Raspberry Pi GND ───────┐
                        ├── common ground
LED supply GND ─────────┘
```

Without a common ground, the transistor or other control circuitry may not interpret the GPIO
voltage correctly.

When multiple power supplies are used, disconnect **all** of them before changing wiring.

## Before Applying Power

Before powering a new or modified breadboard circuit, check:

- power rails are connected to the intended voltage;
- ground is connected correctly;
- GPIO wires are on the correct physical pins;
- no GPIO is connected directly to +5 V;
- components are not shifted by one breadboard row;
- resistor and transistor connections match the circuit design;
- bare leads are not touching unrelated conductors.

For this project:

> **Wire while unpowered. Inspect. Then apply power.**

See [Hardware Safety](hardware-safety.md) for the complete handling rules.

## Why These Conventions Matter

These conventions are not required for electricity to flow.

They are intended to make a prototype:

- easier to debug;
- easier to explain;
- easier for another student to reproduce;
- safer to modify;
- less dependent on remembering how it was originally assembled.

A useful rule for prototyping is:

> **The wiring itself should help document the circuit.**
