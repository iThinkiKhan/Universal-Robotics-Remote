# Harness package: proposal for owner review (2026-11-10, buttons added 2026-11-11)

**Status: proposal.** `hardware/signals.json` and `electronics/harnesses.json` remain the authority for signals and harness pins, as the [project plan](PROJECT_PLAN.md) and issue 5 require. This package adds three things without creating a competing pin table: where each connection lands on the board (pad IDs from the [pad table](../measurements/boards/gamepad-gh-wii-u002-pads.csv)), what has to be decided or measured before a permanent harness is built, and what can safely be ordered now. J1 pin numbers below are the registry's; J2A, J2B and J3 are not in the registry yet (the registry still lists J2 as unresolved until D1 and D2 are approved).

Files: [connection list](../electronics/harness-sources-proposed.csv), [tap map](../exports/boards/gamepad-gh-wii-u002/gamepad-gh-wii-u002-harness-taps-REAR.png), [button check sheet](../measurements/templates/button-check-sheet.csv), [continuity sheet](../measurements/templates/harness-continuity-sheet.csv), [ordering list](../electronics/harness-procurement-proposed.csv) and the full [pad map](../exports/boards/gamepad-gh-wii-u002/gamepad-gh-wii-u002-pad-map-REAR.png). Every row is checked against the pad table and the registry by `tests/test_harness_package.py`.

## 1. The connections

Every stick axis, stick click and useful button has its own **free round test pad** on the rear side, so nothing has to be soldered onto a ribbon joint. Three removable signal connectors are proposed, split by where the pads sit so the soldered tails stay short:

| Connector | Carries | Lands on (pad IDs) | Status |
| --- | --- | --- | --- |
| **J1**, 8 positions | L-X, L-Y, R-X, R-Y, L-3, R-3 | TP31, TP32, TP11, TP10, TP30, TP12 | **plan-ready**, electrical use gated by LX-01 |
| **J2A**, 8 positions (right-hand buttons) | R-UP, R-RIGHT, R-DOWN, R-LEFT (face X, A, B, Y), R-1, R-2 | TP19, TP20, TP22, TP21, TP58, TP59 | **plan-ready**, gated by M4 and D2 |
| **J2B**, 10 positions (left-hand buttons) | L-UP, L-RIGHT, L-DOWN, L-LEFT (D-pad), L-1, L-2, K-+ (Plus), H (HOME) | TP26, TP25, TP27, TP24, TP72, TP71, TP73, TP68 | **plan-ready**, gated by M4 and D2 |
| J2B pin 8 | K-- (Minus) | TP69 or TP70 | **blocked** by M4: two candidate pads |
| each connector | Ground reference | TP01 (J1, J2A), TP54 (J1, J2B) | **blocked** by M2 |
| **J3** | Gamepad power | B+ TP02, GND TP01, VCC, +5V TP07 | **hold**: no power harness until backfeed is qualified |
| none | SDA, SCL | TP05, TP06 | **hold**: do not connect |
| none | K_POW, SYNCO, RSTN, RES, POW_DET, P_EN | TP61, TP75, TP57, TP55, TP78, TP64 | **hold**: the original controller's own power, sync and reset points |
| retained | Both stick ribbons, both shoulder ribbons, battery lead, motor leads, USB | TP14 to TP18, TP33 to TP37, TP38 to TP45, TP48 to TP53, TP46 and TP47 | **stay intact**; recorded where they land |

Pin by pin, with the pad position of each, the list is in the [connection list](../electronics/harness-sources-proposed.csv) and drawn on the [tap map](../exports/boards/gamepad-gh-wii-u002/gamepad-gh-wii-u002-harness-taps-REAR.png). That is 4 analog axes, 2 stick clicks and 15 buttons: 21 signal wires and 3 ground returns.

**What is inferred, and how to close it.** The button names come from the printed labels: `R-UP/RIGHT/DOWN/LEFT` are taken to be the K-X, K-A, K-B and K-Y face buttons and `L-UP/RIGHT/DOWN/LEFT` the D-pad, and `H`, `K-+` and `K--` to be HOME and the two rubber-dome buttons. The voltages themselves are largely on record (`measurements/electrical.csv`, owner-reported 2026-11-10): the logic rail is about 3.0 V, all four axes swing 0 to 3 V around 1.5 V, L-3, R-3 and L-2 read about 3 V released and 0 V pressed, one face button (pad not named) does the same, and the other sampled buttons sit at about 3 V released. That pattern is one active-low line per button. What the record does not yet give is the pressed reading at each **named** pad, so the [button check sheet](../measurements/templates/button-check-sheet.csv) (M4) carries the three recorded buttons already filled in and asks only for a press-and-confirm on the other 13: does this pad drop when this button is pressed.

