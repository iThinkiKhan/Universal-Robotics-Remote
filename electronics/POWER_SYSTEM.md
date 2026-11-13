# Single-pack power system

Rev G, 2026-11-13. Approved by the project owner on 2026-11-13, including the existing EGSCST switch. Use one MakerFocus 103665, one HiLetgo charger/protection board and one switched distribution point. The original gamepad gets battery voltage through its donor lead. The purchased XL63020 supplies both ESPs at 3.3 V. The existing switch opens the positive supply to both branches; the charger stays connected to the pack.

Current measurements will determine the fuse, wiring, switch loading and regulator margin before perfboard layout. The integrated power assembly has yet to be bench-tested.

## Approved connections

The diagram shows the complete power path. The [terminal netlist](power/netlist.md) identifies each external connection, including the donor connector view to record.

```text
MakerFocus external + → fuse near pack → HiLetgo B+
MakerFocus external − ─────────────────→ HiLetgo B−

HiLetgo OUT+ → existing switch COM
                  ├─ ON throw → switched supply ─┬─ donor gamepad JST lead → gamepad battery +
                  │                              └─ XL63020 VIN
                  └─ OFF throw → unused, insulated

HiLetgo OUT− ─┬─ donor gamepad JST return → gamepad battery −
              ├─ XL63020 GND
              ├─ S3 GND
              └─ WROOM GND

XL63020 VOUT, verified 3.3 V ─┬─ S3 3V3 header
                             └─ DevKitC V4 / WROOM-32U 3V3 header

USB charging → HiLetgo USB-C only, handheld switch OFF
```

Use the pack's external leads; do not open its protection wrap. The original battery is removed from this single-pack circuit. The donor JST plug/lead is retained for a removable gamepad connection; connector family, contact count and signed polarity must be confirmed from the actual parts, not inferred from wire colours or the word JST. Do not parallel the original and new packs.

All system returns use **OUT−**, including gamepad and ESP signal-reference grounds. Keep **B− separate from OUT−** in external wiring; a bridge would bypass the module's low-side protection. The actual module's OUT protection implementation and usable current remain to be checked. Its protected output is a battery-voltage supply, not a regulated 3.3 V or 5 V rail.

Split power before the gamepad. Do not route both ESP loads through the gamepad's B+ test pad, its stock battery connector or unknown board copper. Gamepad VCC and +5V pads are not ESP power sources. No original gamepad USB charging connection is used in this design.

The existing three-terminal SPDT switch is used as an on/off switch: COM to OUT+, one throw to both loads, other throw unconnected and insulated. Identify the common by continuity with all power removed; do not assume the centre terminal is common. There is no charge connection on the unused throw. Break-before-make changeover between charge and load is no longer part of this topology.

## Operating states

| Switch | HiLetgo USB | Intended behavior |
| --- | --- | --- |
| ON | Disconnected | Gamepad and ESP branches run from protected battery output |
| OFF | Disconnected | Load positive disconnected; pack and charger/protector standby drain remain |
| OFF | Connected | Pack charges; handheld loads remain off after rail discharge |
| ON | Connected | Electrically possible, but outside the chosen off-only charging procedure; switch OFF before charging |

Off-only charging is an operating rule here, not a switch-enforced interlock. Unplug the charge cable before switching ON. The TP4056 has no separate managed system power path; a simultaneous load can mask charge-current taper. Do not describe this topology as preventing USB-powered operation in ON or isolating the pack from its charger in ON.

## Parts and accepted choices

