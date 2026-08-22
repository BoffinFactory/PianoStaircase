#!/usr/bin/env python3

"""
Piano Staircase Demo 2 application.

The application connects:

    distance sensor
        -> interaction interpretation
        -> response selection / special events
        -> lighting
        -> audio

Two articulation styles are supported:

    one-shot
        The original Demo 2 behavior. A proximity trigger launches one
        short generated WAV and lighting cue.

    instrument
        FluidSynth remains running continuously.

        Cycle/random response modes:
            ENTER -> NOTE ON + light on
            HELD  -> sustain
            EXIT  -> NOTE OFF + light off

        Distance response mode:
            The active sensor range becomes a chromatic one-dimensional
            keyboard. Moving the hand changes the held note continuously.

An optional Rich terminal presentation runs in a separate process so
rendering cannot delay the timing-sensitive hardware loop.

Press Ctrl+C to stop.
"""

from __future__ import annotations

import argparse
import signal
import time
from collections.abc import Callable
from dataclasses import dataclass

from piano_staircase_demo.articulation import (
    DistanceKeyboard,
    midi_note_name,
)
from piano_staircase_demo.audio import (
    AudioClip,
    AudioSystem,
)
from piano_staircase_demo.display_process import (
    DisplayProcess,
)
from piano_staircase_demo.events import (
    SpecialEventDirector,
    TemporaryEventOverride,
)
from piano_staircase_demo.interaction import (
    CooldownGate,
)
from piano_staircase_demo.lighting import (
    LightingChannel,
    LightingSystem,
)
from piano_staircase_demo.modes import (
    CycleMode,
    DistanceMode,
    InteractionResponse,
    RandomMode,
)
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
from piano_staircase_demo.terminal_display import (
    DisplayState,
)
from piano_staircase_demo.trigger import (
    DistanceTrigger,
)


# ---------------------------------------------------------------------------
# Current validated Demo 2 defaults
# ---------------------------------------------------------------------------

TRIGGER_DISTANCE_MM = 500
REARM_DISTANCE_MM = 750

TRIGGER_SAMPLES = 1
REARM_SAMPLES = 1

POLL_HZ = 30.0
COOLDOWN_SECONDS = 0.20

NOTE_DURATION_SECONDS = 0.15
LIGHT_BRIGHTNESS_PERCENT = 100

RESPONSE_MODE = "cycle"

#
# Keep the old behavior as the default until the new instrument path has
# passed the complete integrated hardware test.
#
ARTICULATION = "one-shot"

PIANO_GAIN = DEFAULT_GAIN
PIANO_VELOCITY = DEFAULT_VELOCITY

#
# Continuous distance-keyboard defaults.
#
# 250 mm -> C5
# 750 mm -> C4
#
KEYBOARD_NEAR_MM = 250
KEYBOARD_FAR_MM = 750

KEYBOARD_LOW_NOTE = 60
KEYBOARD_HIGH_NOTE = 72

SPECIAL_EVERY = 8
SPECIAL_NOTE_DURATION_SECONDS = 0.10
SPECIAL_NOTE_GAP_SECONDS = 0.04

PIPE_EVENT_NAME = "pipes"
PIPE_OVERRIDE_TRIGGERS = 4

DISPLAY_HZ = 5.0
DISPLAY_RESPONSE_HOLD_SECONDS = 0.75


# ---------------------------------------------------------------------------
# Musical / lighting responses
# ---------------------------------------------------------------------------

RESPONSES = (
    InteractionResponse(
        note="C4",
        light_name="green",
    ),
    InteractionResponse(
        note="E4",
        light_name="yellow",
    ),
    InteractionResponse(
        note="G4",
        light_name="blue",
    ),
)


PIPE_PLACEHOLDER_RESPONSES = (
    RESPONSES[2],
    RESPONSES[0],
    RESPONSES[2],
    RESPONSES[1],
)


SPECIAL_SEQUENCES = {
    "ascending": RESPONSES,

    "descending": tuple(
        reversed(
            RESPONSES
        )
    ),

    "bounce": (
        RESPONSES[0],
        RESPONSES[2],
        RESPONSES[1],
        RESPONSES[2],
    ),

    PIPE_EVENT_NAME: (
        PIPE_PLACEHOLDER_RESPONSES
    ),
}


ResponseMode = (
    CycleMode
    | RandomMode
    | DistanceMode
)


# ---------------------------------------------------------------------------
# Runtime state
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LightCue:
    """One timed lighting event."""

    light_name: str
    start_time: float
    end_time: float


@dataclass(frozen=True)
class PlaybackPlan:
    """Everything needed for one one-shot response."""

    responses: tuple[
        InteractionResponse,
        ...
    ]

    clip: AudioClip

    note_duration_seconds: float
    note_gap_seconds: float

    console_message: str
    special_text: str | None = None


@dataclass
class RuntimeState:
    """Mutable state that changes while the demo is running."""

    active_channel: (
        LightingChannel
        | None
    ) = None

    light_cues: tuple[
        LightCue,
        ...
    ] = ()

    #
    # When instrument articulation owns a light, it remains on until the
    # interaction ends rather than using a timed LightCue.
    #
    held_light_name: str | None = None

    #
    # A physical interaction remains engaged until the hand leaves.
    #
    # This is intentionally different from instrument_note. A special event
    # or dropped interaction may be engaged without owning a piano note.
    #
    instrument_engaged: bool = False

    instrument_note: (
        str
        | int
        | None
    ) = None

    last_interaction_time: (
        float
        | None
    ) = None

    last_response_time: (
        float
        | None
    ) = None

    display_note: (
        str
        | None
    ) = None

    display_light_name: (
        str
        | None
    ) = None

    display_special_text: (
        str
        | None
    ) = None


# ---------------------------------------------------------------------------
# Command-line configuration
# ---------------------------------------------------------------------------

