"""Enclosure pod study: load the space-claim record, check that the bodies fit and do not collide, draw three views.

Pure Python (no FreeCAD). The record is cad/enclosure/pod-r<NNN>.json; its frame is the pod interior (see the record).
A pass here means the recorded boxes fit each other. It does not prove a physical fit: several sizes are assumptions.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Pairs that are one physical part and so may touch (the display's own SD slot and header sit on its PCB).
ATTACHED = {frozenset(("DISP1", "DISP1_SD")), frozenset(("DISP1", "DISP1_HDR"))}
# Bodies that must reach a wall: body id -> (axis, "min" or "max").
AT_WALL = {"DISP1": (2, "min"), "MIC1": (2, "min"), "CHG1": (0, "max"), "SW1": (1, "max")}
COLOURS = {"DISP1": "#4a90d9", "DISP1_SD": "#9bbbe0", "DISP1_HDR": "#c9d8ea", "BAT2": "#e0a030", "MCU1": "#3c9a5f",
           "WRM1": "#7ac77a", "CHG1": "#c0504d", "REG1": "#d98880", "SW1": "#8064a2", "MIC1": "#808080"}


def load(revision=1):
    return json.loads((ROOT / f"cad/enclosure/pod-r{revision:03d}.json").read_text(encoding="utf-8"))


def box(body):
    """(x0, y0, z0, x1, y1, z1) of a body."""
    return tuple(body["pos"]) + tuple(p + s for p, s in zip(body["pos"], body["size"]))


def separation(a, b):
    """Largest axis gap between two boxes; negative means they overlap by that much on every axis."""
    return max(max(b[i] - a[i + 3], a[i] - b[i + 3]) for i in range(3))


def check(rec):
    """Return a list of problems (empty when the layout is consistent)."""
    problems = []
    inside = rec["interior_mm"]
    boxes = {b["id"]: box(b) for b in rec["bodies"]}
    if len(boxes) != len(rec["bodies"]):
        problems.append("duplicate body id")
    for bid, bx in boxes.items():
        for i in range(3):
            if bx[i] < -1e-9 or bx[i + 3] > inside[i] + 1e-9:
                problems.append(f"{bid} leaves the interior on axis {'XYZ'[i]}")
    ids = sorted(boxes)
    for n, a in enumerate(ids):
        for b in ids[n + 1:]:
            gap = separation(boxes[a], boxes[b])
            if frozenset((a, b)) in ATTACHED:
                if gap < -1e-9:
                    problems.append(f"{a} and {b} overlap")
            elif gap < rec["min_gap_mm"] - 1e-9:
                problems.append(f"{a} and {b} are {gap:.2f} mm apart (minimum {rec['min_gap_mm']})")
    for bid, (axis, end) in AT_WALL.items():
        want = 0.0 if end == "min" else inside[axis]
        have = boxes[bid][axis] if end == "min" else boxes[bid][axis + 3]
        if abs(have - want) > 1e-9:
            problems.append(f"{bid} does not reach its wall")
    return problems


def outer(rec):
    """Outside size of the pod: interior plus a wall on every side."""
    return tuple(round(v + 2 * rec["wall_mm"], 2) for v in rec["interior_mm"])


def gaps(rec):
    """Smallest gap between any two bodies that are not one part: (gap, id, id)."""
    boxes = {b["id"]: box(b) for b in rec["bodies"]}
    ids = sorted(boxes)
    return min((round(separation(boxes[a], boxes[b]), 2), a, b) for n, a in enumerate(ids) for b in ids[n + 1:]
               if frozenset((a, b)) not in ATTACHED)


def svg(rec, path):
    """Front (XY), top (XZ) and side (ZY) views of the interior with every body as a labelled rectangle."""
    ix, iy, iz = rec["interior_mm"]
    w = rec["wall_mm"]
    s, pad = 5.0, 30.0
    width = pad * 3 + (ix + iz + 4 * w) * s
    height = pad * 3 + (iy + iz + 4 * w) * s + 40
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" font-family="sans-serif" font-size="11">',
           f'<rect width="{width:.0f}" height="{height:.0f}" fill="white"/>',
           f'<text x="{pad}" y="18" font-size="14" font-weight="bold">{rec["id"]}: {rec["state"]}</text>',
           '<text x="%s" y="34">Outside %s x %s x %s mm. Sizes marked ASSUMED in the record are not readings.</text>' % ((pad,) + outer(rec))]

    def view(ox, oy, a, b, flip_b, near_high, title):
        ea, eb = rec["interior_mm"][a], rec["interior_mm"][b]
        out.append(f'<text x="{ox}" y="{oy - 6}" font-weight="bold">{title}</text>')
        out.append(f'<rect x="{ox}" y="{oy}" width="{(ea + 2 * w) * s}" height="{(eb + 2 * w) * s}" fill="#dddddd" stroke="black"/>')
        out.append(f'<rect x="{ox + w * s}" y="{oy + w * s}" width="{ea * s}" height="{eb * s}" fill="white" stroke="black" stroke-width="0.5"/>')
        # Draw the bodies nearest the viewer last so they sit on top.
        depth = 3 - a - b
        for body in sorted(rec["bodies"], key=lambda q: box(q)[depth + 3] if near_high else -box(q)[depth]):
            bx = box(body)
            x = ox + (w + bx[a]) * s
            y = oy + (w + (eb - bx[b + 3] if flip_b else bx[b])) * s
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{body["size"][a] * s:.1f}" height="{body["size"][b] * s:.1f}" '
                       f'fill="{COLOURS.get(body["id"], "#bbbbbb")}" fill-opacity="0.75" stroke="black" stroke-width="0.6"/>')
            out.append(f'<text x="{x + 3:.1f}" y="{y + 12:.1f}">{body["id"]}</text>')

    top = 60
    view(pad, top, 0, 1, True, False, "FRONT (through the front wall): X right, Y up")
    view(pad * 2 + (ix + 2 * w) * s, top, 2, 1, True, True, "RIGHT SIDE: Z back to the right, Y up")
    view(pad, top + pad + (iy + 2 * w) * s, 0, 2, False, True, "TOP: X right, Z back downward")
    out.append('</svg>')
    Path(path).write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    revision = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    record = load(revision)
    found = check(record)
    target = ROOT / f"exports/enclosure/pod-r{revision:03d}-VIEWS.svg"
    target.parent.mkdir(parents=True, exist_ok=True)
    svg(record, target)
    print("outside", outer(record), "smallest gap", gaps(record))
    print("\n".join(found) if found else "layout consistent")
    sys.exit(1 if found else 0)
