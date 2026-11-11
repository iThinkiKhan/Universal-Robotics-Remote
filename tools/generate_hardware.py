"""Validate the electrical registry and generate the shared firmware pin map."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {0, 3, 19, 20, 45, 46} | set(range(22, 38))
AXES = {"L-X", "L-Y", "R-X", "R-Y"}
DESTINATIONS = {"S3", "WROOM-32U", None}
SOURCES = ROOT / "electronics/harness-sources-proposed.csv"
FAR_END = {"S3": ("S3", "ESP32-S3 N16R8 board"), "WROOM-32U": ("DEVKITC", "ESP32-DevKitC V4 (WROOM-32U)")}


def registry_digest(raw):
    """Hash UTF-8 source with LF newlines, matching the Git text contract."""
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


WROOM_STRAPS_FLASH_CONSOLE = {0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 15}


def _validate_wroom(registry, harnesses):
    """The button processor's pins: every button once, on an allowed candidate pin, with the UART and held pins kept apart."""
    w = registry.get("wroom")
    if w is None:
        raise ValueError("Registry has no wroom block")
    if w["state"] not in {"proposed", "measured", "verified"}:
        raise ValueError("Unknown WROOM connection state")
    candidates, input_only = set(w["candidates"]), set(w["input_only"])
    if candidates & WROOM_STRAPS_FLASH_CONSOLE or w["uart_tx_gpio"] in candidates:
        raise ValueError("WROOM candidates include a strap, flash, console or UART TX pin")
    if not input_only <= candidates:
        raise ValueError("WROOM input-only pins must be candidates")
    used = {}
    for entry in w["inputs"] + w["reserved"] + w["spare"]:
        gpio = entry["gpio"]
        if gpio not in candidates:
            raise ValueError(f"WROOM GPIO{gpio} is not an allowed input pin")
        if gpio in used:
            raise ValueError(f"WROOM pin conflict GPIO{gpio}: {used[gpio]} and {entry.get('signal', 'spare')}")
        used[gpio] = entry.get("signal", "spare")
    wanted = list(harnesses["wroom_inputs"])
    got = [e["signal"] for e in w["inputs"]]
    if sorted(got) != sorted(wanted):
        raise ValueError("WROOM inputs must map every button in harnesses.json exactly once")
    homes = {h["id"]: {p["signal"] for p in h["pins"]} for h in harnesses["harnesses"]}
    for e in w["inputs"]:
        if e["signal"] not in homes.get(e["connector"], set()):
            raise ValueError(f"{e['signal']} is not on connector {e['connector']}")