def parse_args(
) -> argparse.Namespace:
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description=(
            "Run the Piano Staircase Demo 2 "
            "tabletop application."
        )
    )

    parser.add_argument(
        "--trigger-mm",
        type=int,
        default=TRIGGER_DISTANCE_MM,
        help=(
            "Trigger / instrument ENTER distance "
            f"(default: {TRIGGER_DISTANCE_MM} mm)."
        ),
    )

    parser.add_argument(
        "--rearm-mm",
        type=int,
        default=REARM_DISTANCE_MM,
        help=(
            "Rearm / instrument EXIT distance "
            f"(default: {REARM_DISTANCE_MM} mm)."
        ),
    )

    parser.add_argument(
        "--trigger-samples",
        type=int,
        default=TRIGGER_SAMPLES,
        help=(
            "Consecutive trigger/ENTER samples "
            f"(default: {TRIGGER_SAMPLES})."
        ),
    )

    parser.add_argument(
        "--rearm-samples",
        type=int,
        default=REARM_SAMPLES,
        help=(
            "Consecutive rearm/EXIT samples "
            f"(default: {REARM_SAMPLES})."
        ),
    )

    parser.add_argument(
        "--hz",
        type=float,
        default=POLL_HZ,
        help=(
            "Sensor polling frequency "
            f"(default: {POLL_HZ:g} Hz)."
        ),
    )

    parser.add_argument(
        "--cooldown",
        type=float,
        default=COOLDOWN_SECONDS,
        help=(
            "Minimum interval between accepted "
            "physical interactions "
            f"(default: {COOLDOWN_SECONDS:.2f} seconds)."
        ),
    )

    parser.add_argument(
        "--response-mode",
        choices=(
            "cycle",
            "random",
            "distance",
        ),
        default=RESPONSE_MODE,
        help=(
            "How ordinary interactions select responses "
            f"(default: {RESPONSE_MODE})."
        ),
    )

    parser.add_argument(
        "--articulation",
        choices=(
            "one-shot",
            "instrument",
        ),
        default=ARTICULATION,
        help=(
            "How ordinary musical responses behave "
            f"(default: {ARTICULATION})."
        ),
    )

    parser.add_argument(
        "--piano-gain",
        type=float,
        default=PIANO_GAIN,
        help=(
            "FluidSynth master gain in instrument mode "
            f"(default: {PIANO_GAIN:g})."
        ),
    )

    parser.add_argument(
        "--piano-velocity",
        type=int,
        default=PIANO_VELOCITY,
        help=(
            "MIDI attack velocity in instrument mode "
            f"(default: {PIANO_VELOCITY})."
        ),
    )

    parser.add_argument(
        "--keyboard-near-mm",
        type=int,
        default=KEYBOARD_NEAR_MM,
        help=(
            "Distance selecting the highest note in "
            "distance + instrument mode "
            f"(default: {KEYBOARD_NEAR_MM} mm)."
        ),
    )

    parser.add_argument(
        "--keyboard-far-mm",
        type=int,
        default=KEYBOARD_FAR_MM,
        help=(
            "Distance selecting the lowest note in "
            "distance + instrument mode; farther readings "
            "leave the keyboard "
            f"(default: {KEYBOARD_FAR_MM} mm)."
        ),
    )

    parser.add_argument(
        "--keyboard-low-note",
        type=int,
        default=KEYBOARD_LOW_NOTE,
        help=(
            "Lowest MIDI note in distance + instrument mode "
            f"(default: {KEYBOARD_LOW_NOTE})."
        ),
    )

    parser.add_argument(
        "--keyboard-high-note",
        type=int,
        default=KEYBOARD_HIGH_NOTE,
        help=(
            "Highest MIDI note in distance + instrument mode "
            f"(default: {KEYBOARD_HIGH_NOTE})."
        ),
    )

    parser.add_argument(
        "--special-every",
        "--flourish-every",
        dest="special_every",
        type=int,
        default=SPECIAL_EVERY,
        help=(
            "Play a random special event every N "
            "accepted interactions; 0 disables "
            "special events "
            f"(default: {SPECIAL_EVERY})."
        ),
    )

    parser.add_argument(
        "--pipe-triggers",
        type=int,
        default=PIPE_OVERRIDE_TRIGGERS,
        help=(
            "Number of accepted interactions in the "
            "temporary pipes override "
            f"(default: {PIPE_OVERRIDE_TRIGGERS})."
        ),
    )

    parser.add_argument(
        "--display",
        action="store_true",
        help=(
            "Show the terminal presentation in a "
            "separate process."
        ),
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help=(
            "Display dropped, invalid, and instrument "
            "transition information."
        ),
    )

    return parser.parse_args()


def validate_args(
    args: argparse.Namespace,
) -> None:
    """Reject invalid configuration before hardware starts."""

    if args.hz <= 0:
        raise SystemExit(
            "--hz must be greater than zero."
        )

    if args.cooldown < 0:
        raise SystemExit(
            "--cooldown cannot be negative."
        )

    if args.special_every < 0:
        raise SystemExit(
            "--special-every cannot be negative."
        )

    if args.pipe_triggers < 1:
        raise SystemExit(
            "--pipe-triggers must be at least 1."
        )

    if args.piano_gain <= 0:
        raise SystemExit(
            "--piano-gain must be greater than zero."
        )

    if not 1 <= args.piano_velocity <= 127:
        raise SystemExit(
            "--piano-velocity must be between 1 and 127."
        )

    #
    # Constructing this also validates all keyboard bounds.
    #
    DistanceKeyboard(
        near_distance_mm=(
            args.keyboard_near_mm
        ),
        far_distance_mm=(
            args.keyboard_far_mm
        ),
        low_note=(
            args.keyboard_low_note
        ),
        high_note=(
            args.keyboard_high_note
        ),
    )


# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

