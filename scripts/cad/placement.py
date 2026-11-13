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


# ---------------------------------------------------------------------------------------------------------------------------------
# ESP32-S3 (r002). Frame: PCB bottom-left corner seen from the component side, antenna at the top, USB at the bottom (the owner's view).
# Header order is Espressif's DevKitC-1 order, assumed for the owner's board (hardware/esp32-s3-header.json).
S3_HEADER = ROOT / "hardware/esp32-s3-header.json"


def s3_board():
    """S3 geometry: dict with width, length (PCB only), pins (side, pos, name, gpio, u, v) and footprint rectangles in the S3 frame."""
    data = json.loads(S3_HEADER.read_text(encoding="utf-8"))
    g = data["geometry"]
    w, ln, pitch = g["pcb_width_mm"], g["pcb_length_mm"], g["pin_pitch_mm"]
    u1 = (w - g["row_centre_spacing_mm"]) / 2
    pins = []
    for side, key, u in (("J1", "j1_left", u1), ("J3", "j3_right", u1 + g["row_centre_spacing_mm"])):
        n = len(data[key])
        for e in data[key]:
            pins.append({"side": side, "pos": e["pos"], "name": e["name"], "gpio": e.get("gpio"), "u": u,
                         "v": g["first_pin_from_usb_end_mm"] + (n - e["pos"]) * pitch})
    mod_c = g["module"]["u_min"] + g["module"]["width"] / 2
    a = g["antenna_width_mm"] / 2
    pcb = [(0, 0), (w, 0), (w, ln), (0, ln)]
    ant = [(mod_c - a, ln), (mod_c + a, ln), (mod_c + a, ln + g["antenna_projection_mm"]), (mod_c - a, ln + g["antenna_projection_mm"])]
    return {"width": w, "length": ln, "pins": pins, "rects": {"pcb": pcb, "antenna": ant}, "geometry": g}


def s3_footprint(pose, board):
    """PCB and antenna rectangles in the gamepad frame (pose centre = PCB centre)."""
    return [[to_gamepad(c, pose, board) for c in r] for r in board["rects"].values()]


def _axes(poly):
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        yield (y1 - y2, x2 - x1)


def convex_overlap(a, b, gap=0.0):
    """True when two convex polygons come closer than gap (separating-axis test)."""
    for ax, ay in list(_axes(a)) + list(_axes(b)):
        n = math.hypot(ax, ay)
        pa = [(x * ax + y * ay) / n for x, y in a]
        pb = [(x * ax + y * ay) / n for x, y in b]
        if max(pa) + gap <= min(pb) or max(pb) + gap <= min(pa):
            return False
    return True


def s3_wires():
    """Wires that end on the S3: the stick connectors J1L and J1R (signals and grounds) from the harness netlist."""
    netlist = _load("harness_netlist_for_placement", "tools/harness_netlist.py")
    wires = []
    for r in netlist.build():
        if not r["far_board"].startswith("ESP32-S3") or r["status"] == "hold":
            continue
        wires.append({"wire_id": r["wire_id"], "connector": r["connector"], "signal": r["signal"],
                      "far": "GND" if r["far_pin"] == "GND" else int(r["far_pin"][4:]), "pads": r["gamepad_pad"].split("|")})
    return wires


UART_LINK = {"wire_id": "LINK-TX", "connector": "UART", "signal": "button link", "dk_gpio": 17, "s3_gpio": 18}