def validate(registry, harnesses):
    if registry.get("schema_version") != 1 or harnesses.get("schema_version") != 2:
        raise ValueError("Unsupported registry/harness schema")
    if registry.get("gamepad_enabled") is not False:
        raise ValueError("Bench profile must leave gamepad disabled pending measured interface approval")
    ids, symbols, pins = set(), set(), {}
    for signal in registry["signals"]:
        name, symbol, pin = signal["id"], signal["symbol"], signal["gpio"]
        if name in ids or symbol in symbols:
            raise ValueError(f"Duplicate signal/symbol: {name}")
        ids.add(name)
        symbols.add(symbol)
        if not symbol.isidentifier() or not signal.get("evidence"):
            raise ValueError(f"Missing evidence or invalid symbol: {name}")
        if signal["state"] not in {"installed", "reserved", "proposed", "measured", "verified"}:
            raise ValueError(f"Unknown connection state: {name}")
        if pin is None:
            if signal["state"] != "proposed":
                raise ValueError(f"Installed signal without GPIO: {name}")
            continue
        if type(pin) is not int or not 0 <= pin <= 48 or pin in FORBIDDEN:
            raise ValueError(f"Unavailable/strap/USB/memory pin: {name} GPIO{pin}")
        if pin in pins:
            raise ValueError(f"Pin conflict GPIO{pin}: {pins[pin]} and {name}")
        if pin in (43, 44) and name not in {"uart_tx", "uart_rx"}:
            raise ValueError(f"UART bridge pin reserved: {name}")
        if name in AXES and not 1 <= pin <= 10:
            raise ValueError(f"Joystick must use ADC1: {name}")
        pins[pin] = name
    by_id = {s["id"]: s for s in registry["signals"]}
    required = {"tft_sck":12,"tft_mosi":11,"tft_miso":13,"tft_cs":10,"tft_dc":9,
                "tft_reset":8,"touch_sck":39,"touch_mosi":40,"touch_miso":41,
                "touch_cs":42,"touch_irq":47,"mic_sck":15,"mic_ws":16,"mic_sd":17,
                "backlight_reserved":4,"uart_tx":43,"uart_rx":44}
    if any(by_id.get(name, {}).get("gpio") != pin for name, pin in required.items()):
        raise ValueError("Established assembly changed; revise the hardware contract before rewiring")
    if not AXES <= ids:
        raise ValueError("Missing joystick axes")
    seen_harnesses = set()
    for harness in harnesses["harnesses"]:
        if harness["id"] in seen_harnesses:
            raise ValueError("Duplicate harness ID")
        seen_harnesses.add(harness["id"])
        positions = set()
        for p in harness["pins"]:
            if type(p["pin"]) is not int or p["pin"] < 1 or p["pin"] in positions:
                raise ValueError(f"Invalid/duplicate connector position: {harness['id']}")
            positions.add(p["pin"])
            if p["signal"] not in ids | set(harnesses["wroom_inputs"]) | {"GND", "SPARE"}:
                raise ValueError(f"Unknown harness signal: {p['signal']}")
            if p["signal"] in set(harnesses["wroom_inputs"]) and harness.get("goes_to") != "WROOM-32U":
                raise ValueError(f"Button signal on a connector that does not go to the WROOM: {harness['id']}")
            if p["signal"] in ids and harness.get("goes_to") != "S3":
                raise ValueError(f"S3 signal on a connector that does not go to the S3: {harness['id']}")
        if harness.get("goes_to") not in DESTINATIONS:
            raise ValueError(f"Unknown harness destination: {harness['id']}")
        if len(harness["pins"]) > 6:
            raise ValueError(f"JST XH housings stop at 6 positions: {harness['id']}")
        if harness["state"] not in {"proposed", "unresolved"}:
            raise ValueError("Installed harness needs measured-interface review before enabling")
    _validate_wroom(registry, harnesses)


def connection_list(path=SOURCES):
    """Connection list rows keyed by (connector, position): where each wire lands on the gamepad."""
    with path.open(newline="", encoding="utf-8") as handle:
        return {(r["harness"], int(r["pin"])): r for r in csv.DictReader(handle) if r["pin"]}


def _harness_parts(registry, harnesses, sources, h):
    """One connector's drawing data: pad end, tails, XH housing, undecided board-side link, far-end pins."""
    hid = h["id"]
    by_id = {s["id"]: s for s in registry["signals"]}
    used = [p for p in h["pins"] if p["signal"] != "SPARE"]
    pads, wires, far_pins, far_labels = [], [], [], []
    for p in used:
        row = sources.get((hid, p["pin"]))
        if row is None or not row["source_pads"]:
            raise ValueError(f"No pad recorded for {hid} position {p['pin']} in the connection list")
        pads.append(row["source_pads"].replace("|", " or "))
        wires.append(f"{hid}-W{p['pin']:02d}")
        far_pins.append(p["signal"])
        if p["signal"] == "GND":
            far_labels.append("GND")
        elif p["signal"] in harnesses["wroom_inputs"]:
            gpio = next((e["gpio"] for e in registry["wroom"]["inputs"] if e["signal"] == p["signal"]), None)
            far_labels.append(f"GPIO{gpio}" if gpio is not None else "input not assigned")
        else:
            gpio = by_id[p["signal"]]["gpio"]
            far_labels.append(f"GPIO{gpio}" if gpio is not None else "GPIO not assigned")
    reserved = sorted((pin, r) for (name, pin), r in sources.items()
                      if name == hid and pin not in {p["pin"] for p in h["pins"]})
    positions = [p["pin"] for p in h["pins"]] + [pin for pin, _ in reserved]
    labels = [p["signal"] for p in h["pins"]] + [f"{r['signal']} ({r['status']}, not wired)" for _, r in reserved]
    if len(positions) > 6:
        raise ValueError(f"JST XH housings stop at 6 positions: {hid}")
    unsettled = [f"{p['signal']} pad not settled ({pad})" for p, pad in zip(used, pads) if " or " in pad]
    return {"id": hid, "used": used, "pads": pads, "wires": wires, "far_pins": far_pins, "far_labels": far_labels,
            "positions": positions, "labels": labels, "signals": [p["signal"] for p in used],
            "pad_note": "Free round test pads on the rear side / solder tails / labels read from the silkscreen"
                        + ("".join(" / " + u for u in unsettled))}