def create_response_mode(
    args: argparse.Namespace,
) -> ResponseMode:
    """Create the selected ordinary response mode."""

    if args.response_mode == "cycle":
        return CycleMode(
            RESPONSES
        )

    if args.response_mode == "random":
        return RandomMode(
            RESPONSES
        )

    if args.response_mode == "distance":
        if args.articulation == "instrument":
            minimum_distance_mm = (
                args.keyboard_near_mm
            )

            maximum_distance_mm = (
                args.keyboard_far_mm
            )

        else:
            minimum_distance_mm = 1

            maximum_distance_mm = (
                args.trigger_mm
            )

        return DistanceMode(
            RESPONSES,
            minimum_distance_mm=(
                minimum_distance_mm
            ),
            maximum_distance_mm=(
                maximum_distance_mm
            ),
        )

    raise AssertionError(
        "Unhandled response mode: "
        f"{args.response_mode}"
    )


def create_audio_clips(
    audio: AudioSystem,
) -> tuple[
    dict[str, AudioClip],
    dict[str, AudioClip],
]:
    """Pre-generate the WAV clips used by one-shot and special events."""

    note_clips = {
        response.note: (
            audio.create_sequence(
                (
                    response.note,
                ),
                note_duration_seconds=(
                    NOTE_DURATION_SECONDS
                ),
            )
        )
        for response in RESPONSES
    }

    special_clips = {
        name: audio.create_sequence(
            tuple(
                response.note
                for response
                in responses
            ),
            note_duration_seconds=(
                SPECIAL_NOTE_DURATION_SECONDS
            ),
            note_gap_seconds=(
                SPECIAL_NOTE_GAP_SECONDS
            ),
        )
        for (
            name,
            responses,
        )
        in SPECIAL_SEQUENCES.items()
    }

    return (
        note_clips,
        special_clips,
    )


def print_startup_summary(
    args: argparse.Namespace,
) -> None:
    """Print the startup configuration."""

    print(
        "=== Piano Staircase Demo 2 ==="
    )

    print()
    print(
        "C4 -> GREEN"
    )

    print(
        "E4 -> YELLOW"
    )

    print(
        "G4 -> BLUE"
    )

    print()

    print(
        "Response mode: "
        f"{args.response_mode}"
    )

    print(
        "Articulation:  "
        f"{args.articulation}"
    )

    if args.articulation == "instrument":
        print(
            "Piano gain:    "
            f"{args.piano_gain:g}"
        )

        if args.response_mode == "distance":
            print(
                "Keyboard:      "
                f"{midi_note_name(args.keyboard_low_note)} "
                f"@ {args.keyboard_far_mm} mm "
                "-> "
                f"{midi_note_name(args.keyboard_high_note)} "
                f"@ {args.keyboard_near_mm} mm"
            )

    print(
        "Terminal display: "
        + (
            "enabled"
            if args.display
            else "disabled"
        )
    )

    print()
    print(
        "Initializing hardware..."
    )


# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------

def build_light_cues(
    responses: tuple[
        InteractionResponse,
        ...
    ],
    *,
    start_time: float,
    duration_seconds: float,
    gap_seconds: float = 0.0,
) -> tuple[
    LightCue,
    ...
]:
    """Build timed lighting cues for a response sequence."""

    cues = []

    cue_start = (
        start_time
    )

    for response in responses:
        cue_end = (
            cue_start
            + duration_seconds
        )

        cues.append(
            LightCue(
                light_name=(
                    response.light_name
                ),
                start_time=(
                    cue_start
                ),
                end_time=(
                    cue_end
                ),
            )
        )

        cue_start = (
            cue_end
            + gap_seconds
        )

    return tuple(
        cues
    )


def switch_active_light(
    *,
    desired_channel: (
        LightingChannel
        | None
    ),
    active_channel: (
        LightingChannel
        | None
    ),
) -> LightingChannel | None:
    """Switch physical lighting only when the desired channel changes."""

    if desired_channel is active_channel:
        return active_channel

    if active_channel is not None:
        active_channel.off()

    if desired_channel is not None:
        desired_channel.set_brightness(
            LIGHT_BRIGHTNESS_PERCENT
        )

    return desired_channel


def choose_active_light(
    *,
    cues: tuple[
        LightCue,
        ...
    ],
    channels: dict[
        str,
        LightingChannel,
    ],
    active_channel: (
        LightingChannel
        | None
    ),
    now: float,
) -> LightingChannel | None:
    """Apply the timed light cue that should currently be active."""

    desired_channel = None

    for cue in cues:
        if (
            cue.start_time
            <= now
            < cue.end_time
        ):
            desired_channel = (
                channels[
                    cue.light_name
                ]
            )

            break

    return switch_active_light(
        desired_channel=(
            desired_channel
        ),
        active_channel=(
            active_channel
        ),
    )


def update_lighting(
    runtime: RuntimeState,
    *,
    channels: dict[
        str,
        LightingChannel,
    ],
    now: float,
) -> None:
    """
    Advance lighting without blocking the sensor loop.

    A held instrument light takes priority over timed one-shot cues.
    """

    if (
        runtime.held_light_name
        is not None
    ):
        runtime.active_channel = (
            switch_active_light(
                desired_channel=(
                    channels[
                        runtime
                        .held_light_name
                    ]
                ),
                active_channel=(
                    runtime
                    .active_channel
                ),
            )
        )

        return

    runtime.active_channel = (
        choose_active_light(
            cues=(
                runtime.light_cues
            ),
            channels=channels,
            active_channel=(
                runtime.active_channel
            ),
            now=now,
        )
    )

    if (
        runtime.light_cues
        and now
        >= runtime
        .light_cues[-1]
        .end_time
    ):
        runtime.light_cues = ()


# ---------------------------------------------------------------------------
# Special-event selection
# ---------------------------------------------------------------------------