def s3_lengths(s3_pose, s3_brd, dk_pose, dk_brd, gp, wires=None):
    """Straight XY length of the S3 stick wires plus the UART link (DevKitC GPIO17 to S3 GPIO18). Ground takes the nearest S3 GND pin."""
    wires = wires or s3_wires()
    by_gpio = {p["gpio"]: p for p in s3_brd["pins"] if p["gpio"] is not None}
    grounds = [p for p in s3_brd["pins"] if p["name"] == "GND"]
    out = []
    for w in wires:
        cands = [to_gamepad((p["u"], p["v"]), s3_pose, s3_brd) for p in ([by_gpio[w["far"]]] if w["far"] != "GND" else grounds)]
        pad = gp["pads"][w["pads"][0]]
        out.append({**w, "length_mm": min(math.dist((pad["x"], pad["y"]), c) for c in cands)})
    dk = {p["gpio"]: p for p in dk_brd["pins"] if p["gpio"] is not None}[UART_LINK["dk_gpio"]]
    a = to_gamepad((dk["u"], dk["v"]), dk_pose, dk_brd)
    b = to_gamepad((by_gpio[UART_LINK["s3_gpio"]]["u"], by_gpio[UART_LINK["s3_gpio"]]["v"]), s3_pose, s3_brd)
    out.append({**UART_LINK, "far": UART_LINK["s3_gpio"], "pads": [], "length_mm": math.dist(a, b)})
    return out


def s3_search(dk_pose, coplanar, step_mm=2.0, rot_step=15, margin=2.0, gap=1.0):
    """Grid search for the S3 pose of least total wire length (stick wires + UART link), the whole S3 (PCB and antenna) inside the
    gamepad bounding rectangle. coplanar=True also keeps it at least gap mm clear of the DevKitC outline (same layer);
    coplanar=False allows it to overlap the DevKitC in XY (the two sit on different layers). Best pose per flip state, best first."""
    dk_brd, s3_brd, gp, wires = devkit(), s3_board(), gamepad_data(), s3_wires()
    bbox = gp["bbox"]
    dk_poly = corners(dk_pose, dk_brd)
    best = {}
    for flip in (False, True):
        for rot in range(0, 360, rot_step):
            cx = bbox[0]
            while cx <= bbox[2]:
                cy = bbox[1]
                while cy <= bbox[3]:
                    pose = {"cx": cx, "cy": cy, "rot_deg": float(rot), "flip": flip}
                    polys = s3_footprint(pose, s3_brd)
                    if all(bbox[0] + margin <= x <= bbox[2] - margin and bbox[1] + margin <= y <= bbox[3] - margin for r in polys for x, y in r)                             and not (coplanar and any(convex_overlap(r, dk_poly, gap) for r in polys)):
                        ls = s3_lengths(pose, s3_brd, dk_pose, dk_brd, gp, wires)
                        t = sum(w["length_mm"] for w in ls)
                        if flip not in best or t < best[flip][0]:
                            best[flip] = (t, max(w["length_mm"] for w in ls), pose)
                    cy += step_mm
                cx += step_mm
    return sorted(({"total_mm": t, "worst_mm": w, "pose": p} for t, w, p in best.values()), key=lambda r: r["total_mm"])


