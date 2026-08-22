#!/usr/bin/env python3

"""
Interactively test the persistent Demo 2 piano engine.

This test does not require the distance sensor or GPIO hardware. It lets the
operator manually reproduce the future ENTER / HELD / EXIT interaction.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from piano_staircase_demo.piano import (
    DEFAULT_GAIN,
    DEFAULT_SOUNDFONT,
    DEFAULT_VELOCITY,
    PianoEngine,
)


def parse_args(
) -> argparse.Namespace:
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description=(
            "Interactively test the Demo 2 "
            "persistent piano engine."
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
        default=DEFAULT_VELOCITY,
        help=(
            "Default MIDI note velocity "
            f"(default: {DEFAULT_VELOCITY})."
        ),
    )

    return parser.parse_args()


def print_help(
) -> None:
    """Display interactive commands."""

    print()
    print("Commands:")
    print()
    print("  c      NOTE ON  C4")
    print("  e      NOTE ON  E4")
    print("  g      NOTE ON  G4")
    print()
    print("  C      NOTE OFF C4")
    print("  E      NOTE OFF E4")
    print("  G      NOTE OFF G4")
    print()
    print("  off    release every held note")
    print("  status show held notes")
    print("  help   show these commands")
    print("  q      quit")
    print()


def main(
) -> None:
    """Run the interactive piano test."""

    args = parse_args()

    print(
        "=== Piano Staircase persistent piano test ==="
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

    print()
    print(
        "Starting FluidSynth..."
    )

    with PianoEngine(
        soundfont=args.soundfont,
        gain=args.gain,
        velocity=args.velocity,
    ) as piano:

        print(
            "FluidSynth is running."
        )

        print_help()

        while True:
            try:
                command = input(
                    "piano> "
                )

            except EOFError:
                print()
                break

            #
            # Do not strip before checking the capital note-off commands;
            # case deliberately distinguishes NOTE ON from NOTE OFF.
            #
            command = command.strip()

            if command == "q":
                break

            if command == "help":
                print_help()
                continue

            if command == "status":
                if piano.active_notes:
                    print(
                        "Held MIDI notes: "
                        + ", ".join(
                            str(note)
                            for note
                            in piano.active_notes
                        )
                    )

                else:
                    print(
                        "No notes are held."
                    )

                continue

            if command == "off":
                piano.release_all()

                print(
                    "All notes released."
                )

                continue

            if command in (
                "c",
                "e",
                "g",
            ):
                note_name = {
                    "c": "C4",
                    "e": "E4",
                    "g": "G4",
                }[
                    command
                ]

                started = piano.note_on(
                    note_name
                )

                if started:
                    print(
                        f"NOTE ON  {note_name}"
                    )

                else:
                    print(
                        f"{note_name} is already held "
                        "— no retrigger."
                    )

                continue

            if command in (
                "C",
                "E",
                "G",
            ):
                note_name = {
                    "C": "C4",
                    "E": "E4",
                    "G": "G4",
                }[
                    command
                ]

                released = piano.note_off(
                    note_name
                )

                if released:
                    print(
                        f"NOTE OFF {note_name}"
                    )

                else:
                    print(
                        f"{note_name} was not held."
                    )

                continue

            print(
                "Unknown command. "
                "Type 'help'."
            )

    print()
    print(
        "Piano test complete."
    )


if __name__ == "__main__":
    main()
