# Piano Staircase Phase 1 Proof-of-Concept Documentation

**Project:** ACM Piano Staircase
**Location:** Russ Atrium Staircase
**Project Lead:** Adrien Abbey
**Faculty Sponsor:** Kayleigh Duncan
**Status:** Draft for team review before formal budget proposal
**Phase:** Phase 1 — Three-step proof-of-concept demo

---

## 1. Executive Summary

The Piano Staircase project has reached the point where the next useful step is not to purchase full-scale hardware, but to build a deliberately limited three-step proof of concept. This Phase 1 build is intended to validate the core hardware, enclosure, wiring, power, sensing, sound, lighting, and mounting assumptions before committing to a semi-permanent or full-staircase installation.

The proposed Phase 1 design uses three independent step modules. Each module includes a Raspberry Pi Zero 2 W, a time-of-flight sensor, a local speaker and amplifier, RGBW lighting, a DIP switch for step identity, local 5V power conversion, and optional RS-485 configuration-bus hardware. The modules will be powered from an existing 12V lab-style DC supply during testing, with fused 12V branches and local 5V buck conversion at each step.

This phase intentionally excludes custom PCBs, spare modules, the Raspberry Pi 5 touchscreen controller, a final DC power supply, and full-staircase purchasing. Those items belong in Phase 2 after the team has learned from physical testing.

**Recommended Phase 1 budget request:** approximately **$775**.

---

## 2. Project Context

The Piano Staircase is an ACM student-led project intended to create an interactive staircase installation in the Russ Atrium. The long-term vision is for one half of the split staircase to function as an interactive musical/visual installation, with each step producing local sound and visual feedback when used.

The intended value of the project includes:

* Showcasing CECS student engineering work to prospective students, parents, visitors, and the campus community.
* Increasing student organization visibility and involvement.
* Giving students hands-on experience with embedded systems, Linux, power distribution, sensors, audio, lighting, mechanical design, installation planning, and documentation.
* Creating a visible, memorable demonstration of engineering creativity in the Russ Atrium.

Phase 1 is not intended to be the final installation. It is an engineering validation phase.

---

## 3. Phase 1 Goal

### Primary Goal

Build a three-step proof-of-concept demo that validates the core per-step module architecture using off-the-shelf components.

### Phase 1 Target

By the end of Phase 1, the team should be able to demonstrate three adjacent stair modules that:

1. Detect when a foot is placed on or removed from a step.
2. Produce local sound from that step.
3. Provide local visual illumination or feedback.
4. Use a generic hardware/software image with step identity selected by DIP switch.
5. Can be configured or tested over a basic RS-485 bus.
6. Fit inside a flush, side-mounted enclosure concept.
7. Use non-destructive mounting and protected low-voltage wiring.

### Why only three steps?

Three steps are enough to validate the hard design questions without prematurely purchasing expensive full-system hardware. This keeps Phase 1 cost controlled while still exposing real integration risks.

---

## 4. Phase Structure

## Phase 1 — Three-Step Proof of Concept

**Included:**

* Three step modules.
* Off-the-shelf electronics.
* No custom PCB.
* No spare modules.
* No final touchscreen controller.
* Existing lab DC supply used for testing.
* 3D-printed prototype enclosures.
* Magnetic/non-destructive mounting experiments.
* Basic RS-485 communication test.
* Explicit validation tests.

**Purpose:** Learn what the final design actually needs before larger purchasing.

## Phase 2 — Installation-Ready MVP

**Likely additions after Phase 1:**

* Custom carrier PCB.
* Improved enclosure design.
* Finalized connector scheme.
* Dedicated power supply.
* Raspberry Pi 5 touchscreen controller.
* Spare modules.
* Facilities-reviewed mounting and cable routing.
* 3–6 step semi-permanent installation-ready MVP.

## Phase 3 — Expanded One-Side Staircase Installation

**Potential future scope:**

* Expand toward one full side of the Russ Atrium split staircase.
* Approximate long-term scale: up to 24 steps.
* Final cost to be estimated after Phase 1 and Phase 2 validation.

---

## 5. Physical Installation Assumptions

