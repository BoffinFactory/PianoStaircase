#!/usr/bin/env python3

"""
Piano Staircase Demo 2 application.

The application connects the Demo 2 subsystems:

    distance sensor
        -> trigger/rearm logic
        -> interaction rate limiting
        -> response selection / special events
        -> synchronized lighting and audio
        -> optional terminal presentation display

The main control loop is intentionally kept small. Individual tasks are
handled by helper functions so future students can study or modify one
piece of behavior at a time.

Press Ctrl+C to stop.
"""

from __future__ import annotations

import argparse
import signal
import time
from collections.abc import Callable
from dataclasses import dataclass

from rich.console import Console
from rich.live import Live

from piano_staircase_demo.audio import (
    AudioClip,
    AudioSystem,
)
from piano_staircase_demo.events import (
    SpecialEventDirector,
    TemporaryEventOverride,
)
from piano_staircase_demo.interaction import CooldownGate
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
from piano_staircase_demo.sensor import DistanceSensor
from piano_staircase_demo.terminal_display import (
    DisplayState,
    TerminalDisplay,
)
from piano_staircase_demo.trigger import DistanceTrigger


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
        reversed(RESPONSES)
    ),

    "bounce": (
        RESPONSES[0],
        RESPONSES[2],
        RESPONSES[1],
        RESPONSES[2],
    ),

    PIPE_EVENT_NAME: PIPE_PLACEHOLDER_RESPONSES,
}


ResponseMode = (
    CycleMode
    | RandomMode
    | DistanceMode
)


# ---------------------------------------------------------------------------
# Small state containers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LightCue:
    """One timed lighting event."""

    light_name: str
    start_time: float
    end_time: float


@dataclass(frozen=True)
class PlaybackPlan:
    """
    Everything needed to start one accepted response.

    A plan may contain one ordinary note or several notes in a special
    sequence.
    """

    responses: tuple[InteractionResponse, ...]
    clip: AudioClip

    note_duration_seconds: float
    note_gap_seconds: float

    console_message: str
    special_text: str | None = None


@dataclass
class RuntimeState:
    """Mutable state that changes while the demo is running."""

    active_channel: LightingChannel | None = None

    light_cues: tuple[LightCue, ...] = ()

    last_interaction_time: float | None = None
    last_response_time: float | None = None

    display_note: str | None = None
    display_light_name: str | None = None
    display_special_text: str | None = None


@dataclass
class DisplaySession:
    """Resources and timing used by the optional terminal display."""

    display: TerminalDisplay
    live: Live

    update_interval_seconds: float
    next_update_time: float


