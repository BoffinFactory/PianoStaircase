"""Persistent sampled-instrument interaction behavior for Demo 2."""

from __future__ import annotations

import argparse
import time

from piano_staircase_demo.app_config import (
    KEYBOARD_EXIT_SAMPLES,
    PIPE_EVENT_NAME,
    RESPONSES,
    ZONE_RESPONSES,
    ResponseMode,
)
from piano_staircase_demo.articulation import DistanceKeyboard, midi_note_name
from piano_staircase_demo.audio import AudioSystem
from piano_staircase_demo.events import (
    SpecialEventDirector,
    TemporaryEventOverride,
)
from piano_staircase_demo.interaction import CooldownGate, RapidPlayDetector
from piano_staircase_demo.lighting import (
    LightingChannel,
    update_lighting,
)
from piano_staircase_demo.piano import PianoEngine
from piano_staircase_demo.pipes import PipeSystem
from piano_staircase_demo.presence import PresenceEvent
from piano_staircase_demo.runtime import LightCue, RuntimeState
from piano_staircase_demo.specials import (
    choose_special_event,
    start_pipe_response,
)
from piano_staircase_demo.zones import DistanceZoneTracker


def instrument_note_label(note: str | int) -> str:
    """Return a display-friendly name for an instrument note."""

    return note if isinstance(note, str) else midi_note_name(note)


def instrument_notes_label(notes: tuple[str | int, ...]) -> str:
    """Return a display-friendly label for one note or a small chord."""

    return " + ".join(instrument_note_label(note) for note in notes)


# ---------------------------------------------------------------------------
# Existing cycle/random/distance instrument behavior
# ---------------------------------------------------------------------------

def start_ordinary_instrument_response(
    *,
    distance_mm: int,
    args: argparse.Namespace,
    mode: ResponseMode,
    keyboard: DistanceKeyboard | None,
    piano: PianoEngine,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
) -> str:
    """Start one sustained ordinary instrument response."""

    response = mode.next_response(distance_mm)

    if args.response_mode == "distance":
        if keyboard is None:
            raise RuntimeError("Distance keyboard was not initialized.")

        note = keyboard.note_for_distance(distance_mm)

        if note is None:
            raise RuntimeError(
                "Instrument entry occurred outside the distance keyboard."
            )
    else:
        note = response.note

    piano.note_on(note, velocity=args.piano_velocity)

    response_time = time.monotonic()
    runtime.light_cues = ()
    runtime.held_light_names = ()
    runtime.held_light_name = response.light_name
    runtime.zone_notes = ()
    runtime.instrument_note = note
    runtime.instrument_note_release_time = None
    runtime.last_interaction_time = response_time
    runtime.last_response_time = response_time
    runtime.display_note = instrument_note_label(note)
    runtime.display_light_name = response.light_name
    runtime.display_special_text = None

    update_lighting(runtime, channels=channels, now=response_time)

    return (
        f"{instrument_note_label(note)} -> "
        f"{response.light_name.upper()} (INSTRUMENT)"
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
    keyboard: DistanceKeyboard | None,
    piano: PianoEngine,
    pipes: PipeSystem | None,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
) -> str | None:
    """Handle exactly one physical legacy instrument entry."""

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

    return start_ordinary_instrument_response(
        distance_mm=distance_mm,
        args=args,
        mode=mode,
        keyboard=keyboard,
        piano=piano,
        channels=channels,
        runtime=runtime,
    )


def finish_instrument_interaction(
    *,
    piano: PianoEngine,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
) -> str | None:
    """Release a held instrument note and end the physical interaction."""

    message = None

    if runtime.instrument_note is not None:
        note = runtime.instrument_note
        piano.note_off(note)
        message = f"NOTE OFF {instrument_note_label(note)}"
        runtime.last_response_time = time.monotonic()

    for note in runtime.zone_notes:
        piano.note_off(note)

    runtime.instrument_note = None
    runtime.zone_notes = ()
    runtime.instrument_note_release_time = None
    runtime.instrument_engaged = False
    runtime.held_light_name = None
    runtime.held_light_names = ()
    runtime.distance_exit_samples = 0

    update_lighting(runtime, channels=channels, now=time.monotonic())
    return message


