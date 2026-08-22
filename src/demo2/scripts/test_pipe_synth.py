#!/usr/bin/env python3

"""
Experiment with procedurally synthesized falling-pipe sounds.

The timing model treats the pipe approximately as a slender rod rocking
end-to-end on a horizontal surface.

For a uniform slender rod of length L pivoting temporarily about one end:

    I_end = (1/3) m L^2

Near horizontal, gravity produces approximately constant angular
acceleration:

    alpha ~= 3g / (2L)

For a small maximum rocking angle theta, this gives an approximate time
between floor impacts of:

    delta_t ~= 4 * sqrt(L * theta / (3g))

Each collision loses energy. If angular velocity retained after an impact
is multiplied by restitution factor e, the next rocking angle is
approximately multiplied by e^2. Successive impact intervals therefore
shrink approximately by e.

The tonal model treats the pipe as a freely vibrating hollow beam. Its
structural bending frequency scales approximately as:

    f proportional to (1 / L^2) * sqrt(E * I / mu)

where:

    L   = pipe length
    E   = Young's modulus
    I   = second moment of area
    mu  = mass per unit length

For a hollow circular pipe:

    I = pi * (D^4 - d^4) / 64

where D and d are outer and inner diameters.

This lets length, diameter, wall thickness, density, and elasticity affect
the synthetic pipe's tone.

The calculated pitch variation is intentionally compressed before mapping
onto MIDI notes. TimGM6mb's Tubular Bells preset is a musical approximation,
not a physical pipe synthesizer, so extreme physical transpositions sound
less convincing rather than more accurate.
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

REFERENCE_LOW_RESONANCE = 66
REFERENCE_HIGH_RESONANCE = 73

PIPE_CHANNEL_VOLUME = 82
PIPE_EXPRESSION = 127

ALL_SOUNDS_OFF_CC = 120

#
# The physical model can easily move more than an octave for realistic
# geometry changes. Compress that range because large sample transpositions
# stop sounding like convincing Tubular Bells in this SoundFont.
#
PHYSICAL_PITCH_SCALE = 0.55
MAX_TONE_SHIFT_SEMITONES = 8

REFERENCE_LENGTH_M = 0.90
REFERENCE_OUTER_DIAMETER_M = 0.038
REFERENCE_WALL_THICKNESS_M = 0.0015


@dataclass(frozen=True)
class PipeMaterial:
    """Mechanical properties used by the simplified tonal model."""

    name: str

    young_modulus_pa: float
    density_kg_m3: float


STEEL = PipeMaterial(
    name="steel",
    young_modulus_pa=205e9,
    density_kg_m3=7850.0,
)


ALUMINUM = PipeMaterial(
    name="aluminum",
    young_modulus_pa=68.9e9,
    density_kg_m3=2700.0,
)


COPPER = PipeMaterial(
    name="copper",
    young_modulus_pa=117e9,
    density_kg_m3=8940.0,
)


PIPE_MATERIALS = (
    STEEL,
    ALUMINUM,
    COPPER,
)


@dataclass(frozen=True)
class PipeModel:
    """Parameters describing one synthetic falling pipe."""

    name: str

    material: PipeMaterial

    length_m: float
    outer_diameter_m: float
    wall_thickness_m: float

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


def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """Clamp a floating-point value to a range."""

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
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


def rocking_interval_seconds(
    *,
    length_m: float,
    angle_radians: float,
) -> float:
    """
    Estimate time between alternate end impacts.

    Small-angle approximation for a uniform slender rod:

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


def structural_frequency_factor(
    *,
    material: PipeMaterial,
    length_m: float,
    outer_diameter_m: float,
    wall_thickness_m: float,
) -> float:
    """
    Return a relative hollow-beam frequency factor.

    The common mode constant is omitted because only frequency ratios are
    needed:

        factor = sqrt(E I / mu) / L^2
    """

    if length_m <= 0:
        raise ValueError(
            "length_m must be greater than zero."
        )

    if outer_diameter_m <= 0:
        raise ValueError(
            "outer_diameter_m must be greater than zero."
        )

    if wall_thickness_m <= 0:
        raise ValueError(
            "wall_thickness_m must be greater than zero."
        )

    inner_diameter_m = (
        outer_diameter_m
        - 2.0
        * wall_thickness_m
    )

    if inner_diameter_m <= 0:
        raise ValueError(
            "Wall thickness leaves no hollow interior."
        )

    second_moment = (
        math.pi
        * (
            outer_diameter_m ** 4
            - inner_diameter_m ** 4
        )
        / 64.0
    )

    cross_section_area = (
        math.pi
        * (
            outer_diameter_m ** 2
            - inner_diameter_m ** 2
        )
        / 4.0
    )

    mass_per_length = (
        material.density_kg_m3
        * cross_section_area
    )

    return (
        math.sqrt(
            (
                material.young_modulus_pa
                * second_moment
            )
            / mass_per_length
        )
        / (
            length_m ** 2
        )
    )


