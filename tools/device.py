"""Bounded diagnostics through either S3 serial connector; no automatic reset."""
import argparse
import os
import json
from pathlib import Path
import re
import struct
import time
import zlib

import serial
from serial.tools import list_ports

BRIDGE_SERIAL = os.environ.get("URR_BRIDGE_SERIAL")


def resolve_port(explicit):
    if explicit:
        return explicit
    if not BRIDGE_SERIAL:
        raise RuntimeError("Specify --port or set URR_BRIDGE_SERIAL locally")
    candidates = [p.device for p in list_ports.comports() if p.serial_number == BRIDGE_SERIAL]
    if len(candidates) != 1:
        raise RuntimeError("Expected one known CH343 bridge; use ports and specify --port")
    return candidates[0]


def connect(port):
    link = serial.Serial(port=None, baudrate=115200, timeout=0.2, write_timeout=2)
    link.dtr = False
    link.rts = False
    link.port = resolve_port(port)
    link.open()
    return link


def exchange(link, command, seconds=1):
    link.reset_input_buffer()
    link.write((command + "\n").encode("ascii"))
    chunks = []
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        data = link.read(max(1, min(link.in_waiting, 65536)))
        if data:
            chunks.append(data)
    return b"".join(chunks).decode("utf-8", errors="replace")


def capture(link):
    exchange(link, "raw off", 0.3)
    link.write(b"capture\n")
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        header = re.fullmatch(rb"FRAME (\d+) (\d+) RGB888", link.readline().strip())
        if header:
            break
    else:
        raise RuntimeError("No frame header; is bench firmware running on this port?")
    width, height = map(int, header.groups())
    if (width, height) != (320, 240):
        raise RuntimeError("Unexpected frame dimensions")
    expected = width * height * 3
    data = bytearray()
    deadline = time.monotonic() + 40
    while len(data) < expected and time.monotonic() < deadline:
        data.extend(link.read(expected - len(data)))
    if len(data) != expected:
        raise RuntimeError(f"Incomplete frame: {len(data)}/{expected}")
    footer = link.read_until(b"END FRAME\n", 64)
    if b"END FRAME" not in footer:
        raise RuntimeError("Frame footer missing")

    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))

    stride = width * 3
    scanlines = b"".join(b"\0" + data[y * stride:(y + 1) * stride] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(scanlines)) + chunk(b"IEND", b""))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port")
    parser.add_argument("--seconds", type=float, default=3)
    parser.add_argument("--output", type=Path)
    parser.add_argument("action", choices=["ports", "status", "selftest", "mic", "capture", "command", "soak"])
    parser.add_argument("command", nargs="?")
    args = parser.parse_args()
    if args.seconds <= 0 or args.seconds > 3600:
        parser.error("--seconds must be >0 and <=3600")
    if args.action == "ports":
        print(json.dumps([{"port":p.device,"description":p.description,"vid":p.vid,"pid":p.pid,
                           "serial":p.serial_number} for p in list_ports.comports()], indent=2))
        return
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
    with connect(args.port) as link:
        if args.action == "capture":
            if not args.output:
                parser.error("capture requires --output")
            args.output.write_bytes(capture(link))
            print(args.output.resolve())
            return
        if args.action == "soak":
            deadline = time.monotonic() + args.seconds
            results = []
            while time.monotonic() < deadline:
                result = exchange(link, "status", 0.6)
                results.append(result)
                if "RIG version=" not in result:
                    raise RuntimeError("Missing status response during soak")
                print(result, end="", flush=True)
                if args.output:
                    args.output.write_text("".join(results), encoding="utf-8")
                time.sleep(max(0, min(4.4, deadline - time.monotonic())))
            return
        command = args.command if args.action == "command" else args.action
        if not command or "\n" in command or "\r" in command or len(command) > 94:
            parser.error("provide one command, at most 94 ASCII characters")
        result = exchange(link, command, args.seconds)
        print(result, end="")
        if args.output:
            args.output.write_text(result, encoding="utf-8")
        if not result.strip():
            raise SystemExit("No response: verify port and installed firmware")
        if args.action == "selftest" and not re.search(r"SELFTEST passed=\d+ failed=0\b", result):
            raise SystemExit("Hardware self-test did not pass")


if __name__ == "__main__":
    main()
