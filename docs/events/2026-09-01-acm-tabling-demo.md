# ACM Piano Staircase Tabling Demo Plan

**Student Organization Event — September 1**

## Goal

Create an attention-grabbing ACM table demonstration that previews the upcoming Piano Staircase
workshops and encourages students to get involved.

The demo should be visually understandable, interactive, reliable, and capable of operating with
minimal supervision while officers are attending classes.

## Demo Concept

The table will feature a small three-step cardboard mockup of the Piano Staircase, approximately
15–16 inches wide with 4-inch treads and rises.

A VL53L0X distance sensor will face pedestrian traffic near the table. When someone crosses the
detection zone:

1. the three mock steps will illuminate sequentially;
2. a short three-note musical sequence will play;
3. the portable display will react and show information about the event;
4. after the person clears the sensor, the system will automatically re-arm.

Occasionally, such as every 8–10 triggers, the system may play a slightly longer musical/light
flourish to add variety.

Current planned step colors are green, yellow/gold, and blue, loosely incorporating Wright State and
ACM colors.

## Hardware

The primary controller will be the existing Raspberry Pi Zero 2 W used for the earlier
proof-of-concept.

Planned components include:

* Raspberry Pi Zero 2 W
* existing VL53L0X time-of-flight sensor
* three cardboard mock staircase steps
* conventional LEDs and transistor driver circuits
* breadboards, resistors, wiring, and related components from a BOJACK electronics kit
* 15.6-inch KYY portable HDMI display
* portable Bluetooth keyboard/touchpad for setup and operator control
* HDMI audio through the display if sufficiently loud; Bluetooth speaker as an alternative
* Anker 737 power bank

The exhibit is being designed to require **no wall outlet, laptop, or campus network connection**.

## Display

The Raspberry Pi will drive the portable display directly over HDMI.

The screen will likely show a simple live visualization including:

* Piano Staircase / ACM branding
* sensor distance and armed/triggered state
* trigger count
* current lighting/music sequence
* small snippets of the Python code controlling the system
* an invitation to help build the full staircase

The physical demonstration will continue functioning even if the display is unavailable.

## Recruitment

A prominent QR code will point to a dedicated Piano Staircase information page.

The page is expected to include:

* a brief explanation of the project
* information about upcoming workshops
* a WhenIsGood/Crab Fit-style availability poll
* a link to the WSU ACM Discord
* a link to the public Piano Staircase GitHub repository
* instructions for getting involved

The objective is to make joining the workshops require only one easy next step after someone becomes
interested.

## Reliability and Staffing

The exhibit should be capable of operating unattended, although an ACM officer or advisor will
hopefully be present during most of the event.

The final system will have:

* automatic sensor re-arming
* automatic startup where practical
* simple keyboard controls for manual triggering, mute, and reset
* battery-powered operation
* clearly labeled wiring and setup instructions
* a fallback recruiting display if part of the interactive system fails

## Schedule

**August 12–14**

* Receive and inventory electronics
* Test Pi power, HDMI display, audio, and keyboard
* Build and test one LED lighting channel

**August 14–17**

* Expand to three independently controlled lighting channels
* Integrate the existing VL53L0X sensor

**August 17–20**

* Integrate lighting, audio, and trigger logic
* Add basic musical variation and trigger counting

**August 20–24**

* Build the cardboard staircase enclosure
* Add diffusers and finalize physical wiring
* Feature freeze by approximately August 24

**August 25–29**

* Build/finalize display interface
* Complete project landing page and QR code
* Perform extended reliability and battery testing
* Prepare signage and operator instructions

**August 30–31**

* Full table-layout rehearsal
* Final testing and packing
* Avoid unnecessary last-minute feature changes

**September 1**

* Deploy at the student organization event

## Scope Priorities

**Required:** reliable sensor trigger, three illuminated steps, audio response, battery operation,
clear signage, and recruitment QR code.

**Preferred:** portable live display, periodic flourish, trigger counter, automatic startup, and
polished diffusion.

**Stretch goals:** physical mode switches, multiple elaborate sound modes, additional lighting
effects, and advanced visualizations.

The priority is a polished and dependable recruiting demonstration rather than maximizing technical
complexity.
