"""
Reusable lighting control for Piano Staircase Demo 2.

This module owns both the low-level GPIO/PWM channels and the small amount of
runtime policy needed to switch or schedule those channels.

Channel assignments:

    Green  -> GPIO17 / physical pin 11
    Yellow -> GPIO27 / physical pin 13
    Blue   -> GPIO22 / physical pin 15
"""

from __future__ import annotations

import time

import board
import pwmio

from piano_staircase_demo.modes import InteractionResponse
from piano_staircase_demo.runtime import LightCue, RuntimeState


PWM_FREQUENCY_HZ = 500
MAX_DUTY_CYCLE = 65535
LIGHT_BRIGHTNESS_PERCENT = 100


def percent_to_duty_cycle(percent: float) -> int:
    """Convert a brightness percentage from 0-100 into a PWM duty cycle."""

    if not 0 <= percent <= 100:
        raise ValueError("Brightness must be between 0 and 100 percent.")

    return round(MAX_DUTY_CYCLE * percent / 100)


class LightingChannel:
    """One PWM-controlled lighting channel."""

    def __init__(self, name: str, pin) -> None:
        self.name = name
        self._brightness = 0.0
        self._pwm = pwmio.PWMOut(
            pin,
            frequency=PWM_FREQUENCY_HZ,
            duty_cycle=0,
        )

    @property
    def brightness(self) -> float:
        """Return the current brightness percentage."""

        return self._brightness

    def set_brightness(self, percent: float) -> None:
        """Immediately set the channel brightness."""

        self._pwm.duty_cycle = percent_to_duty_cycle(percent)
        self._brightness = percent

    def off(self) -> None:
        """Turn the channel off."""

        self.set_brightness(0)

    def fade_to(
        self,
        target_percent: float,
        duration_seconds: float = 1.0,
        steps: int = 50,
    ) -> None:
        """Fade from the current brightness to a target brightness."""

        if not 0 <= target_percent <= 100:
            raise ValueError("Brightness must be between 0 and 100 percent.")
        if duration_seconds < 0:
            raise ValueError("Fade duration cannot be negative.")
        if steps <= 0:
            raise ValueError("Fade steps must be greater than zero.")

        start_percent = self._brightness
        difference = target_percent - start_percent
        delay = duration_seconds / steps

        for step in range(1, steps + 1):
            fraction = step / steps
            brightness = start_percent + difference * fraction
            self.set_brightness(brightness)
            time.sleep(delay)

    def close(self) -> None:
        """Turn the channel off and release its GPIO resource."""

        self.off()
        self._pwm.deinit()


class LightingSystem:
    """The three lighting channels used by Demo 2."""

    def __init__(self) -> None:
        self.green = LightingChannel("GREEN", board.D17)
        self.yellow = LightingChannel("YELLOW", board.D27)
        self.blue = LightingChannel("BLUE", board.D22)
        self.channels = (
            self.green,
            self.yellow,
            self.blue,
        )

    def all_off(self) -> None:
        """Turn every channel off."""

        for channel in self.channels:
            channel.off()

    def fade_all_to(
        self,
        target_percent: float,
        duration_seconds: float = 1.5,
        steps: int = 75,
    ) -> None:
        """Fade every channel toward the same brightness simultaneously."""

        if not 0 <= target_percent <= 100:
            raise ValueError("Brightness must be between 0 and 100 percent.")
        if duration_seconds < 0:
            raise ValueError("Fade duration cannot be negative.")
        if steps <= 0:
            raise ValueError("Fade steps must be greater than zero.")

        starting_brightness = {
            channel: channel.brightness
            for channel in self.channels
        }
        delay = duration_seconds / steps

        for step in range(1, steps + 1):
            fraction = step / steps

            for channel in self.channels:
                start = starting_brightness[channel]
                difference = target_percent - start
                channel.set_brightness(start + difference * fraction)

            time.sleep(delay)

    def close(self) -> None:
        """Turn off all channels and release their GPIO resources."""

        for channel in self.channels:
            channel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def build_light_cues(
    responses: tuple[InteractionResponse, ...],
    *,
    start_time: float,
    duration_seconds: float,
    gap_seconds: float = 0.0,
) -> tuple[LightCue, ...]:
    """Build timed lighting cues for a response sequence."""

    cues: list[LightCue] = []
    cue_start = start_time

    for response in responses:
        cue_end = cue_start + duration_seconds
        cues.append(
            LightCue(
                light_name=response.light_name,
                start_time=cue_start,
                end_time=cue_end,
            )
        )
        cue_start = cue_end + gap_seconds

    return tuple(cues)


def switch_active_light(
    *,
    desired_channel: LightingChannel | None,
    active_channel: LightingChannel | None,
) -> LightingChannel | None:
    """Switch physical lighting only when the desired channel changes."""

    if desired_channel is active_channel:
        return active_channel

    if active_channel is not None:
        active_channel.off()

    if desired_channel is not None:
        desired_channel.set_brightness(LIGHT_BRIGHTNESS_PERCENT)

    return desired_channel


def choose_active_light(
    *,
    cues: tuple[LightCue, ...],
    channels: dict[str, LightingChannel],
    active_channel: LightingChannel | None,
    now: float,
) -> LightingChannel | None:
    """Apply the timed light cue that should currently be active."""

    desired_channel = None

    for cue in cues:
        if cue.start_time <= now < cue.end_time:
            desired_channel = channels[cue.light_name]
            break

    return switch_active_light(
        desired_channel=desired_channel,
        active_channel=active_channel,
    )


def update_lighting(
    runtime: RuntimeState,
    *,
    channels: dict[str, LightingChannel],
    now: float,
) -> None:
    """Advance held or timed lighting without blocking the sensor loop."""

    if runtime.held_light_name is not None:
        runtime.active_channel = switch_active_light(
            desired_channel=channels[runtime.held_light_name],
            active_channel=runtime.active_channel,
        )
        return

    runtime.active_channel = choose_active_light(
        cues=runtime.light_cues,
        channels=channels,
        active_channel=runtime.active_channel,
        now=now,
    )

    if runtime.light_cues and now >= runtime.light_cues[-1].end_time:
        runtime.light_cues = ()