def choose_special_event(
    *,
    event_director: SpecialEventDirector,
    event_override: TemporaryEventOverride,
    pipe_triggers: int,
) -> tuple[
    str | None,
    bool,
]:
    """
    Choose a special event, if any.

    Returns:

        special event name
        whether pipes mode was just activated
    """

    special_name = (
        event_override.consume()
    )

    pipe_activated = False

    if special_name is not None:
        return (
            special_name,
            pipe_activated,
        )

    special_name = (
        event_director
        .record_interaction()
    )

    if (
        special_name
        == PIPE_EVENT_NAME
    ):
        event_override.activate(
            PIPE_EVENT_NAME,
            interactions=(
                pipe_triggers
            ),
        )

        #
        # The interaction that selected pipes mode becomes its first
        # overridden interaction.
        #
        special_name = (
            event_override.consume()
        )

        pipe_activated = True

    return (
        special_name,
        pipe_activated,
    )


def build_special_plan(
    *,
    special_name: str,
    pipe_activated: bool,
    event_override: TemporaryEventOverride,
    special_clips: dict[
        str,
        AudioClip,
    ],
) -> PlaybackPlan:
    """Build the one-shot plan for a special event."""

    responses = (
        SPECIAL_SEQUENCES[
            special_name
        ]
    )

    notes = " ".join(
        response.note
        for response
        in responses
    )

    if (
        special_name
        == PIPE_EVENT_NAME
    ):
        remaining = (
            event_override
            .remaining_interactions
        )

        if pipe_activated:
            console_message = (
                "SPECIAL PIPES MODE -> "
                f"{notes} "
                f"({remaining} remaining)"
            )

            special_text = (
                "PIPES MODE // "
                f"{remaining} REMAINING"
            )

        else:
            console_message = (
                "PIPES OVERRIDE -> "
                f"{notes} "
                f"({remaining} remaining)"
            )

            special_text = (
                "PIPES OVERRIDE // "
                f"{remaining} REMAINING"
            )

    else:
        console_message = (
            "SPECIAL "
            f"{special_name.upper()} "
            f"-> {notes}"
        )

        special_text = (
            "SPECIAL // "
            f"{special_name.upper()}"
        )

    return PlaybackPlan(
        responses=responses,
        clip=(
            special_clips[
                special_name
            ]
        ),
        note_duration_seconds=(
            SPECIAL_NOTE_DURATION_SECONDS
        ),
        note_gap_seconds=(
            SPECIAL_NOTE_GAP_SECONDS
        ),
        console_message=(
            console_message
        ),
        special_text=(
            special_text
        ),
    )


# ---------------------------------------------------------------------------
# One-shot articulation
# ---------------------------------------------------------------------------

def build_ordinary_plan(
    *,
    distance_mm: int,
    mode: ResponseMode,
    note_clips: dict[
        str,
        AudioClip,
    ],
) -> PlaybackPlan:
    """Build an ordinary one-shot response."""

    response = (
        mode.next_response(
            distance_mm
        )
    )

    return PlaybackPlan(
        responses=(
            response,
        ),
        clip=(
            note_clips[
                response.note
            ]
        ),
        note_duration_seconds=(
            NOTE_DURATION_SECONDS
        ),
        note_gap_seconds=0.0,
        console_message=(
            f"{response.note} -> "
            f"{response.light_name.upper()}"
        ),
    )


def choose_playback_plan(
    *,
    distance_mm: int,
    args: argparse.Namespace,
    mode: ResponseMode,
    event_director: SpecialEventDirector,
    event_override: TemporaryEventOverride,
    note_clips: dict[
        str,
        AudioClip,
    ],
    special_clips: dict[
        str,
        AudioClip,
    ],
) -> PlaybackPlan:
    """Choose an ordinary or special one-shot response."""

    (
        special_name,
        pipe_activated,
    ) = choose_special_event(
        event_director=(
            event_director
        ),
        event_override=(
            event_override
        ),
        pipe_triggers=(
            args.pipe_triggers
        ),
    )

    if special_name is not None:
        return build_special_plan(
            special_name=(
                special_name
            ),
            pipe_activated=(
                pipe_activated
            ),
            event_override=(
                event_override
            ),
            special_clips=(
                special_clips
            ),
        )

    return build_ordinary_plan(
        distance_mm=(
            distance_mm
        ),
        mode=mode,
        note_clips=(
            note_clips
        ),
    )


def start_playback(
    plan: PlaybackPlan,
    *,
    audio: AudioSystem,
    channels: dict[
        str,
        LightingChannel,
    ],
    runtime: RuntimeState,
) -> None:
    """Start synchronized one-shot audio and lighting."""

    response_time = (
        time.monotonic()
    )

    runtime.held_light_name = None

    runtime.light_cues = (
        build_light_cues(
            plan.responses,
            start_time=(
                response_time
            ),
            duration_seconds=(
                plan.note_duration_seconds
            ),
            gap_seconds=(
                plan.note_gap_seconds
            ),
        )
    )

    runtime.active_channel = (
        choose_active_light(
            cues=(
                runtime.light_cues
            ),
            channels=channels,
            active_channel=(
                runtime.active_channel
            ),
            now=(
                response_time
            ),
        )
    )

    audio.play(
        plan.clip,
        blocking=False,
    )

    runtime.last_interaction_time = (
        response_time
    )

    runtime.last_response_time = (
        response_time
    )

    runtime.display_note = " ".join(
        response.note
        for response
        in plan.responses
    )

    if plan.responses:
        runtime.display_light_name = (
            plan.responses[0]
            .light_name
        )

    else:
        runtime.display_light_name = None

    runtime.display_special_text = (
        plan.special_text
    )


