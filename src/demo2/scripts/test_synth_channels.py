#!/usr/bin/env python3

"""
Multi-channel FluidSynth smoke test for Piano Staircase Demo 2.

Channel 0 uses Acoustic Grand Piano.
Channels 1 and 2 use Tubular Bells.
"""

from __future__ import annotations

import time

from piano_staircase_demo.synth import (
    FluidSynthEngine,
)


PIANO_CHANNEL = 0
PIPE_A_CHANNEL = 1
PIPE_B_CHANNEL = 2

PIANO_PROGRAM = 0
TUBULAR_BELLS_PROGRAM = 14


def main(
) -> None:
    """Exercise independent MIDI channels."""

    print(
        "=== Multi-channel FluidSynth test ==="
    )

    print()

    with FluidSynthEngine() as synth:
        synth.configure_channel(
            PIANO_CHANNEL,
            bank=0,
            program=PIANO_PROGRAM,
            volume=127,
        )

        synth.configure_channel(
            PIPE_A_CHANNEL,
            bank=0,
            program=TUBULAR_BELLS_PROGRAM,
            volume=70,
        )

        synth.configure_channel(
            PIPE_B_CHANNEL,
            bank=0,
            program=TUBULAR_BELLS_PROGRAM,
            volume=70,
        )

        print(
            "1. Piano C4"
        )

        synth.note_on(
            PIANO_CHANNEL,
            60,
            velocity=100,
        )

        time.sleep(
            0.35
        )

        synth.note_off(
            PIANO_CHANNEL,
            60,
        )

        time.sleep(
            0.5
        )

        print(
            "2. Pipe A"
        )

        synth.note_on(
            PIPE_A_CHANNEL,
            66,
            velocity=115,
        )

        synth.note_on(
            PIPE_A_CHANNEL,
            73,
            velocity=60,
        )

        time.sleep(
            0.04
        )

        synth.note_off(
            PIPE_A_CHANNEL,
            66,
        )

        synth.note_off(
            PIPE_A_CHANNEL,
            73,
        )

        time.sleep(
            0.25
        )

        print(
            "3. Pipe A + Pipe B simultaneously"
        )

        synth.note_on(
            PIPE_A_CHANNEL,
            66,
            velocity=110,
        )

        synth.note_on(
            PIPE_A_CHANNEL,
            73,
            velocity=55,
        )

        synth.note_on(
            PIPE_B_CHANNEL,
            62,
            velocity=105,
        )

        synth.note_on(
            PIPE_B_CHANNEL,
            69,
            velocity=52,
        )

        time.sleep(
            0.05
        )

        synth.note_off(
            PIPE_A_CHANNEL,
            66,
        )

        synth.note_off(
            PIPE_A_CHANNEL,
            73,
        )

        synth.note_off(
            PIPE_B_CHANNEL,
            62,
        )

        synth.note_off(
            PIPE_B_CHANNEL,
            69,
        )

        time.sleep(
            1.5
        )

        print()
        print(
            "Test complete."
        )


if __name__ == "__main__":
    main()
