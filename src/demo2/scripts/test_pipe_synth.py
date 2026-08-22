#!/usr/bin/env python3

"""
Experiment with procedurally synthesized falling-pipe sounds.

This deliberately controls FluidSynth directly so different Tubular Bell
impact patterns can be explored before adding them to the Demo 2 audio
architecture.
"""

from __future__ import annotations

import random
import shutil
import subprocess
import time

from piano_staircase_demo.piano import (
    DEFAULT_GAIN,
    DEFAULT_SOUNDFONT,
)


MIDI_CHANNEL = 0
TUBULAR_BELLS_PROGRAM = 14


def send(
    process: subprocess.Popen[str],
    command: str,
) -> None:
    """Send one command to FluidSynth."""

    if process.stdin is None:
        raise RuntimeError(
            "FluidSynth stdin is unavailable."
        )

    process.stdin.write(
        command + "\n"
    )

    process.stdin.flush()


def strike(
    process: subprocess.Popen[str],
    *,
    primary_note: int,
    secondary_note: int,
    velocity: int,
    hold_seconds: float,
) -> None:
    """
    Produce one metallic impact.

    Both resonances sound on every impact, but the primary resonance is
    deliberately stronger.
    """

    secondary_velocity = max(
        1,
        round(
            velocity * 0.45
        ),
    )

    send(
        process,
        (
            f"noteon {MIDI_CHANNEL} "
            f"{primary_note} {velocity}"
        ),
    )

    send(
        process,
        (
            f"noteon {MIDI_CHANNEL} "
            f"{secondary_note} "
            f"{secondary_velocity}"
        ),
    )

    time.sleep(
        hold_seconds
    )

    send(
        process,
        (
            f"noteoff {MIDI_CHANNEL} "
            f"{primary_note}"
        ),
    )

    send(
        process,
        (
            f"noteoff {MIDI_CHANNEL} "
            f"{secondary_note}"
        ),
    )


def play_pipe(
    process: subprocess.Popen[str],
    *,
    low_note: int,
    high_note: int,
    impacts: int,
    initial_velocity: int,
    velocity_decay: float,
    initial_gap: float,
    gap_decay: float,
    jitter_seconds: float = 0.0,
    rng: random.Random | None = None,
) -> None:
    """Play one modeled falling-and-rocking pipe."""

    velocity = float(
        initial_velocity
    )

    gap = initial_gap

    for impact in range(
        impacts
    ):
        #
        # Alternate which resonance dominates as the pipe rocks from
        # one end to the other.
        #
        if impact % 2 == 0:
            primary = low_note
            secondary = high_note

        else:
            primary = high_note
            secondary = low_note

        current_gap = gap

        if (
            rng is not None
            and jitter_seconds > 0.0
        ):
            current_gap += rng.uniform(
                -jitter_seconds,
                jitter_seconds,
            )

        current_gap = max(
            0.035,
            current_gap,
        )

        #
        # Keep the physical contact brief. The SoundFont's release tail
        # provides the continuing metallic resonance.
        #
        hold_seconds = min(
            0.040,
            current_gap * 0.35,
        )

        strike(
            process,
            primary_note=primary,
            secondary_note=secondary,
            velocity=max(
                1,
                round(
                    velocity
                ),
            ),
            hold_seconds=hold_seconds,
        )

        if (
            impact
            < impacts - 1
        ):
            time.sleep(
                max(
                    0.0,
                    current_gap
                    - hold_seconds,
                )
            )

        velocity *= (
            velocity_decay
        )

        gap *= (
            gap_decay
        )


def play_classic(
    process: subprocess.Popen[str],
) -> None:
    """The 66/73 pipe that inspired this experiment."""

    print(
        "Classic pipe: notes 66 / 73"
    )

    play_pipe(
        process,
        low_note=66,
        high_note=73,
        impacts=6,
        initial_velocity=127,
        velocity_decay=0.82,
        initial_gap=0.130,
        gap_decay=0.78,
    )


def play_heavy(
    process: subprocess.Popen[str],
) -> None:
    """A larger, slower metallic pipe."""

    print(
        "Heavy pipe: notes 62 / 69"
    )

    play_pipe(
        process,
        low_note=62,
        high_note=69,
        impacts=6,
        initial_velocity=127,
        velocity_decay=0.85,
        initial_gap=0.175,
        gap_decay=0.80,
    )


