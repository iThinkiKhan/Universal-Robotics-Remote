"""Pure-Python validation of measured board geometry (no FreeCAD required).

Used by build_board_survey.py (inside FreeCAD) and by unit tests. It never
supplies a default value: geometry is built only from entries marked
"measured", and anything inconsistent raises ValueError.

Board record fields read here (measurements/boards/<board>.json):

  origin_description  non-empty text naming the datum; required before any
                      outline or hole is accepted. X right, Y up, millimetres.
  outline             {"state": "measured" | "traced", "points_mm": [...]}.
                      "traced" (e.g. read from a rectified photo) also needs
                      "method" and a positive "uncertainty_mm". The first
                      entry is the start point [x, y]. Each later entry is
                      either [x, y] (straight segment) or
                      {"to": [x, y], "via": [x, y]} (circular arc from the
                      previous point through "via" to "to"). The contour
                      closes back to the start with a straight segment.
  mounting_holes      list of {"id", "x_mm", "y_mm", "diameter_mm",
                      "state": "measured"} and, for a slot, "slot_length_mm"
                      (overall length) plus optional "angle_deg" (default 0).
                      If diameter_mm is absent, the measured reading with the
                      same id supplies it (hole "A" today).
                      Instead of a centre, a hole may give the raw caliper
                      readings "x_near_mm" and "y_near_mm": the distance from the
                      datum edges to the hole's nearest (left / lower) wall. The
                      centre is then near wall + half the hole's extent (a slot
                      needs angle_deg 0 or 90). Giving both forms is an error.

With no measured outline, measured holes are checked against and cut from the
measured W x H envelope (needs W, H and T). That body is an envelope with holes,
never the board contour, and callers must label it so.
"""
import math

ARC_STEPS = 96
BBOX_TOLERANCE_MM = 0.5     # traced outline vs measured W/H
EPS = 1e-9


