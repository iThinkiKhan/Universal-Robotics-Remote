"""Placement study of the DevKitC V4 (WROOM-32U) against the gamepad board. Pure Python, no FreeCAD.

PROPOSED / NOT FOR ASSEMBLY. This is an XY study. Heights (board thickness, component and header heights, stick travel) are not recorded
(M5), so every length here is the straight-line distance in the board plane: a lower bound for a wire between a pad and a pin, before
connector housings, strain relief, service loops or routing around parts. Nothing here is a cut length.

Frames
  Gamepad: the survey datum (rear/component side toward the viewer, X right, Y up toward USB, rear surface Z = 0).
  DevKitC: origin at the USB-end bottom-left corner seen from the component side, X toward the J3 row, Y toward the antenna end.
           Pin positions come from Espressif's dimensions drawing as recorded in hardware/devkitc-v4-header.json.
Pose: (cx, cy) places the DevKitC board centre in the gamepad frame; rot_deg turns it counter-clockwise; flip turns the board over
(mirrors it about its long axis) before the rotation, which swaps which header row faces which way.
"""
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import survey_geometry  # noqa: E402

HEADER = ROOT / "hardware/devkitc-v4-header.json"


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def devkit():
    """Board geometry and every header position in the DevKitC frame: list of dicts with side, pos, name, gpio, u, v."""
    data = json.loads(HEADER.read_text(encoding="utf-8"))
    g = data["geometry"]
    pitch, rows = g["pitch_mm"], g["row_spacing_mm"]
    u_left = (g["width_mm"] - rows) / 2
    pins = []
    for side, key, u in (("J2", "j2_left", u_left), ("J3", "j3_right", u_left + rows)):
        for e in data[key]:
            v = g["length_mm"] - (g["length_mm"] - (len(data[key]) - 1) * pitch) / 2 - (e["pos"] - 1) * pitch
            pins.append({"side": side, "pos": e["pos"], "name": e["name"], "gpio": e.get("gpio"), "u": u, "v": v})
    return {"width": g["width_mm"], "length": g["length_mm"], "pins": pins}


def to_gamepad(point, pose, board):
    """Map a DevKitC-frame point into the gamepad frame."""
    u, v = point[0] - board["width"] / 2, point[1] - board["length"] / 2
    if pose.get("flip"):
        u = -u
    a = math.radians(pose.get("rot_deg", 0.0))
    x = u * math.cos(a) - v * math.sin(a)
    y = u * math.sin(a) + v * math.cos(a)
    return (x + pose["cx"], y + pose["cy"])


def gamepad_data():
    survey = json.loads((ROOT / "measurements/boards/gamepad-gh-wii-u002.json").read_text(encoding="utf-8"))
    result = survey_geometry.resolve(survey)
    pads = {p["id"]: p for p in survey_geometry.load_pads(ROOT / survey["pads_file"])}
    return {"polygon": result["outline"]["polygon"], "bbox": result["outline"]["bbox"], "pads": pads, "survey": survey}


def button_wires():
    """Wires that end on the DevKitC: dicts with wire_id, connector, signal, far pin (gpio int or 'GND') and the gamepad pad id(s)."""
    netlist = _load("harness_netlist_for_placement", "tools/harness_netlist.py")
    wires = []
    for r in netlist.build():
        if not r["far_board"].startswith("DevKitC") or r["status"] == "hold" or "reserved" in r["far_pin"]:
            continue
        far = "GND" if r["far_pin"] == "GND" else int(r["far_pin"][4:])
        wires.append({"wire_id": r["wire_id"], "connector": r["connector"], "signal": r["signal"], "far": far,
                      "pads": r["gamepad_pad"].split("|")})
    return wires


def lengths(pose, board=None, gp=None, wires=None):
    """Straight XY length of every DevKitC wire for a pose. A wire whose pad is unsettled (two candidates) takes the longer one.
    A ground return takes the nearest of the DevKitC's GND pins. Returns a list of dicts."""
    board = board or devkit()
    gp = gp or gamepad_data()
    wires = wires or button_wires()
    by_gpio = {p["gpio"]: p for p in board["pins"] if p["gpio"] is not None}
    grounds = [p for p in board["pins"] if p["name"] == "GND"]
    out = []
    for w in wires:
        candidates = [to_gamepad((p["u"], p["v"]), pose, board) for p in ([by_gpio[w["far"]]] if w["far"] != "GND" else grounds)]
        per_pad = []
        for pid in w["pads"]:
            pad = gp["pads"][pid]
            per_pad.append(min(math.dist((pad["x"], pad["y"]), c) for c in candidates))
        out.append({**w, "length_mm": max(per_pad)})
    return out


def corners(pose, board):
    return [to_gamepad(c, pose, board) for c in ((0, 0), (board["width"], 0), (board["width"], board["length"]), (0, board["length"]))]


def inside_bbox(pose, board, bbox, margin=0.0):
    return all(bbox[0] + margin <= x <= bbox[2] - margin and bbox[1] + margin <= y <= bbox[3] - margin for x, y in corners(pose, board))


def score(pose, board, gp, wires):
    ls = lengths(pose, board, gp, wires)
    return sum(w["length_mm"] for w in ls), max(w["length_mm"] for w in ls)


