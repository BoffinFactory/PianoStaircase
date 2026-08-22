"""
Physics-inspired falling-pipe synthesis for Piano Staircase Demo 2.

This module models several independently falling / rocking pipes and
schedules their MIDI impacts without sleeping or blocking.

A caller repeatedly invokes PipeSystem.update(). Each active pipe keeps its
own:

    physical properties
    impact schedule
    MIDI channel
    resonance frequencies
    velocity decay

This allows several simulated pipes to fall simultaneously while the main
application remains responsive to sensors, buttons, lighting, and display
updates.

The timing model treats a pipe approximately as a slender rod rocking
end-to-end on a horizontal surface.

For a small rocking angle:

    delta_t ~= 4 * sqrt(L * theta / (3g))

The tonal model treats the pipe approximately as a freely vibrating hollow
beam:

    f proportional to (1 / L^2) * sqrt(E * I / mu)

For a hollow circular pipe:

    I = pi * (D^4 - d^4) / 64

These are intentionally simplified models suitable for an interactive
educational demonstration, not a full rigid-body or acoustic simulation.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass

from piano_staircase_demo.synth import (
    FluidSynthEngine,
)


GRAVITY_M_S2 = 9.80665

TUBULAR_BELLS_BANK = 0
TUBULAR_BELLS_PROGRAM = 14

#
# Channel 0 is reserved for the normal piano.
#
# MIDI channel 9 is traditionally the General MIDI percussion channel, so
# keep the pipe pool comfortably away from it too.
#
DEFAULT_PIPE_CHANNELS = (
    1,
    2,
    3,
    4,
    5,
    6,
)

#
# Solo pipe testing used a higher channel volume. Multiple simultaneous
# Tubular Bell release tails add together quickly, so start conservatively.
#
DEFAULT_PIPE_CHANNEL_VOLUME = 60
DEFAULT_PIPE_EXPRESSION = 127

REFERENCE_LOW_RESONANCE = 66
REFERENCE_HIGH_RESONANCE = 73

PHYSICAL_PITCH_SCALE = 0.55
MAX_TONE_SHIFT_SEMITONES = 8

REFERENCE_LENGTH_M = 0.90
REFERENCE_OUTER_DIAMETER_M = 0.038
REFERENCE_WALL_THICKNESS_M = 0.0015


@dataclass(frozen=True)
class PipeMaterial:
    """Mechanical properties used by the simplified pipe model."""

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
    """Physical and collision parameters for one synthetic pipe."""

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

    timing_jitter_fraction: float
    velocity_jitter: int


@dataclass(frozen=True)
class PipeImpact:
    """One scheduled floor impact in a pipe simulation."""

    time_seconds: float

    primary_note: int
    secondary_note: int

    primary_velocity: int
    secondary_velocity: int

    contact_seconds: float


@dataclass(frozen=True)
class PipeSimulation:
    """Complete reproducible physics calculation for one falling pipe."""

    seed: int

    model: PipeModel

    low_resonance: int
    high_resonance: int

    raw_tone_shift: float
    applied_tone_shift: int

    secondary_mix: float

    impacts: tuple[
        PipeImpact,
        ...
    ]


@dataclass(frozen=True)
class PipeSnapshot:
    """
    Display-friendly state for one currently active pipe.

    This is deliberately independent of Rich or any particular display.
    """

    pipe_id: int
    channel: int

    seed: int

    material: str

    length_m: float
    outer_diameter_mm: float
    wall_thickness_mm: float

    restitution: float

    low_resonance: int
    high_resonance: int

    impact_number: int
    impact_count: int

    next_impact_seconds: (
        float
        | None
    )


@dataclass(frozen=True)
class PipeEvent:
    """One event produced while advancing the pipe scheduler."""

    kind: str

    pipe_id: int
    channel: int

    impact_number: (
        int
        | None
    ) = None

    impact_count: int = 0

    primary_note: (
        int
        | None
    ) = None

    secondary_note: (
        int
        | None
    ) = None


@dataclass
class _ActivePipe:
    """Mutable runtime state for one active falling pipe."""

    pipe_id: int
    channel: int

    simulation: PipeSimulation
    start_time: float

    next_impact_index: int = 0

    sounding_notes: (
        tuple[
            int,
            int,
        ]
        | None
    ) = None

    release_time: (
        float
        | None
    ) = None


def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """Clamp a floating-point value."""

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
    """Clamp a calculated MIDI velocity."""

    return max(
        1,
        min(
            127,
            round(
                value
            ),
        ),
    )


def rocking_interval_seconds(
    *,
    length_m: float,
    angle_radians: float,
) -> float:
    """
    Estimate time from one end impact to the next.

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

    return (
        4.0
        * math.sqrt(
            (
                length_m
                * angle_radians
            )
            / (
                3.0
                * GRAVITY_M_S2
            )
        )
    )


