#!/usr/bin/env python3

"""
Synchronized audio and lighting diagnostic for Piano Staircase Demo 2.

Plays a C4-E4-G4 sequence while illuminating the corresponding green, yellow, and blue lighting
channels.

Press Ctrl+C to stop early.
"""

import time

from piano_staircase_demo.audio import AudioSystem
from piano_staircase_demo.lighting import LightingSystem


NOTES = ("C4", "E4", "G4")

NOTE_DURATION_SECONDS = 0.35
NOTE_GAP_SECONDS = 0.08
SEQUENCE_GAP_SECONDS = 0.75
LEADING_SILENCE_SECONDS = 0.5

REPETITIONS = 3
LIGHT_BRIGHTNESS_PERCENT = 100


def wait_until(deadline: float) -> None:
    """Wait until a monotonic-clock deadline without accumulating drift."""

    remaining = deadline - time.monotonic()

    if remaining > 0:
        time.sleep(remaining)


def main() -> None:
    print("=== Piano Staircase Audio + Lighting Diagnostic ===")
    print()
    print("C4 -> GREEN")
    print("E4 -> YELLOW")
    print("G4 -> BLUE")
    print()

    with LightingSystem() as lights, AudioSystem() as audio:
        channels = (
            lights.green,
            lights.yellow,
            lights.blue,
        )

        sequence = audio.create_sequence(
            NOTES,
            note_duration_seconds=NOTE_DURATION_SECONDS,
            note_gap_seconds=NOTE_GAP_SECONDS,
            repetitions=REPETITIONS,
            sequence_gap_seconds=SEQUENCE_GAP_SECONDS,
            leading_silence_seconds=LEADING_SILENCE_SECONDS,
        )

        lights.all_off()

        print("Starting synchronized sequence...")
        print()

        start_time = time.monotonic()

        audio.play(
            sequence,
            blocking=False,
        )

        deadline = (
            start_time
            + LEADING_SILENCE_SECONDS
        )

        wait_until(deadline)

        for repetition in range(REPETITIONS):
            for index, channel in enumerate(channels):
                channel.set_brightness(
                    LIGHT_BRIGHTNESS_PERCENT
                )

                deadline += NOTE_DURATION_SECONDS
                wait_until(deadline)

                channel.off()

                if index < len(channels) - 1:
                    deadline += NOTE_GAP_SECONDS
                    wait_until(deadline)

            if repetition < REPETITIONS - 1:
                deadline += SEQUENCE_GAP_SECONDS
                wait_until(deadline)

        audio.wait()

    print()
    print("Diagnostic complete.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Diagnostic stopped.")