**S3 side.** The four axes go to the ADC pins already proposed in the registry (GPIO 5, 6, 7 and 2). Only the display, its touch controller and the microphone are wired to the S3 (GPIO 8 to 13, 39 to 42 and 47, and 15 to 17); the owner reports (2026-11-11) that many other S3 pins are exposed and unused, but did not record which. The registry itself leaves only GPIO 1, 14, 38 and 48 unallocated, which is fewer than the seventeen button and click lines (15 buttons plus L-3 and R-3), and it keeps GPIO 18 and 21 reserved for a possible I2C expander. So whether the buttons can go direct to S3 pins depends on a list of exposed, usable header positions that has not been taken yet. Until it is, the proposal for D2 stays as written: a small interface board beside the S3 carrying a 16-input I2C expander (15 buttons, one spare), with L-3 and R-3 on two direct GPIOs or a second expander. It is neither adopted nor ruled out. The expander part, its input thresholds against the gamepad's 3.0 V rail and the per-line protection are D2 work and are not chosen here.

**Gamepad asleep.** If the gamepad's 3 V rail drops (auto power-off), every active-low button reads as pressed. Firmware must treat "all buttons low at once" as "gamepad off", not as input. No rail-sense wire is included in the harness.

## 2. Facts from the physical model that drive the build

- Every pad is on the **rear (component) side**, positions traced at about ±0.4 mm. The stick and button test pads are 1.2 to 1.3 mm round. Most stand at least 2.8 mm from their neighbour; the tight spots are R-1 and R-2 (about 2.2 mm apart), L-2 and the upper K-- candidate (about 1.9 mm), the left-stick row L-3, L-X, L-Y (about 2.7 mm), and L-Y, which sits about 2 mm from a motor lead pad. Ribbon rows are 1.3 mm pads at about 2.0 mm pitch and are **already occupied** by the retained ribbons. Shoulder pads are about 1.5 by 2.4 mm ovals at about 2.1 mm pitch. Power and bus pads are 1.8 to 3.0 mm.
- The original board, daughterboards and ribbons stay intact; no trace cuts and no desoldering of ribbons.
- The 3D model (survey r005) carries every pad, so routing can be studied as soon as the S3, display and battery positions are known.
- Holes B, C, D and E lie near the bottom edge close to the right-stick pads. Whether any is usable as a strain-relief anchor is a mechanical review question, not a decision here.

## 3. Proposed build principles

1. **Tap, do not replace.** Solder thin flexible leads (30 AWG silicone) to the free round test pads. No wire goes onto a ribbon-occupied pad.
2. **One removable connector** between the gamepad-side tails and the S3 or interface-board end, so the gamepad can be separated for service. The gamepad end is soldered wire with strain relief and adhesive-lined shrink.
3. **J1 carries signals only.** No power rail. J3 is physically distinct and keyed differently when it exists.
4. **Label every wire** with its ID (`J1-W03` means J1 pin 3, `J2B-W05` means J2B pin 5) and record continuity before connecting anything, using the continuity sheet.
5. **Lengths come from the routed 3D assembly**, with the service loop set in the routing review. Prototype leads are cut long and recorded.
6. **Connection order follows LX-01:** signal last when connecting, signal first when removing, with both boards powered. A resistor-only interface is not power-off safe, so a permanent harness waits for a reviewed protective interface.
7. **Colour code** (proposed, not final): black for ground, a distinct colour per signal within each connector, and red reserved for power on J3 only.
8. **Connectors that cannot be swapped:** J1 and J2A are both 8 positions, so they need different keying, a different family or clear physical separation at the S3 end (part of D1).

## 4. Connector options (needs D1)

| | JST GH | Hirose DF13 |
| --- | --- | --- |
| Pitch and positions | 1.25 mm, 8-position housing GHR-08V-S (10-position housing for J2B: **verify** the part number) | 1.25 mm, 8-position housing DF13-8S-1.25C (10-position for J2B: **verify**) |
| Contact | SSHL-002T-P0.2, AWG 30 to 26 (SSHL-003 does **not** fit GH) | DF13-2630SCF, AWG 26 to 30 |
| Board-side header | SM08B-GHS-TB (side-entry SMT) | DF13A-8P-1.25H (right-angle SMT) |
| Retention | positive latch (commonly stated; **verify**) | not confirmed by my search; **verify** |
| Pre-crimped assemblies | yes (Farnell lists GHR-08V-S assemblies, 28 AWG) | yes (distributors list DF13 assemblies) |

**Recommendation for the owner to approve or reject:** use JST GH, 8 positions for J1 and J2A and 10 positions for J2B, because it is small, keyed, latching and available as pre-crimped leads, which avoids buying a crimper before the family is final. DF13 is the fallback. Both are cheap enough to evaluate side by side with the evaluation lots (B09 to B12) before D1.

I verified the part numbers and wire ranges from distributor and manufacturer datasheets, but one catalog source gave the GH wire range and I could not confirm it directly from JST. Check each "verify before ordering" note in the ordering list.

