# Audio System

Demo 2 uses PipeWire for audio playback.

The audio subsystem sends playback to the current PipeWire default output rather than depending on a
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
```

The display's physical volume can also be adjusted using its on-screen controls.

Although HDMI playback is clean, the display's built-in speakers are too quiet for the tabletop
demonstration even when both the PipeWire sink and display volume are set to maximum.

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

This output method provides adequate volume and clean playback.

The physical cable and adapter arrangement is less convenient than Bluetooth, but USB/3.5 mm audio
is currently the stronger candidate for the final tabletop demonstration because of its reliability.

The Framework Audio Expansion Card should be checked for full output volume whenever it is
reconnected before evaluating the overall demonstration volume.

### Bluetooth — SoundCore 2

An Anker SoundCore 2 was successfully paired with the Raspberry Pi and exposed by PipeWire as a
Bluetooth audio sink.

Bluetooth greatly simplifies the physical setup and provides adequate volume.

Current testing has shown recurring choppy or crackling playback over Bluetooth. The problem is
often most noticeable near the beginning of playback, although its severity varies between tests.

The same diagnostic audio plays cleanly through HDMI, which indicates that the generated WAV data
and general PipeWire playback path are functioning correctly.

Disabling Wi-Fi temporarily eliminated the Bluetooth problem during one test. After Wi-Fi was
re-enabled, Bluetooth playback initially remained clean, but the crackling later returned.

This suggests that Wi-Fi/Bluetooth coexistence on the Raspberry Pi Zero 2 W may contribute to the
problem, but cycling Wi-Fi is not a reliable permanent workaround.

Bluetooth remains useful for development when convenient, but it should not currently be treated as
the preferred output for the final demonstration.

## Reusable Audio Software

Reusable audio behavior is implemented in:

```text
piano_staircase_demo/audio.py
```

The module provides two primary abstractions.

### `AudioClip`

`AudioClip` represents generated audio that is ready to be played.

It records:

- the generated WAV file path; and
- the approximate duration of the audio.

Audio clips can be generated once and reused during the lifetime of an `AudioSystem`.

This will allow the complete demonstration to prepare commonly used sounds during startup rather
than regenerating them every time the sensor is triggered.

### `AudioSystem`

`AudioSystem` generates musical sequences, manages temporary WAV files, and sends playback through
PipeWire.

For example:

```python
with AudioSystem() as audio:
    sequence = audio.create_sequence(("C4", "E4", "G4"))
    audio.play(sequence)
```

Sequences are generated as complete WAV files before playback begins.

This keeps audio generation outside the real-time playback path and allows a complete musical
sequence to use one playback stream.

The audio system supports both blocking and non-blocking playback.

Blocking playback waits for the sound to finish:

```python
audio.play(sequence)
```

Non-blocking playback allows other behavior to occur at the same time:

```python
audio.play(sequence, blocking=False)
```

The application can later wait for completion with:

```python
audio.wait()
```

or stop playback with:

```python
audio.stop()
```

Non-blocking playback will allow the complete demonstration to animate lighting while a musical
sequence is playing.

The audio diagnostic in:

```text
scripts/test_audio.py
```

uses `AudioSystem` rather than implementing its own audio generation and playback.

## Current Diagnostic Sequence

The current diagnostic uses the notes:

```text
C4  261.63 Hz
E4  329.63 Hz
G4  392.00 Hz
```

Audio is currently generated as:

- 48 kHz stereo;
- 16-bit PCM WAV data;
- simple sine-wave tones;
- short fade-in and fade-out envelopes; and
- a continuous sequence played through a single PipeWire playback process.

These settings are intended primarily for subsystem testing.

## Sound Quality

The current diagnostic generates simple sine-wave tones.

Sine waves are useful during development because they are easy to generate, predictable, and make
timing or playback problems easy to hear.

They are not intended to represent the final sound of the demonstration.

A later refinement should replace or supplement the synthesized tones with piano-like audio.

The preferred approach is expected to be short prerecorded WAV samples rather than adding a full
MIDI or software-synthesizer stack.

Sample-based playback would preserve the existing `AudioSystem` and PipeWire architecture while
providing more realistic:

- attack;
- decay;
- harmonics; and
- timbre.

The final demonstration currently needs only a small number of notes, so a compact set of audio
samples should be sufficient.

Any audio samples distributed with the project must have licensing terms compatible with the
project.

Sound-quality improvements should be made after basic audio and lighting synchronization has been
validated so that timing and timbre are not debugged simultaneously.

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

The audio subsystem normally plays through the current PipeWire default sink.

This keeps the reusable application code independent of the final physical audio transport.

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

The project setup script installs this configuration automatically.

Bluetooth pairing remains device-specific and is not hard-coded into the application or setup
script.

## Current Development Decision

No final audio transport has been permanently selected.

For now:

- PipeWire is the common software interface.
- USB/3.5 mm audio is the strongest candidate for the final demonstration.
- Bluetooth remains convenient for development but has recurring playback reliability problems.
- HDMI provides a useful known-good diagnostic output but is too quiet for the event.
- The application should not contain Bluetooth MAC addresses, ALSA card numbers, or PipeWire sink
  IDs.
- More natural piano-like sound should be added after basic synchronization is working.

The next major audio milestone is synchronized playback with the three lighting channels.
