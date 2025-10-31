import sensors

from playsound import playsound


def get_distance(input_analog):
    voltage = input_analog * (5.0 / 1023.0)
    try:
        dist = 15.0 * pow(voltage, -1.1)
        return dist
    except ZeroDivisionError:
        return 0


audio = [r"audio\piano-g-6200.mp3", r"audio\middle-c-piano-c4.mp3"]


def outer():
    prev = 0

    def handle_line(line, info: sensors.SerialManager):
        nonlocal prev
        voltage = int(line) * (5.0 / 1023.0)
        dist = get_distance(int(line))
        if voltage > 1.0 and prev >= 10:
            playsound(audio[info.index], block=False)
            print(f"Distance: {dist:.4f} cm by {info.config['name']} Voltage {voltage}")
        if voltage < 1.0:
            prev += 1
        else:
            prev = 0

    return handle_line


try:
    for i, serial in sensors.SERIAL_MANAGERS.items():
        serial.callbacks.add_callback(outer())

    while True:
        pass

except KeyboardInterrupt:
    print("Terminated...")
finally:
    sensors.shutdown()
