"""Legacy generated-WAV articulation for Piano Staircase Demo 2."""

from __future__ import annotations

import argparse
import time

from piano_staircase_demo.app_config import (
    NOTE_DURATION_SECONDS,
    PIPE_EVENT_NAME,
    RESPONSES,
    ResponseMode,
)
from piano_staircase_demo.audio import AudioClip, AudioSystem
from piano_staircase_demo.events import (
    SpecialEventDirector,
    TemporaryEventOverride,
)
from piano_staircase_demo.interaction import CooldownGate
from piano_staircase_demo.lighting import (
    LightingChannel,
    build_light_cues,
    choose_active_light,
)
from piano_staircase_demo.pipes import PipeSystem
from piano_staircase_demo.runtime import PlaybackPlan, RuntimeState
from piano_staircase_demo.specials import (
    choose_special_event,
    start_pipe_response,
)


def create_note_clips(audio: AudioSystem) -> dict[str, AudioClip]:
    """Pre-generate the short sine-wave notes used only by legacy mode."""

    return {
        response.note: audio.create_sequence(
            (response.note,),
            note_duration_seconds=NOTE_DURATION_SECONDS,
        )
        for response in RESPONSES
    }


def build_ordinary_plan(
    *,
    distance_mm: int,
    mode: ResponseMode,
    note_clips: dict[str, AudioClip],
) -> PlaybackPlan:
    """Build one ordinary legacy one-shot response."""

    response = mode.next_response(distance_mm)

    return PlaybackPlan(
        responses=(response,),
        clip=note_clips[response.note],
        note_duration_seconds=NOTE_DURATION_SECONDS,
        note_gap_seconds=0.0,
        console_message=f"{response.note} -> {response.light_name.upper()}",
    )


def start_playback(
    plan: PlaybackPlan,
    *,
    audio: AudioSystem,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
) -> None:
    """Start synchronized legacy one-shot audio and lighting."""

    response_time = time.monotonic()
    runtime.held_light_name = None
    runtime.light_cues = build_light_cues(
        plan.responses,
        start_time=response_time,
        duration_seconds=plan.note_duration_seconds,
        gap_seconds=plan.note_gap_seconds,
    )
    runtime.active_channel = choose_active_light(
        cues=runtime.light_cues,
        channels=channels,
        active_channel=runtime.active_channel,
        now=response_time,
    )

    audio.play(plan.clip, blocking=False)

    runtime.last_interaction_time = response_time
    runtime.last_response_time = response_time
    runtime.display_note = " ".join(
        response.note for response in plan.responses
    )
    runtime.display_light_name = (
        plan.responses[0].light_name if plan.responses else None
    )
    runtime.display_special_text = plan.special_text


def handle_trigger(
    *,
    distance_mm: int,
    args: argparse.Namespace,
    gate: CooldownGate,
    mode: ResponseMode,
    event_director: SpecialEventDirector,
    event_override: TemporaryEventOverride,
    audio: AudioSystem,
    note_clips: dict[str, AudioClip],
    pipes: PipeSystem | None,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
) -> str | None:
    """Handle one original one-shot sensor trigger."""

    if audio.is_playing:
        return f"{distance_mm:4d} mm -> DROP AUDIO BUSY" if args.verbose else None

    if not gate.allow():
        return f"{distance_mm:4d} mm -> DROP COOLDOWN" if args.verbose else None

    special_name, pipe_activated = choose_special_event(
        event_director=event_director,
        event_override=event_override,
        pipe_triggers=args.pipe_triggers,
    )

    if special_name == PIPE_EVENT_NAME:
        if pipes is None:
            raise RuntimeError(
                "Pipe special selected without an initialized PipeSystem."
            )

        return start_pipe_response(
            distance_mm=distance_mm,
            mode=mode,
            pipe_activated=pipe_activated,
            event_override=event_override,
            pipes=pipes,
            channels=channels,
            runtime=runtime,
        )

    if special_name is not None:
        raise RuntimeError(f"Unknown special event selected: {special_name}")

    plan = build_ordinary_plan(
        distance_mm=distance_mm,
        mode=mode,
        note_clips=note_clips,
    )
    start_playback(
        plan,
        audio=audio,
        channels=channels,
        runtime=runtime,
    )

    return plan.console_message
