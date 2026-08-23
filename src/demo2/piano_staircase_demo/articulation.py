"""
Instrument-articulation helpers for Piano Staircase Demo 2.

Response-selection modes answer:

    "Which response should this interaction use?"

Articulation answers:

    "How should that response behave over time?"

DistanceKeyboard converts the physical space above a distance sensor into
a one-dimensional chromatic keyboard.

By default, the number of virtual chromatic keys is derived from the
physical sensor span using approximately the same key density as a real
acoustic piano keyboard.

A typical modern piano octave is about 164.5 mm wide across seven white
keys. Treating that octave as twelve evenly spaced chromatic positions gives
a target spacing of roughly 13.7 mm per semitone.

This is an abstraction: the virtual keyboard intentionally uses equal
chromatic distance bands rather than reproducing the staggered geometry of
real black and white keys.
"""

from __future__ import annotations


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

STANDARD_PIANO_WHITE_KEY_WIDTH_MM = 23.5
STANDARD_PIANO_OCTAVE_WIDTH_MM = (
    STANDARD_PIANO_WHITE_KEY_WIDTH_MM
    * 7.0
)
STANDARD_PIANO_SEMITONE_PITCH_MM = (
    STANDARD_PIANO_OCTAVE_WIDTH_MM
    / 12.0
)

ACOUSTIC_PIANO_LOW_NOTE = 21
ACOUSTIC_PIANO_HIGH_NOTE = 108
DEFAULT_KEYBOARD_CENTER_NOTE = 60
DEFAULT_KEYBOARD_KEY_SCALE = 1.0


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


class DistanceKeyboard:
    """
    Map physical sensor distance onto a chromatic MIDI keyboard.

    The far edge selects the lowest note.

    Moving closer raises the pitch.

    Moving farther than far_distance_mm leaves the keyboard and returns
    None.

    Distances closer than near_distance_mm remain clamped to the highest
    note.

    Automatic sizing
    ----------------

    When low_note and high_note are omitted, the keyboard derives how many
    semitone intervals fit inside the physical sensor span:

        desired semitone width
            = real-piano semitone pitch * key_scale

        note span
            ~= physical span / desired semitone width

    The derived range is centered around center_note where possible and is
    constrained to the normal 88-key acoustic-piano MIDI range A0-C8.

    A key_scale of 1.0 therefore approximates real acoustic-piano key
    density. Larger values create physically wider virtual keys and fewer
    notes.

    Manual sizing
    -------------

    Passing both low_note and high_note disables automatic note-count
    selection and preserves the older explicit-range behavior.
    """

    def __init__(
        self,
        *,
        near_distance_mm: int,
        far_distance_mm: int,
        low_note: int | None = None,
        high_note: int | None = None,
        center_note: int = DEFAULT_KEYBOARD_CENTER_NOTE,
        key_scale: float = DEFAULT_KEYBOARD_KEY_SCALE,
        minimum_note: int = ACOUSTIC_PIANO_LOW_NOTE,
        maximum_note: int = ACOUSTIC_PIANO_HIGH_NOTE,
    ) -> None:
        if near_distance_mm <= 0:
            raise ValueError(
                "near_distance_mm must be greater than zero."
            )

        if (
            far_distance_mm
            <= near_distance_mm
        ):
            raise ValueError(
                "far_distance_mm must be greater than "
                "near_distance_mm."
            )

        if key_scale <= 0:
            raise ValueError(
                "key_scale must be greater than zero."
            )

        if not 0 <= minimum_note <= 127:
            raise ValueError(
                "minimum_note must be between 0 and 127."
            )

        if not 0 <= maximum_note <= 127:
            raise ValueError(
                "maximum_note must be between 0 and 127."
            )

        if maximum_note <= minimum_note:
            raise ValueError(
                "maximum_note must be greater than minimum_note."
            )

        if not minimum_note <= center_note <= maximum_note:
            raise ValueError(
                "center_note must be inside the configured "
                "automatic MIDI range."
            )

        if (
            low_note is None
            and high_note is not None
        ) or (
            low_note is not None
            and high_note is None
        ):
            raise ValueError(
                "low_note and high_note must either both be supplied "
                "or both be omitted."
            )

        self.near_distance_mm = (
            near_distance_mm
        )

        self.far_distance_mm = (
            far_distance_mm
        )

        self.center_note = (
            center_note
        )

        self.key_scale = (
            key_scale
        )

        self.minimum_note = (
            minimum_note
        )

        self.maximum_note = (
            maximum_note
        )

        self.auto_sized = (
            low_note is None
        )

        if self.auto_sized:
            (
                resolved_low_note,
                resolved_high_note,
            ) = self._derive_note_range()

        else:
            assert low_note is not None
            assert high_note is not None

            if not 0 <= low_note <= 127:
                raise ValueError(
                    "low_note must be between 0 and 127."
                )

            if not 0 <= high_note <= 127:
                raise ValueError(
                    "high_note must be between 0 and 127."
                )

            if high_note <= low_note:
                raise ValueError(
                    "high_note must be greater than low_note."
                )

            resolved_low_note = (
                low_note
            )

            resolved_high_note = (
                high_note
            )

        self.low_note = (
            resolved_low_note
        )

        self.high_note = (
            resolved_high_note
        )

    @property
    def playable_span_mm(
        self,
    ) -> int:
        """Return physical distance represented by the keyboard."""

        return (
            self.far_distance_mm
            - self.near_distance_mm
        )

    @property
    def target_semitone_width_mm(
        self,
    ) -> float:
        """
        Return the desired physical semitone width before MIDI-range limits.
        """

        return (
            STANDARD_PIANO_SEMITONE_PITCH_MM
            * self.key_scale
        )

    @property
    def note_span(
        self,
    ) -> int:
        """Return the number of semitone intervals in the keyboard."""

        return (
            self.high_note
            - self.low_note
        )

    @property
    def note_count(
        self,
    ) -> int:
        """Return the number of selectable chromatic notes."""

        return (
            self.note_span
            + 1
        )

    @property
    def actual_semitone_width_mm(
        self,
    ) -> float:
        """Return the physical width of one resolved semitone interval."""

        return (
            self.playable_span_mm
            / self.note_span
        )

    def _derive_note_range(
        self,
    ) -> tuple[int, int]:
        """
        Derive a piano-like chromatic MIDI range from the physical span.

        The requested number of semitone intervals is rounded to the nearest
        whole interval, then capped to the configured automatic MIDI range.
        """

        requested_note_span = max(
            1,
            round(
                self.playable_span_mm
                / self.target_semitone_width_mm
            ),
        )

        maximum_note_span = (
            self.maximum_note
            - self.minimum_note
        )

        resolved_note_span = min(
            requested_note_span,
            maximum_note_span,
        )

        low_note = (
            self.center_note
            - resolved_note_span // 2
        )

        high_note = (
            low_note
            + resolved_note_span
        )

        if low_note < self.minimum_note:
            shift = (
                self.minimum_note
                - low_note
            )

            low_note += (
                shift
            )

            high_note += (
                shift
            )

        if high_note > self.maximum_note:
            shift = (
                high_note
                - self.maximum_note
            )

            low_note -= (
                shift
            )

            high_note -= (
                shift
            )

        return (
            low_note,
            high_note,
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

        midi_note = round(
            self.low_note
            + position
            * self.note_span
        )

        return max(
            self.low_note,
            min(
                self.high_note,
                midi_note,
            ),
        )