def _num(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if positive and value <= 0:
        raise ValueError(f"{name} must be positive")
    return float(value)


def _pt(value, name):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{name} must be [x, y]")
    return (_num(value[0], name + " x"), _num(value[1], name + " y"))


def _arc_through(p0, pv, p1, name):
    """Return (center, radius, start_angle, signed_sweep) of the arc p0 -> pv -> p1."""
    ax, ay = p0; bx, by = pv; cx, cy = p1
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < EPS:
        raise ValueError(f"{name}: arc points are collinear")
    ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d
    uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0 = math.atan2(ay - uy, ax - ux)
    ccw = ((bx - ax) * (cy - by) - (by - ay) * (cx - bx)) > 0
    a1 = math.atan2(cy - uy, cx - ux)
    sweep = (a1 - a0) % (2 * math.pi) if ccw else -((a0 - a1) % (2 * math.pi))
    return (ux, uy), r, a0, sweep


def parse_outline(outline):
    """Return (start, segments, polygon). segments are ('line', end) or ('arc', via, end)."""
    pts = outline.get("points_mm") or []
    state = outline.get("state")
    if state not in ("measured", "traced"):
        if pts:
            raise ValueError("Outline points are present but outline.state is not 'measured' or 'traced'")
        return None
    if state == "traced":
        # A traced contour (e.g. from a rectified photo) is not a caliper reading: it must say how
        # it was made and how far to trust it.
        if not (outline.get("method") or "").strip():
            raise ValueError("A traced outline must record its method")
        u = outline.get("uncertainty_mm")
        if isinstance(u, bool) or not isinstance(u, (int, float)) or not math.isfinite(u) or u <= 0:
            raise ValueError("A traced outline must record a positive uncertainty_mm")
    if len(pts) < 3:
        raise ValueError("A measured outline needs at least three points")
    start = _pt(pts[0], "outline start")
    segments, polygon, prev = [], [start], start
    for i, entry in enumerate(pts[1:], 1):
        name = f"outline point {i}"
        if isinstance(entry, dict):
            if set(entry) != {"to", "via"}:
                raise ValueError(f"{name}: arc entries need exactly 'to' and 'via'")
            end, via = _pt(entry["to"], name), _pt(entry["via"], name + " via")
            center, r, a0, sweep = _arc_through(prev, via, end, name)
            for k in range(1, ARC_STEPS + 1):
                a = a0 + sweep * k / ARC_STEPS
                polygon.append((center[0] + r * math.cos(a), center[1] + r * math.sin(a)))
            polygon[-1] = end
            segments.append(("arc", via, end))
        else:
            end = _pt(entry, name)
            polygon.append(end)
            segments.append(("line", end))
        prev = end
    if math.hypot(polygon[-1][0] - start[0], polygon[-1][1] - start[1]) < EPS:
        polygon.pop()
        segments.pop() if segments and segments[-1][0] == "line" else None
    _check_simple(polygon)
    if abs(_area(polygon)) < 1e-6:
        raise ValueError("Outline encloses no area")
    return start, segments, polygon


def _area(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                     for i in range(len(poly)))


def _orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _check_simple(poly):
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            c, d = poly[j], poly[(j + 1) % n]
            if (_orient(a, b, c) * _orient(a, b, d) < -EPS) and (_orient(c, d, a) * _orient(c, d, b) < -EPS):
                raise ValueError("Outline crosses itself")


def _inside(poly, p):
    x, y = p
    inside = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def _pt_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0 if L2 < EPS else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def _seg_seg(a, b, c, d):
    if (_orient(a, b, c) * _orient(a, b, d) < 0) and (_orient(c, d, a) * _orient(c, d, b) < 0):
        return 0.0
    return min(_pt_seg(a, c, d), _pt_seg(b, c, d), _pt_seg(c, a, b), _pt_seg(d, a, b))


def parse_holes(survey):
    readings = {r["id"]: r for r in survey.get("readings", [])}
    holes, seen = [], set()
    for raw in survey.get("mounting_holes", []):
        hid = raw.get("id")
        if not hid or hid in seen:
            raise ValueError(f"Hole id missing or duplicated: {hid!r}")
        seen.add(hid)
        if raw.get("state") != "measured":
            continue                       # listed but not built
        dia = raw.get("diameter_mm")
        if dia is None:
            r = readings.get(hid)
            if not r or r.get("state") != "measured":
                raise ValueError(f"Hole {hid}: no measured diameter")
            dia = r["value_mm"]
        dia = _num(dia, f"hole {hid} diameter_mm", positive=True)
        length = raw.get("slot_length_mm")
        angle_deg = _num(raw.get("angle_deg", 0), f"hole {hid} angle_deg")
        if length is not None:
            length = _num(length, f"hole {hid} slot_length_mm", positive=True)
            if length < dia:
                raise ValueError(f"Hole {hid}: slot length is smaller than its width")
        centre_given = raw.get("x_mm") is not None or raw.get("y_mm") is not None
        near_given = raw.get("x_near_mm") is not None or raw.get("y_near_mm") is not None
        if centre_given and near_given:
            raise ValueError(f"Hole {hid}: give the centre (x_mm, y_mm) or near-wall readings, not both")
        if near_given:
            # Caliper readings from the datum edges to the hole's nearest (left / lower) wall.
            nx = _num(raw.get("x_near_mm"), f"hole {hid} x_near_mm")
            ny = _num(raw.get("y_near_mm"), f"hole {hid} y_near_mm")
            ex = ey = dia
            if length is not None:
                if angle_deg % 180 == 0:
                    ex = length
                elif angle_deg % 180 == 90:
                    ey = length
                else:
                    raise ValueError(f"Hole {hid}: near-wall readings need a slot angle of 0 or 90 degrees")
            x, y = nx + ex / 2, ny + ey / 2
        else:
            x, y = _num(raw.get("x_mm"), f"hole {hid} x_mm"), _num(raw.get("y_mm"), f"hole {hid} y_mm")
        if length is None:
            p1 = p2 = (x, y)
        else:
            ang = math.radians(angle_deg)
            h = (length - dia) / 2
            p1 = (x - h * math.cos(ang), y - h * math.sin(ang))
            p2 = (x + h * math.cos(ang), y + h * math.sin(ang))
        holes.append({"id": hid, "p1": p1, "p2": p2, "radius": dia / 2, "center": (x, y)})
    return holes


def resolve(survey):
    """Validate a board record. Returns {'outline', 'holes', 'volume_mm3'} (outline may be None)."""
    parsed = parse_outline(survey.get("outline", {"state": "unmeasured", "points_mm": []}))
    holes = parse_holes(survey)
    if (parsed or holes) and not (survey.get("origin_description") or "").strip():
        raise ValueError("Outline/holes require origin_description: name the datum before recording coordinates")
    result = {"outline": None, "holes": holes, "volume_mm3": None, "envelope_holes": False}
    values = {r["id"]: r["value_mm"] for r in survey.get("readings", []) if r.get("state") == "measured"}
    if not parsed and not holes:
        return result
    if parsed:
        start, segments, polygon = parsed
        xs, ys = [p[0] for p in polygon], [p[1] for p in polygon]
        bbox = (min(xs), min(ys), max(xs), max(ys))
        for key, span in (("W", bbox[2] - bbox[0]), ("H", bbox[3] - bbox[1])):
            if key in values and abs(span - values[key]) > BBOX_TOLERANCE_MM:
                raise ValueError(f"Outline {key} span {span:.2f} mm disagrees with measured {key}={values[key]} mm "
                                 f"(tolerance {BBOX_TOLERANCE_MM} mm)")
    else:
        # No measured contour yet: holes are checked against, and cut from, the measured bounding
        # rectangle only. The caller must label that body as an envelope, never as the board outline.
        if not all(k in values for k in ("W", "H", "T")):
            raise ValueError("Measured holes need a measured outline, or measured W, H and T for an envelope")
        start = None
        segments = []
        bbox = (0.0, 0.0, values["W"], values["H"])
        polygon = [(0.0, 0.0), (values["W"], 0.0), (values["W"], values["H"]), (0.0, values["H"])]
        result["envelope_holes"] = True
    for h in holes:
        for end in (h["p1"], h["p2"]):
            if not _inside(polygon, end):
                raise ValueError(f"Hole {h['id']} lies outside the outline (an edge notch belongs in the outline)")
        edges = [(polygon[i], polygon[(i + 1) % len(polygon)]) for i in range(len(polygon))]
        if min(_seg_seg(h["p1"], h["p2"], a, b) for a, b in edges) < h["radius"] - 1e-6:
            raise ValueError(f"Hole {h['id']} breaks through the outline edge")
    for i, a in enumerate(holes):
        for b in holes[i + 1:]:
            if _seg_seg(a["p1"], a["p2"], b["p1"], b["p2"]) < a["radius"] + b["radius"] - 1e-6:
                raise ValueError(f"Holes {a['id']} and {b['id']} overlap")
    thickness = values.get("T")
    area = abs(_area(polygon)) - sum(math.pi * h["radius"] ** 2 + 2 * h["radius"] * math.dist(h["p1"], h["p2"])
                                      for h in holes)
    result["net_area_mm2"] = area
    if parsed:
        result["outline"] = {"start": start, "segments": segments, "polygon": polygon, "bbox": bbox,
                             "net_area_mm2": area, "state": survey["outline"]["state"]}
    result["volume_mm3"] = area * thickness if thickness else None
    return result


# ---------------------------------------------------------------------------------------------
# Test pads: measurements/boards/<board>-pads.csv, referenced from the board record as "pads_file"
# ---------------------------------------------------------------------------------------------
PAD_SHAPES = {"round", "rect", "oval"}
PAD_STATES = {"measured", "traced"}
PAD_CONFIDENCE = {"high", "medium", "low"}
PAD_HEIGHT_MM = 0.05          # modelled copper thickness, drawn above the rear (Z=0) surface


def _csv_num(text, name, positive=False):
    try:
        value = float(str(text).strip())
    except ValueError:
        raise ValueError(f"{name} is not a number: {text!r}") from None
    return _num(value, name, positive)


def load_pads(path):
    """Read and validate a pads CSV. Returns a list of dicts with centre (x, y) and footprint (w, l) in mm.

    A round pad gives diameter_mm; rect and oval pads give width_mm (X) and length_mm (Y). A "traced"
    row (read from a photograph) must carry a method and a positive uncertainty_mm, exactly like a
    traced outline. label may be empty: an unlabeled pad is allowed and stays unlabeled.
    """
    import csv
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, restkey="_extra"))
    pads, seen = [], set()
    for row in rows:
        pid = (row.get("id") or "").strip()
        if not pid or pid in seen:
            raise ValueError(f"Pad id missing or duplicated: {pid!r}")
        seen.add(pid)
        if "_extra" in row or any(v is None for v in row.values()):
            raise ValueError(f"Pad {pid}: wrong number of columns")
        shape, state, conf = row["shape"], row["state"], row["label_confidence"]
        if shape not in PAD_SHAPES:
            raise ValueError(f"Pad {pid}: unknown shape {shape!r}")
        if state not in PAD_STATES:
            raise ValueError(f"Pad {pid}: state must be one of {sorted(PAD_STATES)}")
        if conf not in PAD_CONFIDENCE:
            raise ValueError(f"Pad {pid}: label_confidence must be one of {sorted(PAD_CONFIDENCE)}")
        x, y = _csv_num(row["x_mm"], f"pad {pid} x_mm"), _csv_num(row["y_mm"], f"pad {pid} y_mm")
        if shape == "round":
            w = l = _csv_num(row["diameter_mm"], f"pad {pid} diameter_mm", positive=True)
        else:
            w = _csv_num(row["width_mm"], f"pad {pid} width_mm", positive=True)
            l = _csv_num(row["length_mm"], f"pad {pid} length_mm", positive=True)
        unc = None
        if state == "traced":
            if not row["method"].strip():
                raise ValueError(f"Pad {pid}: a traced pad must record its method")
            unc = _csv_num(row["uncertainty_mm"], f"pad {pid} uncertainty_mm", positive=True)
        pads.append({"id": pid, "label": row["label"].strip(), "group": row["group"].strip(), "shape": shape,
                     "x": x, "y": y, "w": w, "l": l, "state": state, "confidence": conf, "uncertainty_mm": unc})
    return pads


