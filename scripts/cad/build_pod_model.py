"""Run with native freecadcmd: build the enclosure pod space-claim model from cad/enclosure/pod-r<NNN>.json.

CONCEPT / NOT FOR PRINTING. The shell is a plain box with openings, split into a tub and a flat rear lid; every module is a box
of its recorded size. There are no bosses, retainers, screws or wires, and several sizes are assumptions (see the record).

Environment: ECAD_SURVEY_PROJECT (absolute project root), ECAD_POD_REVISION (integer).
"""
import json
import os
import sys
from pathlib import Path
import FreeCAD as App
import Part

sys.path.insert(0, str(Path(os.environ.get("ECAD_SURVEY_SCRIPTS", Path(__file__).resolve().parent))))
import pod_layout

project = Path(os.environ["ECAD_SURVEY_PROJECT"]).resolve()
revision = int(os.environ["ECAD_POD_REVISION"])
key = f"pod-r{revision:03d}"
rec = json.loads((project / f"cad/enclosure/{key}.json").read_text(encoding="utf-8"))
output = project / f"cad/enclosure/{key}.FCStd"
if output.exists():
    raise RuntimeError("Existing pod model preserved. Increment the revision for a new snapshot.")
problems = pod_layout.check(rec)
if problems:
    raise RuntimeError("Layout is not consistent: " + "; ".join(problems))

ix, iy, iz = rec["interior_mm"]
w = rec["wall_mm"]
V = App.Vector


def block(x0, y0, z0, x1, y1, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cutter(opening):
    """A block through the named wall. Rect meaning per wall is given in the record."""
    a0, b0, a1, b1 = opening["rect"]
    wall = opening["wall"]
    if wall == "front":
        return block(a0, b0, -w - 1, a1, b1, 1)
    if wall == "right":
        return block(ix - 1, a0, b0, ix + w + 1, a1, b1)
    if wall == "top":
        return block(a0, iy - 1, b0, a1, iy + w + 1, b1)
    if wall == "bottom":
        return block(a0, -w - 1, b0, a1, 1, b1)
    raise RuntimeError("Unknown wall " + wall)


tub = block(-w, -w, -w, ix + w, iy + w, iz).cut(block(0, 0, 0, ix, iy, iz + 1))
for o in rec["openings"]:
    tub = tub.cut(cutter(o))
lid = block(-w, -w, iz, ix + w, iy + w, iz + w)

doc = App.newDocument("PodModel")
doc.Label = f"{key} — CONCEPT, NOT FOR PRINTING"
info = doc.addObject("App::FeaturePython", "PodRecord")
for k, v in {"State": rec["state"], "Frame": rec["frame"], "Purpose": rec["purpose"],
             "NotModelled": " | ".join(rec["not_modelled"]), "Source": f"cad/enclosure/{key}.json"}.items():
    info.addProperty("App::PropertyString", k, "Pod")
    setattr(info, k, v)

shell = doc.addObject("App::DocumentObjectGroup", "Shell")
shell.Label = "SHELL (concept)"
for name, shape, label in (("Tub", tub, "Tub: front and side walls with openings"), ("Lid", lid, "Rear lid (plain plate)")):
    o = doc.addObject("Part::Feature", name)
    o.Shape, o.Label = shape, label
    shell.addObject(o)

group = doc.addObject("App::DocumentObjectGroup", "Modules")
group.Label = f"MODULES ({len(rec['bodies'])}) — boxes of the recorded size"
shapes = {}
for b in rec["bodies"]:
    o = doc.addObject("Part::Feature", "Body_" + b["id"])
    o.Shape = block(*pod_layout.box(b))
    o.Label = f"{b['id']} {b['label']} [{b['state']}]"
    for k in ("state", "source", "note"):
        o.addProperty("App::PropertyString", k.capitalize(), "Pod")
        setattr(o, k.capitalize(), b[k])
    shapes[b["id"]] = o.Shape
    group.addObject(o)
doc.recompute()

# Independent check on the built solids: no module cuts the shell, and no two separate parts share volume.
clashes = []
for bid, shp in shapes.items():
    for name, part in (("Tub", tub), ("Lid", lid)):
        vol = shp.common(part).Volume
        if vol > 1e-6:
            clashes.append([bid, name, round(vol, 3)])
ids = sorted(shapes)
for n, a in enumerate(ids):
    for b in ids[n + 1:]:
        vol = shapes[a].common(shapes[b]).Volume
        if vol > 1e-6:
            clashes.append([a, b, round(vol, 3)])

doc.saveAs(str(output))
export = project / "exports/enclosure"
export.mkdir(parents=True, exist_ok=True)
Part.export([o for o in doc.Objects if o.TypeId == "Part::Feature"], str(export / f"{key}-CONCEPT.step"))
box = tub.fuse(lid).BoundBox
report = {"passed": not clashes and tub.isValid() and lid.isValid(), "model": output.relative_to(project).as_posix(),
          "state": rec["state"], "outside_mm": [round(box.XLength, 2), round(box.YLength, 2), round(box.ZLength, 2)],
          "tub_volume_mm3": round(tub.Volume, 1), "lid_volume_mm3": round(lid.Volume, 1),
          "modules": len(shapes), "openings": [o["id"] for o in rec["openings"]], "clashes": clashes,
          "freecad": ".".join(App.Version()[:3])}
(project / f"cad/enclosure/{key}-validation.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
print(json.dumps(report))
if not report["passed"]:
    sys.exit(1)
