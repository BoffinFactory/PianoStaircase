# Raspberry Pi setup and install instructions

Using a Raspberry Pi v4 I assume you have the most up to date installation of Raspberry Pi OS (64bit) via
the raspberry pi imager: https://www.raspberrypi.com/software/


## Automated installation

Download and run the local `raspberry-pi-setup.sh`.  Note, this does not work yet!


## Manual installation

More notes: this is not fully functional yet, but it gets you close...  
Still some audio distortion and tweaking needed to get things working.

Step through the following in relatively the following order:

```bash
sudo apt update
sudo apt install qjackctl fluidsynth a2jmidid ssh

sudo systemctl enable ssh.service
sudo systemctl start ssh.service

sudo vim /etc/group
# add piano (or whatever default user is) to the following groups:
# adm,tty,audio,bluetooth,pulse-access

# overwrite default user's ~/.jackdrc with example given

# configure fluidsynth with the following:
# MIDI driver: jack
# Aduio driver: jack
# soundfonts: /usr/share/sounds/sf2/FluidR3_GM.sf2

a2jmidid -e &
qjackctl &
# fluidsynth ?, or just qsynth??
```