def handle_trigger(
    *,
    distance_mm: int,
    args: argparse.Namespace,
    gate: CooldownGate,
    mode: ResponseMode,
    event_director: SpecialEventDirector,
    event_override: TemporaryEventOverride,
    audio: AudioSystem,
    note_clips: dict[
        str,
        AudioClip,
    ],
    special_clips: dict[
        str,
        AudioClip,
    ],
    channels: dict[
        str,
        LightingChannel,
    ],
    runtime: RuntimeState,
) -> str | None:
    """Handle one original one-shot sensor trigger."""

    if audio.is_playing:
        if args.verbose:
            return (
                f"{distance_mm:4d} mm "
                "-> DROP AUDIO BUSY"
            )

        return None

    if not gate.allow():
        if args.verbose:
            return (
                f"{distance_mm:4d} mm "
                "-> DROP COOLDOWN"
            )

        return None

    plan = choose_playback_plan(
        distance_mm=(
            distance_mm
        ),
        args=args,
        mode=mode,
        event_director=(
            event_director
        ),
        event_override=(
            event_override
        ),
        note_clips=(
            note_clips
        ),
        special_clips=(
            special_clips
        ),
    )

    start_playback(
        plan,
        audio=audio,
        channels=channels,
        runtime=runtime,
    )

    return (
        plan.console_message
    )


# ---------------------------------------------------------------------------
# Instrument articulation
# ---------------------------------------------------------------------------

def instrument_note_label(
    note: str | int,
) -> str:
    """Return a display-friendly name for an instrument note."""

    if isinstance(
        note,
        str,
    ):
        return note

    return midi_note_name(
        note
    )


def start_ordinary_instrument_response(
    *,
    distance_mm: int,
    args: argparse.Namespace,
    mode: ResponseMode,
    keyboard: (
        DistanceKeyboard
        | None
    ),
    piano: PianoEngine,
    channels: dict[
        str,
        LightingChannel,
    ],
    runtime: RuntimeState,
) -> str:
    """Start one sustained ordinary instrument response."""

    response = (
        mode.next_response(
            distance_mm
        )
    )

    if args.response_mode == "distance":
        if keyboard is None:
            raise RuntimeError(
                "Distance keyboard was not initialized."
            )

        note = (
            keyboard.note_for_distance(
                distance_mm
            )
        )

        if note is None:
            raise RuntimeError(
                "Instrument entry occurred outside "
                "the distance keyboard."
            )

    else:
        note = (
            response.note
        )

    piano.note_on(
        note,
        velocity=(
            args.piano_velocity
        ),
    )

    response_time = (
        time.monotonic()
    )

    runtime.light_cues = ()

    runtime.held_light_name = (
        response.light_name
    )

    runtime.instrument_note = (
        note
    )

    runtime.last_interaction_time = (
        response_time
    )

    runtime.last_response_time = (
        response_time
    )

    runtime.display_note = (
        instrument_note_label(
            note
        )
    )

    runtime.display_light_name = (
        response.light_name
    )

    runtime.display_special_text = None

    update_lighting(
        runtime,
        channels=channels,
        now=response_time,
    )

    return (
        f"{instrument_note_label(note)} "
        f"-> "
        f"{response.light_name.upper()} "
        "(INSTRUMENT)"
    )


def handle_instrument_entry(
    *,
    distance_mm: int,
    args: argparse.Namespace,
    gate: CooldownGate,
    mode: ResponseMode,
    event_director: SpecialEventDirector,
    event_override: TemporaryEventOverride,
    audio: AudioSystem,
    special_clips: dict[
        str,
        AudioClip,
    ],
    keyboard: (
        DistanceKeyboard
        | None
    ),
    piano: PianoEngine,
    channels: dict[
        str,
        LightingChannel,
    ],
    runtime: RuntimeState,
) -> str | None:
    """
    Handle exactly one physical instrument interaction.

    Special-event accounting happens here, once per physical entry.

    Musical note changes inside a distance-keyboard sweep do not count as
    additional interactions.
    """

    if audio.is_playing:
        if args.verbose:
            return (
                f"{distance_mm:4d} mm "
                "-> DROP AUDIO BUSY"
            )

        return None

    if not gate.allow():
        if args.verbose:
            return (
                f"{distance_mm:4d} mm "
                "-> DROP COOLDOWN"
            )

        return None

    (
        special_name,
        pipe_activated,
    ) = choose_special_event(
        event_director=(
            event_director
        ),
        event_override=(
            event_override
        ),
        pipe_triggers=(
            args.pipe_triggers
        ),
    )

    if special_name is not None:
        plan = build_special_plan(
            special_name=(
                special_name
            ),
            pipe_activated=(
                pipe_activated
            ),
            event_override=(
                event_override
            ),
            special_clips=(
                special_clips
            ),
        )

        start_playback(
            plan,
            audio=audio,
            channels=channels,
            runtime=runtime,
        )

        return (
            plan.console_message
        )

    return (
        start_ordinary_instrument_response(
            distance_mm=(
                distance_mm
            ),
            args=args,
            mode=mode,
            keyboard=keyboard,
            piano=piano,
            channels=channels,
            runtime=runtime,
        )
    )


def finish_instrument_interaction(
    *,
    piano: PianoEngine,
    channels: dict[
        str,
        LightingChannel,
    ],
    runtime: RuntimeState,
) -> str | None:
    """Release a held instrument note and end the physical interaction."""

    message = None

    if (
        runtime.instrument_note
        is not None
    ):
        note = (
            runtime.instrument_note
        )

        piano.note_off(
            note
        )

        message = (
            "NOTE OFF "
            f"{instrument_note_label(note)}"
        )

        runtime.last_response_time = (
            time.monotonic()
        )

    runtime.instrument_note = None

    runtime.instrument_engaged = False

    runtime.held_light_name = None

    update_lighting(
        runtime,
        channels=channels,
        now=time.monotonic(),
    )

    return message