def update_distance_instrument_note(
    *,
    distance_mm: int,
    args: argparse.Namespace,
    mode: ResponseMode,
    keyboard: DistanceKeyboard,
    piano: PianoEngine,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
) -> str | None:
    """Change the held pitch while remaining inside the distance keyboard."""

    selected_note = keyboard.note_for_distance(distance_mm)

    if selected_note is None:
        return None

    # A special event or dropped interaction may be engaged without owning a
    # piano note. Do not suddenly start a piano halfway through it.
    if runtime.instrument_note is None:
        return None

    response = mode.next_response(distance_mm)

    # Lighting remains three broad bands even though the piano may expose
    # dozens of chromatic keys.
    if runtime.held_light_name != response.light_name:
        runtime.held_light_names = ()
        runtime.held_light_name = response.light_name
        runtime.display_light_name = response.light_name
        update_lighting(runtime, channels=channels, now=time.monotonic())

    if selected_note == runtime.instrument_note:
        return None

    old_note = runtime.instrument_note
    piano.note_off(old_note)
    piano.note_on(selected_note, velocity=args.piano_velocity)

    runtime.instrument_note = selected_note
    runtime.last_response_time = time.monotonic()
    runtime.display_note = midi_note_name(selected_note)

    if args.verbose:
        return (
            f"{distance_mm:4d} mm -> "
            f"{instrument_note_label(old_note)} -> "
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
    keyboard: DistanceKeyboard,
    piano: PianoEngine,
    pipes: PipeSystem | None,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
) -> str | None:
    """
    Process one reading for the proven full chromatic distance keyboard.

    The existing three-consecutive-far-sample EXIT debounce is intentionally
    preserved here unchanged in semantics.
    """

    selected_note = keyboard.note_for_distance(distance_mm)

    if selected_note is None:
        if not runtime.instrument_engaged:
            runtime.distance_exit_samples = 0
            return None

        runtime.distance_exit_samples += 1

        if runtime.distance_exit_samples < KEYBOARD_EXIT_SAMPLES:
            if args.verbose:
                return (
                    f"{distance_mm:4d} mm -> EXIT CANDIDATE "
                    f"{runtime.distance_exit_samples}/{KEYBOARD_EXIT_SAMPLES}"
                )
            return None

        runtime.distance_exit_samples = 0
        return finish_instrument_interaction(
            piano=piano,
            channels=channels,
            runtime=runtime,
        )

    # Any in-range reading cancels a pending exit.
    runtime.distance_exit_samples = 0

    if not runtime.instrument_engaged:
        # Mark engaged even if ENTER is dropped so the loop does not retry on
        # every sensor sample until cooldown/audio becomes available.
        runtime.instrument_engaged = True
        return handle_instrument_entry(
            distance_mm=distance_mm,
            args=args,
            gate=gate,
            mode=mode,
            event_director=event_director,
            event_override=event_override,
            audio=audio,
            keyboard=keyboard,
            piano=piano,
            pipes=pipes,
            channels=channels,
            runtime=runtime,
        )

    return update_distance_instrument_note(
        distance_mm=distance_mm,
        args=args,
        mode=mode,
        keyboard=keyboard,
        piano=piano,
        channels=channels,
        runtime=runtime,
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
    piano: PianoEngine,
    pipes: PipeSystem | None,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
) -> str | None:
    """Handle ENTER/EXIT for cycle/random instrument articulation."""

    if event is PresenceEvent.ENTER:
        runtime.instrument_engaged = True
        return handle_instrument_entry(
            distance_mm=distance_mm,
            args=args,
            gate=gate,
            mode=mode,
            event_director=event_director,
            event_override=event_override,
            audio=audio,
            keyboard=None,
            piano=piano,
            pipes=pipes,
            channels=channels,
            runtime=runtime,
        )

    if event is PresenceEvent.EXIT:
        return finish_instrument_interaction(
            piano=piano,
            channels=channels,
            runtime=runtime,
        )

    return None


# ---------------------------------------------------------------------------
# Normal five-zone Vibraphone behavior
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Normal five-zone Vibraphone + discoverable Pipe Physics behavior
# ---------------------------------------------------------------------------

def release_zone_notes(
    *,
    piano: PianoEngine,
    runtime: RuntimeState,
) -> None:
    """Release every currently held normal-zone Vibraphone key."""

    for note in runtime.zone_notes:
        piano.note_off(note)

    runtime.zone_notes = ()
    runtime.instrument_note_release_time = None


def service_zone_note_release(
    *,
    piano: PianoEngine,
    runtime: RuntimeState,
    now: float,
) -> None:
    """Release the current zone strike/chord after its NOTE ON duration."""

    release_time = runtime.instrument_note_release_time

    if release_time is None or now < release_time:
        return

    release_zone_notes(
        piano=piano,
        runtime=runtime,
    )


