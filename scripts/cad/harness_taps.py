"""Where the proposed harness lands on the board: one tap per pad, from the connection list and the pad table.

Pure Python (no FreeCAD), so the same data feeds the 3D harness model and the unit tests.
"""
import csv
import hashlib
import json
from pathlib import Path

SOURCES = "electronics/harness-sources-proposed.csv"
REGISTRY = "electronics/harnesses.json"
# Display colours for the 3D markers only. They identify the connector; they are NOT wire colours.
MARKER_RGB = {"J1L": (0.10, 0.35, 0.90), "J1R": (0.00, 0.65, 0.85), "J2F": (0.85, 0.20, 0.10), "J2R": (0.95, 0.55, 0.10),
              "J2D": (0.10, 0.60, 0.25), "J2L": (0.55, 0.75, 0.10), "J2C": (0.65, 0.20, 0.75)}
SHARED_RGB = (0.15, 0.15, 0.15)


def lf_sha256(path):
    """Hash a text file with LF newlines, so Windows and Linux checkouts agree."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def collect(project):
    """Return (taps, wires). A tap is one pad with every wire that lands, or may land, on it.

    Rows on hold are not wired and get no tap. A wire whose pad is not settled (two candidate pads)
    appears on each candidate with candidate=True; it is still one wire.
    """
    project = Path(project)
    registry = json.loads((project / REGISTRY).read_text(encoding="utf-8"))
    connectors = {h["id"]: h for h in registry["harnesses"] if h.get("goes_to")}
    with (project / SOURCES).open(newline="", encoding="utf-8") as handle:
        rows = [r for r in csv.DictReader(handle) if r["harness"] in connectors and r["pin"]]
    taps, wires = {}, []
    for r in rows:
        if r["status"] == "hold" or not r["source_pads"]:
            continue
        hid, pin = r["harness"], int(r["pin"])
        registered = {p["pin"]: p["signal"] for p in connectors[hid]["pins"]}
        if pin not in registered:
            raise ValueError(f"{hid} position {pin} is wired in the connection list but is not in the registry")
        pad_ids = r["source_pads"].split("|")
        wire = {"wire_id": f"{hid}-W{pin:02d}", "connector": hid, "pin": pin, "signal": registered[pin],
                "far_end": connectors[hid]["goes_to"], "status": r["status"], "pads": pad_ids}
        wires.append(wire)
        for pid in pad_ids:
            taps.setdefault(pid, []).append({**wire, "candidate": len(pad_ids) > 1})
    out = []
    for pid in sorted(taps):
        landing = taps[pid]
        owners = {w["connector"] for w in landing}
        out.append({"pad": pid, "wires": landing, "connectors": sorted(owners),
                    "rgb": MARKER_RGB[next(iter(owners))] if len(owners) == 1 else SHARED_RGB,
                    "settled": not any(w["candidate"] for w in landing)})
    return out, wires