def play_light(
    process: subprocess.Popen[str],
) -> None:
    """A smaller pipe with quicker rocking impacts."""

    print(
        "Light pipe: notes 70 / 77"
    )

    play_pipe(
        process,
        low_note=70,
        high_note=77,
        impacts=7,
        initial_velocity=115,
        velocity_decay=0.80,
        initial_gap=0.095,
        gap_decay=0.76,
    )


def play_random(
    process: subprocess.Popen[str],
) -> None:
    """Generate a reproducible randomized pipe."""

    seed = random.randrange(
        0,
        2**32,
    )

    rng = random.Random(
        seed
    )

    low_note = rng.choice(
        (
            62,
            64,
            66,
            68,
            70,
        )
    )

    high_note = (
        low_note + 7
    )

    impacts = rng.randint(
        5,
        8,
    )

    initial_velocity = rng.randint(
        112,
        127,
    )

    velocity_decay = rng.uniform(
        0.78,
        0.87,
    )

    initial_gap = rng.uniform(
        0.095,
        0.170,
    )

    gap_decay = rng.uniform(
        0.74,
        0.83,
    )

    jitter_seconds = rng.uniform(
        0.002,
        0.009,
    )

    print(
        f"Random pipe seed: {seed}"
    )

    print(
        f"  notes:          "
        f"{low_note} / {high_note}"
    )

    print(
        f"  impacts:        "
        f"{impacts}"
    )

    print(
        f"  velocity:       "
        f"{initial_velocity}"
    )

    print(
        f"  velocity decay: "
        f"{velocity_decay:.3f}"
    )

    print(
        f"  initial gap:    "
        f"{initial_gap:.3f} s"
    )

    print(
        f"  gap decay:      "
        f"{gap_decay:.3f}"
    )

    play_pipe(
        process,
        low_note=low_note,
        high_note=high_note,
        impacts=impacts,
        initial_velocity=(
            initial_velocity
        ),
        velocity_decay=(
            velocity_decay
        ),
        initial_gap=initial_gap,
        gap_decay=gap_decay,
        jitter_seconds=(
            jitter_seconds
        ),
        rng=rng,
    )


def main(
) -> None:
    """Run the interactive pipe-synthesis playground."""

    fluidsynth = shutil.which(
        "fluidsynth"
    )

    if fluidsynth is None:
        raise RuntimeError(
            "fluidsynth was not found."
        )

    process = subprocess.Popen(
        [
            fluidsynth,
            "-a",
            "pipewire",
            "-g",
            str(
                DEFAULT_GAIN
            ),
            "-n",
            str(
                DEFAULT_SOUNDFONT
            ),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )

    try:
        send(
            process,
            (
                f"select {MIDI_CHANNEL} "
                f"1 0 "
                f"{TUBULAR_BELLS_PROGRAM}"
            ),
        )

        send(
            process,
            f"cc {MIDI_CHANNEL} 7 127",
        )

        send(
            process,
            f"cc {MIDI_CHANNEL} 11 127",
        )

        print(
            "=== Synthetic falling-pipe laboratory ==="
        )

        print()
        print(
            "1 = classic 66/73 pipe"
        )

        print(
            "2 = heavier/larger pipe"
        )

        print(
            "3 = lighter/smaller pipe"
        )

        print(
            "r = generate a random pipe"
        )

        print(
            "q = quit"
        )

        print()

        while True:
            command = input(
                "pipe> "
            ).strip().lower()

            if command == "q":
                break

            if command == "1":
                play_classic(
                    process
                )

            elif command == "2":
                play_heavy(
                    process
                )

            elif command == "3":
                play_light(
                    process
                )

            elif command == "r":
                play_random(
                    process
                )

            else:
                print(
                    "Choose 1, 2, 3, r, or q."
                )

    finally:
        if (
            process.poll()
            is None
        ):
            try:
                send(
                    process,
                    "quit",
                )

                process.wait(
                    timeout=2.0
                )

            except (
                BrokenPipeError,
                subprocess.TimeoutExpired,
            ):
                process.terminate()

                try:
                    process.wait(
                        timeout=1.0
                    )

                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == "__main__":
    main()
