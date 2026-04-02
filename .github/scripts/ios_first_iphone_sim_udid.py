#!/usr/bin/env python3
"""Print UDID of the first available iPhone Simulator (JSON from simctl). Exit 1 if none."""

from __future__ import annotations

import json
import subprocess
import sys


def main() -> None:
    out = subprocess.check_output(
        ["xcrun", "simctl", "list", "devices", "available", "-j"],
        text=True,
    )
    data = json.loads(out)
    for _runtime, devices in data.get("devices", {}).items():
        if "iOS" not in _runtime:
            continue
        for d in devices:
            if d.get("isAvailable") and "iPhone" in d.get("name", ""):
                print(d["udid"])
                sys.exit(0)
    sys.stderr.write("No available iPhone simulator found\n")
    sys.exit(1)


if __name__ == "__main__":
    main()
