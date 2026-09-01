"""Command-line configuration and validated defaults for Demo 2."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from piano_staircase_demo.articulation import (
    DEFAULT_KEYBOARD_CENTER_NOTE,
    DEFAULT_KEYBOARD_KEY_SCALE,
    DistanceKeyboard,
    midi_note_name,
)
from piano_staircase_demo.modes import (
    CycleMode,
    DistanceMode,
    InteractionResponse,
    RandomMode,
)
from piano_staircase_demo.piano import DEFAULT_GAIN, DEFAULT_VELOCITY
from piano_staircase_demo.zones import DistanceZoneTracker


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

# Persistent sampled audio is the normal Demo 2 behavior. The original
# generated one-shot WAV path remains only for diagnostics/legacy testing.
ARTICULATION = "instrument"

# Five nonlinear continuous approach zones are the normal unattended mode.
RESPONSE_MODE = "zones"

PIANO_GAIN = DEFAULT_GAIN
PIANO_VELOCITY = DEFAULT_VELOCITY

# Full 88-key distance-piano alternate mode.
KEYBOARD_NEAR_MM = 50
KEYBOARD_FAR_MM = 1250
KEYBOARD_CENTER_NOTE = DEFAULT_KEYBOARD_CENTER_NOTE
KEYBOARD_KEY_SCALE = DEFAULT_KEYBOARD_KEY_SCALE
KEYBOARD_LOW_NOTE: int | None = None
KEYBOARD_HIGH_NOTE: int | None = None
KEYBOARD_EXIT_SAMPLES = 3

# ---------------------------------------------------------------------------
# Normal five-zone staircase interaction
# ---------------------------------------------------------------------------
#
# Keep the full practical 1250 mm detection envelope so a large nearby target
# can attract attention at long range. The richer hand-controlled part of the
# interaction is compressed closer to the sensor with explicit nonlinear
# boundaries.
#
# Boundaries are ordered NEAREST -> FARTHEST:
#
#   50-250 mm     BLUE             / G4
#   250-375 mm    YELLOW + BLUE    / E4 + G4
#   375-500 mm    YELLOW           / E4
#   500-650 mm    GREEN + YELLOW   / C4 + E4
#   650-1250 mm   GREEN            / C4
#
# The command line can override all four boundaries for physical tuning.
ZONE_NEAR_MM = 50
ZONE_FAR_MM = 1250
ZONE_BOUNDARIES_MM = (
    250,
    375,
    500,
    650,
)
ZONE_HYSTERESIS_MM = 30
ZONE_TRANSITION_SAMPLES = 3
ZONE_EXIT_SAMPLES = 3
ZONE_NOTE_HOLD_SECONDS = 0.8

# General MIDI bank 0, program 11 = Vibraphone.
ZONE_PROGRAM = 11

# Deliberate rapid back-and-forth play unlocks Pipe Physics Mode. These values
# are command-line adjustable so the final exhibit can be tuned on real
# hardware without another source edit.
PIPE_MODE_ENABLED = True
PIPE_GESTURE_WINDOW_SECONDS = 3.0
PIPE_GESTURE_MOVEMENTS = 5
PIPE_GESTURE_REVERSALS = 3
PIPE_IDLE_TIMEOUT_SECONDS = 5.0
PIPE_SPAWN_COOLDOWN_SECONDS = 0.0

# The older every-N-interactions special-event path remains available only for
# explicit legacy development modes. Normal zones mode uses rapid play above.
SPECIAL_EVERY = 0
PIPE_EVENT_NAME = "pipes"
PIPE_OVERRIDE_TRIGGERS = 4


@dataclass(frozen=True)
class ZoneResponse:
    """One normal five-zone musical and lighting response."""

    notes: tuple[str, ...]
    light_names: tuple[str, ...]


# Legacy cycle/random/distance behavior keeps the established single response
# objects. Normal five-zone mode uses ZONE_RESPONSES below instead.
RESPONSES = (
    InteractionResponse(note="C4", light_name="green"),
    InteractionResponse(note="E4", light_name="yellow"),
    InteractionResponse(note="G4", light_name="blue"),
)

# Ordered from farthest/lowest to nearest/highest so tracker zone indices map
# directly into this tuple.
ZONE_RESPONSES = (
    ZoneResponse(
        notes=("C4",),
        light_names=("green",),
    ),
    ZoneResponse(
        notes=("C4", "E4"),
        light_names=("green", "yellow"),
    ),
    ZoneResponse(
        notes=("E4",),
        light_names=("yellow",),
    ),
    ZoneResponse(
        notes=("E4", "G4"),
        light_names=("yellow", "blue"),
    ),
    ZoneResponse(
        notes=("G4",),
        light_names=("blue",),
    ),
)

SPECIAL_EVENT_NAMES = (PIPE_EVENT_NAME,)

ResponseMode = CycleMode | RandomMode | DistanceMode


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description="Run the Piano Staircase Demo 2 tabletop application."
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
        help=f"Sensor polling frequency (default: {POLL_HZ:g} Hz).",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=COOLDOWN_SECONDS,
        help=(
            "Minimum interval between accepted physical interactions "
            f"(default: {COOLDOWN_SECONDS:.2f} seconds)."
        ),
    )
    parser.add_argument(
        "--response-mode",
        choices=("cycle", "random", "zones", "distance"),
        default=RESPONSE_MODE,
        help=(
            "How ordinary interactions select responses "
            f"(default: {RESPONSE_MODE})."
        ),
    )
    parser.add_argument(
        "--articulation",
        choices=("one-shot", "instrument"),
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
            "FluidSynth master gain in instrument mode / procedural pipes "
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

    # Five-zone normal mode.
    parser.add_argument(
        "--zone-near-mm",
        type=int,
        default=ZONE_NEAR_MM,
        help=(
            "Near edge of the five-zone interaction "
            f"(default: {ZONE_NEAR_MM} mm)."
        ),
    )
    parser.add_argument(
        "--zone-far-mm",
        type=int,
        default=ZONE_FAR_MM,
        help=(
            "Far edge of the five-zone interaction "
            f"(default: {ZONE_FAR_MM} mm)."
        ),
    )
    parser.add_argument(
        "--zone-boundaries-mm",
        type=int,
        nargs=4,
        default=ZONE_BOUNDARIES_MM,
        metavar=("B1", "B2", "B3", "B4"),
        help=(
            "Four internal boundaries ordered nearest-to-farthest "
            f"(default: {' '.join(str(value) for value in ZONE_BOUNDARIES_MM)} mm)."
        ),
    )
    parser.add_argument(
        "--zone-hysteresis-mm",
        type=int,
        default=ZONE_HYSTERESIS_MM,
        help=(
            "Hysteresis applied around internal zone boundaries "
            f"(default: {ZONE_HYSTERESIS_MM} mm)."
        ),
    )
    parser.add_argument(
        "--zone-samples",
        type=int,
        default=ZONE_TRANSITION_SAMPLES,
        help=(
            "Consecutive samples required for a zone transition "
            f"(default: {ZONE_TRANSITION_SAMPLES})."
        ),
    )
    parser.add_argument(
        "--zone-exit-samples",
        type=int,
        default=ZONE_EXIT_SAMPLES,
        help=(
            "Consecutive beyond-range samples required for zone EXIT "
            f"(default: {ZONE_EXIT_SAMPLES})."
        ),
    )
    parser.add_argument(
        "--zone-note-hold",
        type=float,
        default=ZONE_NOTE_HOLD_SECONDS,
        help=(
            "NOTE ON duration for each accepted zone strike "
            f"(default: {ZONE_NOTE_HOLD_SECONDS:g} seconds)."
        ),
    )

    # Discoverable rapid-play Pipe Physics Mode.
    parser.add_argument(
        "--no-pipe-mode",
        dest="pipe_mode",
        action="store_false",
        default=PIPE_MODE_ENABLED,
        help="Disable rapid-play Pipe Physics Mode in normal zones mode.",
    )
    parser.add_argument(
        "--pipe-window",
        type=float,
        default=PIPE_GESTURE_WINDOW_SECONDS,
        help=(
            "Rolling time window for the rapid-play unlock "
            f"(default: {PIPE_GESTURE_WINDOW_SECONDS:g} seconds)."
        ),
    )
    parser.add_argument(
        "--pipe-moves",
        type=int,
        default=PIPE_GESTURE_MOVEMENTS,
        help=(
            "Stable in-range zone movements required to unlock Pipe Mode "
            f"(default: {PIPE_GESTURE_MOVEMENTS})."
        ),
    )
    parser.add_argument(
        "--pipe-reversals",
        type=int,
        default=PIPE_GESTURE_REVERSALS,
        help=(
            "Direction reversals required inside the unlock window "
            f"(default: {PIPE_GESTURE_REVERSALS})."
        ),
    )
    parser.add_argument(
        "--pipe-idle-timeout",
        type=float,
        default=PIPE_IDLE_TIMEOUT_SECONDS,
        help=(
            "Seconds without an accepted zone transition before Pipe Mode exits "
            f"(default: {PIPE_IDLE_TIMEOUT_SECONDS:g})."
        ),
    )
    parser.add_argument(
        "--pipe-spawn-cooldown",
        type=float,
        default=PIPE_SPAWN_COOLDOWN_SECONDS,
        help=(
            "Minimum time between newly launched pipes; 0 disables the cooldown "
            f"(default: {PIPE_SPAWN_COOLDOWN_SECONDS:g} seconds)."
        ),
    )

    # Full chromatic distance-piano alternate mode.
    parser.add_argument(
        "--keyboard-near-mm",
        type=int,
        default=KEYBOARD_NEAR_MM,
        help=(
            "Near edge of the continuous distance keyboard "
            f"(default: {KEYBOARD_NEAR_MM} mm)."
        ),
    )
    parser.add_argument(
        "--keyboard-far-mm",
        type=int,
        default=KEYBOARD_FAR_MM,
        help=(
            "Far edge of the continuous distance keyboard; farther readings "
            "begin EXIT confirmation "
            f"(default: {KEYBOARD_FAR_MM} mm)."
        ),
    )
    parser.add_argument(
        "--keyboard-center-note",
        type=int,
        default=KEYBOARD_CENTER_NOTE,
        help=(
            "Preferred MIDI note around which an automatically sized "
            "keyboard is centered when the full piano range is not needed "
            f"(default: {KEYBOARD_CENTER_NOTE}, "
            f"{midi_note_name(KEYBOARD_CENTER_NOTE)})."
        ),
    )
    parser.add_argument(
        "--keyboard-key-scale",
        type=float,
        default=KEYBOARD_KEY_SCALE,
        help=(
            "Physical virtual-key scale relative to a real acoustic piano. "
            "1.0 approximates real piano chromatic density; larger values "
            "make each virtual key wider "
            f"(default: {KEYBOARD_KEY_SCALE:g})."
        ),
    )
    parser.add_argument(
        "--keyboard-low-note",
        type=int,
        default=KEYBOARD_LOW_NOTE,
        help=(
            "Optional manual lowest MIDI note. Supply together with "
            "--keyboard-high-note to disable automatic physical sizing."
        ),
    )
    parser.add_argument(
        "--keyboard-high-note",
        type=int,
        default=KEYBOARD_HIGH_NOTE,
        help=(
            "Optional manual highest MIDI note. Supply together with "
            "--keyboard-low-note to disable automatic physical sizing."
        ),
    )

    parser.add_argument(
        "--special-every",
        "--flourish-every",
        dest="special_every",
        type=int,
        default=SPECIAL_EVERY,
        help=(
            "Legacy development special every N accepted interactions; "
            "0 disables specials "
            f"(default: {SPECIAL_EVERY})."
        ),
    )
    parser.add_argument(
        "--pipe-triggers",
        type=int,
        default=PIPE_OVERRIDE_TRIGGERS,
        help=(
            "Number of accepted interactions in the legacy pipe override "
            f"(default: {PIPE_OVERRIDE_TRIGGERS})."
        ),
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Show the terminal presentation in a separate process.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Display dropped, invalid, and instrument transition information.",
    )

    return parser.parse_args()


def create_distance_keyboard(args: argparse.Namespace) -> DistanceKeyboard:
    """Create the configured continuous distance keyboard."""

    return DistanceKeyboard(
        near_distance_mm=args.keyboard_near_mm,
        far_distance_mm=args.keyboard_far_mm,
        low_note=args.keyboard_low_note,
        high_note=args.keyboard_high_note,
        center_note=args.keyboard_center_note,
        key_scale=args.keyboard_key_scale,
    )


def create_zone_tracker(args: argparse.Namespace) -> DistanceZoneTracker:
    """Create the configured stable five-zone tracker."""

    return DistanceZoneTracker(
        near_distance_mm=args.zone_near_mm,
        far_distance_mm=args.zone_far_mm,
        boundaries_mm=tuple(args.zone_boundaries_mm),
        hysteresis_mm=args.zone_hysteresis_mm,
        transition_samples=args.zone_samples,
        exit_samples=args.zone_exit_samples,
    )


def validate_args(args: argparse.Namespace) -> None:
    """Reject invalid configuration before hardware starts."""

    if args.hz <= 0:
        raise SystemExit("--hz must be greater than zero.")
    if args.cooldown < 0:
        raise SystemExit("--cooldown cannot be negative.")
    if args.special_every < 0:
        raise SystemExit("--special-every cannot be negative.")
    if args.pipe_triggers < 1:
        raise SystemExit("--pipe-triggers must be at least 1.")
    if args.piano_gain <= 0:
        raise SystemExit("--piano-gain must be greater than zero.")
    if not 1 <= args.piano_velocity <= 127:
        raise SystemExit("--piano-velocity must be between 1 and 127.")
    if args.zone_note_hold <= 0:
        raise SystemExit("--zone-note-hold must be greater than zero.")
    if args.pipe_window <= 0:
        raise SystemExit("--pipe-window must be greater than zero.")
    if args.pipe_moves < 2:
        raise SystemExit("--pipe-moves must be at least 2.")
    if args.pipe_reversals < 1:
        raise SystemExit("--pipe-reversals must be at least 1.")
    if args.pipe_reversals >= args.pipe_moves:
        raise SystemExit("--pipe-reversals must be less than --pipe-moves.")
    if args.pipe_idle_timeout <= 0:
        raise SystemExit("--pipe-idle-timeout must be greater than zero.")
    if args.pipe_spawn_cooldown < 0:
        raise SystemExit("--pipe-spawn-cooldown cannot be negative.")

    if args.response_mode == "zones" and args.articulation != "instrument":
        raise SystemExit(
            "--response-mode zones requires --articulation instrument."
        )

    if args.response_mode == "zones" and args.special_every > 0:
        raise SystemExit(
            "Periodic specials are intentionally disabled in normal zones "
            "mode. Procedural pipes will be connected separately to "
            "deliberate rapid play."
        )

    try:
        create_distance_keyboard(args)
    except ValueError as exc:
        raise SystemExit(
            "Invalid distance-keyboard configuration: " f"{exc}"
        ) from exc

    try:
        create_zone_tracker(args)
    except ValueError as exc:
        raise SystemExit(
            "Invalid five-zone configuration: " f"{exc}"
        ) from exc


def create_response_mode(args: argparse.Namespace) -> ResponseMode:
    """Create the selected ordinary response mode."""

    if args.response_mode == "cycle":
        return CycleMode(RESPONSES)

    if args.response_mode == "random":
        return RandomMode(RESPONSES)

    if args.response_mode == "zones":
        # The normal five-zone path is handled directly by the zone tracker
        # and ZONE_RESPONSES. Keep a legacy DistanceMode object available so
        # the rest of the application wiring does not need a special case.
        return DistanceMode(
            RESPONSES,
            minimum_distance_mm=args.zone_near_mm,
            maximum_distance_mm=args.zone_far_mm,
        )

    if args.response_mode == "distance":
        if args.articulation == "instrument":
            minimum_distance_mm = args.keyboard_near_mm
            maximum_distance_mm = args.keyboard_far_mm
        else:
            minimum_distance_mm = 1
            maximum_distance_mm = args.trigger_mm

        return DistanceMode(
            RESPONSES,
            minimum_distance_mm=minimum_distance_mm,
            maximum_distance_mm=maximum_distance_mm,
        )

    raise AssertionError(f"Unhandled response mode: {args.response_mode}")


def print_startup_summary(args: argparse.Namespace) -> None:
    """Print the startup configuration."""

    print("=== Piano Staircase Demo 2 ===")
    print()
    print("Bottom: GREEN / C4")
    print("Middle: YELLOW / E4")
    print("Top:    BLUE / G4")
    print()
    print(f"Response mode: {args.response_mode}")
    print(f"Articulation:  {args.articulation}")

    if args.articulation == "instrument":
        print(f"Synth gain:     {args.piano_gain:g}")

        if args.response_mode == "zones":
            tracker = create_zone_tracker(args)
            boundaries = tracker.boundaries_mm
            print("Instrument:     Vibraphone (GM program 11)")
            print(
                "Zone range:     "
                f"{tracker.near_distance_mm}-{tracker.far_distance_mm} mm"
            )
            print(
                "Zone bounds:    "
                + ", ".join(f"{value} mm" for value in boundaries)
                + " (near -> far)"
            )
            print(
                "Zone stability: "
                f"±{tracker.hysteresis_mm} mm hysteresis, "
                f"{tracker.transition_samples} samples"
            )
            print(f"Note hold:      {args.zone_note_hold:g} s")
            print("Far -> near:")

            for response in ZONE_RESPONSES:
                notes = " + ".join(response.notes)
                lights = " + ".join(
                    name.upper() for name in response.light_names
                )
                print(f"  {notes:<9} -> {lights}")

            if args.pipe_mode:
                print("Pipe Physics:   rapid-play unlock enabled")
                print(
                    "Pipe unlock:    "
                    f"{args.pipe_moves} moves + "
                    f"{args.pipe_reversals} reversals / "
                    f"{args.pipe_window:g} s"
                )
                print(
                    "Pipe activity:  new pipe on unlock/reversal, "
                    f">={args.pipe_spawn_cooldown:g} s apart"
                )
                print(
                    "Pipe exit:      "
                    f"{args.pipe_idle_timeout:g} s without movement"
                )
            else:
                print("Pipe Physics:   disabled")

        elif args.response_mode == "distance":
            keyboard = create_distance_keyboard(args)
            sizing_text = "AUTO" if keyboard.auto_sized else "MANUAL"
            print("Instrument:     Acoustic Grand Piano (GM program 0)")
            print(
                "Keyboard:       "
                f"{midi_note_name(keyboard.low_note)} "
                f"@ {keyboard.far_distance_mm} mm -> "
                f"{midi_note_name(keyboard.high_note)} "
                f"@ {keyboard.near_distance_mm} mm"
            )
            print(
                "Virtual keys:   "
                f"{keyboard.note_count} "
                f"({sizing_text}, {keyboard.key_scale:g}x piano scale)"
            )
            print(
                "Key spacing:    "
                f"{keyboard.actual_semitone_width_mm:.1f} mm/semitone "
                f"across {keyboard.playable_span_mm} mm"
            )

    print(
        "Legacy specials: "
        + (
            f"every {args.special_every} accepted interactions"
            if args.special_every > 0
            else "disabled"
        )
    )

    if args.special_every > 0:
        print(f"Pipe override:   {args.pipe_triggers} interactions")

    print("Terminal display: " + ("enabled" if args.display else "disabled"))
    print()
    print("Initializing hardware...")
