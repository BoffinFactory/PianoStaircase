"""
Reusable persistent FluidSynth support for Piano Staircase Demo 2.

FluidSynthEngine owns one long-running FluidSynth process and exposes
multiple independent MIDI channels.

Higher-level systems decide what those channels mean. For example:

    channel 0 -> piano
    channel 1 -> falling pipe
    channel 2 -> falling pipe
    channel 3 -> falling pipe

This module knows nothing about sensors, piano articulation, pipe physics,
lighting, or special events.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


DEFAULT_SOUNDFONT = Path(
    "/usr/share/sounds/sf2/TimGM6mb.sf2"
)

DEFAULT_GAIN = 2.0
DEFAULT_SAMPLE_RATE = 48000
DEFAULT_PERIOD_SIZE = 1024

MIDI_CHANNEL_MIN = 0
MIDI_CHANNEL_MAX = 15


class FluidSynthEngine:
    """Control one persistent multi-channel FluidSynth process."""

    def __init__(
        self,
        *,
        soundfont: str | Path = DEFAULT_SOUNDFONT,
        gain: float = DEFAULT_GAIN,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        period_size: int = DEFAULT_PERIOD_SIZE,
    ) -> None:
        fluidsynth_path = shutil.which(
            "fluidsynth"
        )

        if fluidsynth_path is None:
            raise RuntimeError(
                "fluidsynth was not found."
            )

        self._soundfont = (
            Path(soundfont)
            .expanduser()
            .resolve()
        )

        if not self._soundfont.is_file():
            raise FileNotFoundError(
                f"SoundFont not found: {self._soundfont}"
            )

        if gain <= 0:
            raise ValueError(
                "gain must be greater than zero."
            )

        if sample_rate <= 0:
            raise ValueError(
                "sample_rate must be greater than zero."
            )

        if period_size <= 0:
            raise ValueError(
                "period_size must be greater than zero."
            )

        self._closed = False

        self._active_notes: dict[
            int,
            set[int],
        ] = {
            channel: set()
            for channel in range(
                MIDI_CHANNEL_MIN,
                MIDI_CHANNEL_MAX + 1,
            )
        }

        self._process = subprocess.Popen(
            [
                fluidsynth_path,
                "-a",
                "pipewire",
                "-r",
                str(
                    sample_rate
                ),
                "-z",
                str(
                    period_size
                ),
                "-g",
                str(
                    gain
                ),
                "-n",
                str(
                    self._soundfont
                ),
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

    @property
    def is_running(
        self,
    ) -> bool:
        """Return whether FluidSynth is still alive."""

        return (
            not self._closed
            and self._process.poll()
            is None
        )

    @staticmethod
    def _validate_channel(
        channel: int,
    ) -> None:
        if not (
            MIDI_CHANNEL_MIN
            <= channel
            <= MIDI_CHANNEL_MAX
        ):
            raise ValueError(
                "MIDI channel must be between 0 and 15."
            )

    @staticmethod
    def _validate_note(
        note: int,
    ) -> None:
        if not 0 <= note <= 127:
            raise ValueError(
                "MIDI note must be between 0 and 127."
            )

    @staticmethod
    def _validate_midi_value(
        value: int,
        *,
        name: str,
    ) -> None:
        if not 0 <= value <= 127:
            raise ValueError(
                f"{name} must be between 0 and 127."
            )

    def _send(
        self,
        command: str,
    ) -> None:
        """Send one FluidSynth shell command."""

        if self._closed:
            raise RuntimeError(
                "FluidSynthEngine is closed."
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

    def configure_channel(
        self,
        channel: int,
        *,
        bank: int,
        program: int,
        volume: int = 127,
        expression: int = 127,
    ) -> None:
        """Select an instrument and MIDI levels for one channel."""

        self._validate_channel(
            channel
        )

        self._validate_midi_value(
            bank,
            name="bank",
        )

        self._validate_midi_value(
            program,
            name="program",
        )

        self._validate_midi_value(
            volume,
            name="volume",
        )

        self._validate_midi_value(
            expression,
            name="expression",
        )

        #
        # Demo 2 loads exactly one SoundFont, so its FluidSynth ID is 1.
        #
        self._send(
            f"select "
            f"{channel} "
            f"1 "
            f"{bank} "
            f"{program}"
        )

        self._send(
            f"cc {channel} 7 {volume}"
        )

        self._send(
            f"cc {channel} 11 {expression}"
        )

    def note_on(
        self,
        channel: int,
        note: int,
        *,
        velocity: int,
    ) -> bool:
        """Start one note on one MIDI channel."""

        self._validate_channel(
            channel
        )

        self._validate_note(
            note
        )

        if not 1 <= velocity <= 127:
            raise ValueError(
                "velocity must be between 1 and 127."
            )

        active = (
            self._active_notes[
                channel
            ]
        )

        if note in active:
            return False

        self._send(
            f"noteon "
            f"{channel} "
            f"{note} "
            f"{velocity}"
        )

        active.add(
            note
        )

        return True

    def note_off(
        self,
        channel: int,
        note: int,
    ) -> bool:
        """Release one note on one MIDI channel."""

        self._validate_channel(
            channel
        )

        self._validate_note(
            note
        )

        active = (
            self._active_notes[
                channel
            ]
        )

        if note not in active:
            return False

        self._send(
            f"noteoff "
            f"{channel} "
            f"{note}"
        )

        active.remove(
            note
        )

        return True

    def active_notes(
        self,
        channel: int,
    ) -> tuple[int, ...]:
        """Return notes currently held on one channel."""

        self._validate_channel(
            channel
        )

        return tuple(
            sorted(
                self._active_notes[
                    channel
                ]
            )
        )

    def release_channel(
        self,
        channel: int,
    ) -> None:
        """Release every application-held note on one channel."""

        self._validate_channel(
            channel
        )

        for note in tuple(
            self._active_notes[
                channel
            ]
        ):
            self.note_off(
                channel,
                note,
            )

    def all_sounds_off(
        self,
        channel: int,
    ) -> None:
        """
        Immediately silence one MIDI channel.

        This is intentionally stronger than ordinary NOTE OFF and is useful
        when recycling a completed falling-pipe channel.
        """

        self._validate_channel(
            channel
        )

        self._send(
            f"cc {channel} 120 0"
        )

        self._active_notes[
            channel
        ].clear()

    def release_all(
        self,
    ) -> None:
        """Release all notes held by the application."""

        for channel in range(
            MIDI_CHANNEL_MIN,
            MIDI_CHANNEL_MAX + 1,
        ):
            self.release_channel(
                channel
            )

    def close(
        self,
    ) -> None:
        """Release notes and terminate FluidSynth."""

        if self._closed:
            return

        try:
            self.release_all()

        except RuntimeError:
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

        for notes in (
            self._active_notes.values()
        ):
            notes.clear()

        self._closed = True

    def __enter__(
        self,
    ) -> FluidSynthEngine:
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()