def hold_zone_lights(
    *,
    response_index: int,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
    now: float,
    is_entry: bool,
) -> None:
    """Track the current physical staircase zone without playing audio."""

    response = ZONE_RESPONSES[response_index]

    runtime.instrument_engaged = True
    runtime.light_cues = ()
    runtime.held_light_name = None
    runtime.held_light_names = response.light_names

    if is_entry:
        runtime.last_interaction_time = now

    runtime.last_response_time = now
    runtime.display_light_name = "+".join(response.light_names)
    runtime.display_special_text = None

    update_lighting(runtime, channels=channels, now=now)


def start_zone_response(
    *,
    response_index: int,
    args: argparse.Namespace,
    piano: PianoEngine,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
    is_entry: bool,
    now: float | None = None,
) -> str:
    """Strike one five-zone Vibraphone response and hold its light rail(s)."""

    if now is None:
        now = time.monotonic()

    response = ZONE_RESPONSES[response_index]

    # Crossing a boundary before the previous hold expires releases every key
    # normally. SoundFont release tails may continue underneath the new chord.
    release_zone_notes(
        piano=piano,
        runtime=runtime,
    )

    for note in response.notes:
        piano.note_on(note, velocity=args.piano_velocity)

    runtime.instrument_note = None
    runtime.zone_notes = response.notes
    runtime.instrument_note_release_time = now + args.zone_note_hold

    hold_zone_lights(
        response_index=response_index,
        channels=channels,
        runtime=runtime,
        now=now,
        is_entry=is_entry,
    )

    runtime.display_note = instrument_notes_label(response.notes)

    notes = instrument_notes_label(response.notes)
    lights = " + ".join(name.upper() for name in response.light_names)
    return f"{notes} -> {lights} (ZONE)"


def build_pipe_fall_light_cues(
    *,
    start_time: float,
) -> tuple[LightCue, ...]:
    """Build a top-to-bottom falling/bouncing staircase animation.

    The three physical rails are used as a coarse vertical visualization:
    BLUE is the top step, YELLOW is the middle, and GREEN is the bottom.
    The first rebound reaches the top again; later rebounds get progressively
    smaller so the animation reads as a damped bounce rather than a loop.
    """

    # (light, duration, dark gap after the light)
    pattern = (
        ("blue",   0.12, 0.00),
        ("yellow", 0.12, 0.00),
        ("green",  0.16, 0.04),  # first floor impact
        ("yellow", 0.10, 0.00),
        ("blue",   0.08, 0.00),  # largest rebound apex
        ("yellow", 0.10, 0.00),
        ("green",  0.14, 0.05),  # second floor impact
        ("yellow", 0.08, 0.00),
        ("green",  0.12, 0.06),  # smaller rebound
        ("yellow", 0.06, 0.00),
        ("green",  0.10, 0.00),  # final small impact
    )

    cues: list[LightCue] = []
    cue_start = start_time

    for light_name, duration, gap in pattern:
        cue_end = cue_start + duration
        cues.append(
            LightCue(
                light_name=light_name,
                start_time=cue_start,
                end_time=cue_end,
            )
        )
        cue_start = cue_end + gap

    return tuple(cues)


def restore_zone_lights_after_pipe_mode(
    *,
    current_zone: int | None,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
    now: float,
) -> None:
    """Return lighting to the current normal zone after Pipe Mode expires."""

    runtime.light_cues = ()
    runtime.held_light_name = None
    runtime.display_note = None

    if current_zone is None:
        runtime.instrument_engaged = False
        runtime.held_light_names = ()
        runtime.display_light_name = None
    else:
        response = ZONE_RESPONSES[current_zone]
        runtime.instrument_engaged = True
        runtime.held_light_names = response.light_names
        runtime.display_light_name = "+".join(response.light_names)

    update_lighting(runtime, channels=channels, now=now)


def leave_zone_during_pipe_mode(
    *,
    piano: PianoEngine,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
    now: float,
) -> str:
    """Leave sensor range while allowing the current pipe animation to finish."""

    release_zone_notes(piano=piano, runtime=runtime)
    runtime.instrument_note = None
    runtime.instrument_engaged = False
    runtime.held_light_name = None
    runtime.held_light_names = ()
    runtime.display_note = None
    runtime.last_response_time = now

    # Do not clear runtime.light_cues here. They visualize the falling pipe,
    # not the visitor's current sensor zone.
    update_lighting(runtime, channels=channels, now=now)
    return "PIPE PHYSICS MODE -> SENSOR EXIT (ANIMATION CONTINUES)"


