#!/usr/bin/env python3

"""
Single LED channel diagnostic for Piano Staircase Demo 2.

Tests the complete LED driver path:

    Raspberry Pi GPIO17
        -> 1 kΩ base resistor
        -> 2N2222 transistor
        -> 5 V LED load

The LED is first tested at several fixed brightness levels and then
faded up and down using pulse-width modulation (PWM).

Press Ctrl+C to stop early.
"""

import time

import board
import pwmio


GPIO_PIN = board.D17
PWM_FREQUENCY_HZ = 500

MAX_DUTY_CYCLE = 65535


def percent_to_duty_cycle(percent: float) -> int:
    """Convert a brightness percentage from 0-100 into a PWM duty cycle."""

    return round(MAX_DUTY_CYCLE * percent / 100)


def set_brightness(pwm: pwmio.PWMOut, percent: float) -> None:
    """Set the LED brightness as a percentage."""

    pwm.duty_cycle = percent_to_duty_cycle(percent)


def fade(
    pwm: pwmio.PWMOut,
    start_percent: float,
    end_percent: float,
    duration_seconds: float = 1.5,
    steps: int = 75,
) -> None:
    """Fade smoothly between two brightness levels."""

    step_delay = duration_seconds / steps
    difference = end_percent - start_percent

    for step in range(steps + 1):
        fraction = step / steps
        brightness = start_percent + difference * fraction

        set_brightness(pwm, brightness)
        time.sleep(step_delay)


def main() -> None:
    print("=== Piano Staircase LED Channel Diagnostic ===")
    print("GPIO: GPIO17 / physical pin 11")
    print(f"PWM frequency: {PWM_FREQUENCY_HZ} Hz")
    print()

    pwm = pwmio.PWMOut(
        GPIO_PIN,
        frequency=PWM_FREQUENCY_HZ,
        duty_cycle=0,
    )

    try:
        print("Testing fixed brightness levels...")

        for brightness in (0, 25, 50, 75, 100):
            print(f"  {brightness:3d}%")
            set_brightness(pwm, brightness)
            time.sleep(1)

        print()
        print("Turning LED off...")
        set_brightness(pwm, 0)
        time.sleep(1)

        print()
        print("Testing fades...")

        for cycle in range(1, 4):
            print(f"  Fade cycle {cycle}/3")

            fade(pwm, 0, 100)
            fade(pwm, 100, 0)

        print()
        print("Diagnostic complete.")

    except KeyboardInterrupt:
        print()
        print("Diagnostic stopped.")

    finally:
        # Always leave the LED off and release the GPIO resource.
        pwm.duty_cycle = 0
        pwm.deinit()


if __name__ == "__main__":
    main()
