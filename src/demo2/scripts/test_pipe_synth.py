#!/usr/bin/env python3

"""
Experiment with procedurally synthesized falling-pipe sounds.

The timing model is inspired by a slender rod rocking end-to-end on a
horizontal surface.

For a uniform slender rod of length L pivoting temporarily about one end:

    I_end = (1/3) m L^2

Near horizontal, gravity produces approximately constant angular
acceleration:

    alpha ~= 3g / (2L)

For a small maximum rocking angle theta, this gives an approximate time
between floor impacts of:

    delta_t ~= 4 * sqrt(L * theta / (3g))

Each collision loses energy. If the angular velocity retained after an
impact is multiplied by a restitution factor e, the next rocking angle is
approximately multiplied by e^2. Consequently, successive impact intervals
shrink approximately by e.

This is a deliberately simplified physical model. A real loose pipe may
also slide, roll, flex, and bounce vertically.

Acoustically, both Tubular Bell notes are struck at every impact. Their
relative strengths alternate to approximate different modal excitation
when opposite ends contact the floor.
"""

from __future__ import annotations

import math
import random
import shutil
import subprocess
import time
from dataclasses import dataclass

from piano_staircase_demo.piano import (
    DEFAULT_GAIN,
    DEFAULT_SOUNDFONT,
)


MIDI_CHANNEL = 0
TUBULAR_BELLS_PROGRAM = 14

GRAVITY_M_S2 = 9.80665

LOW_RESONANCE = 66
HIGH_RESONANCE = 73


@dataclass(frozen=True)
class PipeModel:
    """Parameters describing one synthetic falling pipe."""

    name: str

    length_m: float
    initial_angle_deg: float

    angular_restitution: float

    impacts: int

    initial_velocity: int
    velocity_floor: int

    primary_mix: float
    secondary_mix: float

    contact_seconds: float

    timing_jitter_fraction: float = 0.02
    velocity_jitter: int = 3


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


def rocking_interval_seconds(
    *,
    length_m: float,
    angle_radians: float,
) -> float:
    """
    Estimate time between alternate end impacts.

    This uses the small-angle approximation for a uniform slender rod
    rocking about its endpoints:

        dt ~= 4 sqrt(L theta / 3g)
    """

    if length_m <= 0:
        raise ValueError(
            "length_m must be greater than zero."
        )

    if angle_radians <= 0:
        raise ValueError(
            "angle_radians must be greater than zero."
        )

    return 4.0 * math.sqrt(
        (
            length_m
            * angle_radians
        )
        / (
            3.0
            * GRAVITY_M_S2
        )
    )


def clamp_midi_velocity(
    value: float,
) -> int:
    """Clamp a calculated velocity to the MIDI range."""

    return max(
        1,
        min(
            127,
            round(value),
        ),
    )


