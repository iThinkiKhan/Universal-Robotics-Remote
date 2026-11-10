# GH-Wii U002 â€” logic analyzer observation (2026-11-10)

## Owner-reported bench finding

The project owner constructed and operated a DIY logic analyzer. While monitoring the **large PCB pads silk-screened `SCL` and `SDA`**, the owner observed **no communication** during the sampled startup sequence and subsequent unsuccessful pairing/connection attempt. The board's indicator LEDs illuminate briefly and stop after a few seconds when no receiver connects. The owner also reports consistently stable voltage at sampled locations around the PCB after this behavior, consistent with prior ~3 V rail measurements. No new numeric voltages were provided for this session.

**Classification: owner-reported negative observation within a limited capture window.** Do not claim the physical pads are unconnected, that there is no I2C peripheral, or that no traffic can occur in other operating modes. The capture file, raw timing trace, analyzer input voltage/threshold, sample rate, trigger settings, channel mapping, and common-ground details have not been supplied. This report is not independently decoded or verified.

## Engineering implications

- Do not repurpose the gamepad's `SCL`/`SDA` pads or use them as a connector/bus without a new, positive identification.
- Further bus probing is deferred; the sampled inactivity does not block the first joystick observer test.
- Original PCB, joystick boards, ribbons, and button contacts remain intact.
- The measured joystick axes (~0â€“3 V, ~1.5 V center) and confirmed active-low button examples justify **planning**, not yet declaring installed, an observer harness.

## Next physical test — LX-01 preparation and supervised observer

The reviewed procedure is now [LX-01](../../docs/TEMP_INPUT_TEST.md), with its explicit connection model and staged result record. Start with the S3-only ground reference while the gamepad remains disconnected. Preserve the original battery arrangement and leave the charging USB, other signals and all power-rail joins disconnected.

For the later single-axis step, install common ground with both boards off, leaving the L-X signal break open. Power and verify both devices independently, then attach L-X last through the proposed10 kΩ/100 nF input network. Remove the signal first before any reset, upload, shutdown or cable change. A series resistor and a software timeout do not provide power-off isolation; do not intentionally test a connected unpowered GPIO with this circuit. A permanent interface needs separate component-level power-state qualification.

The dedicated bench firmware starts disarmed, reads only GPIO5/ADC1_CH4 after an explicit command and retains disabled control/radio functions. Native CAD remains a measured envelope; connector family, orientation, pin1, wiring dimensions and enclosure fit remain unresolved. No physical connection is declared installed or verified by these notes.