def search(step_mm=2.0, rot_step=15, margin=2.0):
    """Grid search for the pose of least total wire length with the whole DevKitC inside the gamepad's bounding rectangle
    (a compact stack is assumed, not required by any record). Returns the best pose per flip state, best first."""
    board, gp, wires = devkit(), gamepad_data(), button_wires()
    bbox = gp["bbox"]
    best = {}
    for flip in (False, True):
        for rot in range(0, 360, rot_step):
            cx = bbox[0]
            while cx <= bbox[2]:
                cy = bbox[1]
                while cy <= bbox[3]:
                    pose = {"cx": cx, "cy": cy, "rot_deg": float(rot), "flip": flip}
                    if inside_bbox(pose, board, bbox, margin):
                        total, worst = score(pose, board, gp, wires)
                        if flip not in best or total < best[flip][0]:
                            best[flip] = (total, worst, pose)
                    cy += step_mm
                cx += step_mm
    return sorted(({"total_mm": t, "worst_mm": w, "pose": p} for t, w, p in best.values()), key=lambda r: r["total_mm"])


def svg(pose, path, title):
    """Top view in the gamepad frame: board outline, pads, DevKitC outline and pins, one line per wire."""
    board, gp, wires = devkit(), gamepad_data(), button_wires()
    ls = lengths(pose, board, gp, wires)
    scale, pad_px, w, h = 8.0, 40, 125.5, 62.5

    def pt(x, y):
        return (pad_px + x * scale, pad_px + (h - y) * scale)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(w * scale + 2 * pad_px)}" height="{int(h * scale + 2 * pad_px + 150)}" font-family="sans-serif" font-size="11">',
           '<rect width="100%" height="100%" fill="#ffffff"/>',
           f'<text x="{pad_px}" y="22" font-size="14" font-weight="bold">{title}</text>']
    out.append('<polygon fill="#d8eef2" stroke="#245" stroke-width="1.5" points="' + " ".join("%.1f,%.1f" % pt(*p) for p in gp["polygon"]) + '"/>')
    for pid, pad in gp["pads"].items():
        x, y = pt(pad["x"], pad["y"])
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="#999"/>')
    corner_pts = [pt(*c) for c in corners(pose, board)]
    out.append('<polygon fill="#f6d9a8" fill-opacity="0.55" stroke="#a60" stroke-width="1.5" points="' + " ".join("%.1f,%.1f" % c for c in corner_pts) + '"/>')
    colours = {"J2F": "#d9301a", "J2R": "#f28c1a", "J2D": "#1a9940", "J2L": "#8cbf1a", "J2C": "#a633bf"}
    by_gpio = {p["gpio"]: p for p in board["pins"] if p["gpio"] is not None}
    grounds = [p for p in board["pins"] if p["name"] == "GND"]
    for p in board["pins"]:
        x, y = pt(*to_gamepad((p["u"], p["v"]), pose, board))
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" fill="#a60"/>')
    for wd, wire in zip(ls, wires):
        pins = [by_gpio[wire["far"]]] if wire["far"] != "GND" else grounds
        for pid in wire["pads"]:
            pad = gp["pads"][pid]
            target = min((to_gamepad((p["u"], p["v"]), pose, board) for p in pins), key=lambda c: math.dist(c, (pad["x"], pad["y"])))
            x1, y1, x2, y2 = (*pt(pad["x"], pad["y"]), *pt(*target))
            out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{colours[wire["connector"]]}" stroke-width="1.2"'
                       + (' stroke-dasharray="3,2"' if len(wire["pads"]) > 1 else '') + '/>')
    total = sum(x["length_mm"] for x in ls)
    y0 = int(h * scale + 2 * pad_px) + 4
    out.append(f'<text x="{pad_px}" y="{y0 + 10}">Pose: centre ({pose["cx"]:.1f}, {pose["cy"]:.1f}) mm, rotation {pose["rot_deg"]:.0f} deg, {"turned over" if pose.get("flip") else "component side up"}.'
               f' {len(ls)} wires, straight XY total {total:.0f} mm, longest {max(x["length_mm"] for x in ls):.0f} mm.</text>')
    out.append(f'<text x="{pad_px}" y="{y0 + 28}">XY lower bounds only: heights, housings, routing and service loops are not included. PROPOSED / NOT FOR ASSEMBLY.</text>')
    out.append(f'<text x="{pad_px}" y="{y0 + 46}">Tan: DevKitC V4 outline (27.94 x 48.26 mm, Espressif drawing) with its header pins; grey dots: gamepad test pads; dashed: unsettled pad (longer candidate used).</text>')
    lx = pad_px
    for cid, c in colours.items():
        out.append(f'<line x1="{lx}" y1="{y0 + 66}" x2="{lx + 22}" y2="{y0 + 66}" stroke="{c}" stroke-width="3"/><text x="{lx + 26}" y="{y0 + 70}">{cid}</text>')
        lx += 70
    out.append(f'<text x="{pad_px}" y="{y0 + 92}">Stick connectors (J1L, J1R) go to the S3, which is not placed yet (its size and header positions are not recorded).</text>')
    out.append("</svg>")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    best = search()
    for r in best:
        print(json.dumps(r))
