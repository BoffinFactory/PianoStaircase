#!/usr/bin/env python3

"""
This code is intended to introduce students to the basic usage of Raspberry Pis with the
VL53L0X ToF sensor.
"""

# --- Imports ---
import time
import subprocess
import sys

import board
import busio
import adafruit_vl53l0x

from pathlib import Path

# --- Tuning Knobs ---
TRIP_MM = 250  # Trip when distance is <= this value (mm)
HYST_MM = 50  # Must rise above (TRIP_MM + HYST_MM) to re-arm
POLL_S = 0.05  # Sensor polling interval
COOLDOWN_S = 0.20  # Minimum time between beeps (s)
# Sound to play from the user's home directory:
BEEP_WAV = str(Path.home() / "beep.wave")
PRINT_EVERY_S = 0.5  # Print distance at most this often


def play_beep():
    """
    Non-blocking playback; avoids stalling sensor reads
    """

    wav = Path(BEEP_WAV)
    if not wav.is_file():
        print(f"[BEEP][ERROR] WAV not found: {wav}")
        return

    proc = subprocess.Popen(["aplay", "-q", str(wav)], capture_output=True, text=True)

    if proc.returncode != 0:
        print(f"[BEEP][ERROR] aplay failed (rc={proc.returncode})")
        if proc.stderr.strip():
            print(f"[BEEP][ERROR] stderr: {proc.stderr.strip()}")
    else:
        print("[BEEP] aplay succeeded")


def main():
    print("=== VL53L0X Trip-Beep Diagnostic ===")
    print(
        f"TRIP_MM={TRIP_MM}, HYST_MM={HYST_MM}, POLL_S={POLL_S}, COOLDOWN_S={COOLDOWN_S}"
    )
    print(f"BEEP_WAV={BEEP_WAV}")
    print("Initializing I2C and VL53L0X...")

    # Configure the I2C bus and VL53L0X sensor:
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = adafruit_vl53l0x.VL53L0X(i2c)
    except Exception as e:
        print("\n[ERROR] Failed to initialize VL53L0X over I2C.")
        print("Common causes:")
        print(" - I2C not enabled (raspi-config)")
        print(" - Wiring issue (3V3/GND/SDA/SCL)")
        print(" - Sensor not detected on bus (try: i2cdetect -y 1; expect 0x29)")
        print(f"Exception: {e}")
        sys.exit(1)

    print("Sensor initialized successfully.")
    print("Starting loop... (Ctrl+C to exit)\n")

    # Create variables:
    tripped = False
    last_beep = 0.0
    last_print = 0.0
    last_dist = None

    # Main loop:
    try:
        while True:
            now = time.monotonic()

            # Read the sensor:
            dist_mm = sensor.range
            last_dist = dist_mm

            # Periodically print sensor reading:
            if now - last_print >= PRINT_EVERY_S:
                state = "TRIPPED" if tripped else "ARMED"
                print(f"[DIST] {dist_mm:4d} mm  state={state}")
                last_print = now

            # Trip on the downward crossing:
            if (not tripped) and (dist_mm <= TRIP_MM):
                print(
                    f"[TRIP] Distance {dist_mm} mm <= {TRIP_MM} mm (threshold crossed)"
                )
                if now - last_beep >= COOLDOWN_S:
                    print("[BEEP] Playing sound")
                    play_beep()
                    last_beep = now
                else:
                    print("[BEEP] Skipped (cooldown active)")
                tripped = True

            # Re-arm only after rising above threshold + hysteresis:
            elif tripped and (dist_mm >= TRIP_MM + HYST_MM):
                print(
                    f"[RE-ARM] Distance {dist_mm} mm >= {TRIP_MM + HYST_MM} mm (re-armed)"
                )
                tripped = False

            # Sleep before polling again:
            time.sleep(POLL_S)

    except KeyboardInterrupt:
        print("\n[EXIT] Keyboard interrupt received. Stopping.")
    except Exception as e:
        print("\n[ERROR] Runtime failure while reading sensor or playing audio.")
        if last_dist is not None:
            print(f"Last distance read: {last_dist} mm")
        print(f"Exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