def start_pipe_zone_response(
    *,
    response_index: int,
    args: argparse.Namespace,
    piano: PianoEngine,
    pipes: PipeSystem,
    rapid_play: RapidPlayDetector,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
    now: float,
    is_entry: bool,
    activated: bool,
) -> str | None:
    """
    Handle one accepted zone transition while Pipe Physics Mode is active.

    Normal Vibraphone strikes are suppressed. Each successfully launched pipe
    takes over the staircase LEDs with a top-to-bottom fall and damped-bounce
    animation. Unlocking starts one pipe immediately; after that, every
    accepted in-range zone transition attempts to launch another pipe.
    """

    # Do not leave a normal Vibraphone chord held when the interaction crosses
    # the transition that unlocks Pipe Physics Mode.
    release_zone_notes(
        piano=piano,
        runtime=runtime,
    )

    # Pipe Mode lighting visualizes the simulated falling object instead of
    # mirroring sensor distance. A newly spawned pipe replaces the previous
    # visual sequence; between spawns, the current animation continues.
    runtime.instrument_engaged = True
    runtime.held_light_name = None
    runtime.held_light_names = ()

    if is_entry:
        runtime.last_interaction_time = now

    # The dedicated Pipe Physics display owns the audio presentation while the
    # mode is active. Avoid leaving a stale normal-zone note label underneath.
    runtime.display_note = None

    # Every accepted in-range zone change owns the falling/bounce visual,
    # even if all six pipe MIDI channels are temporarily occupied. This keeps
    # Pipe Mode lighting independent of the visitor's distance-zone lights.
    runtime.light_cues = build_pipe_fall_light_cues(start_time=now)
    runtime.display_light_name = "blue"
    runtime.last_response_time = now
    update_lighting(runtime, channels=channels, now=now)

    if not rapid_play.allow_pipe_spawn(now=now):
        if args.verbose:
            return "PIPE ZONE CHANGE -> SPAWN COOLDOWN"
        return None

    snapshot = pipes.start_pipe(now=now)

    if snapshot is None:
        if args.verbose:
            return (
                "PIPE ZONE CHANGE -> DROP VISUAL ONLY; ALL "
                f"{pipes.maximum_pipes} PIPE CHANNELS BUSY"
            )
        return None

    if activated:
        runtime.last_interaction_time = now
        return f"PIPE PHYSICS MODE UNLOCKED -> PIPE #{snapshot.pipe_id}"

    return f"PIPE ZONE CHANGE -> PIPE #{snapshot.pipe_id}"


def finish_zone_interaction(
    *,
    piano: PianoEngine,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
) -> str:
    """Leave the entire zone range and turn all continuous lights off."""

    release_zone_notes(
        piano=piano,
        runtime=runtime,
    )

    runtime.instrument_note = None
    runtime.instrument_engaged = False
    runtime.held_light_name = None
    runtime.held_light_names = ()
    runtime.light_cues = ()
    runtime.last_response_time = time.monotonic()

    update_lighting(runtime, channels=channels, now=time.monotonic())
    return "ZONE EXIT -> LIGHTS OFF"


def handle_zone_instrument_sample(
    *,
    distance_mm: int,
    args: argparse.Namespace,
    tracker: DistanceZoneTracker,
    piano: PianoEngine,
    channels: dict[str, LightingChannel],
    runtime: RuntimeState,
    rapid_play: RapidPlayDetector | None = None,
    pipes: PipeSystem | None = None,
) -> str | None:
    """Process one valid distance reading for normal five-zone behavior."""

    transition = tracker.update(distance_mm)

    if transition is None:
        return None

    now = time.monotonic()
    rapid_update = None

    if rapid_play is not None:
        rapid_update = rapid_play.observe_transition(
            transition,
            now=now,
        )

    if transition.current_zone is None:
        if rapid_play is not None and rapid_play.active:
            return leave_zone_during_pipe_mode(
                piano=piano,
                channels=channels,
                runtime=runtime,
                now=now,
            )

        return finish_zone_interaction(
            piano=piano,
            channels=channels,
            runtime=runtime,
        )

    if rapid_play is not None and rapid_play.active:
        if pipes is None:
            raise RuntimeError(
                "Pipe Physics Mode activated without an initialized PipeSystem."
            )

        assert rapid_update is not None

        return start_pipe_zone_response(
            response_index=transition.current_zone,
            args=args,
            piano=piano,
            pipes=pipes,
            rapid_play=rapid_play,
            channels=channels,
            runtime=runtime,
            now=now,
            is_entry=transition.previous_zone is None,
            activated=rapid_update.activated,
        )

    return start_zone_response(
        response_index=transition.current_zone,
        args=args,
        piano=piano,
        channels=channels,
        runtime=runtime,
        is_entry=transition.previous_zone is None,
        now=now,
    )
