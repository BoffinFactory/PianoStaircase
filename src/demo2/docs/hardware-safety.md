# Raspberry Pi Hardware Safety

The Raspberry Pi is designed for experimentation, but it is still an exposed computer circuit board.
Incorrect wiring, static electricity, mechanical damage, or accidental shorts can permanently damage
it.

This project uses conservative handling rules intended for students who may be new to working with
exposed electronics.

## The Most Important Rule

**Do not change GPIO or breadboard wiring while the circuit is powered.**

Before adding, removing, or moving a wire or component:

1. Shut down the Raspberry Pi.
2. Disconnect power from the Raspberry Pi.
3. Disconnect any separate breadboard or peripheral power supply.
4. Make the wiring change.
5. Inspect the circuit.
6. Reconnect power.

This takes slightly longer, but greatly reduces the chance of accidentally shorting adjacent pins or
connecting a signal to the wrong voltage.

## Shutting Down Before Rewiring

Do not simply unplug a Raspberry Pi while the operating system is running. An unexpected loss of
power can corrupt the filesystem or microSD card.

Shut it down first:

```bash
sudo poweroff
```

Wait for the system to finish shutting down, then physically disconnect its power cable.

**Important:** a Raspberry Pi that has completed a software shutdown may still have power present if
the power supply remains connected. For hardware work, disconnect the actual power source.

If the breadboard has its own power supply, turn that off or disconnect it too.

## What Is Safe to Touch?

When possible, handle a bare Raspberry Pi by:

- the edges of the circuit board;
- its mounting areas;
- its case, if one is installed.

Avoid unnecessarily touching:

- GPIO pins;
- exposed solder joints;
- integrated circuits;
- component leads;
- small surface-mounted components.

Handling the board by its edges also reduces the chance of electrostatic discharge reaching
sensitive circuitry.

If the Raspberry Pi is powered, avoid handling the exposed circuit board at all.

## Static Electricity

Electronic components can be damaged by **electrostatic discharge (ESD)**.

ESD is the small electrical discharge that can occur when static charge built up on your body
suddenly passes into an electronic device. A discharge can be too small for you to feel and still
potentially damage electronics.

Before handling a bare Raspberry Pi:

- avoid working on carpet when practical;
- avoid clothing that is producing noticeable static;
- discharge yourself by touching a grounded metal object before handling the board;
- use an ESD wrist strap and ESD-safe workspace when available;
- store loose electronics in appropriate antistatic packaging.

Do not deliberately touch GPIO pins or exposed circuitry after generating static electricity.

For normal student work, elaborate laboratory ESD equipment is not required, but basic ESD awareness
and careful handling are expected.

## Never Work on a Conductive Surface

Do not place a powered Raspberry Pi directly on:

- metal tables;
- loose tools;
- aluminum foil;
- screws or other metal hardware;
- other conductive materials.

A conductive object contacting exposed points on the underside of the board can create a short
circuit.

Use a case, non-conductive work surface, or appropriate electronics mat.

## GPIO Is 3.3 V Logic

The Raspberry Pi header contains several different kinds of pins.

These include:

- 5 V power;
- 3.3 V power;
- ground;
- 3.3 V GPIO signals.

The presence of 5 V pins on the header **does not mean that the GPIO pins use 5 V logic**.

Raspberry Pi GPIO operates at 3.3 V.

**Never connect 5 V directly to a GPIO pin.**

This is especially important because 5 V power pins and GPIO pins are located close together on the
header. Moving a jumper by one pin can therefore cause serious damage.

Before powering a new circuit, verify both:

1. the physical pin number; and
2. the GPIO signal name.

Do not rely only on where a pin appears to be located.

## Do Not Short Outputs

A GPIO configured as an output actively drives either approximately:

```text
3.3 V
```

or:

```text
0 V / ground
```

Do not connect an output directly to:

- ground while it is driving high;
- 3.3 V while it is driving low;
- another output that may drive the opposite state.

This can cause excessive current through the GPIO circuitry.

Components such as LEDs must also use appropriate current-limiting resistors.

## External Power Requires Extra Care

This project will eventually use more than one power source.

For example:

```text
Raspberry Pi power
        +
5 V LED power
```

Turning off only one supply does not necessarily make the entire circuit safe to modify.

Before rewiring, disconnect **all** power sources.

Also avoid applying voltage to Raspberry Pi GPIO pins from an externally powered circuit while the
Raspberry Pi itself is unpowered unless the circuit has specifically been designed for that
condition.

## Connecting Normal Peripherals

There is an important difference between:

```text
plugging a normal peripheral into a finished connector
```

and:

```text
changing exposed GPIO wiring
```

USB peripherals and similar external devices are designed to use their normal connectors.

GPIO jumper wires, breadboard circuits, power rails, and loose components should be treated as
development wiring and changed only with power disconnected.

## Before Applying Power

Before powering a new or modified circuit, perform a short visual inspection.

Check:

- Is 5 V connected only where 5 V is intended?
- Is 3.3 V connected only where 3.3 V is intended?
- Is ground connected correctly?
- Are GPIO numbers correct?
- Are any jumpers offset by one pin or one breadboard row?
- Are the breadboard power rails being used correctly?
- Are LED resistors present?
- Are there loose wire strands or metal objects touching the circuit?
- If multiple power supplies are used, are their connections intentional?

For more complicated circuits, have another project member inspect the wiring before first power-on
when practical.

## If Something Looks Wrong

If you see or smell something unexpected:

- immediately disconnect power;
- do not touch a component that may be hot;
- inspect the wiring before reconnecting anything.

Examples include:

- smoke;
- unusual heat;
- a burning smell;
- repeated Raspberry Pi resets;
- unexpected LED brightness;
- components behaving differently immediately after a wiring change.

Do not repeatedly power-cycle a circuit that may be wired incorrectly.

## Project Rule

For the Piano Staircase project:

> **Power off, unplug, wire, inspect, then power on.**

Working on live GPIO circuits is not necessary for this project and is not worth the additional
risk.
