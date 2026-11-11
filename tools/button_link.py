"""Reference model of the PROPOSED button link: WROOM-32U GPIO17 (UART TX) to S3 GPIO18 (UART RX).

This is a virtual model for testing the idea before any hardware or firmware exists. Nothing here is flashed or wired, and the
packet format is a proposal the project owner has not accepted. It carries inputs only: no actuator command can be expressed.

Frame (5 bytes): SYNC 0xA5, sequence number, button mask low byte, button mask high byte, CRC-8 (poly 0x07) over the middle three.
Mask bit i is 1 while button i is pressed; i follows `wroom_inputs` in electronics/harnesses.json, and bit 15 is POWER (held, always 0 until
its voltage is measured, M8). The sender transmits every SEND_PERIOD_MS and immediately on a change. The receiver reports "link lost"
(all buttons released) when no valid frame has arrived for TIMEOUT_MS, and "gamepad off" when every wired button reads pressed at once,
which is what a collapsed gamepad rail looks like on active-low lines.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC = 0xA5
FRAME_LEN = 5
BAUD = 115200
BITS_PER_BYTE = 10  # 8N1
SEND_PERIOD_MS = 10
TIMEOUT_MS = 50
POWER_BIT = 15


def button_order():
    return list(json.loads((ROOT / "electronics/harnesses.json").read_text(encoding="utf-8"))["wroom_inputs"])


WIRED_MASK = (1 << len(button_order())) - 1


def crc8(data, poly=0x07):
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ poly) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def encode(seq, mask):
    if not 0 <= mask <= 0xFFFF:
        raise ValueError("mask is 16 bits")
    body = bytes([seq & 0xFF, mask & 0xFF, mask >> 8])
    return bytes([SYNC]) + body + bytes([crc8(body)])


def frame_time_ms():
    return FRAME_LEN * BITS_PER_BYTE * 1000 / BAUD


class Receiver:
    """Byte-stream decoder with resynchronisation, sequence-gap counting and the link-lost / gamepad-off rules."""

    def __init__(self):
        self.buffer = bytearray()
        self.mask = 0
        self.last_ok_ms = None
        self.last_seq = None
        self.dropped = 0       # frames missed, from sequence gaps
        self.rejected = 0      # bad-CRC candidate frames skipped

    def feed(self, data, now_ms):
        self.buffer += data
        while len(self.buffer) >= FRAME_LEN:
            if self.buffer[0] != SYNC:
                del self.buffer[0]
                continue
            frame = bytes(self.buffer[:FRAME_LEN])
            if crc8(frame[1:4]) != frame[4]:
                self.rejected += 1
                del self.buffer[0]
                continue
            del self.buffer[:FRAME_LEN]
            seq = frame[1]
            if self.last_seq is not None:
                self.dropped += (seq - self.last_seq - 1) & 0xFF
            self.last_seq = seq
            self.mask = frame[2] | (frame[3] << 8)
            self.last_ok_ms = now_ms

    def link_ok(self, now_ms):
        return self.last_ok_ms is not None and now_ms - self.last_ok_ms <= TIMEOUT_MS

    def state(self, now_ms):
        """What the S3 firmware would act on: pressed set, plus a status."""
        if not self.link_ok(now_ms):
            return {"status": "link-lost", "pressed": set()}
        if self.mask & WIRED_MASK == WIRED_MASK:
            return {"status": "gamepad-off", "pressed": set()}
        order = button_order()
        return {"status": "ok", "pressed": {order[i] for i in range(len(order)) if self.mask >> i & 1}}


def simulate(events, duration_ms, corrupt=None):
    """Run a sender against a receiver. `events` maps time (ms) to the mask the buttons take from then on.
    `corrupt` is an optional function (time_ms, frame_bytes) -> bytes applied on the wire (return b'' to drop a frame).
    Returns the receiver and the list of (time_ms, state) samples taken each millisecond."""
    rx = Receiver()
    seq = 0
    mask = 0
    last_sent_mask = None
    next_periodic = 0
    samples = []
    for t in range(duration_ms + 1):
        if t in events:
            mask = events[t]
        if t >= next_periodic or mask != last_sent_mask:
            frame = encode(seq, mask)
            seq += 1
            last_sent_mask = mask
            next_periodic = t + SEND_PERIOD_MS
            wire = corrupt(t, frame) if corrupt else frame
            rx.feed(wire, t)
        samples.append((t, rx.state(t)))
    return rx, samples


if __name__ == "__main__":
    print(f"frame time {frame_time_ms():.3f} ms at {BAUD} baud; period {SEND_PERIOD_MS} ms; timeout {TIMEOUT_MS} ms")
    print("bit order:", ", ".join(f"{i}={n}" for i, n in enumerate(button_order())), f", {POWER_BIT}=POWER (held)")