def update_distance_instrument_note(
    *,
    distance_mm: int,
    args: argparse.Namespace,
    mode: ResponseMode,
    keyboard: DistanceKeyboard,
    piano: PianoEngine,
    channels: dict[
        str,
        LightingChannel,
    ],
    runtime: RuntimeState,
) -> str | None:
    """Change the held pitch while remaining inside the distance keyboard."""

    selected_note = (
        keyboard.note_for_distance(
            distance_mm
        )
    )

    if selected_note is None:
        return None

    #
    # An interaction occupied by a special event or a dropped ENTER has no
    # instrument note. Do not suddenly start a piano halfway through it.
    #
    if (
        runtime.instrument_note
        is None
    ):
        return None

    response = (
        mode.next_response(
            distance_mm
        )
    )

    #
    # Lighting uses the original three distance response bands even though
    # the piano now has many chromatic virtual keys.
    #
    light_changed = (
        runtime.held_light_name
        != response.light_name
    )

    if light_changed:
        runtime.held_light_name = (
            response.light_name
        )

        runtime.display_light_name = (
            response.light_name
        )

        update_lighting(
            runtime,
            channels=channels,
            now=time.monotonic(),
        )

    if (
        selected_note
        == runtime.instrument_note
    ):
        return None

    old_note = (
        runtime.instrument_note
    )

    piano.note_off(
        old_note
    )

    piano.note_on(
        selected_note,
        velocity=(
            args.piano_velocity
        ),
    )

    runtime.instrument_note = (
        selected_note
    )

    runtime.last_response_time = (
        time.monotonic()
    )

    runtime.display_note = (
        midi_note_name(
            selected_note
        )
    )

    if args.verbose:
        return (
            f"{distance_mm:4d} mm -> "
            f"{instrument_note_label(old_note)} "
            "-> "
            f"{midi_note_name(selected_note)}"
        )

    return None


def handle_distance_instrument_sample(
    *,
    distance_mm: int,
    args: argparse.Namespace,
    gate: CooldownGate,
    mode: ResponseMode,
    event_director: SpecialEventDirector,
    event_override: TemporaryEventOverride,
    audio: AudioSystem,
    special_clips: dict[
        str,
        AudioClip,
    ],
    keyboard: DistanceKeyboard,
    piano: PianoEngine,
    channels: dict[
        str,
        LightingChannel,
    ],
    runtime: RuntimeState,
) -> str | None:
    """
    Process one reading for the continuous distance keyboard.

    Crossing into the active distance range counts as one interaction.

    Crossing virtual note boundaries while still inside that range changes
    musical pitch but does not increment interaction/event counters.
    """

    selected_note = (
        keyboard.note_for_distance(
            distance_mm
        )
    )

    #
    # Leave the keyboard.
    #
    if selected_note is None:
        if runtime.instrument_engaged:
            return (
                finish_instrument_interaction(
                    piano=piano,
                    channels=channels,
                    runtime=runtime,
                )
            )

        return None

    #
    # Enter the keyboard.
    #
    if not runtime.instrument_engaged:
        #
        # Mark the physical interaction engaged even if it is dropped.
        # Otherwise the loop would retry ENTER every 33 ms until cooldown
        # or the audio bus became available.
        #
        runtime.instrument_engaged = True

        return (
            handle_instrument_entry(
                distance_mm=(
                    distance_mm
                ),
                args=args,
                gate=gate,
                mode=mode,
                event_director=(
                    event_director
                ),
                event_override=(
                    event_override
                ),
                audio=audio,
                special_clips=(
                    special_clips
                ),
                keyboard=keyboard,
                piano=piano,
                channels=channels,
                runtime=runtime,
            )
        )

    #
    # Already inside the keyboard: this is a musical transition, not a new
    # physical interaction.
    #
    return (
        update_distance_instrument_note(
            distance_mm=(
                distance_mm
            ),
            args=args,
            mode=mode,
            keyboard=keyboard,
            piano=piano,
            channels=channels,
            runtime=runtime,
        )
    )


def handle_presence_instrument_event(
    *,
    event: PresenceEvent,
    distance_mm: int,
    args: argparse.Namespace,
    gate: CooldownGate,
    mode: ResponseMode,
    event_director: SpecialEventDirector,
    event_override: TemporaryEventOverride,
    audio: AudioSystem,
    special_clips: dict[
        str,
        AudioClip,
    ],
    piano: PianoEngine,
    channels: dict[
        str,
        LightingChannel,
    ],
    runtime: RuntimeState,
) -> str | None:
    """Handle ENTER/EXIT for cycle/random instrument articulation."""

    if event is PresenceEvent.ENTER:
        runtime.instrument_engaged = True

        return (
            handle_instrument_entry(
                distance_mm=(
                    distance_mm
                ),
                args=args,
                gate=gate,
                mode=mode,
                event_director=(
                    event_director
                ),
                event_override=(
                    event_override
                ),
                audio=audio,
                special_clips=(
                    special_clips
                ),
                keyboard=None,
                piano=piano,
                channels=channels,
                runtime=runtime,
            )
        )

    if event is PresenceEvent.EXIT:
        return (
            finish_instrument_interaction(
                piano=piano,
                channels=channels,
                runtime=runtime,
            )
        )

    #
    # HELD does nothing. The persistent synth continues to hold the key.
    #
    return None


# ---------------------------------------------------------------------------
# Terminal presentation
# ---------------------------------------------------------------------------

def display_code_stage(
    *,
    interaction_time: (
        float
        | None
    ),
    now: float,
) -> str:
    """Choose the simulated code line highlighted on the display."""

    if interaction_time is None:
        return "sensor"

    elapsed = (
        now
        - interaction_time
    )

    if elapsed < 0.15:
        return "trigger"

    if elapsed < 0.30:
        return "response"

    if elapsed < 0.45:
        return "lighting"

    if elapsed < 0.75:
        return "audio"

    return "sensor"


def piano_audio_active(
    piano: (
        PianoEngine
        | None
    ),
) -> bool:
    """Return whether the application currently holds any piano keys."""

    return (
        piano is not None
        and bool(
            piano.active_notes
        )
    )


