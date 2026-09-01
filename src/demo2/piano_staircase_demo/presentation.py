"""Terminal-presentation plumbing for Piano Staircase Demo 2."""

from __future__ import annotations

import argparse

from piano_staircase_demo.audio import AudioSystem
from piano_staircase_demo.display_process import DisplayProcess
from piano_staircase_demo.piano import PianoEngine
from piano_staircase_demo.pipes import PipeSystem
from piano_staircase_demo.runtime import RuntimeState
from piano_staircase_demo.terminal_display import DisplayState


DISPLAY_HZ = 5.0
DISPLAY_RESPONSE_HOLD_SECONDS = 0.75


def display_code_stage(
    *,
    interaction_time: float | None,
    now: float,
) -> str:
    """Choose the simulated code line highlighted on the display."""

    if interaction_time is None:
        return "sensor"

    elapsed = now - interaction_time

    if elapsed < 0.15:
        return "trigger"
    if elapsed < 0.30:
        return "response"
    if elapsed < 0.45:
        return "lighting"
    if elapsed < 0.75:
        return "audio"

    return "sensor"


def piano_audio_active(piano: PianoEngine | None) -> bool:
    """Return whether the application currently holds any synth keys."""

    return piano is not None and bool(piano.active_notes)


def pipe_audio_active(pipes: PipeSystem | None) -> bool:
    """Return whether one or more procedural pipe simulations are active."""

    return pipes is not None and pipes.active_count > 0


def clear_expired_display_response(
    runtime: RuntimeState,
    *,
    audio: AudioSystem,
    piano: PianoEngine | None,
    pipes: PipeSystem | None,
    now: float,
) -> None:
    """Return the presentation to idle after a completed response."""

    if runtime.last_response_time is None:
        return
    if now - runtime.last_response_time < DISPLAY_RESPONSE_HOLD_SECONDS:
        return
    if audio.is_playing:
        return
    if piano_audio_active(piano):
        return
    if pipe_audio_active(pipes):
        return
    if runtime.held_light_names:
        return
    if runtime.active_channel is not None:
        return

    runtime.display_note = None
    runtime.display_light_name = None
    runtime.display_special_text = None


def build_display_state(
    *,
    args: argparse.Namespace,
    runtime: RuntimeState,
    audio: AudioSystem,
    piano: PianoEngine | None,
    pipes: PipeSystem | None,
    distance_mm: int | None,
    now: float,
) -> DisplayState:
    """Build one small state snapshot for the presentation process."""

    clear_expired_display_response(
        runtime,
        audio=audio,
        piano=piano,
        pipes=pipes,
        now=now,
    )

    if args.articulation == "instrument":
        trigger_state = "HELD" if runtime.instrument_engaged else "ARMED"
    else:
        interaction_is_recent = (
            runtime.last_interaction_time is not None
            and now - runtime.last_interaction_time < 0.75
        )
        trigger_state = "FIRED" if interaction_is_recent else "ARMED"

    if runtime.held_light_names:
        light_name = "+".join(runtime.held_light_names)
    elif runtime.active_channel is not None:
        light_name = runtime.active_channel.name.lower()
    else:
        light_name = runtime.display_light_name

    return DisplayState(
        distance_mm=distance_mm,
        trigger_state=trigger_state,
        response_mode=args.response_mode,
        note=runtime.display_note,
        light_name=light_name,
        output_active=(
            bool(runtime.held_light_names)
            or runtime.active_channel is not None
        ),
        audio_active=(
            audio.is_playing
            or piano_audio_active(piano)
            or pipe_audio_active(pipes)
        ),
        code_stage=display_code_stage(
            interaction_time=runtime.last_interaction_time,
            now=now,
        ),
        special_text=runtime.display_special_text,
    )


def start_display_process(args: argparse.Namespace) -> DisplayProcess | None:
    """Start the optional presentation process."""

    if not args.display:
        return None

    try:
        return DisplayProcess.start(
            initial_state=DisplayState(response_mode=args.response_mode),
            refresh_hz=DISPLAY_HZ,
        )
    except Exception as exc:
        print(f"WARNING: Terminal display unavailable: {exc}")
        print("Continuing without the presentation display.")
        return None


def publish_display_state(
    display_process: DisplayProcess | None,
    *,
    args: argparse.Namespace,
    runtime: RuntimeState,
    audio: AudioSystem,
    piano: PianoEngine | None,
    pipes: PipeSystem | None,
    distance_mm: int | None,
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
        pipes=pipes,
        distance_mm=distance_mm,
        now=now,
    )

    if display_process.publish(state):
        return display_process

    error_message = display_process.error_message()
    display_process.close()
    print()

    if error_message is None:
        print("WARNING: Terminal display process stopped unexpectedly.")
    else:
        print(f"WARNING: Terminal display failed: {error_message}")

    print("Continuing without the presentation display.")
    return None
