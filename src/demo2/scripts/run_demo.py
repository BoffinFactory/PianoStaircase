#!/usr/bin/env python3

"""
Piano Staircase Demo 2 tabletop application.

This entry point intentionally contains only application wiring, the hardware
loop, and shutdown handling. Interaction policy, presentation, lighting
runtime behavior, scheduler timing, and legacy articulation live in reusable
package modules.

Normal unattended behavior:

    five nonlinear distance zones
        -> stable hysteretic transition
        -> Vibraphone C4 / C4+E4 / E4 / E4+G4 / G4 strike
        -> matching GREEN / GREEN+YELLOW / YELLOW / YELLOW+BLUE / BLUE lights

Deliberate rapid back-and-forth zone movement unlocks Pipe Physics Mode:

    repeated direction reversals
        -> procedural falling Tubular Bell pipes
        -> LEDs animate a top-to-bottom fall and damped bounce
        -> normal Vibraphone strikes are temporarily suppressed
        -> idle timeout returns to normal zone behavior

The full 88-key distance piano remains available with:

    --response-mode distance

Legacy cycle/random and generated-WAV one-shot behavior remain available for
diagnostics, but are not the normal exhibit configuration.
"""

from __future__ import annotations

import argparse
import signal
import time
from collections.abc import Callable

from piano_staircase_demo.app_config import (
    SPECIAL_EVENT_NAMES,
    ZONE_PROGRAM,
    create_distance_keyboard,
    create_response_mode,
    create_zone_tracker,
    parse_args,
    print_startup_summary,
    validate_args,
)
from piano_staircase_demo.audio import AudioSystem
from piano_staircase_demo.events import (
    SpecialEventDirector,
    TemporaryEventOverride,
)
from piano_staircase_demo.instrument import (
    handle_distance_instrument_sample,
    handle_presence_instrument_event,
    handle_zone_instrument_sample,
    restore_zone_lights_after_pipe_mode,
    service_zone_note_release,
)
from piano_staircase_demo.interaction import CooldownGate, RapidPlayDetector
from piano_staircase_demo.lighting import LightingSystem, update_lighting
from piano_staircase_demo.one_shot import create_note_clips, handle_trigger
from piano_staircase_demo.piano import PIANO_PROGRAM, PianoEngine
from piano_staircase_demo.pipes import PipeSystem
from piano_staircase_demo.presence import PresenceEvent, PresenceTracker
from piano_staircase_demo.presentation import (
    publish_display_state,
    start_display_process,
)
from piano_staircase_demo.runtime import RuntimeState
from piano_staircase_demo.scheduler import (
    advance_sample_schedule,
    service_pipe_system,
    sleep_until_next_work,
)
from piano_staircase_demo.sensor import DistanceSensor
from piano_staircase_demo.synth import FluidSynthEngine
from piano_staircase_demo.trigger import DistanceTrigger


