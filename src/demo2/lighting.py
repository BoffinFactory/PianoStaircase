"""
Reusable lighting control for Piano Staircase Demo 2.

This module hides the GPIO and PWM details used to control the three
transistor-driven lighting channels.

Channel assignments:

    Green  -> GPIO17 / physical pin 11
    Yellow -> GPIO27 / physical pin 13
    Blue   -> GPIO22 / physical pin 15
"""

import time

import board
import pwmio


PWM_FREQUENCY_HZ = 500
MAX_DUTY_CYCLE = 65535


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

                channel.set_brightness(
                    start + difference * fraction
                )

            time.sleep(delay)

    def close(self) -> None:
        """Turn off all channels and release their GPIO resources."""

        for channel in self.channels:
            channel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