def svg_s3(dk_pose, s3_pose, path, title):
    """Top view for r002: the r001 drawing plus the S3 (PCB blue, antenna lighter) and its stick and UART wires."""
    board, s3b, gp = devkit(), s3_board(), gamepad_data()
    scale, pad_px, w, h = 8.0, 40, 125.5, 62.5

    def pt(x, y):
        return (pad_px + x * scale, pad_px + (h - y) * scale)

    def poly(points):
        return " ".join("%.1f,%.1f" % pt(*p) for p in points)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(w * scale + 2 * pad_px)}" height="{int(h * scale + 2 * pad_px + 150)}" font-family="sans-serif" font-size="11">',
           '<rect width="100%" height="100%" fill="#ffffff"/>', f'<text x="{pad_px}" y="22" font-size="14" font-weight="bold">{title}</text>',
           '<polygon fill="#d8eef2" stroke="#245" stroke-width="1.5" points="' + poly(gp["polygon"]) + '"/>']
    for pad in gp["pads"].values():
        x, y = pt(pad["x"], pad["y"])
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="#999"/>')
    out.append('<polygon fill="#f6d9a8" fill-opacity="0.55" stroke="#a60" stroke-width="1.5" points="' + poly(corners(dk_pose, board)) + '"/>')
    pcb, ant = s3_footprint(s3_pose, s3b)
    out.append('<polygon fill="#9db8e8" fill-opacity="0.55" stroke="#235" stroke-width="1.5" points="' + poly(pcb) + '"/>')
    out.append('<polygon fill="#cfdcf5" fill-opacity="0.7" stroke="#235" stroke-width="1" stroke-dasharray="4,2" points="' + poly(ant) + '"/>')
    for p in s3b["pins"]:
        x, y = pt(*to_gamepad((p["u"], p["v"]), s3_pose, s3b))
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="#235"/>')
    for p in board["pins"]:
        x, y = pt(*to_gamepad((p["u"], p["v"]), dk_pose, board))
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="#a60"/>')
    ls = s3_lengths(s3_pose, s3b, dk_pose, board, gp)
    by_gpio = {p["gpio"]: p for p in s3b["pins"] if p["gpio"] is not None}
    grounds = [p for p in s3b["pins"] if p["name"] == "GND"]
    dk_by = {p["gpio"]: p for p in board["pins"] if p["gpio"] is not None}
    for wd in ls:
        if wd["connector"] == "UART":
            a = to_gamepad((dk_by[wd["dk_gpio"]]["u"], dk_by[wd["dk_gpio"]]["v"]), dk_pose, board)
            b = to_gamepad((by_gpio[wd["s3_gpio"]]["u"], by_gpio[wd["s3_gpio"]]["v"]), s3_pose, s3b)
            colour = "#000"
        else:
            pad = gp["pads"][wd["pads"][0]]
            a = (pad["x"], pad["y"])
            cands = [to_gamepad((p["u"], p["v"]), s3_pose, s3b) for p in ([by_gpio[wd["far"]]] if wd["far"] != "GND" else grounds)]
            b = min(cands, key=lambda c: math.dist(c, a))
            colour = "#1a5fd9" if wd["connector"] == "J1L" else "#6a2fb8"
        x1, y1, x2, y2 = (*pt(*a), *pt(*b))
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{colour}" stroke-width="1.3"/>')
    total = sum(x["length_mm"] for x in ls)
    y0 = int(h * scale + 2 * pad_px) + 4
    out.append(f'<text x="{pad_px}" y="{y0 + 10}">S3 pose: PCB centre ({s3_pose["cx"]:.1f}, {s3_pose["cy"]:.1f}) mm, rotation {s3_pose["rot_deg"]:.0f} deg, {"turned over" if s3_pose.get("flip") else "component side up"}.'
               f' {len(ls)} wires (8 stick wires, 1 UART link), straight XY total {total:.0f} mm, longest {max(x["length_mm"] for x in ls):.0f} mm.</text>')
    out.append(f'<text x="{pad_px}" y="{y0 + 28}">The S3 overlaps the DevKitC in this view on purpose: with both in one layer no pose fits. Layers and heights are not assigned. XY lower bounds only. PROPOSED / NOT FOR ASSEMBLY.</text>')
    out.append(f'<text x="{pad_px}" y="{y0 + 46}">Blue: S3 PCB 28 x 57 mm (owner readings 2026-11-12), lighter dashed: antenna overhang (centring assumed). Tan: DevKitC V4. Grey dots: gamepad test pads.</text>')
    out.append(f'<text x="{pad_px}" y="{y0 + 64}">S3 header order is Espressif DevKitC-1 order, assumed for the owner board; 2.54 mm pitch is a hypothesis. Lines: J1L blue, J1R purple, UART link black.</text>')
    out.append("</svg>")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(chr(10).join(out) + chr(10), encoding="utf-8", newline=chr(10))


if __name__ == "__main__":
    best = search()
    for r in best:
        print(json.dumps(r))
