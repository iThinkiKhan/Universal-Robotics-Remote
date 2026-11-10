# LX-01: one predictable input before a custom harness

Start with **one L-X observer**, keeping the gamepad, daughterboards and ribbons intact. The goal is to see the physical joystick move on the S3 while screen, touch and microphone remain responsive. This is a supervised diagnostic connection, not the permanent power/interface design.

The machine-readable test model is [lx-observer.json](../hardware/bench/lx-observer.json). The [connection diagram](../electronics/bench/lx-observer-proposed.svg) and its editable DOT source describe only this temporary circuit. The actual mechanical source is still the r002 **measured bounding envelope**, not an enclosure or exact PCB contour.

## What we know and what remains open

- Owner-reported readings: four axes about 0â€“3 V, centered near 1.5 V; L-3/R-3/L-2 and one unnamed face button are active-low examples. Instrument model/uncertainty and physical axis directions are unspecified. See the dated bench note and ledger.
- A DIY analyzer showed no observed activity on the large SCL/SDA pads in the reported startup/failed-pairing window. No raw capture/settings were supplied. Leave these pads disconnected; this does not prove there is no bus.
- GPIO5 is ADC1 channel 4 at the chip level. The owner separately confirmed the labelled physical GPIO5 header is accessible and unused. This is not the fifth physical header position.
- The original battery/charge behavior, off-state backfeed, every button's topology and the final protective interface remain unqualified. Unknowns stay explicit rather than becoming wiring assumptions.

## Circuit and boundaries

```text
gamepad L-X -- removable break -- 10 kÎ© --+-- S3 GPIO5 (ADC1_CH4)
                                        |
                                      100 nF
                                        |
gamepad GND ----------------------------+-- S3 GND
```

Put the ceramic 100 nF capacitor at the S3 end. There is **no connection** between gamepad B+/VCC/+5V and S3 3V3/USB power. The gamepad uses its original battery with its charging USB unplugged. The S3 uses its own USB supply. Disconnect the analyzer and other temporary signal leads for this test.

The 10 kÎ©/100 nF pair has a nominal 1 ms time constant and 159 Hz cutoff before adding the joystick's source impedance and ADC loading. It reduces noise and limits some fault current. **It neither level-shifts nor makes an unpowered GPIO safe.** A software stop or timeout also does not electrically disconnect the wire.

## G0 â€” preparation

1. Keep the gamepad completely disconnected. Verify the labelled GPIO5 header and board GND; preserve installed display/touch/microphone wiring.
2. Retain verified private recovery before loading the `bench-axis-test` build. Upload only with all external input leads disconnected.
3. The build must boot with observer sampling off. Check `status` and `selftest`; display, touch map, PSRAM and mic must remain healthy. No radio, actuator or whole-gamepad enable is introduced.
4. Have 10 kÎ©,100 nF ceramic, DMM, short removable leads and a physical signal break ready. Avoid loose contacts that can bridge adjacent pads.

## G1 â€” S3-only ground/reference test

1. Unplug S3 USB. Leave the gamepad disconnected.
2. Wire GPIO5 through 10 kÎ© to S3 GND, and 100 nF directly from GPIO5 to S3 GND. Reconnect S3 USB.
3. Start `axis start`; collect at least 5 seconds. Ground should read near the bottom of the ADC range; a provisional bench target is `mv_est`â‰¤100 mV after settling. This is a test target, not a guaranteed ADC accuracy specification. Record the actual DMM value and ADC offset.
4. Send `axis stop`. Confirm `active=0`, then `selftest`. Sampling stops; the wire is still physically attached.
5. If two extra equal 10 kÎ© resistors are available, an optional S3-only divider between its own 3V3 and GND gives a midpoint near 1.65 V. Measure that node with the DMM, feed it through the same input 10 kÎ©, and compare the ADC. Do not feed S3 3V3 directly as a3.0 V reference. A one-point ground test alone is not a full ADC calibration.
6. Disconnect the reference signal before any upload/reset or power change. Do not interpret a floating, disconnected ADC value as a joystick measurement.

## G2 â€” gamepad alone

With no S3 connection, use original battery power and unplug the charging USB. Record battery B+, VCC, and L-X low/center/high, including LED-active and timed-out states. Identify physical movement directions and the exact ground/pad. Do not use continuity/resistance on a powered circuit.

Review observed L-X against the nominal ADC range before connection; an input outside 0â€“3.1 V blocks this proposed direct test. DMM readings do not establish the absence of fast transients. If startup behavior or ground identity is uncertain, obtain an appropriate capture/measurement rather than treating the resistor as protection. Never intentionally drive the unpowered S3 through this input to discover whether it backfeeds.

