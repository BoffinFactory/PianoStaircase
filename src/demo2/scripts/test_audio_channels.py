#!/usr/bin/env python3

"""
Exercise the Demo 2 multi-channel audio system.

The test demonstrates:

    - several simultaneous effects;
    - independent note/effect/announcer channels;
    - the effects polyphony limit;
    - monophonic announcer behavior.

No GPIO or sensor hardware is required.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from piano_staircase_demo.audio import (
    AudioSystem,
)


DEFAULT_PIPE_WAV = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "audio"
    / "pipes.wav"
)


def parse_args(
) -> argparse.Namespace:
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description=(
            "Test independent and polyphonic "
            "Demo 2 audio channels."
        )
    )

    parser.add_argument(
        "--wav",
        type=Path,
        default=DEFAULT_PIPE_WAV,
        help=(
            "WAV file used for overlapping effects "
            f"(default: {DEFAULT_PIPE_WAV})."
        ),
    )

    parser.add_argument(
        "--voices",
        type=int,
        default=4,
        help=(
            "Number of overlapping effects to request "
            "(default: 4)."
        ),
    )

    parser.add_argument(
        "--spacing",
        type=float,
        default=0.30,
        help=(
            "Seconds between effect starts "
            "(default: 0.30)."
        ),
    )

    return parser.parse_args()


def main(
) -> None:
    """Run the multi-channel audio test."""

    args = parse_args()

    if args.voices < 1:
        raise SystemExit(
            "--voices must be at least 1."
        )

    if args.spacing < 0:
        raise SystemExit(
            "--spacing cannot be negative."
        )

    with AudioSystem() as audio:
        pipe = audio.load_wav(
            args.wav
        )

        # These musical tones stand in for future spoken announcer clips.
        announcer_placeholder = (
            audio.create_sequence(
                (
                    "G4",
                    "E4",
                    "C4",
                ),
                note_duration_seconds=0.25,
                note_gap_seconds=0.05,
            )
        )

        note_placeholder = (
            audio.create_sequence(
                ("C4",),
                note_duration_seconds=0.50,
            )
        )

        print(
            "=== Multi-channel audio test ==="
        )
        print()

        print(
            "Effect polyphony: "
            f"{audio.effects.max_voices}"
        )

        print(
            "Requested effects: "
            f"{args.voices}"
        )

        print()

        print(
            "Starting overlapping pipe effects..."
        )

        for number in range(
            1,
            args.voices + 1,
        ):
            accepted = (
                audio.effects.play(
                    pipe,
                    blocking=False,
                )
            )

            status = (
                "STARTED"
                if accepted
                else "DROPPED: EFFECT BUS FULL"
            )

            print(
                f"Pipe {number}: "
                f"{status} "
                "("
                f"{audio.effects.active_count}"
                "/"
                f"{audio.effects.max_voices}"
                " active"
                ")"
            )

            if args.spacing:
                time.sleep(
                    args.spacing
                )

        print()
        print(
            "Starting an ordinary note while "
            "the pipes are still playing..."
        )

        note_started = (
            audio.notes.play(
                note_placeholder,
                blocking=False,
            )
        )

        print(
            "Note channel: "
            + (
                "STARTED"
                if note_started
                else "BUSY"
            )
        )

        print()
        print(
            "Testing monophonic announcer behavior..."
        )

        first_announcement = (
            audio.announcer.play(
                announcer_placeholder,
                blocking=False,
            )
        )

        second_announcement = (
            audio.announcer.play(
                announcer_placeholder,
                blocking=False,
            )
        )

        print(
            "First announcement: "
            + (
                "STARTED"
                if first_announcement
                else "BUSY"
            )
        )

        print(
            "Immediate second announcement: "
            + (
                "STARTED"
                if second_announcement
                else "REJECTED AS EXPECTED"
            )
        )

        print()
        print(
            "Current channel state:"
        )

        print(
            "  notes:     "
            f"{audio.notes.active_count}"
        )

        print(
            "  effects:   "
            f"{audio.effects.active_count}"
        )

        print(
            "  announcer: "
            f"{audio.announcer.active_count}"
        )

        print()
        print(
            "Waiting for all playback to finish..."
        )

        audio.notes.wait()
        audio.effects.wait()
        audio.announcer.wait()

        print(
            "All channels idle."
        )


if __name__ == "__main__":
    main()
