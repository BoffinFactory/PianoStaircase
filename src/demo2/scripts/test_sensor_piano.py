#!/usr/bin/env python3

"""
Sensor-controlled piano diagnostic for Piano Staircase Demo 2.

Two interaction modes are available:

    distance
        Distance continuously selects a note from a chromatic scale.

        Moving the hand closer raises the pitch.
        Moving farther lowers the pitch.

        When the selected note changes:

            old note -> NOTE OFF
            new note -> NOTE ON

        This behaves somewhat like running a hand across piano keys.

    held
        Traditional sustained-presence behavior:

            ENTER -> NOTE ON
            HELD  -> no retrigger
            EXIT  -> NOTE OFF

Invalid VL53L0X readings are ignored so transient bad samples do not
incorrectly change or release the current note.

Press Ctrl+C to stop.
"""

from __future__ import annotations

import argparse
import signal
import time

from piano_staircase_demo.piano import (
    DEFAULT_GAIN,
    DEFAULT_VELOCITY,
    PianoEngine,
)
from piano_staircase_demo.presence import (
    PresenceEvent,
    PresenceTracker,
)
from piano_staircase_demo.sensor import (
    DistanceSensor,
)


DEFAULT_MODE = "distance"

DEFAULT_NEAR_MM = 250
DEFAULT_FAR_MM = 750

DEFAULT_LOW_NOTE = 60
DEFAULT_HIGH_NOTE = 72

DEFAULT_ENTER_MM = 500
DEFAULT_EXIT_MM = 750

DEFAULT_HZ = 30.0


NOTE_NAMES = (
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
)


def midi_note_name(
    midi_note: int,
) -> str:
    """Return a readable MIDI note name such as C4 or F#5."""

    pitch_class = (
        midi_note % 12
    )

    octave = (
        midi_note // 12
        - 1
    )

    return (
        f"{NOTE_NAMES[pitch_class]}"
        f"{octave}"
    )


def distance_to_note(
    distance_mm: int,
    *,
    near_mm: int,
    far_mm: int,
    low_note: int,
    high_note: int,
) -> int | None:
    """
    Map distance onto a chromatic MIDI-note range.

    Distances beyond far_mm are inactive.

    Distances closer than near_mm remain clamped to the highest note.
    """

    if distance_mm > far_mm:
        return None

    clamped_distance = max(
        near_mm,
        distance_mm,
    )

    position = (
        far_mm
        - clamped_distance
    ) / (
        far_mm
        - near_mm
    )

    note_span = (
        high_note
        - low_note
    )

    midi_note = round(
        low_note
        + position
        * note_span
    )

    return max(
        low_note,
        min(
            high_note,
            midi_note,
        ),
    )


