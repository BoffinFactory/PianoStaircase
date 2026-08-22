#!/usr/bin/env python3

"""
Sensor-controlled sustained-piano diagnostic for Piano Staircase Demo 2.

This combines:

    VL53L0X
        ↓
    PresenceTracker
        ↓
    PianoEngine

Interaction behavior:

    hand enters active region
        -> NOTE ON

    hand remains present
        -> no retrigger

    hand leaves release region
        -> NOTE OFF

Invalid VL53L0X readings are ignored so a transient bad sample does not
incorrectly release a held note.

Press Ctrl+C to stop.
"""

from __future__ import annotations

import argparse
import signal
import time

from piano_staircase_demo.piano import (
    DEFAULT_GAIN,
    DEFAULT_VELOCITY,
    MIDI_NOTES,
    PianoEngine,
)
from piano_staircase_demo.presence import (
    PresenceEvent,
    PresenceTracker,
)
from piano_staircase_demo.sensor import (
    DistanceSensor,
)


DEFAULT_ENTER_MM = 500
DEFAULT_EXIT_MM = 750
DEFAULT_HZ = 30.0
DEFAULT_NOTE = "C4"


def parse_args(
) -> argparse.Namespace:
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description=(
            "Test sustained piano articulation "
            "using the Demo 2 VL53L0X sensor."
        )
    )

    parser.add_argument(
        "--enter-mm",
        type=int,
        default=DEFAULT_ENTER_MM,
        help=(
            "Distance at or below which presence begins "
            f"(default: {DEFAULT_ENTER_MM} mm)."
        ),
    )

    parser.add_argument(
        "--exit-mm",
        type=int,
        default=DEFAULT_EXIT_MM,
        help=(
            "Distance at or above which presence ends "
            f"(default: {DEFAULT_EXIT_MM} mm)."
        ),
    )

    parser.add_argument(
        "--enter-samples",
        type=int,
        default=1,
        help=(
            "Consecutive close samples required to enter "
            "(default: 1)."
        ),
    )

    parser.add_argument(
        "--exit-samples",
        type=int,
        default=1,
        help=(
            "Consecutive far samples required to exit "
            "(default: 1)."
        ),
    )

    parser.add_argument(
        "--hz",
        type=float,
        default=DEFAULT_HZ,
        help=(
            "Sensor polling frequency "
            f"(default: {DEFAULT_HZ:g} Hz)."
        ),
    )

    parser.add_argument(
        "--note",
        choices=tuple(
            MIDI_NOTES.keys()
        ),
        default=DEFAULT_NOTE,
        help=(
            "Piano note controlled by the sensor "
            f"(default: {DEFAULT_NOTE})."
        ),
    )

    parser.add_argument(
        "--velocity",
        type=int,
        default=DEFAULT_VELOCITY,
        help=(
            "MIDI attack velocity "
            f"(default: {DEFAULT_VELOCITY})."
        ),
    )

    parser.add_argument(
        "--gain",
        type=float,
        default=DEFAULT_GAIN,
        help=(
            "FluidSynth master gain "
            f"(default: {DEFAULT_GAIN:g})."
        ),
    )

    return parser.parse_args()


def main(
) -> None:
    """Run the sensor-controlled piano diagnostic."""

    args = parse_args()

    if args.hz <= 0:
        raise SystemExit(
            "--hz must be greater than zero."
        )

    if not 1 <= args.velocity <= 127:
        raise SystemExit(
            "--velocity must be between 1 and 127."
        )

    stop_requested = False

    def request_stop(
        signum,
        frame,
    ) -> None:
        nonlocal stop_requested

        stop_requested = True

    #
    # Do not allow KeyboardInterrupt to land in the middle of an I2C
    # transaction. The handler only requests a clean exit from the loop.
    #
    signal.signal(
        signal.SIGINT,
        request_stop,
    )

    try:
        presence = PresenceTracker(
            enter_distance_mm=args.enter_mm,
            exit_distance_mm=args.exit_mm,
            enter_samples=args.enter_samples,
            exit_samples=args.exit_samples,
        )

    except ValueError as exc:
        raise SystemExit(
            f"Invalid presence configuration: {exc}"
        ) from exc

    print(
        "=== Sensor-Controlled Piano Diagnostic ==="
    )

    print()
    print(
        f"Enter distance:    {args.enter_mm} mm"
    )

    print(
        f"Exit distance:     {args.exit_mm} mm"
    )

    print(
        f"Polling frequency: {args.hz:g} Hz"
    )

    print(
        f"Note:              {args.note}"
    )

    print(
        f"Velocity:          {args.velocity}"
    )

    print(
        f"FluidSynth gain:   {args.gain:g}"
    )

    print()

    print(
        "Initializing VL53L0X..."
    )

    try:
        sensor = DistanceSensor()

    except Exception as exc:
        print()
        print(
            "ERROR: Unable to initialize the VL53L0X."
        )

        print()
        print(
            "Check sensor power, SDA/SCL wiring, "
            "and I2C address 0x29."
        )

        print()
        print(
            f"Python error: {exc}"
        )

        raise SystemExit(
            1
        ) from exc

    print(
        "Sensor initialized."
    )

    print(
        "Starting persistent FluidSynth piano..."
    )

    try:
        piano = PianoEngine(
            gain=args.gain,
            velocity=args.velocity,
        )

    except Exception:
        sensor.close()
        raise

    print(
        "Piano initialized."
    )

    print()
    print(
        "Move your hand into the active region."
    )

    print(
        "Hold it there, then move beyond the release distance."
    )

    print(
        "Press Ctrl+C to stop."
    )

    print()

    interval = (
        1.0
        / args.hz
    )

    next_sample = (
        time.monotonic()
    )

    invalid_samples = 0

    try:
        with sensor, piano:
            while not stop_requested:
                now = time.monotonic()

                if now < next_sample:
                    time.sleep(
                        next_sample
                        - now
                    )

                distance_mm = (
                    sensor.distance_mm
                )

                #
                # A transient invalid measurement must not become a false
                # EXIT. Preserve the current presence/note state instead.
                #
                if distance_mm is None:
                    invalid_samples += 1

                    next_sample += (
                        interval
                    )

                    continue

                event = presence.update(
                    distance_mm
                )

                if event is PresenceEvent.ENTER:
                    started = piano.note_on(
                        args.note,
                        velocity=args.velocity,
                    )

                    if started:
                        print(
                            f"ENTER  "
                            f"{distance_mm:4d} mm  "
                            f"-> NOTE ON  {args.note}"
                        )

                elif event is PresenceEvent.EXIT:
                    released = piano.note_off(
                        args.note
                    )

                    if released:
                        print(
                            f"EXIT   "
                            f"{distance_mm:4d} mm  "
                            f"-> NOTE OFF {args.note}"
                        )

                #
                # PresenceEvent.HELD intentionally does nothing.
                #
                # Thirty sensor readings per second should not produce
                # thirty hammer strikes per second.
                #

                next_sample += (
                    interval
                )

                #
                # If something stalls us substantially, resume normal
                # timing instead of rapidly processing catch-up samples.
                #
                if (
                    next_sample
                    < time.monotonic()
                    - interval
                ):
                    next_sample = (
                        time.monotonic()
                        + interval
                    )

    finally:
        print()
        print(
            "Diagnostic stopped."
        )

        print(
            f"Invalid sensor samples ignored: "
            f"{invalid_samples}"
        )


if __name__ == "__main__":
    main()
