"""Virtual netlist of the PROPOSED gamepad harness: gamepad pad -> tail wire -> XH pin -> S3 or WROOM-32U pin.

Built only from the records (connection list, harness registry, GPIO registry); it adds no facts. Use it to check the design before
anything is built. `python tools/harness_netlist.py` prints it, `--write` refreshes electronics/netlist-proposed.csv and `--check`
verifies that file is current.
"""
import argparse
import csv
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["wire_id", "connector", "position", "signal", "gamepad_pad", "far_board", "far_pin", "status", "gate"]


def build(root=ROOT):
    registry = json.loads((root / "hardware/signals.json").read_text(encoding="utf-8"))
    harnesses = json.loads((root / "electronics/harnesses.json").read_text(encoding="utf-8"))
    with (root / "electronics/harness-sources-proposed.csv").open(newline="", encoding="utf-8") as handle:
        sources = {(r["harness"], int(r["pin"])): r for r in csv.DictReader(handle) if r["pin"]}
    s3 = {s["id"]: s["gpio"] for s in registry["signals"]}
    wroom = {e["signal"]: e["gpio"] for e in registry["wroom"]["inputs"]}
    held = {e["signal"]: e["gpio"] for e in registry["wroom"]["reserved"]}
    rows = []
    for h in harnesses["harnesses"]:
        far = h.get("goes_to")
        for pin in sorted({p["pin"] for p in h["pins"]} | {k[1] for k in sources if k[0] == h["id"]}):
            src = sources.get((h["id"], pin))
            registry_pin = next((p for p in h["pins"] if p["pin"] == pin), None)
            signal = registry_pin["signal"] if registry_pin else src["signal"]
            if signal == "GND":
                far_pin = "GND"
            elif signal in wroom:
                far_pin = f"GPIO{wroom[signal]}"
            elif signal in held:
                far_pin = f"GPIO{held[signal]} (reserved, not wired)"
            elif s3.get(signal) is not None:
                far_pin = f"GPIO{s3[signal]}"
            else:
                far_pin = "unassigned"
            rows.append({"wire_id": f"{h['id']}-W{pin:02d}", "connector": h["id"], "position": pin,
                         "signal": signal, "gamepad_pad": src["source_pads"] if src else "",
                         "far_board": {"S3": "ESP32-S3", "WROOM-32U": "DevKitC V4 (WROOM-32U)"}.get(far, ""),
                         "far_pin": far_pin, "status": src["status"] if src else "", "gate": src["gate"] if src else ""})
    return rows


def to_csv(rows):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = to_csv(build())
    target = ROOT / "electronics/netlist-proposed.csv"
    if args.write:
        target.write_text(text, encoding="utf-8", newline="")
    elif args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            raise SystemExit("Stale netlist; run python tools/harness_netlist.py --write")
        print("Netlist matches.")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