The intended initial location is the bottom few steps of the Russ Atrium Staircase. The staircase includes a side alcove on each step. The enclosure must fit flush within this side area and must not protrude into the walking path.

Key assumptions:

* Each step has a side alcove suitable for an enclosure.
* The enclosure must be flush or recessed for safety.
* The stairs are concrete with what appears to be steel side structure/I-beam material.
* Magnets may be viable for non-destructive retention, pending testing.
* Cables can pass through a small protected gap between steps.
* Nothing should destructively modify the stair structure.
* Facilities approval will be required before any semi-permanent installation.

---

## 6. High-Level System Architecture

Each step is an independent module.

```text
12V lab DC supply
  -> main current limit / optional main fuse
  -> 12V distribution
  -> inline fuse per step
  -> DFRobot DFR0831 buck converter per step
  -> 5V electronics inside each module
```

Each step module contains:

```text
Raspberry Pi Zero 2 W
  -> VL53L4CD ToF sensor over I2C
  -> MAX98357A I2S amplifier
  -> 40mm 4-ohm local speaker
  -> Adafruit 5162 RGBW lighting module
  -> SparkFun BOB-10124 RS-485 breakout over UART
  -> C&K BD08 DIP switch for step identity
  -> DFRobot DFR0831 5V buck converter
```

The RS-485 bus is optional for normal operation. Each module should boot and function independently using its local configuration. The RS-485 bus is for testing/configuration and future maintainability.

---

## 7. Design Principles

1. **Validate before scaling.**
   Do not purchase full-system hardware until the team has validated the module design.

2. **Keep Phase 1 inexpensive but meaningful.**
   The build should be limited, but it must still test the important risks.

3. **Use off-the-shelf modules first.**
   Custom PCBs should wait until after the wiring, mounting, and component layout are better understood.

4. **Keep each step independent.**
   Each module should operate without depending on a central controller during normal use.

5. **Use generic hardware/software images.**
   The DIP switch selects the step identity, allowing the same image to be deployed to all modules.

6. **Favor public-space robustness.**
   Even a proof of concept should avoid unsafe cabling, loose exposed conductors, or protruding enclosures.

7. **Document the validation results.**
   Phase 1 should produce enough evidence to support or revise the Phase 2 design.

---

## 8. Phase 1 Explicit Validation Goals

These should be treated as formal Phase 1 deliverables.

### 8.1 Step Module Feasibility

Determine whether all selected components can fit safely inside a flush, side-mounted stair enclosure.

**Pass criteria:** The module can be assembled and placed in the alcove without protruding into the walking path.

### 8.2 Foot Detection Reliability

Validate whether the VL53L4CD sensor can detect foot-on and foot-off behavior from the side-mounted position.

**Pass criteria:** The module reliably detects several users stepping on and off under realistic placement conditions.

### 8.3 Sensor Comparison

Compare the VL53L4CD against the VL53L1X to determine whether range, field-of-view, or mounting angle affects reliability.

**Pass criteria:** The team can justify which sensor should be used in Phase 2.

### 8.4 Local Audio Behavior

Determine whether the Raspberry Pi Zero 2 W and MAX98357A amplifier can produce responsive local sound.

**Pass criteria:** The sound begins when a foot is detected and stops/fades/releases when the foot is removed with acceptable latency.

### 8.5 Sound Level Control

Confirm that per-step audio can remain local and non-disruptive.

**Pass criteria:** Volume can be software-limited to avoid disrupting nearby classrooms or exams.

### 8.6 Lighting Visibility and Safety

Evaluate whether the Adafruit 5162 RGBW module visibly illuminates the step area without unacceptable glare or heat.

**Pass criteria:** The light is locally visible, controllable, and does not create a safety or distraction concern.

### 8.7 Lighting Geometry Comparison

Compare compact RGBW module lighting against a short addressable strip segment.

**Pass criteria:** The team can recommend a lighting geometry for Phase 2.

### 8.8 Power Architecture

Validate 12V distribution with local 5V buck conversion.

**Pass criteria:** Each step remains stable under simultaneous sensor, audio, and lighting operation.

### 8.9 Branch Protection

Test inline fused branches for each step.

**Pass criteria:** Each step branch is individually protected and can be isolated without disabling the entire prototype.