REFERENCE_FREQUENCY_FACTOR = (
    structural_frequency_factor(
        material=STEEL,
        length_m=REFERENCE_LENGTH_M,
        outer_diameter_m=(
            REFERENCE_OUTER_DIAMETER_M
        ),
        wall_thickness_m=(
            REFERENCE_WALL_THICKNESS_M
        ),
    )
)


def calculate_tone(
    model: PipeModel,
) -> tuple[int, int, float, int]:
    """
    Calculate the two Tubular Bell notes for one pipe.

    Return:

        low note
        high note
        raw physical semitone shift
        applied/compressed semitone shift
    """

    factor = structural_frequency_factor(
        material=model.material,
        length_m=model.length_m,
        outer_diameter_m=(
            model.outer_diameter_m
        ),
        wall_thickness_m=(
            model.wall_thickness_m
        ),
    )

    frequency_ratio = (
        factor
        / REFERENCE_FREQUENCY_FACTOR
    )

    raw_semitone_shift = (
        12.0
        * math.log2(
            frequency_ratio
        )
    )

    applied_shift = round(
        clamp(
            (
                raw_semitone_shift
                * PHYSICAL_PITCH_SCALE
            ),
            -MAX_TONE_SHIFT_SEMITONES,
            MAX_TONE_SHIFT_SEMITONES,
        )
    )

    low_note = (
        REFERENCE_LOW_RESONANCE
        + applied_shift
    )

    high_note = (
        REFERENCE_HIGH_RESONANCE
        + applied_shift
    )

    return (
        low_note,
        high_note,
        raw_semitone_shift,
        applied_shift,
    )