def structural_frequency_factor(
    *,
    material: PipeMaterial,
    length_m: float,
    outer_diameter_m: float,
    wall_thickness_m: float,
) -> float:
    """Return a relative hollow-beam resonance factor."""

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
) -> tuple[
    int,
    int,
    float,
    int,
]:
    """Calculate the two Tubular Bell resonances for a pipe."""

    factor = (
        structural_frequency_factor(
            material=model.material,
            length_m=model.length_m,
            outer_diameter_m=(
                model.outer_diameter_m
            ),
            wall_thickness_m=(
                model.wall_thickness_m
            ),
        )
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

    return (
        REFERENCE_LOW_RESONANCE
        + applied_shift,
        REFERENCE_HIGH_RESONANCE
        + applied_shift,
        raw_semitone_shift,
        applied_shift,
    )


def calculate_secondary_mix(
    model: PipeModel,
) -> float:
    """
    Estimate how strongly the second resonance should be heard.

    Longer tubes receive a slightly richer secondary resonance.
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
        + 0.28
        * length_fraction
    )

    return clamp(
        (
            model.secondary_mix
            * richness_multiplier
        ),
        0.30,
        0.54,
    )


def create_random_pipe_model(
    rng: random.Random,
) -> PipeModel:
    """Generate physically plausible randomized pipe properties."""

    material = rng.choices(
        PIPE_MATERIALS,
        weights=(
            0.60,
            0.25,
            0.15,
        ),
        k=1,
    )[0]

    return PipeModel(
        material=material,
        length_m=rng.uniform(
            0.55,
            1.30,
        ),
        outer_diameter_m=rng.uniform(
            0.028,
            0.052,
        ),
        wall_thickness_m=rng.uniform(
            0.0010,
            0.0028,
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


def create_pipe_simulation(
    *,
    seed: int | None = None,
) -> PipeSimulation:
    """Create one complete reproducible falling-pipe simulation."""

    if seed is None:
        seed = random.randrange(
            0,
            2**32,
        )

    rng = random.Random(
        seed
    )

    model = (
        create_random_pipe_model(
            rng
        )
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

    elapsed = 0.0

    impacts = []

    for impact_index in range(
        model.impacts
    ):
        current_velocity = max(
            model.velocity_floor,
            round(
                velocity
            ),
        )

        velocity_jitter = rng.randint(
            -model.velocity_jitter,
            model.velocity_jitter,
        )

        impact_velocity = (
            current_velocity
            + velocity_jitter
        )

        primary_velocity = (
            clamp_midi_velocity(
                impact_velocity
                * model.primary_mix
            )
        )

        secondary_velocity = (
            clamp_midi_velocity(
                impact_velocity
                * secondary_mix
            )
        )

        if impact_index % 2 == 0:
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

        impacts.append(
            PipeImpact(
                time_seconds=elapsed,
                primary_note=(
                    primary_note
                ),
                secondary_note=(
                    secondary_note
                ),
                primary_velocity=(
                    primary_velocity
                ),
                secondary_velocity=(
                    secondary_velocity
                ),
                contact_seconds=(
                    model.contact_seconds
                ),
            )
        )

        if (
            impact_index
            < model.impacts - 1
        ):
            interval = (
                rocking_interval_seconds(
                    length_m=(
                        model.length_m
                    ),
                    angle_radians=(
                        angle
                    ),
                )
            )

            interval *= (
                1.0
                + rng.uniform(
                    -model.timing_jitter_fraction,
                    model.timing_jitter_fraction,
                )
            )

            elapsed += (
                interval
            )

        angle *= (
            model.angular_restitution
            ** 2
        )

        velocity *= (
            model.angular_restitution
        )

    return PipeSimulation(
        seed=seed,
        model=model,
        low_resonance=(
            low_resonance
        ),
        high_resonance=(
            high_resonance
        ),
        raw_tone_shift=(
            raw_tone_shift
        ),
        applied_tone_shift=(
            applied_tone_shift
        ),
        secondary_mix=(
            secondary_mix
        ),
        impacts=tuple(
            impacts
        ),
    )


class PipeSystem:
    """
    Nonblocking scheduler for several simultaneous falling pipes.

    PipeSystem does not own FluidSynthEngine. The caller owns the shared
    synth and may also use it for the normal piano.
    """

    def __init__(
        self,
        synth: FluidSynthEngine,
        *,
        channels: tuple[
            int,
            ...
        ] = DEFAULT_PIPE_CHANNELS,
        channel_volume: int = (
            DEFAULT_PIPE_CHANNEL_VOLUME
        ),
        expression: int = (
            DEFAULT_PIPE_EXPRESSION
        ),
    ) -> None:
        if not channels:
            raise ValueError(
                "PipeSystem requires at least one MIDI channel."
            )

        if (
            len(
                set(
                    channels
                )
            )
            != len(
                channels
            )
        ):
            raise ValueError(
                "Pipe MIDI channels must be unique."
            )

        if not 0 <= channel_volume <= 127:
            raise ValueError(
                "channel_volume must be between 0 and 127."
            )

        if not 0 <= expression <= 127:
            raise ValueError(
                "expression must be between 0 and 127."
            )

        self._synth = (
            synth
        )

        self._channels = tuple(
            channels
        )

        self._free_channels = list(
            channels
        )

        self._active: dict[
            int,
            _ActivePipe,
        ] = {}

        self._next_pipe_id = 1

        for channel in self._channels:
            self._synth.configure_channel(
                channel,
                bank=(
                    TUBULAR_BELLS_BANK
                ),
                program=(
                    TUBULAR_BELLS_PROGRAM
                ),
                volume=(
                    channel_volume
                ),
                expression=(
                    expression
                ),
            )

    @property
    def maximum_pipes(
        self,
    ) -> int:
        """Return the number of simultaneous pipe channels."""

        return len(
            self._channels
        )

    @property
    def active_count(
        self,
    ) -> int:
        """Return the number of currently active simulations."""

        return len(
            self._active
        )

    @property
    def available_slots(
        self,
    ) -> int:
        """Return how many more pipes can currently start."""

        return len(
            self._free_channels
        )

    def _snapshot(
        self,
        active: _ActivePipe,
        *,
        now: float,
    ) -> PipeSnapshot:
        """Build display-friendly state for one pipe."""

        simulation = (
            active.simulation
        )

        model = (
            simulation.model
        )

        next_impact_seconds = None

        if (
            active.next_impact_index
            < len(
                simulation.impacts
            )
        ):
            impact = (
                simulation.impacts[
                    active.next_impact_index
                ]
            )

            next_impact_seconds = max(
                0.0,
                (
                    active.start_time
                    + impact.time_seconds
                    - now
                ),
            )

        return PipeSnapshot(
            pipe_id=(
                active.pipe_id
            ),
            channel=(
                active.channel
            ),
            seed=(
                simulation.seed
            ),
            material=(
                model.material.name
            ),
            length_m=(
                model.length_m
            ),
            outer_diameter_mm=(
                model.outer_diameter_m
                * 1000.0
            ),
            wall_thickness_mm=(
                model.wall_thickness_m
                * 1000.0
            ),
            restitution=(
                model.angular_restitution
            ),
            low_resonance=(
                simulation.low_resonance
            ),
            high_resonance=(
                simulation.high_resonance
            ),
            impact_number=(
                active.next_impact_index
            ),
            impact_count=(
                len(
                    simulation.impacts
                )
            ),
            next_impact_seconds=(
                next_impact_seconds
            ),
        )

    def snapshots(
        self,
        *,
        now: float | None = None,
    ) -> tuple[
        PipeSnapshot,
        ...
    ]:
        """Return state for all currently active pipes."""

        if now is None:
            now = (
                time.monotonic()
            )

        return tuple(
            self._snapshot(
                active,
                now=now,
            )
            for active
            in sorted(
                self._active.values(),
                key=lambda pipe: (
                    pipe.pipe_id
                ),
            )
        )

    def start_pipe(
        self,
        *,
        seed: int | None = None,
        now: float | None = None,
        delay_seconds: float = 0.0,
    ) -> PipeSnapshot | None:
        """
        Start another independent falling pipe.

        Return None if all pipe channels are currently occupied.
        """

        if not self._free_channels:
            return None

        if now is None:
            now = (
                time.monotonic()
            )

        if delay_seconds < 0:
            raise ValueError(
                "delay_seconds cannot be negative."
            )

        simulation = (
            create_pipe_simulation(
                seed=seed
            )
        )

        channel = (
            self._free_channels
            .pop(0)
        )

        pipe_id = (
            self._next_pipe_id
        )

        self._next_pipe_id += 1

        active = _ActivePipe(
            pipe_id=pipe_id,
            channel=channel,
            simulation=simulation,
            start_time=(
                now
                + delay_seconds
            ),
        )

        self._active[
            pipe_id
        ] = active

        return (
            self._snapshot(
                active,
                now=now,
            )
        )

    def _release_contact(
        self,
        active: _ActivePipe,
    ) -> None:
        """Release the short physical-contact notes for one impact."""

        if (
            active.sounding_notes
            is None
        ):
            return

        for note in (
            active.sounding_notes
        ):
            self._synth.note_off(
                active.channel,
                note,
            )

        active.sounding_notes = None
        active.release_time = None

    def _strike_next_impact(
        self,
        active: _ActivePipe,
        *,
        now: float,
    ) -> PipeEvent:
        """Start the next scheduled collision for one pipe."""

        impact_index = (
            active.next_impact_index
        )

        impact = (
            active.simulation
            .impacts[
                impact_index
            ]
        )

        self._synth.note_on(
            active.channel,
            impact.primary_note,
            velocity=(
                impact.primary_velocity
            ),
        )

        self._synth.note_on(
            active.channel,
            impact.secondary_note,
            velocity=(
                impact.secondary_velocity
            ),
        )

        active.sounding_notes = (
            impact.primary_note,
            impact.secondary_note,
        )

        #
        # Preserve the intended physical contact duration even if the
        # cooperative scheduler reached this impact a few milliseconds late.
        #
        active.release_time = (
            now
            + impact.contact_seconds
        )

        active.next_impact_index += 1

        return PipeEvent(
            kind="impact",
            pipe_id=(
                active.pipe_id
            ),
            channel=(
                active.channel
            ),
            impact_number=(
                impact_index + 1
            ),
            impact_count=(
                len(
                    active.simulation
                    .impacts
                )
            ),
            primary_note=(
                impact.primary_note
            ),
            secondary_note=(
                impact.secondary_note
            ),
        )

    def update(
        self,
        *,
        now: float | None = None,
    ) -> tuple[
        PipeEvent,
        ...
    ]:
        """
        Advance every active pipe without blocking.

        Call this frequently from the application's main loop.
        """

        if now is None:
            now = (
                time.monotonic()
            )

        events = []

        completed_ids = []

        for active in tuple(
            self._active.values()
        ):
            #
            # End the brief contact pulse first.
            #
            if (
                active.release_time
                is not None
                and now
                >= active.release_time
            ):
                self._release_contact(
                    active
                )

            #
            # If no collision is currently active, start the next impact once
            # its calculated physical time has arrived.
            #
            if (
                active.sounding_notes
                is None
                and active.next_impact_index
                < len(
                    active.simulation
                    .impacts
                )
            ):
                next_impact = (
                    active.simulation
                    .impacts[
                        active.next_impact_index
                    ]
                )

                impact_time = (
                    active.start_time
                    + next_impact.time_seconds
                )

                if now >= impact_time:
                    events.append(
                        self._strike_next_impact(
                            active,
                            now=now,
                        )
                    )

            #
            # Once the final impact's physical contact has ended, the
            # simulation itself is complete.
            #
            # We deliberately do NOT send All Sounds Off here. FluidSynth's
            # natural Tubular Bell release tail is allowed to keep ringing.
            # The MIDI channel can safely be reused for another pipe.
            #
            if (
                active.sounding_notes
                is None
                and active.next_impact_index
                >= len(
                    active.simulation
                    .impacts
                )
            ):
                completed_ids.append(
                    active.pipe_id
                )

        for pipe_id in (
            completed_ids
        ):
            active = (
                self._active.pop(
                    pipe_id
                )
            )

            self._free_channels.append(
                active.channel
            )

            self._free_channels.sort()

            events.append(
                PipeEvent(
                    kind="complete",
                    pipe_id=(
                        active.pipe_id
                    ),
                    channel=(
                        active.channel
                    ),
                    impact_count=(
                        len(
                            active.simulation
                            .impacts
                        )
                    ),
                )
            )

        return tuple(
            events
        )

    def stop_all(
        self,
    ) -> None:
        """Immediately stop every pipe and clear all pipe channels."""

        for channel in (
            self._channels
        ):
            self._synth.all_sounds_off(
                channel
            )

        self._active.clear()

        self._free_channels = list(
            self._channels
        )