def validate_pads(pads, result):
    """Check pads against a resolved board record: on the board, clear of its edge and holes."""
    if not pads:
        return
    if not result.get("outline"):
        raise ValueError("Pads need a measured or traced outline to be placed on")
    polygon = result["outline"]["polygon"]
    edges = [(polygon[i], polygon[(i + 1) % len(polygon)]) for i in range(len(polygon))]
    for p in pads:
        centre = (p["x"], p["y"])
        if not _inside(polygon, centre):
            raise ValueError(f"Pad {p['id']} ({p['label'] or 'unlabeled'}) lies outside the board outline")
        if min(_pt_seg(centre, a, b) for a, b in edges) < min(p["w"], p["l"]) / 2 - 0.05:
            raise ValueError(f"Pad {p['id']} ({p['label'] or 'unlabeled'}) runs over the board edge")
        for h in result["holes"]:
            if min(_pt_seg(centre, h["p1"], h["p2"]), math.dist(centre, h["center"])) < max(p["w"], p["l"]) / 2 + h["radius"] - 0.05:
                raise ValueError(f"Pad {p['id']} overlaps hole {h['id']}")
    for i, a in enumerate(pads):
        for b in pads[i + 1:]:
            if math.dist((a["x"], a["y"]), (b["x"], b["y"])) < 0.5:
                raise ValueError(f"Pads {a['id']} and {b['id']} are less than 0.5 mm apart (duplicate?)")