def clear_expired_display_response(
    runtime: RuntimeState,
    *,
    audio: AudioSystem,
    piano: (
        PianoEngine
        | None
    ),
    now: float,
) -> None:
    """Return the presentation to idle after a completed response."""

    if (
        runtime.last_response_time
        is None
    ):
        return

    if (
        now
        - runtime.last_response_time
        < DISPLAY_RESPONSE_HOLD_SECONDS
    ):
        return

    if audio.is_playing:
        return

    if piano_audio_active(
        piano
    ):
        return

    if (
        runtime.active_channel
        is not None
    ):
        return

    runtime.display_note = None
    runtime.display_light_name = None
    runtime.display_special_text = None


def build_display_state(
    *,
    args: argparse.Namespace,
    runtime: RuntimeState,
    audio: AudioSystem,
    piano: (
        PianoEngine
        | None
    ),
    distance_mm: (
        int
        | None
    ),
    now: float,
) -> DisplayState:
    """Build a small state snapshot for the presentation process."""

    clear_expired_display_response(
        runtime,
        audio=audio,
        piano=piano,
        now=now,
    )

    if (
        args.articulation
        == "instrument"
    ):
        trigger_state = (
            "HELD"
            if runtime.instrument_engaged
            else "ARMED"
        )

    else:
        interaction_is_recent = (
            runtime.last_interaction_time
            is not None
            and (
                now
                - runtime
                .last_interaction_time
            )
            < 0.75
        )

        trigger_state = (
            "FIRED"
            if interaction_is_recent
            else "ARMED"
        )

    if (
        runtime.active_channel
        is not None
    ):
        light_name = (
            runtime
            .active_channel
            .name
            .lower()
        )

    else:
        light_name = (
            runtime
            .display_light_name
        )

    return DisplayState(
        distance_mm=(
            distance_mm
        ),
        trigger_state=(
            trigger_state
        ),
        response_mode=(
            args.response_mode
        ),
        note=(
            runtime.display_note
        ),
        light_name=(
            light_name
        ),
        output_active=(
            runtime.active_channel
            is not None
        ),
        audio_active=(
            audio.is_playing
            or piano_audio_active(
                piano
            )
        ),
        code_stage=(
            display_code_stage(
                interaction_time=(
                    runtime
                    .last_interaction_time
                ),
                now=now,
            )
        ),
        special_text=(
            runtime
            .display_special_text
        ),
    )


def start_display_process(
    args: argparse.Namespace,
) -> DisplayProcess | None:
    """Start the optional presentation process."""

    if not args.display:
        return None

    try:
        return DisplayProcess.start(
            initial_state=(
                DisplayState(
                    response_mode=(
                        args.response_mode
                    ),
                )
            ),
            refresh_hz=(
                DISPLAY_HZ
            ),
        )

    except Exception as exc:
        print(
            "WARNING: Terminal display "
            f"unavailable: {exc}"
        )

        print(
            "Continuing without the "
            "presentation display."
        )

        return None


def publish_display_state(
    display_process: (
        DisplayProcess
        | None
    ),
    *,
    args: argparse.Namespace,
    runtime: RuntimeState,
    audio: AudioSystem,
    piano: (
        PianoEngine
        | None
    ),
    distance_mm: (
        int
        | None
    ),
    now: float,
) -> DisplayProcess | None:
    """Publish the newest presentation state without blocking."""

    if display_process is None:
        return None

    state = build_display_state(
        args=args,
        runtime=runtime,
        audio=audio,
        piano=piano,
        distance_mm=(
            distance_mm
        ),
        now=now,
    )

    if display_process.publish(
        state
    ):
        return display_process

    error_message = (
        display_process
        .error_message()
    )

    display_process.close()

    print()

    if error_message is None:
        print(
            "WARNING: Terminal display "
            "process stopped unexpectedly."
        )

    else:
        print(
            "WARNING: Terminal display "
            f"failed: {error_message}"
        )

    print(
        "Continuing without the "
        "presentation display."
    )

    return None


# ---------------------------------------------------------------------------
# Sensor timing
# ---------------------------------------------------------------------------

def advance_sample_schedule(
    *,
    next_sample: float,
    interval: float,
) -> float:
    """Schedule the next sensor poll without catch-up bursts."""

    next_sample += (
        interval
    )

    now = (
        time.monotonic()
    )

    if (
        next_sample
        < now - interval
    ):
        return (
            now
            + interval
        )

    return next_sample


# ---------------------------------------------------------------------------
# Main hardware loop
# ---------------------------------------------------------------------------

