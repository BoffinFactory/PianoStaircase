from __future__ import annotations
import serial
import serial.tools.list_ports
from serial.threaded import LineReader, ReaderThread
from typing import Callable, Dict, List, Set, TypedDict, Optional
import threading
import time

BASIC_SENSOR_CONFIGURATION: List[SerialDeviceConfig] = [
    {"serial_number": "74134373633351D09221", "baudrate": 9600, "name": "Step1"},
    {"serial_number": "D2CC78A7249375CD4E42", "baudrate": 9600, "name": "Step2"},
]


# --- Configuration type ---
class SerialDeviceConfig(TypedDict):
    serial_number: str
    baudrate: int
    name: str


# --- Custom LineReader with multiple removable callbacks ---
class MultiCallbackReader(LineReader):
    TERMINATOR = b"\n"

    def __init__(self, info: SerialManager) -> None:
        super().__init__()
        self.callbacks: Set[Callable[[str, SerialManager], None]] = set()
        self.info = info

    def set_serial_device_info(self, info: SerialManager):
        self.info = info

    def add_callback(self, func: Callable[[str, SerialManager], None]) -> None:
        """Register a new callback (must accept a single str argument)."""
        if callable(func):
            self.callbacks.add(func)

    def remove_callback(self, func: Callable[[str, SerialManager], None]) -> None:
        """Unregister a previously added callback."""
        self.callbacks.discard(func)

    def clear_callbacks(self) -> None:
        """Remove all callbacks."""
        self.callbacks.clear()

    def handle_line(self, line: str) -> None:
        """Dispatch received lines to all registered callbacks."""
        for cb in list(self.callbacks):
            try:
                cb(line, self.info)
            except Exception as e:
                print(f"Callback error: {e}")

    def handle_exception(self, exc: Exception):
        print("⚠️ Serial error:", exc)
        if self.on_disconnect:
            self.on_disconnect(exc)


def find_port_by_serial(serial_number: str) -> Optional[str]:
    for p in serial.tools.list_ports.comports():
        if p.serial_number == serial_number:
            return p.device
    return None


class SerialManager:
    def __init__(self, config: SerialDeviceConfig, idx: int):
        self.config = config
        self.index = idx
        self.thread: Optional[ReaderThread] = None
        self.ser: Optional[serial.Serial] = None
        self.callbacks = MultiCallbackReader(self)
        self.stop_event = threading.Event()

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        found_prev = False
        while not self.stop_event.is_set():
            port = find_port_by_serial(self.config["serial_number"])
            if not port:
                if not found_prev:
                    print(f"Could not find {self.config['name']}")
                    found_prev = True
                time.sleep(2)
                continue
            found_prev = False

            try:
                print(f"Connecting to {port}")
                self.ser = serial.Serial(port, self.config["baudrate"], timeout=1)
                with ReaderThread(self.ser, lambda: self.callbacks) as self.thread:
                    while not self.stop_event.is_set():
                        time.sleep(0.5)
            except (serial.SerialException, OSError) as e:
                print(f"Serial error {self.config['name']}: {e}")
            finally:
                if self.ser and self.ser.is_open:
                    try:
                        self.ser.close()
                    except Exception:
                        pass
                print(f"Reconnecting {self.config['name']}")

    def stop(self):
        self.stop_event.set()
        if self.ser and self.ser.is_open:
            self.ser.close()
        print(f"Serial manager {self.config['name']} stopped.")


def _initialize_serial_managers(
    configs: List[SerialDeviceConfig],
) -> Dict[int, SerialManager]:
    """Initialize serial devices and start threaded readers."""
    devices: Dict[int, SerialManager] = {}

    for idx, cfg in enumerate(configs):
        serial_manager = SerialManager(cfg, idx)
        devices[idx] = serial_manager
        serial_manager.start()

    return devices


def shutdown():
    print("Clearing callbacks and closing connections...")
    for dev in SERIAL_MANAGERS.values():
        dev.stop()


SERIAL_MANAGERS = _initialize_serial_managers(BASIC_SENSOR_CONFIGURATION)
