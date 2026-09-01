"""Shared runtime state for Piano Staircase Demo 2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from piano_staircase_demo.audio import AudioClip
from piano_staircase_demo.modes import InteractionResponse

if TYPE_CHECKING:
    from piano_staircase_demo.lighting import LightingChannel


@dataclass(frozen=True)
class LightCue:
    """One timed lighting event."""

    light_name: str
    start_time: float
    end_time: float


@dataclass(frozen=True)
class PlaybackPlan:
    """Everything needed for one legacy one-shot response."""

    responses: tuple[InteractionResponse, ...]
    clip: AudioClip
    note_duration_seconds: float
    note_gap_seconds: float
    console_message: str
    special_text: str | None = None


@dataclass
class RuntimeState:
    """Mutable application state shared by interaction subsystems."""

    active_channel: LightingChannel | None = None
    light_cues: tuple[LightCue, ...] = ()

    # Legacy instrument paths hold one light at a time. Normal five-zone mode
    # may instead hold one or two rails simultaneously.
    held_light_name: str | None = None
    held_light_names: tuple[str, ...] = ()

    # A physical instrument interaction can remain engaged after a struck
    # note has been released. Legacy modes hold one note; normal five-zone
    # mode may strike a one- or two-note Vibraphone response.
    instrument_engaged: bool = False
    instrument_note: str | int | None = None
    zone_notes: tuple[str | int, ...] = ()
    instrument_note_release_time: float | None = None

    last_interaction_time: float | None = None
    last_response_time: float | None = None

    display_note: str | None = None
    display_light_name: str | None = None
    display_special_text: str | None = None

    # Continuous distance-keyboard EXIT debounce. This remains separate from
    # zone tracking because the 88-key keyboard has already validated this
    # behavior on the real VL53L0X hardware.
    distance_exit_samples: int = 0
