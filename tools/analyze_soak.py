"""Check continuity, resource stability and mic acquisition in a recorded bench soak."""
import argparse
import json
from pathlib import Path
import re


def fields(line):
    return dict(re.findall(r"([a-z_]+)=([^ ]+)", line))


def analyze(path, minimum_seconds=290):
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("RIG "):
            records.append({"rig":fields(line)})
        elif records:
            for prefix, key in [("DISPLAY ","display"),("MIC ","mic"),("POLICY ","policy"),("TOUCH ","touch")]:
                if line.startswith(prefix):
                    records[-1][key] = fields(line)
    if len(records) < 2 or any(not {"rig","display","mic","policy","touch"} <= r.keys() for r in records):
        raise ValueError("Need at least two complete status records")
    uptime = [int(r["rig"]["uptime_ms"]) for r in records]
    samples = [int(r["mic"]["samples"]) for r in records]
    elapsed = (uptime[-1] - uptime[0]) / 1000
    rate = (samples[-1] - samples[0]) / elapsed if elapsed > 0 else 0
    heap = [int(r["rig"]["heap"]) for r in records]
    max_loop = max(int(r["display"]["max_loop_us"]) for r in records)
    max_paint = max(int(r["display"]["max_paint_us"]) for r in records)
    checks = {
        "duration":elapsed >= minimum_seconds,
        "uptime_monotonic":all(b > a for a,b in zip(uptime,uptime[1:])),
        "one_firmware_version":len({r["rig"]["version"] for r in records}) == 1,
        "one_registry":len({r["rig"]["registry"] for r in records}) == 1,
        "memory_sizes":all(int(r["rig"]["flash"]) == 16777216 and int(r["rig"]["psram"]) >= 8000000 for r in records),
        "display_and_calibration":all(r["display"]["identified"] == "1" and r["display"]["calibrated"] == "1" for r in records),
        "mic_active":all(r["mic"]["initialized"] == "1" and int(r["mic"]["window"]) > 0 and int(r["mic"]["age_ms"]) < 1500 for r in records),
        "mic_samples_advance":all(b > a for a,b in zip(samples,samples[1:])),
        "mic_average_rate":14000 <= rate <= 18000,
        "mic_read_errors_zero":all(r["mic"]["errors"] == "0" for r in records),
        "control_paths_disabled":all(r["policy"]["gamepad_enabled"] == "0" and r["policy"]["radio_control"] == "0" for r in records),
        "no_large_heap_drift":heap[0]-heap[-1] < 4096,
        "bounded_main_loop":max_loop < 100000,
    }
    return {"passed":all(checks.values()),"checks":checks,"records":len(records),"seconds":round(elapsed,3),
            "version":records[-1]["rig"]["version"],"mic_samples_per_second":round(rate,2),
            "heap_first":heap[0],"heap_last":heap[-1],"heap_min":min(heap),"heap_max":max(heap),
            "max_loop_us":max_loop,"max_render_band_us":max_paint,
            "touch_taps_first":int(records[0]["touch"]["taps"]),"touch_taps_last":int(records[-1]["touch"]["taps"]),
            "rms_percent_min":min(float(r["mic"]["rms_pct"]) for r in records),
            "rms_percent_max":max(float(r["mic"]["rms_pct"]) for r in records)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--minimum-seconds", type=float, default=290)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = analyze(args.file, args.minimum_seconds)
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded)
    if not report["passed"]:
        raise SystemExit(1)
