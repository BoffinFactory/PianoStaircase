#!/bin/bash
# Script to start FluidSynth & aconnect
echo Attempting to start FluidSynth
amixer cset numid=3 1
fluidsynth -si -f /home/mkijowski/git/PianoStaircase/src/fluidsynth/config.txt -a alsa -m alsa_seq /usr/share/sounds/sf2/FluidR3_GM.sf2 &
sleep 2
aconnect 20:0 128:0
