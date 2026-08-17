#!/usr/bin/env python3

"""
Three-channel LED diagnostic for Piano Staircase Demo 2.

Tests the green, yellow, and blue transistor-controlled lighting channels
individually and together using PWM.

Channel assignments:

    Green  -> GPIO17 / physical pin 11
    Yellow -> GPIO27 / physical pin 13
    Blue   -> GPIO22 / physical pin 15

Press Ctrl+C to stop early.
"""

import time

import board
import pwmio


PWM_FREQUENCY_HZ = 500
MAX_DUTY_CYCLE = 65535

CHANNEL_PINS = {
    "GREEN": board.D17,
    "YELLOW": board.D27,
    "BLUE": board.D22,
}


def percent_to_duty_cycle(percent: float) -> int:
    """Convert a brightness percentage from 0-100 into a PWM duty cycle."""

    return round(MAX_DUTY_CYCLE * percent / 100)


def set_brightness(pwm: pwmio.PWMOut, percent: float) -> None:
    """Set one LED channel to the requested brightness."""

    pwm.duty_cycle = percent_to_duty_cycle(percent)


def fade(
    pwm: pwmio.PWMOut,
    start_percent: float,
    end_percent: float,
    duration_seconds: float = 1.0,
    steps: int = 50,
) -> None:
    """Fade one LED channel between two brightness levels."""

    delay = duration_seconds / steps
    difference = end_percent - start_percent

    for step in range(steps + 1):
        fraction = step / steps
        brightness = start_percent + difference * fraction

        set_brightness(pwm, brightness)
        time.sleep(delay)


def fade_all(
    channels: dict[str, pwmio.PWMOut],
    start_percent: float,
    end_percent: float,
    duration_seconds: float = 1.5,
    steps: int = 75,
) -> None:
    """Fade every LED channel together."""

    delay = duration_seconds / steps
    difference = end_percent - start_percent

    for step in range(steps + 1):
        fraction = step / steps
        brightness = start_percent + difference * fraction

        for pwm in channels.values():
            set_brightness(pwm, brightness)

        time.sleep(delay)


def all_off(channels: dict[str, pwmio.PWMOut]) -> None:
    """Turn every lighting channel off."""

    for pwm in channels.values():
        set_brightness(pwm, 0)


def main() -> None:
    print("=== Piano Staircase Three-Channel LED Diagnostic ===")
    print()

    channels = {
        name: pwmio.PWMOut(
            pin,
            frequency=PWM_FREQUENCY_HZ,
            duty_cycle=0,
        )
        for name, pin in CHANNEL_PINS.items()
    }

    try:
        # Test each channel independently.
        for name, pwm in channels.items():
            print(f"Testing {name} channel...")

            for brightness in (25, 50, 75, 100):
                print(f"  {brightness:3d}%")
                set_brightness(pwm, brightness)
                time.sleep(0.75)

            set_brightness(pwm, 0)
            time.sleep(0.5)

        print()
        print("Testing staircase sequence...")

        for _ in range(3):
            for name, pwm in channels.items():
                print(f"  {name}")
                set_brightness(pwm, 100)
                time.sleep(0.4)
                set_brightness(pwm, 0)

        print()
        print("Testing individual fades...")

        for name, pwm in channels.items():
            print(f"  Fading {name}")
            fade(pwm, 0, 100)
            fade(pwm, 100, 0)

        print()
        print("Testing simultaneous fade...")

        for _ in range(3):
            fade_all(channels, 0, 100)
            fade_all(channels, 100, 0)

        print()
        print("Diagnostic complete.")

    except KeyboardInterrupt:
        print()
        print("Diagnostic stopped.")

    finally:
        all_off(channels)

        for pwm in channels.values():
            pwm.deinit()

        print("All channels OFF.")


if __name__ == "__main__":
    main()
