"""
Persistent sampled-piano support for Piano Staircase Demo 2.

The piano engine owns one long-running FluidSynth process. Notes are controlled
with MIDI-style NOTE ON and NOTE OFF events rather than by playing fixed WAV
files.

This allows the physical interaction to behave more like a real piano key:

    ENTER -> note_on()
    HELD  -> do nothing; let the piano resonate
    EXIT  -> note_off()

Sound effects and announcer clips remain separate in audio.py.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


DEFAULT_SOUNDFONT = Path(
    "/usr/share/sounds/sf2/TimGM6mb.sf2"
)

DEFAULT_GAIN = 2.0
DEFAULT_VELOCITY = 100

DEFAULT_SAMPLE_RATE = 48000
DEFAULT_PERIOD_SIZE = 2048

MIDI_CHANNEL = 0

# General MIDI bank 0, program 0 = Acoustic Grand Piano.
PIANO_BANK = 0
PIANO_PROGRAM = 0

MIDI_NOTES = {
    "C4": 60,
    "E4": 64,
    "G4": 67,
}


class PianoEngine:
    """
    Control a persistent FluidSynth piano through its command shell.

    Only one FluidSynth process is started. Individual notes are turned on
    and off by writing MIDI commands to the process's standard input.
    """

    def __init__(
        self,
        *,
        soundfont: str | Path = DEFAULT_SOUNDFONT,
        gain: float = DEFAULT_GAIN,
        velocity: int = DEFAULT_VELOCITY,
    ) -> None:
        fluidsynth_path = shutil.which(
            "fluidsynth"
        )

        if fluidsynth_path is None:
            raise RuntimeError(
                "fluidsynth was not found. "
                "Install FluidSynth before using PianoEngine."
            )

        self._soundfont = (
            Path(soundfont)
            .expanduser()
            .resolve()
        )

        if not self._soundfont.is_file():
            raise FileNotFoundError(
                "SoundFont not found: "
                f"{self._soundfont}"
            )

        if gain <= 0:
            raise ValueError(
                "gain must be greater than zero."
            )

        if not 1 <= velocity <= 127:
            raise ValueError(
                "velocity must be between 1 and 127."
            )

        self._default_velocity = velocity

        self._active_notes: set[
            int
        ] = set()

        self._closed = False

        #
        # -a pipewire
        #     Use the native PipeWire output driver.
        #
        # -g
        #     Set FluidSynth's master gain.
        #
        # -n
        #     Do not create an external MIDI-input driver. Demo 2 controls
        #     the synth entirely through its command shell.
        #
        # -r 48000
        #     Match the Pi's PipeWire audio graph and avoid unnecessary
        #     44.1 kHz -> 48 kHz resampling.
        #
        # -z 2048
        #     Use a deliberately conservative audio period. FluidSynth's Linux
        #     default of 64 frames drove PipeWire toward ~1.3 ms graph cycles,
        #     which caused xruns on the Pi Zero 2 W.
        #
        # FluidSynth reads shell commands from stdin by default.
        #
        self._process = subprocess.Popen(
            [
                fluidsynth_path,
                "-a",
                "pipewire",
                "-r",
                str(
                    DEFAULT_SAMPLE_RATE
                ),
                "-z",
                str(
                    DEFAULT_PERIOD_SIZE
                ),
                "-g",
                str(gain),
                "-n",
                str(self._soundfont),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )

        if self._process.stdin is None:
            self._process.terminate()

            raise RuntimeError(
                "Unable to open FluidSynth command input."
            )

        #
        # Only one SoundFont is supplied at startup, so it receives
        # SoundFont ID 1.
        #
        # Explicit selection avoids depending on FluidSynth's default
        # channel state.
        #
        self._send(
            f"select "
            f"{MIDI_CHANNEL} "
            f"1 "
            f"{PIANO_BANK} "
            f"{PIANO_PROGRAM}"
        )

        # Maximize MIDI channel volume and expression. Overall loudness is
        # controlled by FluidSynth's master gain instead.
        self._send(
            f"cc {MIDI_CHANNEL} 7 127"
        )

        self._send(
            f"cc {MIDI_CHANNEL} 11 127"
        )

    @property
    def is_running(
        self,
    ) -> bool:
        """Return whether the FluidSynth process is still alive."""

        return (
            not self._closed
            and self._process.poll()
            is None
        )

    @property
    def active_notes(
        self,
    ) -> tuple[int, ...]:
        """Return the MIDI notes currently held by the application."""

        return tuple(
            sorted(
                self._active_notes
            )
        )

    def _send(
        self,
        command: str,
    ) -> None:
        """Send one command to the persistent FluidSynth shell."""

        if self._closed:
            raise RuntimeError(
                "PianoEngine is closed."
            )

        return_code = (
            self._process.poll()
        )

        if return_code is not None:
            raise RuntimeError(
                "FluidSynth exited unexpectedly "
                f"with status {return_code}."
            )

        if self._process.stdin is None:
            raise RuntimeError(
                "FluidSynth command input is unavailable."
            )

        try:
            self._process.stdin.write(
                command + "\n"
            )

            self._process.stdin.flush()

        except BrokenPipeError as exc:
            raise RuntimeError(
                "FluidSynth stopped accepting commands."
            ) from exc

    @staticmethod
    def _resolve_note(
        note: str | int,
    ) -> int:
        """Convert a note name or MIDI number into a MIDI note number."""

        if isinstance(
            note,
            str,
        ):
            try:
                return MIDI_NOTES[
                    note
                ]

            except KeyError as exc:
                raise ValueError(
                    f"Unknown piano note: {note}"
                ) from exc

        if not 0 <= note <= 127:
            raise ValueError(
                "MIDI note must be between 0 and 127."
            )

        return note

    def note_on(
        self,
        note: str | int,
        *,
        velocity: int | None = None,
    ) -> bool:
        """
        Start one piano note.

        Return False if that note is already being held. This prevents a
        repeated sensor sample from retriggering the hammer attack.
        """

        midi_note = (
            self._resolve_note(
                note
            )
        )

        if midi_note in self._active_notes:
            return False

        if velocity is None:
            velocity = (
                self._default_velocity
            )

        if not 1 <= velocity <= 127:
            raise ValueError(
                "velocity must be between 1 and 127."
            )

        self._send(
            f"noteon "
            f"{MIDI_CHANNEL} "
            f"{midi_note} "
            f"{velocity}"
        )

        self._active_notes.add(
            midi_note
        )

        return True

    def note_off(
        self,
        note: str | int,
    ) -> bool:
        """
        Release one piano note.

        Return False when the requested note was not currently held.
        """

        midi_note = (
            self._resolve_note(
                note
            )
        )

        if (
            midi_note
            not in self._active_notes
        ):
            return False

        self._send(
            f"noteoff "
            f"{MIDI_CHANNEL} "
            f"{midi_note}"
        )

        self._active_notes.remove(
            midi_note
        )

        return True

    def release_all(
        self,
    ) -> None:
        """Release every note currently held by the application."""

        for midi_note in tuple(
            self._active_notes
        ):
            self.note_off(
                midi_note
            )

    def close(
        self,
    ) -> None:
        """Release all notes and stop the FluidSynth process."""

        if self._closed:
            return

        try:
            self.release_all()

        except RuntimeError:
            # FluidSynth may already have failed. Cleanup should still
            # continue.
            pass

        if (
            self._process.poll()
            is None
        ):
            try:
                if (
                    self._process.stdin
                    is not None
                ):
                    self._process.stdin.write(
                        "quit\n"
                    )

                    self._process.stdin.flush()

                self._process.wait(
                    timeout=2.0
                )

            except (
                BrokenPipeError,
                subprocess.TimeoutExpired,
            ):
                if (
                    self._process.poll()
                    is None
                ):
                    self._process.terminate()

                    try:
                        self._process.wait(
                            timeout=1.0
                        )

                    except subprocess.TimeoutExpired:
                        self._process.kill()
                        self._process.wait()

        if (
            self._process.stdin
            is not None
        ):
            self._process.stdin.close()

        self._active_notes.clear()
        self._closed = True

    def __enter__(
        self,
    ) -> PianoEngine:
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()
