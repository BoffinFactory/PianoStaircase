#!/usr/bin/env python3

"""Audition candidate General MIDI voices for Demo 2 normal interaction."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from piano_staircase_demo.synth import (
    DEFAULT_GAIN,
    DEFAULT_SOUNDFONT,
    FluidSynthEngine,
)


CHANNEL = 0
BANK = 0
VELOCITY = 100
VOLUME = 127
EXPRESSION = 127

NOTE_HOLD_SECONDS = 0.8
NOTE_GAP_SECONDS = 0.35
VOICE_TAIL_SECONDS = 1.5

PATTERN = (
    ("C4", 60),
    ("E4", 64),
    ("G4", 67),
)

VOICES = {
    0: "Acoustic Grand Piano",
    4: "Electric Piano 1",
    5: "Electric Piano 2",
    8: "Celesta",
    11: "Vibraphone",
}


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description=(
            "Play the Demo 2 C4-E4-G4 pattern through selected "
            "TimGM General MIDI voices."
        )
    )

    parser.add_argument(
        "--soundfont",
        type=Path,
        default=DEFAULT_SOUNDFONT,
        help=(
            "SoundFont used by FluidSynth "
            f"(default: {DEFAULT_SOUNDFONT})."
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
        "--velocity",
        type=int,
        default=VELOCITY,
        help=(
            "MIDI note velocity "
            f"(default: {VELOCITY})."
        ),
    )

    parser.add_argument(
        "--hold",
        type=float,
        default=NOTE_HOLD_SECONDS,
        help=(
            "Seconds to hold each NOTE ON "
            f"(default: {NOTE_HOLD_SECONDS:g})."
        ),
    )

    parser.add_argument(
        "--gap",
        type=float,
        default=NOTE_GAP_SECONDS,
        help=(
            "Seconds after NOTE OFF before the next note "
            f"(default: {NOTE_GAP_SECONDS:g})."
        ),
    )

    parser.add_argument(
        "--program",
        type=int,
        action="append",
        choices=sorted(VOICES),
        help=(
            "Audition only this zero-based GM program. "
            "May be specified more than once. "
            "Default: audition all candidates."
        ),
    )

    args = parser.parse_args()

    if not 1 <= args.velocity <= 127:
        parser.error(
            "--velocity must be between 1 and 127."
        )

    if args.hold <= 0:
        parser.error(
            "--hold must be greater than zero."
        )

    if args.gap < 0:
        parser.error(
            "--gap cannot be negative."
        )

    if args.gain <= 0:
        parser.error(
            "--gain must be greater than zero."
        )

    return args


def audition_voice(
    synth: FluidSynthEngine,
    *,
    program: int,
    name: str,
    velocity: int,
    hold_seconds: float,
    gap_seconds: float,
) -> None:
    """Play one candidate voice using the common C4-E4-G4 pattern."""

    # Prevent the previous instrument's release tail from contaminating
    # the next audition. Individual notes are still allowed to decay
    # naturally after NOTE OFF.
    synth.all_sounds_off(
        CHANNEL
    )

    synth.configure_channel(
        CHANNEL,
        bank=BANK,
        program=program,
        volume=VOLUME,
        expression=EXPRESSION,
    )

    print()
    print(
        f"Program {program}: {name}"
    )

    print(
        "-" * (
            len(name)
            + len(str(program))
            + 10
        )
    )

    for note_name, midi_note in PATTERN:
        print(
            f"  {note_name}: NOTE ON for "
            f"{hold_seconds:.2f} s"
        )

        synth.note_on(
            CHANNEL,
            midi_note,
            velocity=velocity,
        )

        time.sleep(
            hold_seconds
        )

        synth.note_off(
            CHANNEL,
            midi_note,
        )

        time.sleep(
            gap_seconds
        )

    print(
        "  Letting release tail ring for "
        f"{VOICE_TAIL_SECONDS:.1f} s..."
    )

    time.sleep(
        VOICE_TAIL_SECONDS
    )


def main() -> None:
    """Run the voice audition."""

    args = parse_args()

    selected_programs = (
        args.program
        if args.program is not None
        else list(VOICES)
    )

    print(
        "=== Piano Staircase TimGM voice audition ==="
    )

    print()
    print(
        f"SoundFont: {args.soundfont}"
    )

    print(
        f"Gain:      {args.gain:g}"
    )

    print(
        f"Velocity:  {args.velocity}"
    )

    print(
        f"Hold:      {args.hold:.2f} s"
    )

    print(
        f"Gap:       {args.gap:.2f} s"
    )

    print()
    print(
        "Starting FluidSynth..."
    )

    with FluidSynthEngine(
        soundfont=args.soundfont,
        gain=args.gain,
    ) as synth:

        print(
            "FluidSynth is running."
        )

        for program in selected_programs:
            audition_voice(
                synth,
                program=program,
                name=VOICES[program],
                velocity=args.velocity,
                hold_seconds=args.hold,
                gap_seconds=args.gap,
            )

        synth.all_sounds_off(
            CHANNEL
        )

    print()
    print(
        "Voice audition complete."
    )


if __name__ == "__main__":
    main()