### 8.10 RS-485 Configuration Concept

Demonstrate that a laptop can address/configure three modules over an RS-485 bus.

**Pass criteria:** A laptop can send commands to specific DIP-addressed nodes and receive useful status/configuration responses.

### 8.11 Non-Destructive Mounting

Test magnetic mounting to the steel side structure.

**Pass criteria:** The module remains flush and stable without destructive attachment.

### 8.12 Cable Routing and Serviceability

Determine whether wiring can pass between steps safely and remain protected.

**Pass criteria:** Cables are protected, labeled, removable, and do not create a trip, snag, or maintenance hazard.

### 8.13 Facilities Readiness

Identify what must change before a semi-permanent installation request.

**Pass criteria:** The team can document open facilities/safety issues and propose Phase 2 corrections.

---

## 9. Hardware Decisions and Rationale

## 9.1 Per-Step Compute: Raspberry Pi Zero 2 W

**Selected:** 3 x unheadered Raspberry Pi Zero 2 W.

**Rationale:**

* Supports Linux and Python development.
* Temporary WiFi/SSH/Raspberry Pi Connect can be used during development.
* Can later support automated SD-card provisioning using CloudInit, Ansible, scripts, or image-building tools.
* Sufficient compute for sensor polling, local audio, lighting, and RS-485 configuration.
* Small enough to test in the side alcove.

**Important concern:** The board is approximately 30 mm wide, so enclosure fit is tight. Unheadered boards are preferred to reduce height and wiring bulk.

**Phase 2 revisit:** If the Pi Zero 2 W proves too bulky, power-hungry, or maintenance-heavy, compare against Pico 2 W or ESP32-S3 alternatives.

Reference: [https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/)

---

## 9.2 Foot Detection: VL53L4CD + VL53L1X Comparison

**Selected:**

* 3 x Adafruit VL53L4CD ToF sensors.
* 1 x Adafruit VL53L1X ToF sensor for comparison.

**Rationale:**

* ToF sensors are appropriate for non-contact foot detection.
* VL53L4CD is well suited to short-range proximity detection.
* VL53L1X provides a longer-range comparison option.
* STEMMA QT/Qwiic connectors simplify sensor wiring during prototyping.

**Phase 1 question:** Can side-mounted ToF sensing reliably detect foot-on and foot-off from the stair alcove?

References:

