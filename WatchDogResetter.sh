#!/bin/sh
# This script resets the timer of the hardware watchdog of the RevPi
# Usage: sudo bash ./WatchDogResetter.sh
value=$(piTest -q -1 -r RevPiLED)
value=$(( ($value + 128) % 256 ))
piTest -w RevPiLED,"$value" # write value