Sources: [JST GH datasheets via Farnell](https://www.farnell.com/datasheets/4803940.pdf), [Hirose DF13 catalog via Mouser](https://www.mouser.lt/datasheet/3/731/1/DF13_Catalog_en_DF13_CAT.pdf), [30 AWG silicone wire example](https://adafruit.com/products/2051).

## 5. Decisions only the owner can make

- **D1. Connector family** for the removable harness interfaces (recommendation above). The owner reports (2026-11-11) having JST connectors in two sizes on hand; series, pitch and position counts are not yet recorded, so the GH 8-position and 10-position housings above are unconfirmed against that stock.
- **D2. Interface architecture:** wire J1 straight to the S3 header, or through a small interface board with per-channel protection near the S3. The plan requires a qualified protective interface before a permanent harness; a board is the cleaner way to provide it, but it is a design task. With the buttons included, the registry's unallocated GPIOs are not enough, so the proposal is an I2C input expander on the reserved GPIO 18 and 21 on that board; the owner's report of many exposed S3 pins may change this once the usable positions are listed (see section 1).
- **D3. Shoulder-button tap strategy:** proposed answer, for your approval: use the free round test pads L-1, L-2, R-1 and R-2 (TP72, TP71, TP58, TP59) and leave both shoulder ribbons and their solder joints untouched. The earlier options (piggyback on the ribbon pads, tap at the shoulder boards, or an inline connector in the ribbon) are then not needed.
- **D4. Ground return:** which pad is the reference and how many returns are used (one per group reduces noise). Depends on M2.
- **D5. Layout:** where the S3, display and battery sit in the enclosure, or the measured envelopes so I can place them. This sets every length.
- **D6. Whether a permanent gamepad power harness is wanted at all.** The alternative is to leave the gamepad on its own battery and never connect its power to the S3.

## 6. Measurements still needed

- **M1. Confirm by eye** the labels beside the round pads next to the left-stick ribbon. Read from photos 3086 and 3089 on 2026-11-11 they are, from the ribbon outward, L-Y (TP32), L-X (TP31) and L-3 (TP30); the fourth pad (TP29) has no label. A glance at the board confirms it.
- **M2. Ground identity,** with every source disconnected: continuity between TP01, TP54, the ribbon GND pads (TP17, TP36), the shoulder GND pads and the battery negative pad (TP48).
- **M3. Spot-checks** with the caliper of three pad centres and the far-end diagonal, to tighten the traced positions.
- **M4. Button check:** finish the [button check sheet](../measurements/templates/button-check-sheet.csv). L-3, R-3 and L-2 are filled in from the recorded readings. For each of the other 13 buttons, press it and confirm its expected pad drops from about 3 V to 0 V, and note any other pad that moves (that would mean a matrix). It also settles which of TP69 and TP70 is K--.
- **M5. Heights and envelopes:** component heights near the pads, ribbon free lengths and exit directions, joystick travel, the S3, display and battery envelopes, USB access. The S3, display and microphone readings are listed in [module-readings.csv](../measurements/templates/module-readings.csv) with a [sheet](../measurements/templates/modules/) for each; the battery is not yet purchased and stays open.
- **M6. Battery pack:** dimensions (DIM05 to DIM07), connector pin count and wire colours, the third wire's function.
- **M7. S3 end:** which header positions are used and whether the connector is socketed or soldered.

## 7. What to order

The full list is in the [ordering list](../electronics/harness-procurement-proposed.csv).

- **Buy now (12 lines):** 30 AWG silicone wire, fine solder and flux, heat-shrink, Kapton tape, 10 kOhm resistors and 100 nF capacitors for LX-01, micro test hooks, wire labels, and a small **evaluation lot** of GH and DF13 leads and headers. None of it commits a design decision, and all of it is needed for the measurements and the first prototype.
- **Buy after a decision (7 lines):** final connectors, the crimp tool, interface-board parts, S3-side connectors, sleeving, cut-to-length wire and any shoulder-tap hardware. Each names the decision it waits for.
- **Hold (3 lines):** any gamepad power connector, anything on SDA or SCL, and any actuator or radio connector.

## 8. Test and acceptance

Use the [continuity sheet](../measurements/templates/harness-continuity-sheet.csv) for every wire, with all sources disconnected: continuity end to end, no continuity to the nearest neighbouring pad (some sit only about 2 mm away), insulation, and a pull test. Before any button wire is soldered, complete the button check sheet (M4). Then follow LX-01 G1 to G3 for the electrical connection.

Against issue 5's acceptance milestone, this package covers the "trace a signal from a pad to a named contact" step for 20 signals (6 on J1, 6 on J2A, 8 on J2B) and makes every unresolved step visible. It does not yet provide routed 3D cables, wire lengths, a WireViz drawing for J2A and J2B, a KiCad schematic or a cut list; those need D1, D2 and D5 first.

## 9. What happens next

- With M4, the button rows are confirmed (or corrected) and K-- gets its pad.
- With D5, I model the S3, display and battery in the FreeCAD assembly and route the J1, J2A and J2B leads in 3D to get real lengths.
- With D1 and D2, the button signals go into `hardware/signals.json`, J2A and J2B into `electronics/harnesses.json`, and the WireViz data is extended from the connection list.
- With M2, the ground rows move from blocked to plan-ready.