def _add_harness(doc, parts, far, pad_name, far_prefix=""):
    """Add one connector's pad group, tails, housing and board-side link to a WireViz document."""
    hid = parts["id"]
    far_name, far_type = FAR_END[far]
    n = len(parts["used"])
    doc["connectors"][pad_name] = {"type": "GH-Wii U002 test pads", "subtype": hid, "pins": parts["pads"],
                                   "pinlabels": parts["signals"], "notes": parts["pad_note"]}
    doc["connectors"][hid] = {"type": "JST XH housing", "subtype": f"{len(parts['positions'])}-position, 2.5 mm pitch",
                              "pins": parts["positions"], "pinlabels": parts["labels"],
                              "notes": "PROPOSED / owner stock, part numbers TBD / pin 1 and mating view not finalized"}
    board = doc["connectors"].setdefault(far_name, {"type": far_type, "pins": [], "pinlabels": [],
                                                    "notes": "Header positions not recorded / PROPOSED pins, nothing wired"})
    far_pins = [f"{far_prefix}{pin}" if (far_prefix and pin == "GND") else pin for pin in parts["far_pins"]]
    board["pins"] += far_pins
    board["pinlabels"] += parts["far_labels"]
    doc["cables"][f"W-{hid}"] = {"type": "Solder tails", "wirecount": n, "wirelabels": parts["wires"],
                                 "notes": "Colors, gauge and length TBD / no power rail"}
    doc["cables"][f"B-{hid}"] = {"type": "Board-side link", "wirecount": n, "wirelabels": parts["signals"],
                                 "notes": "Mating header and wiring undecided"}
    wire_numbers = list(range(1, n + 1))
    housing_pins = [p["pin"] for p in parts["used"]]
    doc["connections"] += [[{pad_name: parts["pads"]}, {f"W-{hid}": wire_numbers}, {hid: housing_pins}],
                           [{hid: housing_pins}, {f"B-{hid}": wire_numbers}, {far_name: far_pins}]]


def wireviz_inputs(registry, harnesses, sources):
    """One WireViz input per signal connector plus an overview of all of them (JSON syntax, a YAML subset)."""
    files = {}
    overview = {"metadata": {"title": "PROPOSED gamepad signal harness, all connectors \u2014 NOT FOR ASSEMBLY", "revision": "planning-3"},
                "connectors": {}, "cables": {}, "connections": []}
    for h in harnesses["harnesses"]:
        if not [p for p in h["pins"] if p["signal"] != "SPARE"]:
            continue
        parts = _harness_parts(registry, harnesses, sources, h)
        far = h["goes_to"]
        doc = {"metadata": {"title": f"{h['id']} PROPOSED {h['purpose']} harness to the {far} \u2014 NOT FOR ASSEMBLY",
                            "revision": "planning-3"},
               "connectors": {}, "cables": {}, "connections": []}
        _add_harness(doc, parts, far, "PADS")
        _add_harness(overview, parts, far, f"PADS-{h['id']}", far_prefix=f"{h['id']} ")
        files[ROOT / f"electronics/harnesses/{h['id'].lower()}-proposed.yml"] = json.dumps(doc, indent=2) + "\n"
    link = next((s for s in registry["signals"] if s["id"] == "button_link_rx"), None)
    if link and "DEVKITC" in overview["connectors"] and "S3" in overview["connectors"]:
        overview["connectors"]["DEVKITC"]["pins"] += ["UART TX", "LINK GND"]
        overview["connectors"]["DEVKITC"]["pinlabels"] += [f"GPIO{registry['wroom']['uart_tx_gpio']}", "GND"]
        overview["connectors"]["S3"]["pins"] += ["button_link_rx", "LINK GND"]
        overview["connectors"]["S3"]["pinlabels"] += [f"GPIO{link['gpio']}", "GND"]
        overview["cables"]["LINK"] = {"type": "Button link (UART)", "wirecount": 2, "wirelabels": ["button state", "GND"],
                                      "notes": "PROPOSED / connector, packet format and direction undecided / not a registered harness"}
        overview["connections"].append([{"DEVKITC": ["UART TX", "LINK GND"]}, {"LINK": [1, 2]}, {"S3": ["button_link_rx", "LINK GND"]}])
    if overview["connections"]:
        files[ROOT / "electronics/harnesses/overview-proposed.yml"] = json.dumps(overview, indent=2) + "\n"
    return files