def run_demo(
    args: argparse.Namespace,
    *,
    should_stop: Callable[[], bool],
) -> None:
    """Initialize hardware and run the Demo 2 cooperative control loop."""

    trigger = None
    presence = None
    keyboard = None
    zone_tracker = None

    if args.articulation == "one-shot":
        trigger = DistanceTrigger(
            trigger_distance_mm=args.trigger_mm,
            rearm_distance_mm=args.rearm_mm,
            trigger_samples=args.trigger_samples,
            rearm_samples=args.rearm_samples,
        )
    elif args.response_mode == "zones":
        zone_tracker = create_zone_tracker(args)
    elif args.response_mode == "distance":
        keyboard = create_distance_keyboard(args)
    else:
        presence = PresenceTracker(
            enter_distance_mm=args.trigger_mm,
            exit_distance_mm=args.rearm_mm,
            enter_samples=args.trigger_samples,
            exit_samples=args.rearm_samples,
        )

    rapid_play = None

    if (
        args.articulation == "instrument"
        and args.response_mode == "zones"
        and args.pipe_mode
    ):
        rapid_play = RapidPlayDetector(
            window_seconds=args.pipe_window,
            required_movements=args.pipe_moves,
            required_reversals=args.pipe_reversals,
            idle_timeout_seconds=args.pipe_idle_timeout,
            pipe_spawn_cooldown_seconds=args.pipe_spawn_cooldown,
        )

    gate = CooldownGate(args.cooldown)
    mode = create_response_mode(args)
    event_director = SpecialEventDirector(
        every_n_interactions=args.special_every,
        event_names=SPECIAL_EVENT_NAMES,
    )
    event_override = TemporaryEventOverride()
    runtime = RuntimeState()
    interval = 1.0 / args.hz

    with (
        DistanceSensor() as sensor,
        LightingSystem() as lights,
        AudioSystem() as audio,
    ):
        synth = None
        piano = None
        pipes = None

        try:
            needs_synth = (
                args.articulation == "instrument"
                or args.special_every > 0
            )

            if needs_synth:
                synth = FluidSynthEngine(gain=args.piano_gain)

            # Normal zones mode now owns a discoverable Pipe Physics path.
            # Legacy periodic specials may also still request PipeSystem in
            # explicit development modes.
            if rapid_play is not None or args.special_every > 0:
                if synth is None:
                    raise RuntimeError(
                        "Procedural pipes require FluidSynth."
                    )
                pipes = PipeSystem(synth)

            if args.articulation == "instrument":
                if synth is None:
                    raise RuntimeError("Instrument mode requires FluidSynth.")

                program = (
                    ZONE_PROGRAM
                    if args.response_mode == "zones"
                    else PIANO_PROGRAM
                )

                piano = PianoEngine(
                    synth=synth,
                    velocity=args.piano_velocity,
                    program=program,
                )

            channels = {
                "green": lights.green,
                "yellow": lights.yellow,
                "blue": lights.blue,
            }

            # Generated sine-wave notes exist only for the explicit legacy
            # one-shot articulation. Sampled instrument mode never builds them.
            note_clips = (
                create_note_clips(audio)
                if args.articulation == "one-shot"
                else {}
            )

            lights.all_off()
            print("Hardware initialized successfully.")

            if synth is not None:
                print("Shared FluidSynth initialized.")

            if rapid_play is not None and pipes is not None:
                print(
                    "Pipe Physics Mode ready: "
                    f"up to {pipes.maximum_pipes} simultaneous pipes."
                )
            elif pipes is not None:
                print(
                    "Procedural pipes ready for legacy development: "
                    f"{pipes.maximum_pipes} simultaneous channels."
                )

            print("Ready.")
            print("Press Ctrl+C to stop.")
            print()

            display_process = start_display_process(args)
            next_sample = time.monotonic()

            try:
                while not should_stop():
                    # Pipe synthesis needs more frequent cooperative servicing
                    # than the 30 Hz VL53L0X sensor poll.
                    now = time.monotonic()

                    if rapid_play is not None:
                        pipe_mode_expired = rapid_play.service(now=now)

                        if pipe_mode_expired and zone_tracker is not None:
                            restore_zone_lights_after_pipe_mode(
                                current_zone=zone_tracker.current_zone,
                                channels=channels,
                                runtime=runtime,
                                now=now,
                            )

                    service_pipe_system(pipes, now=now)

                    if now < next_sample:
                        sleep_until_next_work(
                            next_sample=next_sample,
                            pipes=pipes,
                        )
                        continue

                    sample_time = time.monotonic()

                    # 1. Advance existing output state.
                    update_lighting(
                        runtime,
                        channels=channels,
                        now=sample_time,
                    )

                    if (
                        args.articulation == "instrument"
                        and args.response_mode == "zones"
                    ):
                        if piano is None:
                            raise RuntimeError(
                                "Zone instrument was not initialized."
                            )

                        service_zone_note_release(
                            piano=piano,
                            runtime=runtime,
                            now=sample_time,
                        )

                    # 2. Read the distance sensor. Invalid samples are ignored;
                    # raw VL53L0X far values such as 8190 remain meaningful to
                    # the established EXIT/rearm logic.
                    distance_mm = sensor.distance_mm
                    message = None

                    # 3. Interpret one valid distance sample.
                    if distance_mm is None:
                        if args.verbose and display_process is None:
                            print("INVALID SENSOR SAMPLE")

                    elif args.articulation == "one-shot":
                        if trigger is None:
                            raise RuntimeError(
                                "One-shot trigger was not initialized."
                            )

                        if trigger.update(distance_mm):
                            message = handle_trigger(
                                distance_mm=distance_mm,
                                args=args,
                                gate=gate,
                                mode=mode,
                                event_director=event_director,
                                event_override=event_override,
                                audio=audio,
                                note_clips=note_clips,
                                pipes=pipes,
                                channels=channels,
                                runtime=runtime,
                            )

                    elif args.response_mode == "zones":
                        if zone_tracker is None or piano is None:
                            raise RuntimeError(
                                "Five-zone instrument was not initialized."
                            )

                        message = handle_zone_instrument_sample(
                            distance_mm=distance_mm,
                            args=args,
                            tracker=zone_tracker,
                            piano=piano,
                            channels=channels,
                            runtime=runtime,
                            rapid_play=rapid_play,
                            pipes=pipes,
                        )

                    elif args.response_mode == "distance":
                        if keyboard is None or piano is None:
                            raise RuntimeError(
                                "Distance instrument was not initialized."
                            )

                        message = handle_distance_instrument_sample(
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

                    else:
                        if presence is None or piano is None:
                            raise RuntimeError(
                                "Presence instrument was not initialized."
                            )

                        event = presence.update(distance_mm)

                        if event in (PresenceEvent.ENTER, PresenceEvent.EXIT):
                            message = handle_presence_instrument_event(
                                event=event,
                                distance_mm=distance_mm,
                                args=args,
                                gate=gate,
                                mode=mode,
                                event_director=event_director,
                                event_override=event_override,
                                audio=audio,
                                piano=piano,
                                pipes=pipes,
                                channels=channels,
                                runtime=runtime,
                            )

                    if message is not None and display_process is None:
                        print(message)

                    # 4. Publish presentation state without delaying I/O.
                    display_process = publish_display_state(
                        display_process,
                        args=args,
                        runtime=runtime,
                        audio=audio,
                        piano=piano,
                        pipes=pipes,
                        distance_mm=distance_mm,
                        now=sample_time,
                        rapid_play=rapid_play,
                    )

                    # 5. Schedule the next sensor poll without catch-up bursts.
                    next_sample = advance_sample_schedule(
                        next_sample=next_sample,
                        interval=interval,
                    )

            finally:
                if display_process is not None:
                    display_process.close()

        finally:
            # Clients share one FluidSynth process. Stop clients first, then
            # terminate the common synth exactly once.
            if pipes is not None:
                try:
                    pipes.stop_all()
                except RuntimeError:
                    pass

            if piano is not None:
                piano.close()

            if synth is not None:
                synth.close()


def main() -> None:
    """Run the Demo 2 application."""

    args = parse_args()
    validate_args(args)

    stop_requested = False

    def request_stop(signum, frame) -> None:
        # Signal handlers intentionally request clean shutdown only. Do not
        # interrupt a VL53L0X register transaction from inside the handler.
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    print_startup_summary(args)

    try:
        run_demo(
            args,
            should_stop=lambda: stop_requested,
        )
    except KeyboardInterrupt:
        pass
    except ValueError as exc:
        raise SystemExit(f"Invalid configuration: {exc}") from exc
    finally:
        print()
        print("Demo stopped.")


if __name__ == "__main__":
    main()