## G3 â€” supervised one-axis connection

1. Power both boards off. Attach common GND, the S3-side capacitor and 10 kÎ© series path. Leave the physical break to gamepad L-X **open**.
2. Power S3 over USB, then gamepad from its battery. Check both rails and firmware readiness independently. Neither charging USB nor any other gamepad signal is attached.
3. Only with both boards powered and checked, attach the L-X signal through the resistor. This is **signal last**. Start `axis start` and use the Plan tab to see raw counts, filtered counts and estimated mV.
4. Hold low, center and high for at least 5 seconds each; repeat three returns to center. Capture direction, DMM values, median/range/jitter, raw/filtered response, supply conditions and timestamps. A3 V input is not required to equal4095 counts. Millivolts are a calibrated estimate, not an independent voltage measurement or input-protection monitor.
5. Compare the unloaded and connected gamepad readings to detect loading. Provisional diagnostic targets: continuous sensible movement; no unexplained plateau; repeat-center medians within 2% of measured ADC span; filtered held-center spread within 2% of that span; midrange ADC-vs-DMM agreement within100 mV. These are proposed bench gates, not product specifications. Investigate failure before adding channels or inventing calibration/deadbands.
6. Confirm mic acquisition, touch responsiveness and loop timing; the recorded baseline used maximum loop work under 100 ms. Stop before doing a binary screen capture; captures are rejected while the observer is active to prevent telemetry corrupting image transfers.
7. **Remove the L-X signal first while both boards are still powered.** Then stop sampling and change power or cables. Remove common ground last. If one board resets or unexpectedly loses power, remove the signal immediately and stop the test.

Do not perform a connected one-board-off experiment with this resistor-only interface. Controlled power-state qualification belongs to a reviewed interface with documented power-off tolerance/isolation. This limitation is why this temporary setup is not yet a custom harness design.

## Firmware and evidence

```sh
python -m platformio run -d firmware -e bench-axis-test
python tools/device.py --port YOUR_PORT command "axis status"
python tools/device.py --port YOUR_PORT --seconds 5 --output local/lx-ground.log command "axis start"
python tools/device.py --port YOUR_PORT command "axis stop"
```

The observer uses 12-bit ADC1 input, highest attenuation,100 Hz acquisition, an alpha 1/4 raw-count filter and 10 Hz reports. Estimated mV is derived from the **same raw sample**, with calibration source reported. The absolute session limit is 5 minutes; reboot does not re-arm. Repeated start while active is rejected. Stop resets the pin to an input with pulls disabled. Calibration/display pattern commands stop the observer; full-screen binary capture requires a prior stop. Full gamepad, button, bus and actuator functions remain disabled.

Put raw runtime records in ignored `local/`. Transcribe reviewed engineering results into the [session template](../measurements/templates/lx-observer-session.csv), keeping actual values blank until measured. Record wiring/photo reference, component tolerances, power arrangement, firmware commit/profile and reset/startup behavior. Do not publish device identities or private machine metadata in the results.

## Later stages and release gates

| Stage | Gate before moving on |
| --- | --- |
| Four analog axes | G1â€“G3 accepted for L-X; same input design reviewed for each added axis; repeat loading/noise/latency checks |
| Buttons | Exact pad identity, released/pressed behavior and topology established per input; reserved pins/expander reviewed |
| Permanent power/interface | Component-level powered/unpowered behavior, current budget, voltage protection, ground and startup/shutdown matrix verified |
| Custom removable harness | Stable signal list, protective circuit, keyed connector family, mating-face view, pin1, colors, lengths and strain relief reconciled with schematic and firmware |
| Mechanical model | Actual board contour, hole centers, component heights, module locations, datum and ribbon reach measured; native assembly/clearance review passes |
| Control transport | Receiver arming, deadman, freshness, duplicate/stale rejection and link-loss timeout tested before actuator commands |

Do not convert the current 125.5Ã—62.5Ã—1.15 mm rectangle into an exact board shape. Hole A's 4.83 mm diameter still does not locate it. Screen/S3/battery envelopes and daughterboard mounting positions remain unknown, so a detailed enclosure model would be premature.

## Primary references

- [Espressif S3 schematic guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html): ADC1 pin map and recommended 0.1 Î¼F ADC capacitor.
- [ESP-IDF 4.4.7 S3 ADC guide](https://docs.espressif.com/projects/esp-idf/en/v4.4.7/esp32s3/api-reference/peripherals/adc.html): input range, calibration and noise considerations, matching the firmware generation used here.
- [ESP32-S3 datasheet](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf): GPIO/supply limits. ADC attenuation is not permission to exceed GPIO limits or power an unpowered input.