# ---------------------------------------------------------------------------
# Command-line configuration
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description=(
            "Run the Piano Staircase Demo 2 tabletop application."
        )
    )

    parser.add_argument(
        "--trigger-mm",
        type=int,
        default=TRIGGER_DISTANCE_MM,
        help=(
            "Trigger distance in millimeters "
            f"(default: {TRIGGER_DISTANCE_MM})."
        ),
    )

    parser.add_argument(
        "--rearm-mm",
        type=int,
        default=REARM_DISTANCE_MM,
        help=(
            "Rearm distance in millimeters "
            f"(default: {REARM_DISTANCE_MM})."
        ),
    )

    parser.add_argument(
        "--trigger-samples",
        type=int,
        default=TRIGGER_SAMPLES,
        help=(
            "Consecutive trigger samples "
            f"(default: {TRIGGER_SAMPLES})."
        ),
    )

    parser.add_argument(
        "--rearm-samples",
        type=int,
        default=REARM_SAMPLES,
        help=(
            "Consecutive rearm samples "
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
            "Minimum interval between accepted interactions "
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
            "How accepted interactions select responses "
            f"(default: {RESPONSE_MODE})."
        ),
    )

    parser.add_argument(
        "--special-every",
        "--flourish-every",
        dest="special_every",
        type=int,
        default=SPECIAL_EVERY,
        help=(
            "Play a random special event every N accepted "
            "interactions; 0 disables special events "
            f"(default: {SPECIAL_EVERY})."
        ),
    )

    parser.add_argument(
        "--pipe-triggers",
        type=int,
        default=PIPE_OVERRIDE_TRIGGERS,
        help=(
            "Number of accepted interactions in a temporary "
            "pipes override "
            f"(default: {PIPE_OVERRIDE_TRIGGERS})."
        ),
    )

    parser.add_argument(
        "--display",
        action="store_true",
        help="Show the live terminal presentation display.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Display dropped and invalid interactions.",
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

    if args.special_every < 0:
        raise SystemExit(
            "--special-every cannot be negative."
        )

    if args.pipe_triggers < 1:
        raise SystemExit(
            "--pipe-triggers must be at least 1."
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
        return DistanceMode(
            RESPONSES,
            minimum_distance_mm=1,
            maximum_distance_mm=args.trigger_mm,
        )

    raise AssertionError(
        f"Unhandled response mode: {args.response_mode}"
    )


def create_audio_clips(
    audio: AudioSystem,
) -> tuple[
    dict[str, AudioClip],
    dict[str, AudioClip],
]:
    """Pre-generate all musical clips used by the demo."""

    note_clips = {
        response.note: audio.create_sequence(
            (response.note,),
            note_duration_seconds=NOTE_DURATION_SECONDS,
        )
        for response in RESPONSES
    }

    special_clips = {
        name: audio.create_sequence(
            tuple(
                response.note
                for response in responses
            ),
            note_duration_seconds=(
                SPECIAL_NOTE_DURATION_SECONDS
            ),
            note_gap_seconds=(
                SPECIAL_NOTE_GAP_SECONDS
            ),
        )
        for name, responses
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

    print("=== Piano Staircase Demo 2 ===")
    print()
    print("C4 -> GREEN")
    print("E4 -> YELLOW")
    print("G4 -> BLUE")
    print()
    print(
        f"Response mode: {args.response_mode}"
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
    print("Initializing hardware...")


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
) -> tuple[LightCue, ...]:
    """Build timed lighting cues for a response sequence."""

    cues = []
    cue_start = start_time

    for response in responses:
        cue_end = (
            cue_start
            + duration_seconds
        )

        cues.append(
            LightCue(
                light_name=response.light_name,
                start_time=cue_start,
                end_time=cue_end,
            )
        )

        cue_start = (
            cue_end
            + gap_seconds
        )

    return tuple(cues)


def choose_active_light(
    *,
    cues: tuple[LightCue, ...],
    channels: dict[
        str,
        LightingChannel,
    ],
    active_channel: LightingChannel | None,
    now: float,
) -> LightingChannel | None:
    """
    Apply the light that should be active at the current time.

    Returns the newly active channel, or None if all channels should be off.
    """

    desired_channel = None

    for cue in cues:
        if (
            cue.start_time
            <= now
            < cue.end_time
        ):
            desired_channel = channels[
                cue.light_name
            ]

            break

    if desired_channel is active_channel:
        return active_channel

    if active_channel is not None:
        active_channel.off()

    if desired_channel is not None:
        desired_channel.set_brightness(
            LIGHT_BRIGHTNESS_PERCENT
        )

    return desired_channel


def update_lighting(
    runtime: RuntimeState,
    *,
    channels: dict[
        str,
        LightingChannel,
    ],
    now: float,
) -> None:
    """Advance lighting cues without blocking the sensor loop."""

    runtime.active_channel = (
        choose_active_light(
            cues=runtime.light_cues,
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
        >= runtime.light_cues[-1].end_time
    ):
        runtime.light_cues = ()


# ---------------------------------------------------------------------------
# Deciding what an accepted interaction should play
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

    An active temporary override gets first priority.

    Returns:

        (special event name, pipes-was-just-activated)
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
        event_director.record_interaction()
    )

    if special_name == PIPE_EVENT_NAME:
        event_override.activate(
            PIPE_EVENT_NAME,
            interactions=pipe_triggers,
        )

        # The interaction that selected pipes mode
        # becomes the first pipe interaction.
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
    """Build the playback plan for a special event."""

    responses = SPECIAL_SEQUENCES[
        special_name
    ]

    notes = " ".join(
        response.note
        for response in responses
    )

    if special_name == PIPE_EVENT_NAME:
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
            f"SPECIAL "
            f"{special_name.upper()} "
            f"-> {notes}"
        )

        special_text = (
            f"SPECIAL // "
            f"{special_name.upper()}"
        )

    return PlaybackPlan(
        responses=responses,
        clip=special_clips[
            special_name
        ],
        note_duration_seconds=(
            SPECIAL_NOTE_DURATION_SECONDS
        ),
        note_gap_seconds=(
            SPECIAL_NOTE_GAP_SECONDS
        ),
        console_message=console_message,
        special_text=special_text,
    )


def build_ordinary_plan(
    *,
    distance_mm: int,
    mode: ResponseMode,
    note_clips: dict[
        str,
        AudioClip,
    ],
) -> PlaybackPlan:
    """Build the playback plan for an ordinary interaction."""

    response = mode.next_response(
        distance_mm
    )

    return PlaybackPlan(
        responses=(
            response,
        ),
        clip=note_clips[
            response.note
        ],
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
    """
    Decide whether this accepted interaction is ordinary or special.
    """

    (
        special_name,
        pipe_activated,
    ) = choose_special_event(
        event_director=event_director,
        event_override=event_override,
        pipe_triggers=args.pipe_triggers,
    )

    if special_name is not None:
        return build_special_plan(
            special_name=special_name,
            pipe_activated=pipe_activated,
            event_override=event_override,
            special_clips=special_clips,
        )

    return build_ordinary_plan(
        distance_mm=distance_mm,
        mode=mode,
        note_clips=note_clips,
    )


# ---------------------------------------------------------------------------
# Playing an accepted response
# ---------------------------------------------------------------------------

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
    """Start synchronized audio and lighting for one playback plan."""

    response_time = (
        time.monotonic()
    )

    runtime.light_cues = (
        build_light_cues(
            plan.responses,
            start_time=response_time,
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
            cues=runtime.light_cues,
            channels=channels,
            active_channel=(
                runtime.active_channel
            ),
            now=response_time,
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
        for response in plan.responses
    )

    if plan.responses:
        runtime.display_light_name = (
            plan.responses[0].light_name
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
    """
    Handle one sensor trigger.

    Returns a short console message, or None when nothing should be logged.
    """

    # Do not start another sound while one is still playing.
    if audio.is_playing:
        if args.verbose:
            return (
                f"{distance_mm:4d} mm "
                "-> DROP AUDIO BUSY"
            )

        return None

    # Rate-limit successfully serviceable interactions.
    if not gate.allow():
        if args.verbose:
            return (
                f"{distance_mm:4d} mm "
                "-> DROP COOLDOWN"
            )

        return None

    # Decide what this interaction should do.
    plan = choose_playback_plan(
        distance_mm=distance_mm,
        args=args,
        mode=mode,
        event_director=event_director,
        event_override=event_override,
        note_clips=note_clips,
        special_clips=special_clips,
    )

    # Start its audio and lights.
    start_playback(
        plan,
        audio=audio,
        channels=channels,
        runtime=runtime,
    )

    return plan.console_message


# ---------------------------------------------------------------------------
# Terminal presentation display
# ---------------------------------------------------------------------------

def display_code_stage(
    *,
    interaction_time: float | None,
    now: float,
) -> str:
    """
    Choose the simulated code line highlighted on the display.

    Real execution happens too quickly for visitors to watch, so the display
    deliberately slows the logical flow without slowing the hardware.
    """

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


def start_terminal_display(
    args: argparse.Namespace,
) -> DisplaySession | None:
    """Start the optional Rich presentation display."""

    if not args.display:
        return None

    try:
        console = Console()

        display = TerminalDisplay(
            console
        )

        initial_state = DisplayState(
            response_mode=(
                args.response_mode
            ),
        )

        live = Live(
            display.render(
                initial_state,
                now_seconds=0.0,
            ),
            console=console,
            screen=True,
            auto_refresh=False,
        )

        live.start()

        return DisplaySession(
            display=display,
            live=live,
            update_interval_seconds=(
                1.0 / DISPLAY_HZ
            ),
            next_update_time=(
                time.monotonic()
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


def stop_terminal_display(
    session: DisplaySession | None,
) -> None:
    """Stop the terminal display and restore the normal console."""

    if session is not None:
        session.live.stop()


def refresh_terminal_display(
    session: DisplaySession | None,
    *,
    args: argparse.Namespace,
    runtime: RuntimeState,
    audio: AudioSystem,
    distance_mm: int | None,
    sample_time: float,
) -> DisplaySession | None:
    """
    Refresh the visitor-facing display.

    The sensor runs at 30 Hz by default, while this display refreshes at
    only 10 Hz. There is no need to redraw a terminal as quickly as the
    sensor is sampled.
    """

    if session is None:
        return None

    if (
        sample_time
        < session.next_update_time
    ):
        return session

    try:
        now = time.monotonic()

        # Once the physical response has ended, leave the result visible
        # briefly and then return the display to its idle state.
        if (
            runtime.last_response_time
            is not None
            and (
                now
                - runtime.last_response_time
            )
            >= DISPLAY_RESPONSE_HOLD_SECONDS
            and not audio.is_playing
            and runtime.active_channel
            is None
        ):
            runtime.display_note = None
            runtime.display_light_name = None
            runtime.display_special_text = None

        interaction_is_recent = (
            runtime.last_interaction_time
            is not None
            and (
                now
                - runtime.last_interaction_time
            )
            < 0.75
        )

        if interaction_is_recent:
            trigger_state = "FIRED"
        else:
            trigger_state = "ARMED"

        # During a multi-light sequence, show the channel that is actually
        # active right now. Otherwise retain the last selected response.
        if runtime.active_channel is not None:
            display_light_name = (
                runtime
                .active_channel
                .name
                .lower()
            )
        else:
            display_light_name = (
                runtime.display_light_name
            )

        display_state = DisplayState(
            distance_mm=distance_mm,
            trigger_state=trigger_state,
            response_mode=(
                args.response_mode
            ),
            note=runtime.display_note,
            light_name=display_light_name,
            output_active=(
                runtime.active_channel
                is not None
            ),
            audio_active=audio.is_playing,
            code_stage=display_code_stage(
                interaction_time=(
                    runtime
                    .last_interaction_time
                ),
                now=now,
            ),
            special_text=(
                runtime.display_special_text
            ),
        )

        session.live.update(
            session.display.render(
                display_state,
                now_seconds=now,
            ),
            refresh=True,
        )

        session.next_update_time = (
            now
            + session.update_interval_seconds
        )

        return session

    except Exception as exc:
        session.live.stop()

        print()
        print(
            "WARNING: Terminal display "
            f"failed: {exc}"
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
    """
    Schedule the next sensor poll.

    If something temporarily delays the program, do not rapidly replay all
    of the sensor polls that were missed.
    """

    next_sample += interval

    now = time.monotonic()

    if (
        next_sample
        < now - interval
    ):
        return (
            now + interval
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
    """
    Initialize the hardware and run the Demo 2 control loop.

    The loop intentionally reads like a short checklist:

        update lights
        read sensor
        handle trigger
        update display
        schedule next poll
    """

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

    gate = CooldownGate(
        args.cooldown
    )

    mode = create_response_mode(
        args
    )

    event_director = SpecialEventDirector(
        every_n_interactions=(
            args.special_every
        ),
        event_names=tuple(
            SPECIAL_SEQUENCES
        ),
    )

    event_override = (
        TemporaryEventOverride()
    )

    runtime = RuntimeState()

    interval = (
        1.0 / args.hz
    )

    with (
        DistanceSensor() as sensor,
        LightingSystem() as lights,
        AudioSystem() as audio,
    ):
        channels = {
            "green": lights.green,
            "yellow": lights.yellow,
            "blue": lights.blue,
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
        print("Ready.")
        print("Press Ctrl+C to stop.")
        print()

        display_session = (
            start_terminal_display(
                args
            )
        )

        next_sample = (
            time.monotonic()
        )

        try:
            while not should_stop():

                # 1. Wait for the next 30 Hz sensor poll.
                now = time.monotonic()

                if now < next_sample:
                    time.sleep(
                        next_sample - now
                    )

                sample_time = (
                    time.monotonic()
                )

                # 2. Advance any lighting sequence already in progress.
                update_lighting(
                    runtime,
                    channels=channels,
                    now=sample_time,
                )

                # 3. Read the distance sensor.
                distance_mm = (
                    sensor.distance_mm
                )

                # 4. Feed valid readings into the trigger logic.
                if distance_mm is None:
                    if (
                        args.verbose
                        and display_session
                        is None
                    ):
                        print(
                            "INVALID SENSOR SAMPLE"
                        )

                else:
                    fired = trigger.update(
                        distance_mm
                    )

                    if fired:
                        message = handle_trigger(
                            distance_mm=distance_mm,
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
                            note_clips=note_clips,
                            special_clips=(
                                special_clips
                            ),
                            channels=channels,
                            runtime=runtime,
                        )

                        if (
                            message is not None
                            and display_session
                            is None
                        ):
                            print(message)

                # 5. Refresh the visitor display at 10 Hz.
                display_session = (
                    refresh_terminal_display(
                        display_session,
                        args=args,
                        runtime=runtime,
                        audio=audio,
                        distance_mm=distance_mm,
                        sample_time=sample_time,
                    )
                )

                # 6. Schedule the next sensor poll.
                next_sample = (
                    advance_sample_schedule(
                        next_sample=(
                            next_sample
                        ),
                        interval=interval,
                    )
                )

        finally:
            stop_terminal_display(
                display_session
            )


# ---------------------------------------------------------------------------
# Program entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the Demo 2 application."""

    args = parse_args()

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
                lambda: stop_requested
            ),
        )

    except KeyboardInterrupt:
        pass

    except ValueError as exc:
        raise SystemExit(
            f"Invalid configuration: {exc}"
        ) from exc

    finally:
        print()
        print("Demo stopped.")


if __name__ == "__main__":
    main()
