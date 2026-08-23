#!/usr/bin/env bash

#
# Local-console launcher for Piano Staircase Demo 2.
#
# This script turns tty1 into an unattended demonstration console:
#
#   - starts the complete Demo 2 application;
#   - restarts it if it exits;
#   - prevents common terminal-control keys from exposing a shell;
#   - disables console blanking;
#   - provides a maintenance mode controlled through SSH.
#
# The normal SSH environment is not affected.
#

set -u

DEMO_DIR="$HOME/PianoStaircase/src/demo2"
VENV_DIR="$HOME/.venv/piano-demo"

MAINTENANCE_FILE="$HOME/.piano-demo-maintenance"

# ---------------------------------------------------------------------------
# Protect the local exhibit console
# ---------------------------------------------------------------------------

# Ctrl+C should be handled by run_demo.py. If the application exits because
# of Ctrl+C, this launcher itself must remain alive so it can restart it.
trap '' INT

# Prevent Ctrl+S from accidentally freezing terminal output.
stty -ixon 2>/dev/null || true

# Disable common job-control / shell-escape style keys on this console.
#
# Ctrl+Z normally suspends the foreground process.
# Ctrl+\ normally sends SIGQUIT.
stty susp undef quit undef 2>/dev/null || true

# Keep the exhibit display awake.
#
# Some console/video configurations do not support every setterm option, so
# failure here should not prevent the demo from starting.
setterm \
	--blank 0 \
	--powerdown 0 \
	--powersave off \
	2>/dev/null ||
	true

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

wait_for_maintenance_mode() {
	clear

	echo
	echo "============================================================"
	echo "                PIANO STAIRCASE MAINTENANCE"
	echo "============================================================"
	echo
	echo "Automatic demo startup is temporarily paused."
	echo
	echo "Maintenance is controlled through SSH."
	echo
	echo "To resume:"
	echo
	echo "    rm ~/.piano-demo-maintenance"
	echo
	echo "============================================================"
	echo

	while [ -e "$MAINTENANCE_FILE" ]; do
		sleep 1
	done
}

wait_for_pipewire() {
	#
	# The login session normally starts PipeWire automatically. At boot,
	# however, the demo may reach this point slightly before PipeWire is
	# completely ready.
	#
	# Wait up to approximately five seconds, then continue either way.
	#

	for _ in $(seq 1 20); do
		if wpctl status >/dev/null 2>&1; then
			return
		fi

		sleep 0.25
	done
}

# ---------------------------------------------------------------------------
# Main launcher loop
# ---------------------------------------------------------------------------

while true; do

	if [ -e "$MAINTENANCE_FILE" ]; then
		wait_for_maintenance_mode
	fi

	if [ ! -d "$DEMO_DIR" ]; then
		clear

		echo
		echo "Piano Staircase cannot start."
		echo
		echo "Demo directory not found:"
		echo
		echo "    $DEMO_DIR"
		echo
		echo "Retrying in 10 seconds..."

		sleep 10
		continue
	fi

	if [ ! -f "$VENV_DIR/bin/activate" ]; then
		clear

		echo
		echo "Piano Staircase cannot start."
		echo
		echo "Python environment not found:"
		echo
		echo "    $VENV_DIR"
		echo
		echo "Retrying in 10 seconds..."

		sleep 10
		continue
	fi

	cd "$DEMO_DIR" || {
		sleep 10
		continue
	}

	# shellcheck disable=SC1091
	source "$VENV_DIR/bin/activate"

	wait_for_pipewire
	clear

	# -----------------------------------------------------------------------
	# Normal event configuration
	# -----------------------------------------------------------------------
	#
	# Normal unattended behavior is the stable three-zone Vibraphone mode.
	# Procedural pipes are explicitly disabled and remain development/Kayleigh
	# machinery rather than a random visitor special.
	#

	./scripts/run_demo.py \
		--display \
		--articulation instrument \
		--response-mode zones \
		--special-every 0

	exit_status=$?

	clear

	echo
	echo "Piano Staircase stopped."
	echo
	echo "Exit status: $exit_status"
	echo
	echo "Restarting in 2 seconds..."

	sleep 2
done
