# GH-Wii U002 — logic analyzer observation (2026-11-10)

## Owner-reported bench finding

The project owner constructed and operated a DIY logic analyzer. While monitoring the **large PCB pads silk-screened `SCL` and `SDA`**, the owner observed **no communication** during the sampled startup sequence and subsequent unsuccessful pairing/connection attempt. The board's indicator LEDs illuminate briefly and stop after a few seconds when no receiver connects. The owner also reports consistently stable voltage at sampled locations around the PCB after this behavior, consistent with prior ~3 V rail measurements. No new numeric voltages were provided for this session.

**Classification: owner-reported negative observation within a limited capture window.** Do not claim the physical pads are unconnected, that there is no I2C peripheral, or that no traffic can occur in other operating modes. The capture file, raw timing trace, analyzer input voltage/threshold, sample rate, trigger settings, channel mapping, and common-ground details have not been supplied. This report is not independently decoded or verified.

## Engineering implications

- Do not repurpose the gamepad's `SCL`/`SDA` pads or use them as a connector/bus without a new, positive identification.
- Further bus probing is deferred; the sampled inactivity does not block the first joystick observer test.
- Original PCB, joystick boards, ribbons, and button contacts remain intact.
- The measured joystick axes (~0–3 V, ~1.5 V center) and confirmed active-low button examples justify **planning**, not yet declaring installed, an observer harness.

## Next physical test — first joystick input (planning only)

1. Retain original gamepad battery power; unplug its USB charging lead. Keep original VCC / B+ / +5V entirely separate from the S3's 3V3 and USB supply.
2. Before wiring, establish electrical readiness: original board's L-X rail reaches 0–3 V with movement and does not exceed S3 input limits in observed startup/shutdown; establish safe power sequencing and behavior when either system is off. If uncertain, stop rather than assuming a resistor is a voltage level shifter.
3. With **both boards unpowered**, connect a common GND and a single observed signal: `L-X` pad through a **candidate 10 kΩ series resistor** to proposed S3 GPIO5 (confirm physical pin availability and firmware allocation before use). The resistor offers limited fault-current reduction, not guaranteed overvoltage protection; review ADC sampling/settling if readings are inaccurate. No other signals or power rails are connected.
4. Power S3 from USB and gamepad from its battery. Firmware must configure the GPIO as high-impedance ADC input with **no pull-up, no drive/output**, log raw ADC and filtered samples, and leave radio/actuators disabled.
5. Move only the left X axis through extremes and center. Compare ADC trend to the independent meter readings and note orientation, drift, supply voltage, startup state, and whether the gamepad rail changes under probe load. A 3 V input may not reach 4095 raw counts; use calibration, not assumed direct voltage proportionality.
6. Power down both systems and verify the signal cannot backfeed the off board. Add one input group at a time only after the first channel's behavior is reviewed.

No connection has been physically installed or verified through these notes. J1's connector family, orientation, pin1, wiring dimensions and enclosure remain TBD. Follow `docs/MEASUREMENTS.md`, `hardware/signals.json`, `electronics/harnesses.json` and Git PR review before soldering a final harness.