def outputs(registry, harnesses, digest, sources=None):
    lines = ["// Generated by tools/generate_hardware.py; edit hardware/signals.json.",
             "#pragma once", "#include <Arduino.h>", "namespace Board {"]
    for s in registry["signals"]:
        lines.append(f"constexpr int {s['symbol']} = {s['gpio'] if s['gpio'] is not None else -1}; // {s['state']}")
    lines += ["constexpr uint32_t displayHz = 10000000;", "constexpr bool gamepadEnabled = false;",
              f'constexpr const char *registryHash = "{digest[:12]}";', "}", ""]
    doc = ["# Pin assignments", "", "Generated from hardware/signals.json. Proposed pins are not connection instructions.",
           "", f"Registry SHA-256: `{digest}`", "", "| Signal | GPIO | Group | State |", "| --- | --- | --- | --- |"]
    for s in registry["signals"]:
        doc.append(f"| {s['id']} | {s['gpio'] if s['gpio'] is not None else 'TBD'} | {s['group']} | {s['state']} |")
    doc += ["", "GPIO4 stays INPUT. Gamepad and button-link pins are never initialized in the bench profile.",
            "GPIO14/38/48 remain unallocated; unallocated does not prove exposed or free. GPIO38 and 48 may carry an on-board RGB LED, so they are not used for wired inputs.",
            "", "## Button processor: " + registry["wroom"]["board"] + f" ({registry['wroom']['state']})", "",
            "Proposed pins, movable for wiring convenience. " + registry["wroom"]["evidence"], "",
            f"UART TX to the S3 `button_link_rx` (GPIO{next(s['gpio'] for s in registry['signals'] if s['id'] == 'button_link_rx')}): WROOM GPIO{registry['wroom']['uart_tx_gpio']}. Common ground required.", "",
            "| WROOM GPIO | Signal | Connector | Note |", "| --- | --- | --- | --- |"]
    wroom_rows = [(e["gpio"], e["signal"], e["connector"], "input-only, no internal pull-up" if e["gpio"] in registry["wroom"]["input_only"] else "")
                  for e in registry["wroom"]["inputs"]]
    wroom_rows += [(e["gpio"], e["signal"], e["connector"], e["note"]) for e in registry["wroom"]["reserved"]]
    wroom_rows += [(e["gpio"], "spare", "", e["note"]) for e in registry["wroom"]["spare"]]
    doc += [f"| {g} | {sig} | {c} | {n} |" for g, sig, c, n in sorted(wroom_rows)]
    doc += ["", "## Candidate harnesses", ""]
    for h in harnesses["harnesses"]:
        goes = f", goes to {h['goes_to']}" if h.get("goes_to") else ""
        doc += [f"### {h['id']} — {h['purpose']} ({h['state']}{goes})", "", h["notes"], ""]
        if h["pins"]:
            doc += ["| Candidate position | Signal | S3 GPIO |", "| --- | --- | --- |"]
            by_id = {s["id"]: s for s in registry["signals"]}
            for p in h["pins"]:
                gpio = by_id.get(p["signal"], {}).get("gpio")
                if p["signal"] in harnesses["wroom_inputs"]:
                    gpio = "WROOM input, not assigned"
                doc.append(f"| {p['pin']} | {p['signal']} | {gpio if gpio is not None else 'TBD / not a GPIO'} |")
            doc.append("")
    files = wireviz_inputs(registry, harnesses, sources if sources is not None else connection_list())
    files[ROOT / "firmware/include/Board.h"] = "\n".join(lines)
    files[ROOT / "docs/PINOUT.md"] = "\n".join(doc)
    return files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raw = (ROOT / "hardware/signals.json").read_bytes()
    registry = json.loads(raw)
    harnesses = json.loads((ROOT / "electronics/harnesses.json").read_text())
    validate(registry, harnesses)
    for path, content in outputs(registry, harnesses, registry_digest(raw)).items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Stale generated file: {path}; run tools/generate_hardware.py")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    print("Hardware registry valid; generated files " + ("match." if args.check else "updated."))


if __name__ == "__main__":
    main()
