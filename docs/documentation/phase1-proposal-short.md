# Piano Staircase Phase 1 — Broad Review Summary

**Project:** ACM Piano Staircase
**Location:** Russ Atrium Staircase
**Project Lead:** Adrien Abbey
**Faculty Sponsor:** Kayleigh Duncan
**Draft purpose:** Short review version before formal budget proposal

---

## 1. Overview

The Piano Staircase project aims to create an interactive musical and visual staircase installation in the Russ Atrium. When someone steps on a stair, that step will detect the interaction, play a local sound, and provide local lighting feedback.

Rather than purchasing hardware for the full staircase immediately, Phase 1 will build a small three-step proof of concept. The purpose is to learn what works before committing to a larger installation.

**Recommended Phase 1 budget request:** approximately **$725**.

---

## 2. Why Phase 1 Is Limited to Three Steps

The full project could eventually cover one side of the split Russ Atrium staircase, potentially up to 24 steps. However, many design questions still need to be answered before buying parts at that scale.

Phase 1 intentionally limits the build to three steps so the team can test:

* whether the electronics fit safely in the side alcove,
* whether the sensors reliably detect feet,
* whether local speakers are practical,
* whether the lighting is visible without glare,
* whether magnetic mounting is safe and stable,
* whether the wiring can be clean, protected, and removable,
* whether the selected architecture should be scaled up or revised.

This keeps the first request modest while still producing useful engineering evidence.

---

## 3. Phase 1 Goal

Phase 1 will build and test **three independent step modules**.

Each step should be able to:

1. Detect when a foot is placed on or removed from the step.
2. Play sound locally from that step.
3. Provide local RGBW lighting feedback.
4. Identify which step it is using a DIP switch.
5. Operate independently without WiFi during normal use.
6. Support temporary wired configuration/testing through RS-485.
7. Fit into a flush, removable, non-destructive enclosure.

Temporary WiFi may be used during development and testing, but the final design should not depend on WiFi.

Advisor-feedback updates reflected in this revision:

* Use smaller microSD cards in greater quantity rather than 32 GB cards.
* Do not purchase Pico W boards; use existing inventory only if the team wants an optional comparison.
* Treat existing VL53L0X sensors as the baseline sensor option.
* Purchase only one VL53L4CD and one VL53L1X for comparison testing.
* Use existing proto boxes for early bench work and reduce the mechanical prototyping allowance.

---

## 4. Proposed Per-Step Design

Each step module will include:

| Subsystem           | Selected Phase 1 Hardware              | Purpose                                                       |
| ------------------- | -------------------------------------- | ------------------------------------------------------------- |
| Compute             | Raspberry Pi Zero 2 W                  | Runs sensor, audio, lighting, and configuration software      |
| Baseline foot detection | Existing VL53L0X time-of-flight sensors, if available | Uses existing inventory as the baseline foot-detection test |
| Sensor comparison   | VL53L4CD and VL53L1X time-of-flight sensors | Compares newer range, field-of-view, and polling options against the baseline |
| Audio               | MAX98357A I2S amplifier + 40mm speaker | Plays sound locally from each step                            |
| Lighting            | Adafruit 5162 RGBW module              | Provides local visual feedback                                |
| Lighting comparison | 1m addressable RGB strip               | Tests whether strip lighting works better than point lighting |
| Power               | DFRobot DFR0831 12V-to-5V converter    | Converts shared 12V power to local 5V power                   |
| Configuration bus   | SparkFun RS-485 breakout               | Allows wired configuration/testing                            |
| Step identity       | 8-position DIP switch                  | Lets identical modules know which step they are               |
| Mounting            | Existing proto boxes + limited printed/magnetic fit testing | Tests removable, non-destructive stair mounting |

---

## 5. Power and Wiring Concept

Phase 1 will use an existing lab-style 12V DC power supply if suitable.

The proposed power flow is:

```text
12V DC supply
  -> fused branch for each step
  -> local 5V converter inside each step module
  -> Raspberry Pi, speaker amplifier, sensor, lighting, and RS-485 hardware
```

Important safety and wiring decisions:

