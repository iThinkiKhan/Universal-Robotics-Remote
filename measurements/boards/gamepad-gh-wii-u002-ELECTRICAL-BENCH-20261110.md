# GH-Wii U002 — bench electrical observations, 2026-11-10

## Provenance and limits

These are **project-owner-reported multimeter readings** from a hands-on bench conversation, not independently witnessed or verified by an agent. Instrument make/model, calibration, uncertainty, test-point photo annotations and detailed meter response are not yet provided. See `measurements/electrical.csv` for individual entries and conditions.

The gamepad PCB, ribbons and daughterboards remained intact. The ESP32-S3 was not connected during testing. The original battery and USB charging arrangement were used for initial power readings; four-axis sweeps were explicitly measured on **battery-only power** with USB disconnected. The owner reports readings after the four pairing LEDs extinguished within seconds.

## Power observations

| Point | Reading | Conditions |
| --- | --- | --- |
| B+ vs board GND | 4.15 V | Battery connected; USB charging |
| +5V vs board GND | 5.00 V | USB charging |
| VCC near right stick vs GND | 2.99 V | Battery connected; USB charging; after LEDs stop |
| VCC near left stick vs GND | 2.99 V | Battery connected; USB charging; after LEDs stop |
| VCC near left shoulder connector vs GND | approx. 3.0 V | Battery connected; USB charging; after LEDs stop |
| VCC persistence after pairing LEDs stop | approximately 3 V remains present | Owner observes the rail remains active after LEDs stop; do not infer full shutdown/backfeed behavior |

The battery was described as initially dead. The owner reports it stayed stable and cool while charging for approximately one hour. That observation alone does not demonstrate battery condition, protection function, usable capacity, or charge termination. Battery-only B+ and USB-only behavior remain unmeasured in this record.

## Joystick sweeps

All four axes, on battery-only power, read **approximately 3.0 V at one extreme, 1.5 V at center, and 0 V at the other extreme**:

- `L-X`: 3.0 / 1.5 / 0 V
- `L-Y`: 3.0 / 1.5 / 0 V
- `R-X`: 3.0 / 1.5 / 0 V
- `R-Y`: 3.0 / 1.5 / 0 V

Physical directions for each extreme were **not** recorded. Intermediate linearity, jitter and startup transients were not characterized. Earlier right-stick center readings while USB charging were `R-X=1.47 V` and `R-Y=1.47 V`. The owner said the left equivalents were similar, without individual precision values.

## Button observations

- `L-3` and `R-3`: approximately 3 V released; approximately 0 V pressed.
- `L-2` shoulder pad, as named by owner: approximately 3 V released, 0 V pressed. Exact silkscreen spelling/position to reconcile with earlier `L2` notation and photo before harness naming.
- One face-button pad (exact label not supplied): approximately 3 V released, 0 V pressed. Do not extrapolate to all face buttons.
- Other sampled buttons: approximately 3 V **released**. Remaining pressed states not measured individually.
- Do not assume that the entire button PCB has independent ground-switched inputs. Matrix scanning, resistor networks, intermittent line activity and attached original ICs remain possible.

## Suspected serial-bus pads

- `SCL`: approximately 3 V DC at rest, after LEDs stop.
- `SDA`: approximately 3 V DC at rest, after LEDs stop.

These readings are **consistent with**, but do **not prove**, idle I2C. They do not identify devices, clock/data direction, voltage transients, connected pull-ups, or whether original ICs own the bus.

### Investigation sequence

1. For a passive check, use a **3.3 V-compatible** logic analyzer/oscilloscope with common board GND. Observe `SCL` and `SDA` during the brief startup/pairing LED interval and after timeout. Ensure analyzer channels are **inputs**, do not enable pull-ups or drive either line, and verify analyzer voltage specifications. Label and retain capture conditions.
2. Determine whether `SCL` carries a repeated clock and whether `SDA` shows synchronous transitions. If the trace decodes as I2C, record addresses/ACKs with capture evidence; no device address has yet been observed.
3. Only consider an active ESP32-S3 I2C address scan **after** proving bus voltage levels, shared-ground wiring, and safe coexistence with any original controller master. Avoid changing the original device state just to scan.
4. If signals are static, no-bus-traffic is not evidence of no device; the original processor may be idle after the LEDs stop.

## Next bench checks

1. On battery power and with S3 disconnected, record the exact face-button pad whose active-low state was just confirmed, and test a named D-pad signal and at least one additional shoulder/trigger signal released **and pressed**. Record pad label and behavior. If signal is unstable, use a logic analyzer instead of drawing conclusions from DMM average voltage.
2. With USB disconnected, measure the resting `B+` voltage. Check `VCC` with LEDs active and after timeout; record gamepad on/off states.
3. With all sources unplugged, use continuity only for targeted ground/pad confirmation as needed. Do not use resistance/continuity on a powered board.
4. Reconcile power transition and off-state behavior before designing any common-ground/observer connection to the S3; **do not bridge the original VCC, B+ or +5V rail to S3 3V3**.
5. Keep the proposed J1 joystick connector and GPIO allocations provisional until the protective interface and connector orientation are reviewed.

This document does not authorize soldering a powered harness, powering both MCUs together, cutting traces, modifying the original processor, or enabling radio/actuators.
