# Audio System

Demo 2 uses PipeWire for audio playback.

The application sends audio to the current PipeWire default output rather than depending on a
specific physical audio device. This allows the same software to be used with HDMI, USB audio, or
Bluetooth.

## Tested Audio Outputs

Three output methods have been evaluated.

### HDMI Display Audio

Audio over HDMI to the portable display works reliably.

The display and PipeWire output both need sufficient volume:

```bash
wpctl status
wpctl set-volume <sink-id> 100%
wpctl set-mute <sink-id> 0
````

The display's physical volume can also be adjusted using its on-screen controls.

Although HDMI playback is clean, the display's built-in speakers are too quiet for the tabletop
demonstration even at maximum volume.

HDMI remains useful as a known-good diagnostic output.

### Framework Audio Expansion Card

The Framework Audio Expansion Card was successfully tested as a USB audio output connected to a
powered speaker through a 3.5 mm cable.

The card exposes an ALSA mixer control named `Speaker Volume`.

Its initial playback level was substantially attenuated:

```text
72% / -20.50 dB
```

Setting the hardware output to 100% produced a much more useful signal:

```bash
amixer -c Card sset 'Speaker Volume' 100% unmute
```

At 100%, the card reported:

```text
100% / 0.00 dB
```

This output method provides adequate volume but currently requires an inconvenient cable and adapter
arrangement.

### Bluetooth — SoundCore 2

An Anker SoundCore 2 was successfully paired with the Raspberry Pi and exposed by PipeWire as a
Bluetooth audio sink.

Bluetooth greatly simplifies the physical setup and provides adequate volume.

However, current testing has shown that playback is often choppy during approximately the first one
or two seconds of a newly started Bluetooth audio stream. Playback generally becomes smoother after
the connection has been active briefly.

The same diagnostic audio plays cleanly through HDMI, which indicates that the problem is specific
to the Bluetooth audio path rather than the generated WAV file or general PipeWire playback.

Bluetooth remains suitable for development, but its startup latency and playback stability should be
investigated before the final demonstration audio output is selected.

## PipeWire

The Raspberry Pi OS Lite installation uses PipeWire and WirePlumber for audio routing.

Useful commands include:

```bash
wpctl status
```

to display available audio devices and sinks, and:

```bash
wpctl set-default <sink-id>
```

to choose the default playback destination.

Sink IDs may change between boots or device reconnections and should not be hard-coded into the demo
application.

The application should normally play to the current default PipeWire sink.

## Headless Bluetooth Audio

On this headless Raspberry Pi OS Lite installation, WirePlumber's default Bluetooth seat monitoring
prevented Bluetooth audio profiles from becoming available from an SSH-managed session.

The following WirePlumber configuration allows Bluetooth audio to operate on the dedicated headless
system:

```text
~/.config/wireplumber/wireplumber.conf.d/51-bluez-headless.conf
```

```ini
wireplumber.profiles = {
  main = {
    monitor.bluez.seat-monitoring = disabled
  }
}
```

After changing this configuration, WirePlumber can be restarted with:

```bash
systemctl --user restart wireplumber
```

## Current Development Decision

No final audio transport has been selected.

For now:

* PipeWire is the common software interface.
* Bluetooth is convenient for development.
* HDMI provides a useful known-good diagnostic output.
* USB/3.5 mm audio remains a viable wired fallback.
* The application should not contain Bluetooth MAC addresses, ALSA card numbers, or PipeWire sink
  IDs.

The final output method will be selected after audio/lighting synchronization and Bluetooth latency
are evaluated more thoroughly.