* Do not distribute 5V across the staircase.
* Use 12V distribution with local 5V conversion at each step.
* Include an inline fuse for each step branch.
* Use removable low-voltage connectors and labeled wiring.
* Keep wiring protected and out of the walking path.

---

## 6. Enclosure and Mounting Concept

The modules must fit flush into the side alcove of each step. The design should not protrude into the walking path or require permanent modification of the staircase.

The current mounting concept is:

* existing proto boxes for early electronics assembly,
* limited 3D-printed fit-test pieces or brackets as needed,
* magnetic attachment to the steel side structure, pending testing,
* rubber or TPU pads to improve grip and avoid surface damage,
* printed geometry to prevent sliding or protrusion,
* temporary safety tether during early testing.

Friction-fit alone is not considered sufficient because shifting over time could create a safety concern.

---

## 7. Explicit Phase 1 Validation Goals

Phase 1 should answer the following questions before Phase 2 funding is requested.

### Fit and Safety

Can the electronics fit in a flush side-mounted enclosure without protruding into the walking path?

### Foot Detection

Can the existing VL53L0X sensor reliably detect when a foot is placed on and removed from a step, and do the VL53L4CD or VL53L1X provide a meaningful improvement?

### Local Audio

Can the Raspberry Pi Zero 2 W produce responsive local sound through the amplifier and speaker?

### Lighting

Is the RGBW module visible enough to illuminate the local step area without glare, distraction, or heat problems?

### Power

Does the 12V distribution and local 5V conversion remain stable when audio and lighting are active?

### RS-485 Configuration

Can a laptop communicate with all three modules over a wired RS-485 bus?

### Mounting

Can magnets and printed geometry hold the modules securely and non-destructively?

### Cable Routing

Can wiring between steps be protected, labeled, removable, and kept away from the walking path?

### Facilities Readiness

What changes are needed before any semi-permanent or permanent installation is requested?

---

## 8. Phase 1 Budget Summary

| Category                                            | Estimated Cost |
| --------------------------------------------------- | -------------: |
| Core step electronics                               |          ~$191 |
| Lighting                                            |           ~$58 |
| RS-485 communication hardware                       |           ~$56 |
| Power, wiring, fuses, and connectors                |          ~$150 |
| Proto-box, limited printed fit-test, and magnetic mounting hardware |           ~$75 |
| Integration reserve, shipping, and price variance   |          ~$175 |
| **Recommended Phase 1 request**                     |  **$705–$725** |

The reserve is included because physical electronics prototypes often require small additional parts such as connectors, adapters, wire lengths, mounting hardware, or replacement support components once assembly begins.

---

## 9. What Is Deliberately Deferred to Phase 2

Phase 1 does **not** include:

* custom PCBs,
* spare modules,
* new Pico W boards,
* Raspberry Pi 5 touchscreen controller,
* dedicated final DC power supply,
* final enclosure design,
* full 3–6 step semi-permanent MVP,
* full 24-step hardware purchase,
* final facilities-approved installation plan.

These should wait until Phase 1 identifies what the final design actually needs.

---

## 10. Expected Phase 1 Deliverables

By the end of Phase 1, the team should have:

1. A working three-step proof-of-concept demo.
2. Notes on which hardware worked and which should change.
3. Photos of the enclosure/proto-box fit and wiring layout.
4. Sensor reliability observations comparing VL53L0X, VL53L4CD, and VL53L1X.
5. Audio and lighting test results.
6. Basic power/current measurements.
7. RS-485 communication test results.
8. Mounting stability observations.
9. A revised recommendation for Phase 2.

---

## 11. Summary

Phase 1 is a controlled, low-cost engineering validation build. It is designed to answer the most important design questions before requesting funds for a larger, more permanent installation.

The updated Phase 1 plan uses existing inventory where practical, reduces the enclosure budget, avoids purchasing additional Pico W boards, and treats existing VL53L0X sensors as the baseline while still testing newer ToF options.

The goal is not just to make three steps work. The goal is to learn enough from three steps to make the next funding request accurate, safe, and technically justified.
