"""Legacy special-event runtime glue for Piano Staircase Demo 2."""

from __future__ import annotations

import time

from piano_staircase_demo.app_config import PIPE_EVENT_NAME
from piano_staircase_demo.events import (
    SpecialEventDirector,
    TemporaryEventOverride,
)
from piano_staircase_demo.lighting import (
    LightingChannel,
    choose_active_light,
)
from piano_staircase_demo.modes import CycleMode, DistanceMode, RandomMode
from piano_staircase_demo.pipes import PipeSystem
from piano_staircase_demo.runtime import LightCue, RuntimeState


PIPE_LIGHT_DURATION_SECONDS = 0.15
ResponseMode = CycleMode | RandomMode | DistanceMode


def choose_special_event(
    *,
    event_director: SpecialEventDirector,
    event_override: TemporaryEventOverride,
    pipe_triggers: int,
) -> tuple[str | None, bool]:
    """Choose one legacy special event, if any."""

    special_name = event_override.consume()
    pipe_activated = False

    if special_name is not None:
        return special_name, pipe_activated

    special_name = event_director.record_interaction()

    if special_name == PIPE_EVENT_NAME:
        event_override.activate(
            PIPE_EVENT_NAME,
            interactions=pipe_triggers,
        )

        # The selecting interaction becomes the first overridden interaction.
        special_name = event_override.consume()
        pipe_activated = True

    return special_name, pipe_activated


def start_pipe_response(
    *,
    distance_mm: int,
    mode: ResponseMode,
    pipe_activated: bool,
    event_override: TemporaryEventOverride,
    pipes: PipeSystem,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
) -> str:
    """Launch one real nonblocking procedural falling-pipe response."""

    response_time = time.monotonic()
    pipe = pipes.start_pipe(now=response_time)

    if pipe is None:
        runtime.last_interaction_time = response_time
        runtime.last_response_time = response_time
        runtime.display_note = None
        runtime.display_light_name = None
        runtime.display_special_text = "PIPES // ALL CHANNELS BUSY"

        return (
            "PIPES -> ALL CHANNELS BUSY "
            f"({pipes.active_count}/{pipes.maximum_pipes} active)"
        )

    # Pipe triggers retain the old brief response-selected light cue. This
    # path is development-only until the future Kayleigh Mode owns pipes.
    response = mode.next_response(distance_mm)
    runtime.held_light_name = None
    runtime.light_cues = (
        LightCue(
            light_name=response.light_name,
            start_time=response_time,
            end_time=response_time + PIPE_LIGHT_DURATION_SECONDS,
        ),
    )
    runtime.active_channel = choose_active_light(
        cues=runtime.light_cues,
        channels=channels,
        active_channel=runtime.active_channel,
        now=response_time,
    )

    runtime.last_interaction_time = response_time
    runtime.last_response_time = response_time
    runtime.display_note = f"PIPE #{pipe.pipe_id}"
    runtime.display_light_name = response.light_name

    remaining = event_override.remaining_interactions
    runtime.display_special_text = (
        "PIPES // "
        f"#{pipe.pipe_id} "
        f"{pipe.material.upper()} // "
        f"{remaining} REMAINING"
    )

    prefix = "SPECIAL PIPES MODE" if pipe_activated else "PIPES OVERRIDE"

    return (
        f"{prefix} -> "
        f"PIPE #{pipe.pipe_id} "
        f"{pipe.material.upper()} "
        f"L={pipe.length_m:.2f}m "
        f"e={pipe.restitution:.2f} "
        f"impacts={pipe.impact_count} "
        f"({remaining} remaining)"
    )