def impact(
    process: subprocess.Popen[str],
    *,
    primary_note: int,
    secondary_note: int,
    velocity: int,
    primary_mix: float,
    secondary_mix: float,
    contact_seconds: float,
    rng: random.Random,
    velocity_jitter: int,
) -> None:
    """
    Produce one short metallic collision.

    Both resonances occur on every collision. Opposite pipe ends alter
    their relative emphasis rather than changing the physical modes.
    """

    jitter = rng.randint(
        -velocity_jitter,
        velocity_jitter,
    )

    impact_velocity = (
        velocity
        + jitter
    )

    primary_velocity = clamp_midi_velocity(
        impact_velocity
        * primary_mix
    )

    secondary_velocity = clamp_midi_velocity(
        impact_velocity
        * secondary_mix
    )

    send(
        process,
        (
            f"noteon {MIDI_CHANNEL} "
            f"{primary_note} "
            f"{primary_velocity}"
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

    #
    # Floor contact is brief. The SoundFont's release tail supplies
    # the continuing metallic ringing after the contact ends.
    #
    time.sleep(
        contact_seconds
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
    model: PipeModel,
    rng: random.Random,
) -> None:
    """Play one end-to-end rocking pipe."""

    angle = math.radians(
        model.initial_angle_deg
    )

    velocity = float(
        model.initial_velocity
    )

    print()
    print(
        model.name
    )

    print(
        f"  length:       "
        f"{model.length_m:.2f} m"
    )

    print(
        f"  initial lift: "
        f"{model.initial_angle_deg:.1f} degrees"
    )

    print(
        f"  restitution:  "
        f"{model.angular_restitution:.2f}"
    )

    print()

    for impact_number in range(
        model.impacts
    ):
        interval = (
            rocking_interval_seconds(
                length_m=model.length_m,
                angle_radians=angle,
            )
        )

        #
        # Real impacts will not be perfectly repeatable. Keep this tiny;
        # we want physical imperfection, not random rhythm.
        #
        timing_multiplier = (
            1.0
            + rng.uniform(
                -model.timing_jitter_fraction,
                model.timing_jitter_fraction,
            )
        )

        interval *= (
            timing_multiplier
        )

        current_velocity = max(
            model.velocity_floor,
            round(
                velocity
            ),
        )

        #
        # A single tube keeps the same modes. We merely change which
        # resonance is more strongly excited at alternating contacts.
        #
        if impact_number % 2 == 0:
            primary_note = (
                LOW_RESONANCE
            )

            secondary_note = (
                HIGH_RESONANCE
            )

        else:
            primary_note = (
                HIGH_RESONANCE
            )

            secondary_note = (
                LOW_RESONANCE
            )

        print(
            f"  impact "
            f"{impact_number + 1}: "
            f"{interval:.3f} s, "
            f"velocity "
            f"{current_velocity}"
        )

        impact(
            process,
            primary_note=primary_note,
            secondary_note=secondary_note,
            velocity=current_velocity,
            primary_mix=model.primary_mix,
            secondary_mix=model.secondary_mix,
            contact_seconds=(
                model.contact_seconds
            ),
            rng=rng,
            velocity_jitter=(
                model.velocity_jitter
            ),
        )

        if (
            impact_number
            < model.impacts - 1
        ):
            #
            # interval represents impact-to-impact time, so subtract the
            # short contact pulse we have already waited through.
            #
            remaining_wait = max(
                0.0,
                interval
                - model.contact_seconds,
            )

            time.sleep(
                remaining_wait
            )

        #
        # Retained angular speed is multiplied by e.
        #
        # Since rocking height is proportional to angular speed squared
        # in this small-angle approximation:
        #
        #     theta_next ~= e^2 theta
        #
        # This automatically causes the intervals to get shorter.
        #
        angle *= (
            model.angular_restitution
            ** 2
        )

        velocity *= (
            model.angular_restitution
        )


CLASSIC_PIPE = PipeModel(
    name="Classic medium pipe",
    length_m=0.90,
    initial_angle_deg=18.0,
    angular_restitution=0.76,
    impacts=7,
    initial_velocity=127,
    velocity_floor=28,
    primary_mix=1.00,
    secondary_mix=0.48,
    contact_seconds=0.030,
)


HEAVY_PIPE = PipeModel(
    name="Long heavy pipe",
    length_m=1.25,
    initial_angle_deg=20.0,
    angular_restitution=0.79,
    impacts=7,
    initial_velocity=127,
    velocity_floor=30,
    primary_mix=1.00,
    secondary_mix=0.42,
    contact_seconds=0.035,
)


LIGHT_PIPE = PipeModel(
    name="Short light pipe",
    length_m=0.55,
    initial_angle_deg=15.0,
    angular_restitution=0.72,
    impacts=6,
    initial_velocity=118,
    velocity_floor=25,
    primary_mix=1.00,
    secondary_mix=0.52,
    contact_seconds=0.025,
)


SLOW_PIPE = PipeModel(
    name="Slow dramatic pipe",
    length_m=1.10,
    initial_angle_deg=25.0,
    angular_restitution=0.78,
    impacts=8,
    initial_velocity=127,
    velocity_floor=27,
    primary_mix=1.00,
    secondary_mix=0.46,
    contact_seconds=0.032,
)


def play_random_pipe(
    process: subprocess.Popen[str],
) -> None:
    """Generate one reproducible physics-inspired pipe."""

    seed = random.randrange(
        0,
        2**32,
    )

    rng = random.Random(
        seed
    )

    model = PipeModel(
        name=(
            f"Random pipe "
            f"(seed {seed})"
        ),
        length_m=rng.uniform(
            0.55,
            1.30,
        ),
        initial_angle_deg=rng.uniform(
            14.0,
            26.0,
        ),
        angular_restitution=rng.uniform(
            0.71,
            0.82,
        ),
        impacts=rng.randint(
            6,
            9,
        ),
        initial_velocity=rng.randint(
            116,
            127,
        ),
        velocity_floor=rng.randint(
            23,
            32,
        ),
        primary_mix=1.0,
        secondary_mix=rng.uniform(
            0.38,
            0.58,
        ),
        contact_seconds=rng.uniform(
            0.024,
            0.038,
        ),
        timing_jitter_fraction=rng.uniform(
            0.01,
            0.035,
        ),
        velocity_jitter=rng.randint(
            1,
            5,
        ),
    )

    play_pipe(
        process,
        model=model,
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

    rng = random.Random()

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
            "=== Falling-pipe physics laboratory ==="
        )

        print()
        print(
            "1 = classic medium pipe"
        )

        print(
            "2 = long/heavy pipe"
        )

        print(
            "3 = short/light pipe"
        )

        print(
            "4 = slow dramatic pipe"
        )

        print(
            "r = randomized pipe"
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
                play_pipe(
                    process,
                    model=CLASSIC_PIPE,
                    rng=rng,
                )

            elif command == "2":
                play_pipe(
                    process,
                    model=HEAVY_PIPE,
                    rng=rng,
                )

            elif command == "3":
                play_pipe(
                    process,
                    model=LIGHT_PIPE,
                    rng=rng,
                )

            elif command == "4":
                play_pipe(
                    process,
                    model=SLOW_PIPE,
                    rng=rng,
                )

            elif command == "r":
                play_random_pipe(
                    process
                )

            else:
                print(
                    "Choose 1, 2, 3, 4, r, or q."
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