* VL53L4CD Adafruit: [https://www.adafruit.com/product/5396](https://www.adafruit.com/product/5396)
* VL53L1X Adafruit: [https://www.adafruit.com/product/3967](https://www.adafruit.com/product/3967)

---

## 9.3 Local Audio: MAX98357A + 40mm Speaker

**Selected:**

* 3 x Adafruit MAX98357A I2S mono Class-D amplifiers.
* 3 x Adafruit 40mm 4-ohm speakers.

**Rationale:**

* Local sound per step is a core requirement.
* I2S audio avoids analog audio complexity on the Pi Zero 2 W.
* The MAX98357A is compact and Pi-compatible.
* A 40mm speaker is a plausible fit for the alcove while still producing local sound.

**Phase 1 question:** Can the module behave like a piano key, starting sound on foot press and releasing/fading on foot removal?

**Important concern:** The speaker is mechanically significant and may drive enclosure layout.

References:

* MAX98357A: [https://www.adafruit.com/product/3006](https://www.adafruit.com/product/3006)
* Speaker: [https://www.adafruit.com/product/3968](https://www.adafruit.com/product/3968)

---

## 9.4 Lighting: Adafruit 5162 RGBW + Seeed Strip Comparison

**Selected:**

* 3 x Adafruit 5162 ultra-bright 4W RGBW chainable NeoPixel modules.
* 1 x Seeed 1m addressable RGB strip for comparison.
* Level shifting and support components.

**Rationale:**

* RGBW is better for actual visible illumination than RGB-only.
* The compact module can test local step illumination.
* The strip provides a comparison for linear/diffuse lighting geometry.
* The lighting subsystem is one of the largest unknowns, so direct physical testing is necessary.

**Important concerns:**

* Glare.
* Heat.
* Width/fit in the enclosure.
* Whether a point-source module or strip produces better local visibility.

References:

* Adafruit 5162: [https://www.adafruit.com/product/5162](https://www.adafruit.com/product/5162)
* Seeed WS2813 strip: [https://www.seeedstudio.com/Grove-RGB-LED-Strip-Waterproof-WS2813-30-LED-m-1m.html](https://www.seeedstudio.com/Grove-RGB-LED-Strip-Waterproof-WS2813-30-LED-m-1m.html)

---

## 9.5 Power Conversion: DFRobot DFR0831

**Selected:** 3 x DFRobot DFR0831 7-24V to 5V/4A buck converters.

**Rationale:**

* Supports the intended 12V distribution architecture.
* Provides 5V/4A per step, enough for Pi, sensor, audio, RS-485, and modest lighting.
* Six onboard output ports simplify Phase 1 wiring.
* Low cost and Digi-Key availability.

**Power architecture:**

```text
12V branch -> inline fuse -> DFR0831 buck converter -> 5V module electronics
```

**Important concern:** Measure real current draw and temperature under audio + lighting load.

Reference: [https://wiki.dfrobot.com/dfr0831/](https://wiki.dfrobot.com/dfr0831/)

---

## 9.6 RS-485 Configuration Bus

**Selected:**

* 3 x SparkFun BOB-10124 RS-485 breakout boards.
* 1 x DFRobot FIT0737 USB-to-RS-485 adapter.
* Termination/bias resistor assortment.
* Bus wiring.

**Rationale:**

* RS-485 supports a robust wired configuration bus concept.
* Each step remains independent during normal operation.
* A laptop can serve as the Phase 1 controller using the USB-to-RS-485 adapter.
* Testing the bus now informs Phase 2 PCB and wiring design.

**Phase 1 goal:** Demonstrate basic addressed communication with three modules.

**Important concern:** SparkFun BOB-10124 is not isolated or industrially protected. This is acceptable for Phase 1, but Phase 2 should revisit protection, connector retention, termination, biasing, and possible isolation.

References:

* SparkFun BOB-10124: [https://www.sparkfun.com/sparkfun-transceiver-breakout-rs-485.html](https://www.sparkfun.com/sparkfun-transceiver-breakout-rs-485.html)
* DFRobot FIT0737: [https://www.dfrobot.com/product-2189.html](https://www.dfrobot.com/product-2189.html)

---

## 9.7 Step Identity: C&K BD08 DIP Switch

**Selected:** 3 x C&K BD08 8-position through-hole DIP switches.

**Rationale:**

* Enables generic step modules.
* Five bits support 24 step addresses.
* Remaining switches can support test or maintenance modes.
* Simple GPIO reading using internal pull-ups.

**Proposed mapping:**

| Switches | Use                   |
| -------- | --------------------- |
| 1-5      | Step address, 0-31    |
| 6        | Test/maintenance mode |
| 7        | Reserved              |
| 8        | Reserved              |

Reference: [https://www.digikey.com/en/products/detail/c-k/BD08/181325](https://www.digikey.com/en/products/detail/c-k/BD08/181325)

---

## 9.8 Wiring, Connectors, and Protection

**Selected approach:**

* Separate low-voltage 12V power wiring for Phase 1.
* WAGO/terminal-style connectors for power distribution.
* Inline blade fuse holders for branch protection.
* STEMMA QT/Qwiic cables for ToF sensors.
* Screw terminals for RS-485 bus connections.
* Short internal wiring with heat shrink, strain relief, and labels.

**Rationale:**

* Phase 1 should be easy to debug and inspect.
* Power should be easy to measure and protect.
* Final compact connector strategy should wait until the custom PCB phase.

**Default fuse strategy:**

* Fuse each 12V branch before the DFR0831 buck converter.
* Start with 3A fuses.
* Include 2A and 5A fuses for testing.

---

## 9.9 Enclosure and Mounting

**Selected approach:**

* 3D-printed prototype enclosures.
* PETG for functional prototypes.
* PLA acceptable for fit checks.
* Magnetic retention to steel side structure, pending magnet test.
* Rubber/TPU pads for grip and non-marring contact.
* Printed geometry to prevent sliding/protrusion.
* Temporary tether or restraint during early testing.

**Rationale:**

* Friction-fit alone is not robust enough for a stair installation.
* Magnets may provide non-destructive mounting if the side structure is ferromagnetic.
* Printed geometry should prevent shifting; magnets should not be the only anti-slide mechanism.

**Immediate test:** Bring a small magnet to the intended stair location and verify strong attachment to the exact surface where the enclosure would mount.

---

## 10. Phase 1 Bill of Materials

Prices are working estimates and must be verified before purchase.

## 10.1 Core Step Electronics

| Item                                           | Qty. | Est. Unit | Est. Subtotal | Link / Notes                                                                                                                                                                                       |
| ---------------------------------------------- | ---: | --------: | ------------: | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Raspberry Pi Zero 2 W, unheadered, SC1176      |    3 |    $15.00 |        $45.00 | [https://www.digikey.com/en/products/base-product/raspberry-pi/1690/Raspberry-Pi-Zero-2-W/725745](https://www.digikey.com/en/products/base-product/raspberry-pi/1690/Raspberry-Pi-Zero-2-W/725745) |
| 32GB microSD cards                             |    3 |    $10.00 |        $30.00 | Exact source TBD; Digi-Key stock may be limited                                                                                                                                                    |
| Adafruit VL53L4CD ToF sensor, product 5396     |    3 |    $14.95 |        $44.85 | [https://www.digikey.com/en/products/detail/adafruit-industries-llc/5396/16129669](https://www.digikey.com/en/products/detail/adafruit-industries-llc/5396/16129669)                               |
| Adafruit VL53L1X ToF sensor, product 3967      |    1 |    $14.95 |        $14.95 | [https://www.digikey.com/en/products/detail/adafruit-industries-llc/3967/17039169](https://www.digikey.com/en/products/detail/adafruit-industries-llc/3967/17039169)                               |
| STEMMA QT / Qwiic cables, mixed 100mm/200mm    |    6 |    ~$1.10 |        ~$6.60 | Mixed lengths for placement testing                                                                                                                                                                |
| Adafruit MAX98357A I2S amplifier, product 3006 |    3 |     $5.95 |        $17.85 | [https://www.digikey.com/en/products/detail/adafruit-industries-llc/3006/6058477](https://www.digikey.com/en/products/detail/adafruit-industries-llc/3006/6058477)                                 |
| Adafruit 40mm 4-ohm speaker, product 3968      |    3 |     $4.95 |        $14.85 | [https://www.digikey.com/en/products/detail/adafruit-industries-llc/3968/9745251](https://www.digikey.com/en/products/detail/adafruit-industries-llc/3968/9745251)                                 |
| DFRobot DFR0831 7-24V to 5V/4A buck converter  |    3 |     $4.90 |        $14.70 | [https://www.digikey.com/en/products/detail/dfrobot/DFR0831/14322651](https://www.digikey.com/en/products/detail/dfrobot/DFR0831/14322651)                                                         |
| C&K BD08 8-position DIP switch                 |    3 |     $3.13 |         $9.39 | [https://www.digikey.com/en/products/detail/c-k/BD08/181325](https://www.digikey.com/en/products/detail/c-k/BD08/181325)                                                                           |

**Subtotal:** approximately **$198.19**

---

## 10.2 Lighting

| Item                                               |  Qty. | Est. Unit | Est. Subtotal | Link / Notes                                                                                                                                                                 |
| -------------------------------------------------- | ----: | --------: | ------------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Adafruit 5162 ultra-bright 4W RGBW NeoPixel module |     3 |     $5.50 |        $16.50 | [https://www.digikey.com/en/products/detail/adafruit-industries-llc/5162/15189160](https://www.digikey.com/en/products/detail/adafruit-industries-llc/5162/15189160)         |
| Seeed 104020108 WS2813 1m addressable RGB strip    |     1 |     $6.50 |         $6.50 | [https://www.digikey.com/en/products/detail/seeed-technology-co-ltd/104020108/9606876](https://www.digikey.com/en/products/detail/seeed-technology-co-ltd/104020108/9606876) |
| 74AHCT125 level shifter ICs                        |     3 |     $1.50 |         $4.50 | Level shifting from Pi 3.3V GPIO to 5V LED data                                                                                                                              |
| LED support parts                                  | 1 lot |         — |        $30.00 | Resistors, capacitors, wiring, connectors, diffuser/thermal test materials                                                                                                   |

**Subtotal:** approximately **$57.50**

---

## 10.3 RS-485 Configuration Bus

| Item                                  |  Qty. | Est. Unit | Est. Subtotal | Link / Notes                                                                                                                                                   |
| ------------------------------------- | ----: | --------: | ------------: | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SparkFun BOB-10124 RS-485 breakout    |     3 |    $12.50 |        $37.50 | [https://www.digikey.com/en/products/detail/sparkfun-electronics/10124/6006043](https://www.digikey.com/en/products/detail/sparkfun-electronics/10124/6006043) |
| DFRobot FIT0737 USB-to-RS-485 adapter |     1 |     $8.50 |         $8.50 | [https://www.digikey.com/en/products/detail/dfrobot/FIT0737/13688358](https://www.digikey.com/en/products/detail/dfrobot/FIT0737/13688358)                     |
| Termination/bias resistor assortment  | 1 lot |         — |        $10.00 | 120-ohm termination and pull-up/pull-down bias testing                                                                                                         |

**Subtotal:** approximately **$56.00**

---

## 10.4 Power, Wiring, and Protection

| Item                                                                     |  Qty. | Est. Subtotal | Notes                                                                  |
| ------------------------------------------------------------------------ | ----: | ------------: | ---------------------------------------------------------------------- |
| Inline blade fuse holders                                                |     4 |        $25.00 | One per step plus one extra/main option                                |
| 2A / 3A / 5A blade fuse assortment                                       |     1 |        $10.00 | Default 3A per step branch                                             |
| WAGO 221 lever connectors                                                | 1 lot |        $25.00 | Low-voltage distribution and removable wiring                          |
| Power wire, RS-485 wire, hookup wire, heat shrink, labels, strain relief | 1 lot |        $50.00 | Exact lengths depend on physical mockup                                |
| Screw terminals, headers, perfboard/protoboard                           | 1 lot |        $40.00 | For RS-485 breakouts, DIP switches, level shifters, and clean assembly |

**Subtotal:** approximately **$150.00**

---

## 10.5 Enclosure and Mounting

| Item                                                                          |  Qty. | Est. Subtotal | Notes                                                                                             |
| ----------------------------------------------------------------------------- | ----: | ------------: | ------------------------------------------------------------------------------------------------- |
| 3D-printed enclosure and non-destructive magnetic mounting hardware allowance | 1 lot |       $125.00 | PETG/PLA, magnets, rubber/TPU pads, inserts, screws, tether/restraint, diffuser/thermal materials |

**Subtotal:** **$125.00**

---

## 10.6 Reserve, Shipping, and Price Variance

| Item                                        | Est. Subtotal | Notes                                                                                            |
| ------------------------------------------- | ------------: | ------------------------------------------------------------------------------------------------ |
| Additional integration parts reserve        |       $100.00 | Adapters, alternate connectors, extra wire lengths, replacement small parts                      |
| Shipping / vendor variance / price movement |        $75.00 | Useful if parts are split across Digi-Key, Amazon Business, Adafruit, SparkFun, or local sources |

**Subtotal:** **$175.00**

---

## 10.7 Estimated Phase 1 Total

| Section                                |      Subtotal |
| -------------------------------------- | ------------: |
| Core step electronics                  |         ~$198 |
| Lighting                               |          ~$58 |
| RS-485                                 |          ~$56 |
| Power/wiring/protection                |         ~$150 |
| Enclosure/mounting                     |          $125 |
| Reserve/shipping/variance              |          $175 |
| **Recommended Phase 1 budget request** | **$750-$775** |

**Recommended request amount:** **$775**.

---

## 11. Preliminary Wiring Notes

## 11.1 Power Wiring

* Use an existing 12V lab supply for Phase 1.
* Verify voltage, current capability, and current-limiting behavior before connecting modules.
* Use separate 12V branches for each step.
* Fuse each branch before the DFR0831 buck converter.
* Convert 12V to 5V locally in each step.
* Do not distribute 5V across the staircase.

## 11.2 RS-485 Wiring

* Use trunk-style bus wiring.
* Do not wire RS-485 as a star.
* Include A, B, and GND reference conductors.
* Terminate only at the two ends of the bus during tests.
* Use the USB-to-RS-485 adapter from a laptop for Phase 1.

## 11.3 Sensor Wiring

* Use STEMMA QT/Qwiic I2C cables.
* Test multiple cable lengths and sensor angles.
* Keep sensor wiring short and protected.

## 11.4 Lighting Wiring

* Use level shifting from Pi GPIO to 5V LED data.
* Include signal resistor and bulk capacitance near LED power.
* Software-limit brightness during initial tests.
* Monitor LED temperature during extended use.

## 11.5 Audio Wiring

* Use I2S from the Pi Zero 2 W to the MAX98357A amplifier.
* Keep speaker wiring short when possible.
* Design the enclosure so the speaker can emit outward without obstructing the walking path.

---

## 12. Preliminary Software Plan

The Phase 1 software should remain simple and test-focused.

## 12.1 Module Boot Behavior

Each module should:

1. Boot from its SD card.
2. Read DIP switch state.
3. Determine its step address.
4. Load local configuration.
5. Start sensor polling.
6. Start audio and lighting services.
7. Optionally listen for RS-485 commands.

## 12.2 Step Identity

The same SD-card image should work on all modules. The DIP switch provides the physical address.

Example:

```text
DIP switch address 1 -> Step 1 -> Note C4 -> Color A
DIP switch address 2 -> Step 2 -> Note D4 -> Color B
DIP switch address 3 -> Step 3 -> Note E4 -> Color C
```

## 12.3 Foot Detection State Machine

Recommended simple state machine:

```text
IDLE
  -> foot detected consistently
  -> PRESSED

PRESSED
  -> start/play/sustain note
  -> maintain light effect
  -> foot absent consistently
  -> RELEASE

RELEASE
  -> fade/release note
  -> fade/change light
  -> return to IDLE
```

Use filtering/debounce to avoid false triggers.

## 12.4 RS-485 Test Protocol

The Phase 1 protocol should be simple and inspectable.

Example commands:

```text
ADDR=01 STATUS?
ADDR=01 SET NOTE=C4
ADDR=01 SET COLOR=BLUE
ADDR=01 SET VOLUME=40
BROADCAST MUTE
BROADCAST TEST
```

The goal is not a final protocol. The goal is to prove that addressed configuration is possible.

## 12.5 Provisioning Direction

Phase 1 development may use temporary WiFi, SSH, or Raspberry Pi Connect. Final operation should not depend on WiFi.

Future provisioning options:

* SD-card image build script.
* CloudInit-style first-boot configuration if feasible.
* Ansible playbook during development.
* Git-based deployment during testing.

---

## 13. Phase 1 Test Plan

## 13.1 Bench Test

Before stair testing:

* Verify each DFR0831 output voltage.
* Verify each Pi boots.
* Verify I2C sensor communication.
* Verify audio output.
* Verify RGBW light control.
* Verify DIP switch reading.
* Verify RS-485 communication between laptop and one module.
* Verify per-step fuse behavior with safe current-limited supply settings.

## 13.2 Three-Module Integration Test

* Connect all three modules to the 12V bus.
* Connect all three modules to the RS-485 bus.
* Confirm each module identifies itself by DIP switch.
* Send addressed commands to each module.
* Trigger each sensor and confirm correct audio/light behavior.

## 13.3 Physical Fit Test

* Place enclosure mockups in the stair alcove.
* Confirm flush fit.
* Confirm cable routing.
* Confirm no protrusion into walking path.
* Confirm service access.

## 13.4 Magnetic Retention Test

* Verify magnet attachment to the actual steel side structure.
* Test rubber/TPU anti-slip pads.
* Test for sliding/shear movement.
* Test temporary tethering.
* Leave mounted mockup in place for an extended static test if permitted.

## 13.5 User Interaction Test

* Have several users step normally on the stairs.
* Observe sensor reliability.
* Observe audio timing.
* Observe lighting visibility.
* Check whether the module feels distracting, unsafe, or too quiet/loud.

## 13.6 Thermal and Stability Test

Run each module for an extended period with audio and lighting active.

Check:

* Pi stability.
* Buck converter temperature.
* LED temperature.
* Speaker/amplifier behavior.
* Cable warmth.
* Enclosure temperature.

---

## 14. Known Risks

| Risk                                          | Severity    | Mitigation                                                                 |
| --------------------------------------------- | ----------- | -------------------------------------------------------------------------- |
| Enclosure may be too tight                    | High        | Use unheadered Pi, low-profile wiring, iterative prints                    |
| Magnetic mounting may be weaker than expected | High        | Test actual steel surface; use rubber-coated magnets, geometry, and tether |
| ToF sensor may false-trigger                  | Medium/High | Test angles; compare VL53L4CD and VL53L1X; add filtering                   |
| Lighting may glare or overheat                | Medium      | Limit brightness; test diffuser/shroud; monitor temperature                |
| Speaker may not fit or sound good             | Medium      | Test enclosure geometry and grille; adjust placement                       |
| Pi audio latency may feel poor                | Medium      | Use simple audio stack; test WAV playback and fade behavior                |
| Wiring may become messy                       | Medium      | Use WAGO/terminal connectors, labels, heat shrink, strain relief           |
| RS-485 may not be needed                      | Low/Medium  | Still useful as Phase 1 validation for future configuration                |
| Facilities approval may require changes       | High        | Treat Phase 1 as pre-approval learning build                               |

---

## 15. Items Deliberately Deferred to Phase 2

* Custom PCB / carrier board.
* Pi 5 touchscreen controller.
* Final DC power supply.
* Final cable harness.
* Final enclosure design.
* Spare modules.
* Semi-permanent 3-6 step installation.
* Full 24-step hardware purchase.
* Facilities-approved installation plan.
* Long-term maintenance plan.

---

## 16. Team Review Questions

The team should review and answer the following before the formal budget proposal is finalized.

### Hardware

1. Are there any major objections to using Raspberry Pi Zero 2 W for Phase 1?
2. Does the ToF sensor plan adequately test foot detection?
3. Is the local speaker requirement still correct?
4. Is the RGBW lighting approach sufficient for Phase 1?
5. Are we comfortable deferring custom PCBs to Phase 2?

### Mechanical

1. Can the selected components plausibly fit in the alcove?
2. What should the first enclosure mockup prioritize: fit, sensor angle, speaker placement, or lighting projection?
3. Can we test magnet attachment to the actual stair structure before purchase?
4. Are there any safety concerns with magnetic mounting?

### Electrical

1. Do we have access to a suitable 12V lab supply?
2. Should we include any additional protection beyond inline branch fuses?
3. Are the DFR0831 converters acceptable for Phase 1?
4. Is the wiring/support allowance reasonable?

### Software

1. Who will own the first Pi image/software setup?
2. Which language/library should be used for sensor, audio, and lighting control?
3. Should RS-485 testing be integrated early or after basic step behavior works?
4. What is the minimum successful demo behavior?

### Project Planning

1. What evidence should Phase 1 produce before requesting Phase 2 funds?
2. Who needs to be involved before facilities review?
3. What would make us decide not to scale this design?

---

## 17. Recommended Phase 1 Deliverables

By the end of Phase 1, the team should produce:

1. Working three-step proof-of-concept demo.
2. Documented BOM revisions.
3. Photos of enclosure fit and wiring.
4. Sensor test results.
5. Audio/lighting behavior notes.
6. Power/current measurements.
7. RS-485 communication test notes.
8. Mounting stability notes.
9. Facilities-readiness concerns.
10. Phase 2 recommendation: proceed, revise, or pivot.

---

## 18. Summary

The proposed Phase 1 design is a conservative, validation-focused approach. It avoids prematurely purchasing a full staircase system while still testing the important engineering risks. The estimated $775 budget is modest relative to the project’s long-term scope and should provide enough hardware and support parts to build a meaningful three-step demo.

The most important outcome of Phase 1 is not the demo itself. The most important outcome is the information needed to design Phase 2 responsibly.
