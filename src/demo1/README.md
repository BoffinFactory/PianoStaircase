# Using the VL53L0X ToF sensor on a Raspberry Pi with Python

**Notes:**

- This should work with most Raspberry Pi models (excluding Picos).
- Raspberry Pi 4s have 3.5mm audio connectors. Raspberry Pi 5s and Zeros do not.

## Wiring

| Raspberry Pi (header pin) | Signal       | VL53L0X   |
| ------------------------- | ------------ | --------- |
| Pin 1                     | 3V3          | VCC / VIN |
| Pin 6                     | GND          | GND       |
| Pin 3                     | GPIO2 (SDA1) | SDA       |
| Pin 5                     | GPIO3 (SCL1) | SCL       |

🔗 [Raspberry Pi GPIO reference](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio)

## Software Procedure

1. Install Raspberry Pi OS Lite 32-bit
   - Be sure to enable Raspberry Pi Connect!
2. Update packages
3. Wire the VL53L0X to the Raspberry Pi (see above section on wiring)
4. Enable the I2C bus on the Raspberry Pi:

   ```bash
   sudo raspi-config
   # Interface Options -> I2C -> Enable
   sudo reboot
   ```

5. Verify the sensor is visible:

   ```bash
   sudo apt update
   sudo apt install -y i2c-tools
   i2cdetect -y 1
   ```

   You should see 29 in the output if the sensor is correctly connected:

   ```
        0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
   00:                         -- -- -- -- -- -- -- --
   10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
   20: -- -- -- -- -- -- -- -- -- 29 -- -- -- -- -- --
   30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
   40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
   50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
   60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
   70: -- -- -- -- -- -- -- --
   ```

6. Connect and test a speaker (optional)

   ```bash
   pw-play /usr/share/sounds/alsa/Front_Center.wav
   ```

7. Install the requisite packages for Python development

   ```bash
   sudo apt install -y python3-pip python3-venv alsa-utils sox
   ```

8. Setup a Python virtual environment

   ```bash
   python3 -m venv ~/.venv/vl53
   source ~/.venv/vl53/bin/activate
   pip install --upgrade pip
   pip install adafruit-blinka adafruit-circuitpython-vl53l0x
   ```

9. Create an audio file for testing

   ```bash
   sox -n -r 48000 -c 1 -b 16 ~/beep.wav synth 0.12 sine 880 vol 0.3
   aplay ~/beep.wav
   ```

10. Create/copy the Python code.
11. Source into the virtual environment and run the code:

    ```bash
    source ~/.venv/vl53/bin/activate
    python3 demo1.py
    ```
