#!/usr/bin/env python3

"""
Cooldown-gate diagnostic for Piano Staircase Demo 2.

Attempts actions faster than the configured cooldown and reports which ones are accepted or
rejected.
"""

import time

from piano_staircase_demo.interaction import CooldownGate


def main() -> None:
    gate = CooldownGate(0.20)

    print("=== Interaction Cooldown Diagnostic ===")
    print("Attempting an event every 50 ms.")
    print("Cooldown: 200 ms")
    print()

    start = time.monotonic()

    for _ in range(40):
        elapsed = time.monotonic() - start
        accepted = gate.allow()

        result = "ACCEPT" if accepted else "DROP"

        print(f"{elapsed:5.2f}s  {result}")

        time.sleep(0.05)


if __name__ == "__main__":
    main()
