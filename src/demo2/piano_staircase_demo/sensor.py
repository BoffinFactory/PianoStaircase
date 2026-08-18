"""
Reusable distance-sensor support for Piano Staircase Demo 2.

This module hides the I2C and VL53L0X implementation details from higher-level demonstration code.
"""

from __future__ import annotations

import board
import busio
import adafruit_vl53l0x


class DistanceSensor:
    """VL53L0X distance sensor used by Demo 2."""

    def __init__(self) -> None:
        self._closed = False

        self._i2c = busio.I2C(
            board.SCL,
            board.SDA,
        )

        self._sensor = adafruit_vl53l0x.VL53L0X(
            self._i2c
        )

    @property
    def distance_mm(self) -> int | None:
        """Return the current distance in millimeters, or None for an invalid reading."""

        if self._closed:
            raise RuntimeError("DistanceSensor is closed.")

        distance_mm = self._sensor.range

        if distance_mm == 0:
            return None

        return distance_mm

    def close(self) -> None:
        """Release the I2C interface used by the sensor."""

        if self._closed:
            return

        self._i2c.deinit()
        self._closed = True

    def __enter__(self) -> DistanceSensor:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
