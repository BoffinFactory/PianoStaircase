"""
Persistent sampled-instrument support for Piano Staircase Demo 2.

PianoEngine is a small MIDI-note controller layered on top of the reusable
FluidSynthEngine. The historical class name is retained because the alternate
88-key distance mode is a piano, but callers may select another General MIDI
program such as the normal-mode Vibraphone.

It can either create and own its own FluidSynthEngine or use a shared synth
owned by the main application. Channel 0 remains reserved for this controller;
procedural pipes use channels 1-6 when explicitly enabled.
"""

from __future__ import annotations

from pathlib import Path

from piano_staircase_demo.synth import (
    DEFAULT_GAIN,
    DEFAULT_PERIOD_SIZE,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_SOUNDFONT,
    FluidSynthEngine,
)


DEFAULT_VELOCITY = 100

PIANO_CHANNEL = 0
PIANO_BANK = 0
PIANO_PROGRAM = 0
PIANO_VOLUME = 127
PIANO_EXPRESSION = 127

MIDI_NOTES = {
    "C4": 60,
    "E4": 64,
    "G4": 67,
}


class PianoEngine:
    """Control one persistent FluidSynth MIDI channel."""

    def __init__(
        self,
        *,
        synth: FluidSynthEngine | None = None,
        soundfont: str | Path = DEFAULT_SOUNDFONT,
        gain: float = DEFAULT_GAIN,
        velocity: int = DEFAULT_VELOCITY,
        channel: int = PIANO_CHANNEL,
        program: int = PIANO_PROGRAM,
    ) -> None:
        if not 1 <= velocity <= 127:
            raise ValueError("velocity must be between 1 and 127.")
        if not 0 <= channel <= 15:
            raise ValueError("channel must be between 0 and 15.")
        if not 0 <= program <= 127:
            raise ValueError("program must be between 0 and 127.")

        self._default_velocity = velocity
        self._channel = channel
        self._closed = False
        self._owns_synth = synth is None

        if synth is None:
            self._synth = FluidSynthEngine(
                soundfont=soundfont,
                gain=gain,
                sample_rate=DEFAULT_SAMPLE_RATE,
                period_size=DEFAULT_PERIOD_SIZE,
            )
        else:
            self._synth = synth

        try:
            self._synth.configure_channel(
                self._channel,
                bank=PIANO_BANK,
                program=program,
                volume=PIANO_VOLUME,
                expression=PIANO_EXPRESSION,
            )
        except Exception:
            if self._owns_synth:
                self._synth.close()
            raise

    @property
    def is_running(self) -> bool:
        """Return whether the underlying FluidSynth process is alive."""

        return not self._closed and self._synth.is_running

    @property
    def active_notes(self) -> tuple[int, ...]:
        """Return MIDI notes currently held on this channel."""

        if self._closed:
            return ()

        return self._synth.active_notes(self._channel)

    @staticmethod
    def _resolve_note(note: str | int) -> int:
        """Convert a supported note name or MIDI number into a MIDI note."""

        if isinstance(note, str):
            try:
                return MIDI_NOTES[note]
            except KeyError as exc:
                raise ValueError(f"Unknown piano note: {note}") from exc

        if not 0 <= note <= 127:
            raise ValueError("MIDI note must be between 0 and 127.")

        return note

    def _require_open(self) -> None:
        """Reject operations after this controller has closed."""

        if self._closed:
            raise RuntimeError("PianoEngine is closed.")

    def note_on(
        self,
        note: str | int,
        *,
        velocity: int | None = None,
    ) -> bool:
        """Start one note, returning False if that key is already held."""

        self._require_open()
        midi_note = self._resolve_note(note)

        if velocity is None:
            velocity = self._default_velocity

        if not 1 <= velocity <= 127:
            raise ValueError("velocity must be between 1 and 127.")

        return self._synth.note_on(
            self._channel,
            midi_note,
            velocity=velocity,
        )

    def note_off(self, note: str | int) -> bool:
        """Release one note, returning False when it was not held."""

        self._require_open()
        midi_note = self._resolve_note(note)
        return self._synth.note_off(self._channel, midi_note)

    def release_all(self) -> None:
        """Release every note currently held by this controller."""

        self._require_open()
        self._synth.release_channel(self._channel)

    def close(self) -> None:
        """Release notes and clean up resources owned by this controller."""

        if self._closed:
            return

        try:
            self._synth.release_channel(self._channel)
        except RuntimeError:
            # A shared synth may already have stopped. Cleanup remains safe and
            # idempotent.
            pass

        if self._owns_synth:
            self._synth.close()

        self._closed = True

    def __enter__(self) -> "PianoEngine":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
