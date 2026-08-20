#!/usr/bin/env bash

#
# Toggle Piano Staircase maintenance mode.
#
# Maintenance ON:
#   - creates ~/.piano-demo-maintenance
#   - gracefully stops the running demo
#   - the console launcher remains alive and waits
#
# Maintenance OFF:
#   - removes ~/.piano-demo-maintenance
#   - the console launcher notices and restarts the demo automatically
#

set -u

MAINTENANCE_FILE="$HOME/.piano-demo-maintenance"

if [ -e "$MAINTENANCE_FILE" ]; then

	# ---------------------------------------------------------------
	# Maintenance mode is currently ON -> turn it OFF.
	# ---------------------------------------------------------------

	rm "$MAINTENANCE_FILE"

	echo "Piano Staircase maintenance mode: OFF"
	echo "The demo should restart automatically within a few seconds."

else

	# ---------------------------------------------------------------
	# Maintenance mode is currently OFF -> turn it ON.
	# ---------------------------------------------------------------

	touch "$MAINTENANCE_FILE"

	echo "Piano Staircase maintenance mode: ON"

	#
	# Gracefully stop run_demo.py if it is currently running.
	#
	# SIGINT follows the same shutdown path as Ctrl+C, allowing the
	# application to turn off LEDs, stop audio, close the sensor, and
	# shut down the display process cleanly.
	#

	if pgrep \
		-u "$USER" \
		-f 'scripts/run_demo.py' \
		>/dev/null; then
		pkill \
			-INT \
			-u "$USER" \
			-f 'scripts/run_demo.py'

		echo "Requested graceful shutdown of the running demo."
	else
		echo "The demo was not currently running."
	fi

	echo "The local console will remain in maintenance mode."

fi