def parse_args(
) -> argparse.Namespace:
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description=(
            "Test interactive piano behavior "
            "using the Demo 2 VL53L0X sensor."
        )
    )

    parser.add_argument(
        "--mode",
        choices=(
            "distance",
            "held",
        ),
        default=DEFAULT_MODE,
        help=(
            "Interaction style "
            f"(default: {DEFAULT_MODE})."
        ),
    )

    parser.add_argument(
        "--near-mm",
        type=int,
        default=DEFAULT_NEAR_MM,
        help=(
            "Distance corresponding to the highest note "
            f"(default: {DEFAULT_NEAR_MM} mm)."
        ),
    )

    parser.add_argument(
        "--far-mm",
        type=int,
        default=DEFAULT_FAR_MM,
        help=(
            "Distance corresponding to the lowest note; "
            "farther readings release the keyboard "
            f"(default: {DEFAULT_FAR_MM} mm)."
        ),
    )

    parser.add_argument(
        "--low-note",
        type=int,
        default=DEFAULT_LOW_NOTE,
        help=(
            "Lowest MIDI note in distance mode "
            f"(default: {DEFAULT_LOW_NOTE}, "
            f"{midi_note_name(DEFAULT_LOW_NOTE)})."
        ),
    )

    parser.add_argument(
        "--high-note",
        type=int,
        default=DEFAULT_HIGH_NOTE,
        help=(
            "Highest MIDI note in distance mode "
            f"(default: {DEFAULT_HIGH_NOTE}, "
            f"{midi_note_name(DEFAULT_HIGH_NOTE)})."
        ),
    )

    parser.add_argument(
        "--enter-mm",
        type=int,
        default=DEFAULT_ENTER_MM,
        help=(
            "Held mode ENTER threshold "
            f"(default: {DEFAULT_ENTER_MM} mm)."
        ),
    )

    parser.add_argument(
        "--exit-mm",
        type=int,
        default=DEFAULT_EXIT_MM,
        help=(
            "Held mode EXIT threshold "
            f"(default: {DEFAULT_EXIT_MM} mm)."
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

    parser.add_argument(
        "--hz",
        type=float,
        default=DEFAULT_HZ,
        help=(
            "Sensor polling frequency "
            f"(default: {DEFAULT_HZ:g} Hz)."
        ),
    )

    return parser.parse_args()


def validate_args(
    args: argparse.Namespace,
) -> None:
    """Validate command-line configuration."""

    if args.hz <= 0:
        raise SystemExit(
            "--hz must be greater than zero."
        )

    if not 1 <= args.velocity <= 127:
        raise SystemExit(
            "--velocity must be between 1 and 127."
        )

    if not 0 <= args.low_note <= 127:
        raise SystemExit(
            "--low-note must be between 0 and 127."
        )

    if not 0 <= args.high_note <= 127:
        raise SystemExit(
            "--high-note must be between 0 and 127."
        )

    if args.high_note <= args.low_note:
        raise SystemExit(
            "--high-note must be greater than --low-note."
        )

    if args.near_mm <= 0:
        raise SystemExit(
            "--near-mm must be greater than zero."
        )

    if args.far_mm <= args.near_mm:
        raise SystemExit(
            "--far-mm must be greater than --near-mm."
        )


def run_distance_mode(
    *,
    sensor: DistanceSensor,
    piano: PianoEngine,
    args: argparse.Namespace,
    stop_requested,
) -> int:
    """Run the continuous distance-to-pitch keyboard."""

    print()
    print(
        "=== DISTANCE KEYBOARD ==="
    )

    print()
    print(
        f"Near edge:   {args.near_mm} mm "
        f"-> {midi_note_name(args.high_note)}"
    )

    print(
        f"Far edge:    {args.far_mm} mm "
        f"-> {midi_note_name(args.low_note)}"
    )

    print(
        f"Notes:       "
        f"{midi_note_name(args.low_note)} "
        f"through "
        f"{midi_note_name(args.high_note)}"
    )

    print()
    print(
        "Move your hand toward and away from the sensor."
    )

    print(
        "Move beyond the far edge to release the current note."
    )

    print()

    interval = (
        1.0
        / args.hz
    )

    next_sample = (
        time.monotonic()
    )

    current_note: int | None = None
    invalid_samples = 0

    while not stop_requested():
        now = time.monotonic()

        if now < next_sample:
            time.sleep(
                next_sample
                - now
            )

        distance_mm = (
            sensor.distance_mm
        )

        if distance_mm is None:
            invalid_samples += 1
            next_sample += interval
            continue

        selected_note = distance_to_note(
            distance_mm,
            near_mm=args.near_mm,
            far_mm=args.far_mm,
            low_note=args.low_note,
            high_note=args.high_note,
        )

        #
        # Nothing changed. Let the currently selected piano key remain
        # held rather than retriggering it at sensor polling speed.
        #
        if selected_note == current_note:
            next_sample += interval
            continue

        #
        # Release the previous key first. FluidSynth's sampled piano
        # release tail will continue naturally underneath the new note.
        #
        if current_note is not None:
            piano.note_off(
                current_note
            )

        if selected_note is None:
            print(
                f"{distance_mm:4d} mm  "
                f"-> RELEASE"
            )

            current_note = None

        else:
            piano.note_on(
                selected_note,
                velocity=args.velocity,
            )

            print(
                f"{distance_mm:4d} mm  "
                f"-> "
                f"{midi_note_name(selected_note):3s} "
                f"(MIDI {selected_note})"
            )

            current_note = (
                selected_note
            )

        next_sample += interval

        if (
            next_sample
            < time.monotonic()
            - interval
        ):
            next_sample = (
                time.monotonic()
                + interval
            )

    if current_note is not None:
        piano.note_off(
            current_note
        )

    return invalid_samples


def run_held_mode(
    *,
    sensor: DistanceSensor,
    piano: PianoEngine,
    args: argparse.Namespace,
    stop_requested,
) -> int:
    """Run the earlier single-note PresenceTracker diagnostic."""

    tracker = PresenceTracker(
        enter_distance_mm=args.enter_mm,
        exit_distance_mm=args.exit_mm,
        enter_samples=1,
        exit_samples=1,
    )

    note = args.low_note

    print()
    print(
        "=== HELD NOTE ==="
    )

    print()
    print(
        f"Note:   {midi_note_name(note)}"
    )

    print(
        f"ENTER:  {args.enter_mm} mm"
    )

    print(
        f"EXIT:   {args.exit_mm} mm"
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

    while not stop_requested():
        now = time.monotonic()

        if now < next_sample:
            time.sleep(
                next_sample
                - now
            )

        distance_mm = (
            sensor.distance_mm
        )

        if distance_mm is None:
            invalid_samples += 1
            next_sample += interval
            continue

        event = tracker.update(
            distance_mm
        )

        if event is PresenceEvent.ENTER:
            piano.note_on(
                note,
                velocity=args.velocity,
            )

            print(
                f"ENTER  "
                f"{distance_mm:4d} mm "
                f"-> NOTE ON "
                f"{midi_note_name(note)}"
            )

        elif event is PresenceEvent.EXIT:
            piano.note_off(
                note
            )

            print(
                f"EXIT   "
                f"{distance_mm:4d} mm "
                f"-> NOTE OFF "
                f"{midi_note_name(note)}"
            )

        next_sample += interval

        if (
            next_sample
            < time.monotonic()
            - interval
        ):
            next_sample = (
                time.monotonic()
                + interval
            )

    piano.release_all()

    return invalid_samples


def main(
) -> None:
    """Run the selected sensor-piano diagnostic."""

    args = parse_args()

    validate_args(
        args
    )

    stop = False

    def request_stop(
        signum,
        frame,
    ) -> None:
        nonlocal stop

        stop = True

    def stop_requested(
    ) -> bool:
        return stop

    #
    # Request a clean shutdown instead of allowing KeyboardInterrupt to
    # interrupt an I2C register transaction.
    #
    signal.signal(
        signal.SIGINT,
        request_stop,
    )

    print(
        "=== Sensor-Controlled Piano Diagnostic ==="
    )

    print()
    print(
        f"Mode:              {args.mode}"
    )

    print(
        f"Polling frequency: {args.hz:g} Hz"
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

        print(
            "Check power, SDA/SCL wiring, "
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
        "Starting persistent FluidSynth..."
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

    print(
        "Press Ctrl+C to stop."
    )

    try:
        with sensor, piano:
            if args.mode == "distance":
                invalid_samples = (
                    run_distance_mode(
                        sensor=sensor,
                        piano=piano,
                        args=args,
                        stop_requested=stop_requested,
                    )
                )

            else:
                invalid_samples = (
                    run_held_mode(
                        sensor=sensor,
                        piano=piano,
                        args=args,
                        stop_requested=stop_requested,
                    )
                )

    finally:
        print()
        print(
            "Diagnostic stopped."
        )

        print(
            "Invalid sensor samples ignored: "
            f"{invalid_samples}"
        )


if __name__ == "__main__":
    main()
