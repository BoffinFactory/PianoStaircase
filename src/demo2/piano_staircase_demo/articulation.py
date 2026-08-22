"""
Instrument-articulation helpers for Piano Staircase Demo 2.

Response-selection modes answer:

    "Which response should this interaction use?"

Articulation answers:

    "How should that response behave over time?"

DistanceKeyboard converts the physical space above a distance sensor into
a one-dimensional chromatic keyboard.
"""

from __future__ import annotations

from dataclasses import dataclass


NOTE_NAMES = (
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
)


def midi_note_name(
    midi_note: int,
) -> str:
    """Return a readable MIDI note name such as C4 or F#5."""

    if not 0 <= midi_note <= 127:
        raise ValueError(
            "MIDI note must be between 0 and 127."
        )

    pitch_class = midi_note % 12

    octave = (
        midi_note // 12
        - 1
    )

    return (
        f"{NOTE_NAMES[pitch_class]}"
        f"{octave}"
    )


@dataclass(frozen=True)
class DistanceKeyboard:
    """
    Map a distance range onto a chromatic MIDI-note range.

    The far edge selects the lowest note.

    Moving closer raises the pitch.

    Moving farther than far_distance_mm leaves the keyboard and returns
    None.

    Distances closer than near_distance_mm remain clamped to the highest
    note.
    """

    near_distance_mm: int
    far_distance_mm: int

    low_note: int
    high_note: int

    def __post_init__(
        self,
    ) -> None:
        if self.near_distance_mm <= 0:
            raise ValueError(
                "near_distance_mm must be greater than zero."
            )

        if (
            self.far_distance_mm
            <= self.near_distance_mm
        ):
            raise ValueError(
                "far_distance_mm must be greater than "
                "near_distance_mm."
            )

        if not 0 <= self.low_note <= 127:
            raise ValueError(
                "low_note must be between 0 and 127."
            )

        if not 0 <= self.high_note <= 127:
            raise ValueError(
                "high_note must be between 0 and 127."
            )

        if self.high_note <= self.low_note:
            raise ValueError(
                "high_note must be greater than low_note."
            )

    def note_for_distance(
        self,
        distance_mm: int,
    ) -> int | None:
        """
        Return the MIDI note corresponding to a distance.

        Return None when the measurement is beyond the far edge.
        """

        if distance_mm < 0:
            raise ValueError(
                "distance_mm cannot be negative."
            )

        if (
            distance_mm
            > self.far_distance_mm
        ):
            return None

        clamped_distance = max(
            self.near_distance_mm,
            distance_mm,
        )

        position = (
            self.far_distance_mm
            - clamped_distance
        ) / (
            self.far_distance_mm
            - self.near_distance_mm
        )

        note_span = (
            self.high_note
            - self.low_note
        )

        midi_note = round(
            self.low_note
            + position
            * note_span
        )

        return max(
            self.low_note,
            min(
                self.high_note,
                midi_note,
            ),
        )
