#!/usr/bin/env bash

set -euo pipefail

if [[ ! -r /proc/device-tree/model ]] ||
	! grep -qi "Raspberry Pi" /proc/device-tree/model; then
	echo "ERROR: This setup script is intended to run on a Raspberry Pi."
	echo
	echo "No Raspberry Pi hardware was detected."
	echo "Run this script directly on the Pi used for the Piano Staircase demo."
	exit 1
fi

VENV_PATH="${VENV_PATH:-$HOME/.venv/piano-demo}"

echo "========================================"
echo " Piano Staircase Demo 2 Setup"
echo "========================================"
echo

echo "[1/5] Installing Raspberry Pi OS packages..."

sudo apt update
sudo apt install -y \
	python3-lgpio \
	python3-venv \
	i2c-tools \
	bluez \
	pipewire-audio

echo
echo "[2/5] Creating Python virtual environment..."

if [[ -d "$VENV_PATH" ]]; then
	echo "Virtual environment already exists:"
	echo "  $VENV_PATH"
else
	python3 -m venv --system-site-packages "$VENV_PATH"
	echo "Created:"
	echo "  $VENV_PATH"
fi

echo
echo "[3/5] Installing Python packages..."

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEMO_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

"$VENV_PATH/bin/python" -m pip install \
	-r "$DEMO_DIR/requirements.txt"

echo
echo "Installing Demo 2 Python package..."

"$VENV_PATH/bin/python" -m pip install -e "$DEMO_DIR"

echo
echo "[4/5] Configuring headless audio..."

WIREPLUMBER_CONFIG_DIR="$HOME/.config/wireplumber/wireplumber.conf.d"
WIREPLUMBER_CONFIG="$WIREPLUMBER_CONFIG_DIR/51-bluez-headless.conf"

mkdir -p "$WIREPLUMBER_CONFIG_DIR"

cat >"$WIREPLUMBER_CONFIG" <<'EOF'
wireplumber.profiles = {
  main = {
    monitor.bluez.seat-monitoring = disabled
  }
}
EOF

echo "Installed WirePlumber configuration:"
echo "  $WIREPLUMBER_CONFIG"

if systemctl --user is-active --quiet wireplumber 2>/dev/null; then
	systemctl --user restart wireplumber
	echo "Restarted WirePlumber."
fi

echo
echo "[5/5] Checking software and hardware libraries..."

for command in wpctl pw-play bluetoothctl; do
	if command -v "$command" >/dev/null; then
		echo "$command: OK"
	else
		echo "ERROR: Required command not found: $command" >&2
		exit 1
	fi
done

"$VENV_PATH/bin/python" - <<'PY'
import lgpio
import board
import busio
import adafruit_vl53l0x

print("lgpio:   OK")
print("Blinka:  OK")
print("VL53L0X: OK")
PY

echo
echo "Setup complete."
echo
echo "Before using the sensor, make sure I2C is enabled:"
echo
echo "  sudo raspi-config"
echo "  Interface Options -> I2C -> Enable"
echo
echo "Then check for the VL53L0X:"
echo
echo "  i2cdetect -y 1"
echo
echo "Expected address: 0x29"
echo
echo "Activate the Python environment with:"
echo
echo "  source $VENV_PATH/bin/activate"