def calculate_secondary_mix(
    model: PipeModel,
) -> float:
    """
    Calculate how prominently the secondary resonance should sound.

    Longer tubes tend to produce a richer spectrum of audible partials.
    Shorter tubes are therefore given a slightly weaker secondary resonance.

    This is a psychoacoustic approximation rather than a modal simulation.
    """

    length_fraction = clamp(
        (
            model.length_m
            - 0.55
        )
        / (
            1.30
            - 0.55
        ),
        0.0,
        1.0,
    )

    richness_multiplier = (
        0.82
        + (
            0.28
            * length_fraction
        )
    )

    return clamp(
        (
            model.secondary_mix
            * richness_multiplier
        ),
        0.30,
        0.54,
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
    # Physical contact is brief. The SoundFont release supplies the
    # continuing metallic ring after the pipe leaves the floor again.
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

    #
    # Previous Tubular Bell strikes can keep ringing long after the modeled
    # pipe has finished moving. Each test invocation represents a separate
    # pipe, so discard tails from the previous test.
    #
    send(
        process,
        (
            f"cc {MIDI_CHANNEL} "
            f"{ALL_SOUNDS_OFF_CC} 0"
        ),
    )

    time.sleep(
        0.025
    )

    (
        low_resonance,
        high_resonance,
        raw_tone_shift,
        applied_tone_shift,
    ) = calculate_tone(
        model
    )

    secondary_mix = (
        calculate_secondary_mix(
            model
        )
    )

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
        f"  material:       "
        f"{model.material.name}"
    )

    print(
        f"  length:         "
        f"{model.length_m:.2f} m"
    )

    print(
        f"  diameter:       "
        f"{model.outer_diameter_m * 1000:.1f} mm"
    )

    print(
        f"  wall thickness: "
        f"{model.wall_thickness_m * 1000:.1f} mm"
    )

    print(
        f"  initial lift:   "
        f"{model.initial_angle_deg:.1f} degrees"
    )

    print(
        f"  restitution:    "
        f"{model.angular_restitution:.2f}"
    )

    print(
        f"  raw tone shift: "
        f"{raw_tone_shift:+.2f} semitones"
    )

    print(
        f"  applied shift:  "
        f"{applied_tone_shift:+d} semitones"
    )

    print(
        f"  resonances:     "
        f"{low_resonance} / "
        f"{high_resonance}"
    )

    print(
        f"  secondary mix:  "
        f"{secondary_mix:.2f}"
    )

    print()

    for impact_number in range(
        model.impacts
    ):
        interval = rocking_interval_seconds(
            length_m=model.length_m,
            angle_radians=angle,
        )

        #
        # Real impacts will not be perfectly repeatable. Keep timing
        # variation small so this remains a rocking object rather than
        # a randomized rhythm.
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
        # A single pipe retains the same resonant frequencies. Alternating
        # contacts merely alter which resonance is emphasized.
        #
        if impact_number % 2 == 0:
            primary_note = (
                low_resonance
            )

            secondary_note = (
                high_resonance
            )

        else:
            primary_note = (
                high_resonance
            )

            secondary_note = (
                low_resonance
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
            secondary_mix=secondary_mix,
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
        # Since rocking height is proportional to angular speed squared:
        #
        #     theta_next ~= e^2 theta
        #
        angle *= (
            model.angular_restitution
            ** 2
        )

        velocity *= (
            model.angular_restitution
        )


CLASSIC_PIPE = PipeModel(
    name="Classic medium steel pipe",
    material=STEEL,
    length_m=0.90,
    outer_diameter_m=0.038,
    wall_thickness_m=0.0015,
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
    name="Long heavy steel pipe",
    material=STEEL,
    length_m=1.25,
    outer_diameter_m=0.048,
    wall_thickness_m=0.0025,
    initial_angle_deg=20.0,
    angular_restitution=0.79,
    impacts=7,
    initial_velocity=127,
    velocity_floor=30,
    primary_mix=1.00,
    secondary_mix=0.46,
    contact_seconds=0.035,
)


LIGHT_PIPE = PipeModel(
    name="Short light aluminum pipe",
    material=ALUMINUM,
    length_m=0.55,
    outer_diameter_m=0.030,
    wall_thickness_m=0.0012,
    initial_angle_deg=15.0,
    angular_restitution=0.72,
    impacts=6,
    initial_velocity=118,
    velocity_floor=25,
    primary_mix=1.00,
    secondary_mix=0.48,
    contact_seconds=0.025,
)


SLOW_PIPE = PipeModel(
    name="Slow copper pipe",
    material=COPPER,
    length_m=1.10,
    outer_diameter_m=0.042,
    wall_thickness_m=0.0015,
    initial_angle_deg=25.0,
    angular_restitution=0.78,
    impacts=8,
    initial_velocity=123,
    velocity_floor=27,
    primary_mix=1.00,
    secondary_mix=0.45,
    contact_seconds=0.032,
)


def create_random_pipe(
    seed: int,
) -> tuple[
    PipeModel,
    random.Random,
]:
    """Create one reproducible randomized physical pipe."""

    rng = random.Random(
        seed
    )

    material = rng.choices(
        PIPE_MATERIALS,
        weights=(
            0.60,
            0.25,
            0.15,
        ),
        k=1,
    )[0]

    outer_diameter_m = rng.uniform(
        0.028,
        0.052,
    )

    wall_thickness_m = rng.uniform(
        0.0010,
        0.0028,
    )

    model = PipeModel(
        name=(
            f"Random pipe "
            f"(seed {seed})"
        ),
        material=material,
        length_m=rng.uniform(
            0.55,
            1.30,
        ),
        outer_diameter_m=(
            outer_diameter_m
        ),
        wall_thickness_m=(
            wall_thickness_m
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
            0.40,
            0.50,
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

    return (
        model,
        rng,
    )


def play_random_pipe(
    process: subprocess.Popen[str],
    *,
    seed: int | None = None,
) -> None:
    """Generate or replay one reproducible physics-inspired pipe."""

    if seed is None:
        seed = random.randrange(
            0,
            2**32,
        )

    (
        model,
        rng,
    ) = create_random_pipe(
        seed
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
            (
                f"cc {MIDI_CHANNEL} "
                f"7 {PIPE_CHANNEL_VOLUME}"
            ),
        )

        send(
            process,
            (
                f"cc {MIDI_CHANNEL} "
                f"11 {PIPE_EXPRESSION}"
            ),
        )

        print(
            "=== Falling-pipe physics laboratory ==="
        )

        print()
        print(
            "1 = classic medium steel pipe"
        )

        print(
            "2 = long/heavy steel pipe"
        )

        print(
            "3 = short/light aluminum pipe"
        )

        print(
            "4 = slow copper pipe"
        )

        print(
            "r = randomized pipe"
        )

        print(
            "s <seed> = replay a random seed"
        )

        print(
            "q = quit"
        )

        print()

        while True:
            raw_command = input(
                "pipe> "
            ).strip()

            command = (
                raw_command.lower()
            )

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

            elif command.startswith(
                "s "
            ):
                try:
                    seed = int(
                        command.split(
                            maxsplit=1
                        )[1]
                    )

                except ValueError:
                    print(
                        "Seed must be an integer."
                    )

                    continue

                play_random_pipe(
                    process,
                    seed=seed,
                )

            else:
                print(
                    "Choose 1, 2, 3, 4, r, "
                    "s <seed>, or q."
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