| Item | Current evidence and design choice |
| --- | --- |
| Battery | Owner-confirmed MakerFocus 103665, 3.7 V nominal, 3000 mAh / 11.1 Wh. Nominal envelope 65 × 36 × 10 mm; not a measured enclosure-fit clearance. The [MakerFocus listing](https://www.makerfocus.com/products/makerfocus-3-7v-3000mah-lithium-rechargeable-battery-1s-3c-lipo-battery-pack-of-4) describes integrated protection, about 1.5 A working current and 1.8–2.1 A overcurrent protection. Confirm actual pack identity, connector and allowed charge/discharge limits. |
| Charger | Owner-confirmed [HiLetgo B07PKND8KG](https://www.amazon.com/HiLetgo-Lithium-Charging-Protection-Functions/dp/B07PKND8KG), advertised TP4056 USB-C single-cell charger/protection board, nominal 4.2 V and up to 1 A charge current. Use B pair for pack and OUT pair for all loads. Actual board revision, charge setting and protected-output capacity remain unverified. |
| Charge setting | Retain the earlier proposed 500 mA target. MakerFocus lists 0.2C standard charge, or 600 mA for 3 Ah; this does not establish 1 A as an allowed maximum. Its voltage wording is inconsistent, so confirm the actual pack specification. Identify the fitted IC/PROG resistor before changing the board. For the cited [Top Power TP4056](https://toppwr.com/uploadfile/file/20240130/65b892bb04a3c.pdf), the prior design uses nominal 2.4 kΩ for 500 mA; verify actual CC, nominal 4.20 V CV and termination. No resistor modification or factory setting is claimed as completed. |
| Regulator | Owner purchased [EC Buying XL63020-3.3, B0D8T3J8QZ](https://www.amazon.com/dp/B0D8T3J8QZ). Seller claims TPS63020-based buck-boost, 1.8–5.5 V input, selectable 3.3/4.2/5 V and 1.3 A at 3.3 V with 3.7 V input. Nominal seller envelope 17.4 × 26.2 mm. Actual chip, jumper selection, usable current, ripple and temperature remain unverified. [TI's IC specification](https://www.ti.com/product/TPS63020) does not qualify the assembled marketplace board. |
| Switch | The existing EGSCST SPDT is the approved load switch. The listing gives 0.5 A. During sizing, compare measured battery-side operating current and inrush with the specimen's DC contact ratings. [Switch listing](https://www.amazon.com/EGSCST-Switches-Position-Miniature-Vertical/dp/B0FNK8B1YV) |
| Fuse and wiring | Near-pack fuse shown; type, rating, time-current curve, wire gauge, connector ratings and lengths remain to be selected from actual current/startup and physical routing. The fuse protects the wiring; it does not establish a higher switch current rating. |

## ESP power and existing signal design

Feed regulated 3.3 V into each board's **3V3 input**, not 5V/VIN. The S3's existing display, backlight, touch and microphone wiring stays on its rail and counts toward regulator load. Do not connect the regulator output to gamepad VCC, B+ or +5V.

Espressif permits external 3V3/GND on the [DevKitC V4](https://docs.espressif.com/projects/esp-idf/en/v5.0/esp32/hw-reference/esp32/get-started-devkitc.html) and [reference S3 DevKitC-1](https://docs.espressif.com/projects/esp-idf/en/v5.3/esp32s3/hw-reference/esp32s3/user-guide-devkitc-1.html), with USB/5V/3V3 supply options mutually exclusive. The actual S3 carrier manufacturer/revision and reverse-current behavior remain unidentified. Verify that carrier's external 3V3 power path before treating the reference schematic as its wiring.

Use removable 3V3/GND branches. Before USB programming: switch OFF, disconnect the target's external 3V3 lead, charge cable and inter-board signal connections before plugging in PC USB. One USB-powered board must not feed the shared supply through the still-connected other board. No extra isolation hardware is selected without an established need.

The power harness carries supply and return only. The S3 and WROOM signal connections are documented separately from the power circuit.

## Load budget

Use loaded voltage at regulator VIN, including switch/protector/wire drop:

**Ipack ≈ Igamepad + (3.3 V × combined 3.3 V output current) / (VIN × efficiency)**.

Examples assume VIN 3.2 V, 85% efficiency and 0.10 A gamepad current. These are assumptions, not measurements.

| Shared 3.3 V load | Estimated total pack current |
| --- | --- |
| 0.80 A | 1.07 A |
| 1.00 A | 1.31 A |
| 1.30 A | 1.68 A |

The 1.30 A example exceeds the pack's listed 1.5 A working current. At the switch's listed 0.5 A, these same assumptions leave about 0.33 A on the shared 3.3 V rail: (0.50 − 0.10) × 3.2 × 0.85 / 3.3. This is a sizing illustration. Measure actual battery-side demand from an independent rated supply path before testing the direct switch with the full load. Compare steady current, startup and inrush against the contact specification; a stable rail or a cool contact alone cannot qualify an overload.

Manufacturer guidance calls for at least a 500 mA-capable supply for each [ESP32](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/schematic-checklist.html) and [ESP32-S3](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html). This is supply-capacity guidance, not proof the two boards continuously draw 1 A. Regulator input down to 1.8 V does not establish a suitable battery discharge cutoff.

## Next engineering gates

1. **Temporary power assembly:** verify polarity/contact mapping, actual charger pads and unloaded 3.3 V output before attaching boards. Use current-limited supply/dummy loads first where available. Check the shared rail at both ESP headers under startup and operation; proposed target 3.3 V ±5% (3.135–3.465 V), subject to all attached devices' actual limits. Log current, voltage drop and thermal behavior. DMM checks establish static readings; transient/ripple claims require suitable instrumentation.
2. **Gamepad sleep/wake:** with ESP signal leads disconnected, record the same gamepad VCC pad, elapsed time and stick response before/after LED timeout and after pressing the original power key. Battery-only owner readings on November 12: pack 4.0 V, VCC 3.0 V active then off, +5V 0 V active/idle. Earlier post-LED sweeps showed response under incompletely reconfirmed power conditions. LED timeout alone is not proof of rail state. If the rail falls, investigate intact-board wake/control behavior before proposing an independent supply or any board modification.
3. **Off-only charge test:** verify charge current, CV tolerance for the actual pack, taper/termination and temperature with loads OFF. At the proposed 500 mA setting, six hours is only the ideal 3 Ah/0.5 A time before taper and thermal effects. Charger and pack settings remain pending.
4. **Sizing and integration:** use the terminal netlist to identify branch currents and measure voltage drop at the donor connector and ESP branches. After sizing, choose fuse, wire, connectors and perfboard layout. Use measured module heights and actual plug exits for the enclosure.

Record actual readings in the [bench worksheet](../measurements/templates/power-verification-20261113.csv). The [verification notes](power/verification-20261113.md) apply to this protected-output design.

## Physical integration requirements

Reserve removable battery, HiLetgo, regulator and switch bodies, mated plugs, cable bends and service access. Charger seller envelope is about 25 × 16.5 mm; thickness, USB overhang, switch travel and pin/lead clearance require actual measurements. Keep hot components clear of the pouch and provide strain relief. Bring the HiLetgo USB-C charging port to the outside; retain removable ESP service-power leads. No enclosure cutout, exact footprint, wire length or mechanical fit is established by nominal listing dimensions.