def run_demo(
    args: argparse.Namespace,
    *,
    should_stop: Callable[
        [],
        bool,
    ],
) -> None:
    """Initialize hardware and run the Demo 2 control loop."""

    trigger = None
    presence = None
    keyboard = None

    if (
        args.articulation
        == "one-shot"
    ):
        trigger = DistanceTrigger(
            trigger_distance_mm=(
                args.trigger_mm
            ),
            rearm_distance_mm=(
                args.rearm_mm
            ),
            trigger_samples=(
                args.trigger_samples
            ),
            rearm_samples=(
                args.rearm_samples
            ),
        )

    elif (
        args.response_mode
        == "distance"
    ):
        keyboard = DistanceKeyboard(
            near_distance_mm=(
                args.keyboard_near_mm
            ),
            far_distance_mm=(
                args.keyboard_far_mm
            ),
            low_note=(
                args.keyboard_low_note
            ),
            high_note=(
                args.keyboard_high_note
            ),
        )

    else:
        presence = PresenceTracker(
            enter_distance_mm=(
                args.trigger_mm
            ),
            exit_distance_mm=(
                args.rearm_mm
            ),
            enter_samples=(
                args.trigger_samples
            ),
            exit_samples=(
                args.rearm_samples
            ),
        )

    gate = CooldownGate(
        args.cooldown
    )

    mode = create_response_mode(
        args
    )

    event_director = (
        SpecialEventDirector(
            every_n_interactions=(
                args.special_every
            ),
            event_names=tuple(
                SPECIAL_SEQUENCES
            ),
        )
    )

    event_override = (
        TemporaryEventOverride()
    )

    runtime = (
        RuntimeState()
    )

    interval = (
        1.0
        / args.hz
    )

    with (
        DistanceSensor() as sensor,
        LightingSystem() as lights,
        AudioSystem() as audio,
    ):
        piano = None

        try:
            if (
                args.articulation
                == "instrument"
            ):
                piano = PianoEngine(
                    gain=(
                        args.piano_gain
                    ),
                    velocity=(
                        args.piano_velocity
                    ),
                )

            channels = {
                "green": (
                    lights.green
                ),
                "yellow": (
                    lights.yellow
                ),
                "blue": (
                    lights.blue
                ),
            }

            (
                note_clips,
                special_clips,
            ) = create_audio_clips(
                audio
            )

            lights.all_off()

            print(
                "Hardware initialized successfully."
            )

            print(
                "Ready."
            )

            print(
                "Press Ctrl+C to stop."
            )

            print()

            display_process = (
                start_display_process(
                    args
                )
            )

            next_sample = (
                time.monotonic()
            )

            try:
                while not should_stop():

                    # 1. Wait for the next sensor poll.
                    now = (
                        time.monotonic()
                    )

                    if now < next_sample:
                        time.sleep(
                            next_sample
                            - now
                        )

                    sample_time = (
                        time.monotonic()
                    )

                    # 2. Advance lighting already in progress.
                    update_lighting(
                        runtime,
                        channels=channels,
                        now=sample_time,
                    )

                    # 3. Read the distance sensor.
                    distance_mm = (
                        sensor.distance_mm
                    )

                    message = None

                    # 4. Interpret a valid distance sample.
                    if distance_mm is None:
                        if (
                            args.verbose
                            and display_process
                            is None
                        ):
                            print(
                                "INVALID SENSOR SAMPLE"
                            )

                    elif (
                        args.articulation
                        == "one-shot"
                    ):
                        if trigger is None:
                            raise RuntimeError(
                                "One-shot trigger was not initialized."
                            )

                        fired = (
                            trigger.update(
                                distance_mm
                            )
                        )

                        if fired:
                            message = (
                                handle_trigger(
                                    distance_mm=(
                                        distance_mm
                                    ),
                                    args=args,
                                    gate=gate,
                                    mode=mode,
                                    event_director=(
                                        event_director
                                    ),
                                    event_override=(
                                        event_override
                                    ),
                                    audio=audio,
                                    note_clips=(
                                        note_clips
                                    ),
                                    special_clips=(
                                        special_clips
                                    ),
                                    channels=(
                                        channels
                                    ),
                                    runtime=runtime,
                                )
                            )

                    elif (
                        args.response_mode
                        == "distance"
                    ):
                        if (
                            keyboard is None
                            or piano is None
                        ):
                            raise RuntimeError(
                                "Distance instrument was not initialized."
                            )

                        message = (
                            handle_distance_instrument_sample(
                                distance_mm=(
                                    distance_mm
                                ),
                                args=args,
                                gate=gate,
                                mode=mode,
                                event_director=(
                                    event_director
                                ),
                                event_override=(
                                    event_override
                                ),
                                audio=audio,
                                special_clips=(
                                    special_clips
                                ),
                                keyboard=(
                                    keyboard
                                ),
                                piano=piano,
                                channels=(
                                    channels
                                ),
                                runtime=runtime,
                            )
                        )

                    else:
                        if (
                            presence is None
                            or piano is None
                        ):
                            raise RuntimeError(
                                "Presence instrument was not initialized."
                            )

                        event = (
                            presence.update(
                                distance_mm
                            )
                        )

                        if event in (
                            PresenceEvent.ENTER,
                            PresenceEvent.EXIT,
                        ):
                            message = (
                                handle_presence_instrument_event(
                                    event=event,
                                    distance_mm=(
                                        distance_mm
                                    ),
                                    args=args,
                                    gate=gate,
                                    mode=mode,
                                    event_director=(
                                        event_director
                                    ),
                                    event_override=(
                                        event_override
                                    ),
                                    audio=audio,
                                    special_clips=(
                                        special_clips
                                    ),
                                    piano=piano,
                                    channels=(
                                        channels
                                    ),
                                    runtime=runtime,
                                )
                            )

                    if (
                        message is not None
                        and display_process
                        is None
                    ):
                        print(
                            message
                        )

                    # 5. Publish presentation state.
                    display_process = (
                        publish_display_state(
                            display_process,
                            args=args,
                            runtime=runtime,
                            audio=audio,
                            piano=piano,
                            distance_mm=(
                                distance_mm
                            ),
                            now=sample_time,
                        )
                    )

                    # 6. Schedule the next sensor poll.
                    next_sample = (
                        advance_sample_schedule(
                            next_sample=(
                                next_sample
                            ),
                            interval=(
                                interval
                            ),
                        )
                    )

            finally:
                if (
                    display_process
                    is not None
                ):
                    display_process.close()

        finally:
            if piano is not None:
                piano.close()


# ---------------------------------------------------------------------------
# Program entry point
# ---------------------------------------------------------------------------

def main(
) -> None:
    """Run the Demo 2 application."""

    args = (
        parse_args()
    )

    validate_args(
        args
    )

    stop_requested = False

    def request_stop(
        signum,
        frame,
    ) -> None:
        nonlocal stop_requested

        stop_requested = True

    signal.signal(
        signal.SIGINT,
        request_stop,
    )

    signal.signal(
        signal.SIGTERM,
        request_stop,
    )

    print_startup_summary(
        args
    )

    try:
        run_demo(
            args,
            should_stop=(
                lambda: (
                    stop_requested
                )
            ),
        )

    except KeyboardInterrupt:
        pass

    except ValueError as exc:
        raise SystemExit(
            "Invalid configuration: "
            f"{exc}"
        ) from exc

    finally:
        print()
        print(
            "Demo stopped."
        )


if __name__ == "__main__":
    main()