# Harness package: proposal for owner review (2026-11-10, buttons added 2026-11-11)

**Status: proposal.** `hardware/signals.json` and `electronics/harnesses.json` remain the authority for signals and harness pins, as the [project plan](PROJECT_PLAN.md) and issue 5 require. This package adds three things without creating a competing pin table: where each connection lands on the board (pad IDs from the [pad table](../measurements/boards/gamepad-gh-wii-u002-pads.csv)), what has to be decided or measured before a permanent harness is built, and what can safely be ordered now. The connector pin numbers below are the registry's (J3, power, is still unresolved there).

Files: [connection list](../electronics/harness-sources-proposed.csv), [tap map](../exports/boards/gamepad-gh-wii-u002/gamepad-gh-wii-u002-harness-taps-REAR.png), [button check sheet](../measurements/templates/button-check-sheet.csv), [continuity sheet](../measurements/templates/harness-continuity-sheet.csv), [ordering list](../electronics/harness-procurement-proposed.csv) and the full [pad map](../exports/boards/gamepad-gh-wii-u002/gamepad-gh-wii-u002-pad-map-REAR.png). Every row is checked against the pad table and the registry by `tests/test_harness_package.py`.

## 1. The connections

Every stick axis, stick click and useful button has its own **free round test pad** on the rear side, so nothing has to be soldered onto a ribbon joint. Seven removable JST XH signal connectors (the owner's stock, 2.5 mm pitch, 2 to 6 positions; split approved 2026-11-11) are proposed, grouped by where the pads sit so the soldered tails stay short. Each has its own ground return.

| Connector | Carries | Lands on (pad IDs) | Goes to | Status |
| --- | --- | --- | --- | --- |
| **J1L**, 4 positions (left stick) | L-X, L-Y, L-3, GND | TP31, TP32, TP30 | S3 | **plan-ready**, electrical use gated by LX-01 |
| **J1R**, 4 positions (right stick) | R-X, R-Y, R-3, GND | TP11, TP10, TP12 | S3 | **plan-ready**, electrical use gated by LX-01 |
| **J2F**, 5 positions (face buttons) | R-UP, R-RIGHT, R-DOWN, R-LEFT (face X, A, B, Y), GND | TP19, TP20, TP22, TP21 | WROOM-32U | **plan-ready**, gated by M4 |
| **J2R**, 3 positions (right shoulders) | R-1, R-2, GND | TP58, TP59 | WROOM-32U | **plan-ready**, gated by M4 |
| **J2D**, 5 positions (D-pad) | L-UP, L-RIGHT, L-DOWN, L-LEFT, GND | TP26, TP25, TP27, TP24 | WROOM-32U | **plan-ready**, gated by M4 |
| **J2L**, 3 positions (left shoulders) | L-1, L-2, GND | TP72, TP71 | WROOM-32U | **plan-ready**, gated by M4 |
| **J2C**, 4 positions plus 1 reserved (centre) | K-+ (Plus), K-- (Minus), H (HOME), GND; position 5 reserved for POWER (K_POW) | TP73, TP69 or TP70, TP68; TP61 | WROOM-32U | K-+ and H **plan-ready**; K-- **blocked** by M4 (two candidate pads); POWER **hold** by M8 |
| each connector | Ground return | left-hand connectors (J1L, J2D, J2L, J2C): large VSS pad TP03; right-hand connectors (J1R, J2F, J2R): large GND pad TP01 | n/a | **plan-ready**: the owner checked the two pads against each other (2026-11-11) |
| **J3** | Gamepad power | B+ TP02, GND TP01, VCC, +5V TP07 | undecided | **hold**: the power circuit is undecided |
| none | SDA, SCL | TP05, TP06 | n/a | **hold**: do not connect |
| none | SYNCO, RSTN, RES, POW_DET, P_EN | TP75, TP57, TP55, TP78, TP64 | undecided | **hold** until M8: the original controller's own sync, reset and power-management points |
| retained | Both stick ribbons, both shoulder ribbons, battery lead, motor leads, USB | TP14 to TP18, TP33 to TP37, TP38 to TP45, TP48 to TP53, TP46 and TP47 | n/a | **stay intact**; recorded where they land |

Pin by pin, with the pad position of each, the list is in the [connection list](../electronics/harness-sources-proposed.csv) and drawn on the [tap map](../exports/boards/gamepad-gh-wii-u002/gamepad-gh-wii-u002-harness-taps-REAR.png). That is 4 analog axes, 2 stick clicks and 15 buttons (plus POWER, held): 21 signal wires and 7 ground returns.

**What is inferred, and how to close it.** The button names come from the printed labels: `R-UP/RIGHT/DOWN/LEFT` are taken to be the K-X, K-A, K-B and K-Y face buttons and `L-UP/RIGHT/DOWN/LEFT` the D-pad, and `H`, `K-+` and `K--` to be HOME and the two rubber-dome buttons. The voltages themselves are largely on record (`measurements/electrical.csv`, owner-reported 2026-11-10): the logic rail is about 3.0 V, all four axes swing 0 to 3 V around 1.5 V, L-3, R-3 and L-2 read about 3 V released and 0 V pressed, one face button (pad not named) does the same, and the other sampled buttons sit at about 3 V released. That pattern is one active-low line per button. What the record does not yet give is the pressed reading at each **named** pad, so the [button check sheet](../measurements/templates/button-check-sheet.csv) (M4) carries the three recorded buttons already filled in and asks only for a press-and-confirm on the other 13: does this pad drop when this button is pressed.

**S3 side.** The four axes go to the ADC pins already proposed in the registry (GPIO 5, 6, 7 and 2). Only the display, its touch controller and the microphone are wired to the S3 (GPIO 8 to 13, 39 to 42 and 47, and 15 to 17); the owner's rule (2026-11-11) is that any S3 pin not taken by the screen, the microphone or the S3's own operation (straps, native USB, the UART0 console bridge, flash and PSRAM) is free. Applied to the N16R8 that is 11 GPIOs: 1, 2, 4 (input only), 5, 6, 7, 14, 18, 21, 38 and 48; the owner read the header on 2026-11-11 and confirmed they are exposed (header order not yet recorded, M7). The four axes take 2, 5, 6 and 7. The registry now carries GPIO18 as the proposed UART receive pin from the WROOM-32U (`button_link_rx`); L-3 is proposed on GPIO21 and R-3 on GPIO1; GPIO14 stays free in case sync or reset is wired (M8).

**WROOM side.** The owner has an ESP32-DevKitC V4 carrying an ESP32-WROOM-32U (2026-11-11). The owner left the pin choice open ("choose the best ones for the job; they may move for wiring convenience"), so the registry carries a proposed mapping chosen so that each connector lands on header pins close together (the D-pad's GPIO13 is the one outlier, three positions away from the other three): face buttons on GPIO 36, 39, 34, 35; D-pad on 25, 26, 27, 13; left shoulders on 32, 33; right shoulders on 23, 22; centre buttons on 21, 19, 18; POWER reserved on GPIO4 (held, M8). GPIO34, 35, 36 and 39 are input-only with no internal pull-up, so they carry buttons the gamepad pulls up itself; if the button check (M4) shows a line floating when released, that button moves to a pin with an internal pull-up. Two pins stay spare: GPIO14 (it pulses at boot) and GPIO16 (UART2 receive, for an optional return link). No strap, flash or console pin is used. The mapping was checked on 2026-11-11 against Espressif's DevKitC V4 header tables and the WROOM-32U datasheet (recorded in `hardware/devkitc-v4-header.json`): every pin is on the header, none is a strapping, flash or console pin, and GPIO16 and 17 are free on this module. The gamepad's released level (about 3.0 V) clears the module's input-high level of 0.75 x VDD (about 2.5 V at 3.3 V), and the module's input limit of VDD + 0.3 V is why POWER (possibly battery voltage) stays unwired until M8. The UART runs from WROOM GPIO17 to S3 GPIO18; L-3 is on S3 GPIO21 and R-3 on GPIO1 (GPIO38 and 48 are avoided because an on-board RGB LED may sit on one of them). The board has its own USB for programming; its power source is undecided. Its headers are 2.54 mm pitch while XH is 2.5 mm, so XH housings do not plug straight onto them: a small carrier or perforated board with XH headers is one way to join them.

**Gamepad asleep.** If the gamepad's 3 V rail drops (auto power-off), every active-low button reads as pressed. Firmware must treat "all buttons low at once" as "gamepad off", not as input. No rail-sense wire is included in the harness.

## 2. Facts from the physical model that drive the build

- Every pad is on the **rear (component) side**, positions traced at about ±0.4 mm. The stick and button test pads are 1.2 to 1.3 mm round. Most stand at least 2.8 mm from their neighbour; the tight spots are R-1 and R-2 (about 2.2 mm apart), L-2 and the upper K-- candidate (about 1.9 mm), the left-stick row L-3, L-X, L-Y (about 2.7 mm), and L-Y, which sits about 2 mm from a motor lead pad. Ribbon rows are 1.3 mm pads at about 2.0 mm pitch and are **already occupied** by the retained ribbons. Shoulder pads are about 1.5 by 2.4 mm ovals at about 2.1 mm pitch. Power and bus pads are 1.8 to 3.0 mm.
- The original board, daughterboards and ribbons stay intact; no trace cuts and no desoldering of ribbons.
- The 3D model (survey r005) carries every pad, so routing can be studied as soon as the S3, display and battery positions are known.
- Holes B, C, D and E lie near the bottom edge close to the right-stick pads. Whether any is usable as a strain-relief anchor is a mechanical review question, not a decision here.

## 3. Proposed build principles

1. **Tap, do not replace.** Solder thin flexible leads (30 AWG silicone) to the free round test pads. No wire goes onto a ribbon-occupied pad.
2. **One removable connector** between the gamepad-side tails and the S3 or interface-board end, so the gamepad can be separated for service. The gamepad end is soldered wire with strain relief and adhesive-lined shrink.
3. **The signal connectors carry signals only.** No power rail. J3 is physically distinct and keyed differently when it exists.
4. **Label every wire** with its ID (`J1L-W03` means J1L pin 3, `J2D-W04` means J2D pin 4) and record continuity before connecting anything, using the continuity sheet.
5. **Lengths come from the routed 3D assembly**, with the service loop set in the routing review. Prototype leads are cut long and recorded.
6. **Connection order follows LX-01:** signal last when connecting, signal first when removing, with both boards powered. Protection circuitry is added when a need is measured, not by default (owner direction, 2026-11-11).
7. **Colour code** (proposed, not final): black for ground, a distinct colour per signal within each connector, and red reserved for power on J3 only.
8. **Connectors that cannot be swapped:** several connectors share a position count (J1L and J1R; J2F and J2D), and the stick connectors go to the S3 while the button connectors go to the WROOM, so they need different keying or clear physical separation at the far end (part of D1).

## 4. Connector options (needs D1)

**Update 2026-11-11:** the owner's stock is JST XH (2.5 mm pitch, 2 to 6 positions), so the 8- and 10-position GH and DF13 housings compared below are not used; see D1. The comparison and the recommendation are kept as the record of what was considered, and the GH and DF13 evaluation lots in the ordering list (B09 to B12) are no longer needed.

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

- **D1. Connector family and split. Decided by the owner (2026-11-11):** JST XH from the owner's stock (2.5 mm pitch, 2 to 6 positions). No XH connector exceeds 6 positions, so the earlier 8- and 10-position J1, J2A and J2B are replaced by the seven connectors in section 1, of 3 to 5 positions each. Housing and contact part numbers are still to be read from the stock.
- **D2. Interface architecture:** wire the stick connectors straight to the S3 header, or through a small interface board near the S3. The owner's direction (2026-11-11) is that protection circuitry is added only when a need is shown, not because it is advisable, so a protective board is not assumed; the project plan's older wording that a permanent harness waits for a protective interface is the owner's text and is to be reconciled by the owner. With the buttons included, the 7 free GPIOs left after the axes are not enough for 17 lines, so an I2C input expander was proposed. **Decided by the owner (2026-11-11), replacing the expander:** a second processor, an ESP32-WROOM-32U, reads the 16 buttons (the 12 on the front of the board, including HOME and POWER, plus the four shoulder buttons) and sends their state to the S3 over a UART. The sticks stay on the S3 with their stick clicks, so J1L and J1R are unchanged. The processor is an ESP32-DevKitC V4 carrying the WROOM-32U. The connection list has 15 of the 16 wired; the 16th, POWER, is the original controller's power key (K_POW, held) and its voltage is unmeasured (M8). The packet format, whether the link is bidirectional, and what sync and reset lines would do are undecided: the original controller's own ICs keep running, so its SYNCO and RSTN pads may be worth more than passive taps (M8). The processor is programmed over the DevKitC's own USB and its power source is undecided. The owner's direction is that backfeed and other protection are added only if a need appears, not because they are advisable, so no isolation circuit is proposed.
- **D3. Shoulder-button tap strategy:** proposed answer, for your approval: use the free round test pads L-1, L-2, R-1 and R-2 (TP72, TP71, TP58, TP59) and leave both shoulder ribbons and their solder joints untouched. The earlier options (piggyback on the ribbon pads, tap at the shoulder boards, or an inline connector in the ribbon) are then not needed.
- **D4. Ground return:** which pad is the reference and how many returns are used (one per group reduces noise). **Decided by the owner (2026-11-11):** the owner checked the large VSS pad TP03 (2.8 mm) against the large GND pad TP01 and reports it is ground, and chose it for the left-hand ground returns. J1L, J2D, J2L and J2C return to TP03 (four wires); J1R, J2F and J2R return to the large GND pad TP01 (3 mm, three wires). The small GND test pad TP54 (1.2 mm) is no longer used: it would have had to take three to five wires. Each connector keeps its own ground position.
- **D5. Layout:** where the S3, display and battery sit in the enclosure, or the measured envelopes so I can place them. This sets every length.
- **D6. Whether a permanent gamepad power harness is wanted at all.** The alternative is to leave the gamepad on its own battery and never connect its power to the S3.

## 6. Measurements still needed

- **M1. Confirm by eye** the labels beside the round pads next to the left-stick ribbon. Read from photos 3086 and 3089 on 2026-11-11 they are, from the ribbon outward, L-Y (TP32), L-X (TP31) and L-3 (TP30); the fourth pad (TP29) has no label. A glance at the board confirms it.
- **M2. Ground identity,** with every source disconnected: **done for the two pads the harness uses.** The owner checked the large VSS pad TP03 against the large GND pad TP01 and reports they are the same ground (2026-11-11, `measurements/electrical.csv` GND01; method not stated). The small GND pad TP54, the ribbon GND pads (TP17, TP36), the shoulder GND pads and the battery negative pad (TP48) are no longer needed by the harness.
- **M3. Spot-checks** with the caliper of three pad centres and the far-end diagonal, to tighten the traced positions.
- **M4. Button check. Owner decision (2026-11-11): not done pad by pad before wiring.** The owner is confident the labelled pads are the button lines; each button is confirmed instead at the first read through the button processor, and a wrong name is corrected in firmware. K-- is wired to TP69 first and moved to TP70 if it does not respond. The sheet stays as the place to record what the first read shows. Original text: finish the [button check sheet](../measurements/templates/button-check-sheet.csv). L-3, R-3 and L-2 are filled in from the recorded readings. For each of the other 13 buttons, press it and confirm its expected pad drops from about 3 V to 0 V, and note any other pad that moves (that would mean a matrix). It also settles which of TP69 and TP70 is K--.
- **M5. Heights and envelopes:** component heights near the pads, ribbon free lengths and exit directions, joystick travel, the S3, display and battery envelopes, USB access. The S3, display and microphone readings are listed in [module-readings.csv](../measurements/templates/module-readings.csv) with a [sheet](../measurements/templates/modules/) for each; the controller's battery is not placed yet, but its size is known: the owner confirmed (2026-11-12) that it is a MakerFocus 103665 pack and that its size, 65 x 36 x 10 mm nominal, is recorded in another of his enclosure projects as a plain box (not a measurement of a pack in hand; connector and wire details are not recorded). The gamepad's own original battery (BAT1) is a separate item and its size is still pending (DIM05 to DIM07).
- **M6. Battery pack:** dimensions (DIM05 to DIM07), connector pin count and wire colours, the third wire's function.
- **M7. S3 end:** which header positions are used and whether the connector is socketed or soldered.
- **M8. The original controller's own control pads:** for K_POW (TP61), SYNCO (TP75), RSTN (TP57), RES (TP55), POW_DET (TP78) and P_EN (TP64), record the DC voltage to GND with the battery disconnected and with the gamepad off, on and asleep, and whether the controller IC drives each pad (output) or reads it (input). Use a DMM only; do not drive or short any of them. K_POW may sit at battery voltage, so nothing connects to a 3.3 V input until this is recorded. The pad names alone do not establish direction or logic level.

## 7. What to order

The full list is in the [ordering list](../electronics/harness-procurement-proposed.csv).

- **Buy now (12 lines):** 30 AWG silicone wire, fine solder and flux, heat-shrink, Kapton tape, 10 kOhm resistors and 100 nF capacitors for LX-01, micro test hooks, wire labels, and a small **evaluation lot** of GH and DF13 leads and headers. None of it commits a design decision, and all of it is needed for the measurements and the first prototype.
- **Buy after a decision (7 lines):** final connectors, the crimp tool, interface-board parts, S3-side connectors, sleeving, cut-to-length wire and any shoulder-tap hardware. Each names the decision it waits for.
- **Hold (3 lines):** any gamepad power connector, anything on SDA or SCL, and any actuator or radio connector.

## 8. Test and acceptance

Use the [continuity sheet](../measurements/templates/harness-continuity-sheet.csv) for every wire, with all sources disconnected: continuity end to end, no continuity to the nearest neighbouring pad (some sit only about 2 mm away), insulation, and a pull test. The button names are confirmed at the first read (M4, owner decision). Then follow LX-01 G1 to G3 for the electrical connection.

Against issue 5's acceptance milestone, this package covers the "trace a signal from a pad to a named contact" step for 20 signals (3 on J1L, 3 on J1R, 4 on J2F, 2 on J2R, 4 on J2D, 2 on J2L, 2 on J2C) and makes every unresolved step visible. It generates one proposed WireViz drawing per connector and an [overview of all seven](../electronics/generated/overview-proposed.png) (pad, wire ID, housing position and far-end pin for every wire), and a first [3D harness model](../cad/harness/) that marks every pad the harness lands on. It does not yet provide routed 3D cables, wire lengths, a KiCad schematic or a cut list; those need D5 first.

## 9. What happens next

- At the first read through the button processor, the button rows are confirmed (or corrected) and K-- gets its pad.
- With D5, I model the S3, display and battery in the FreeCAD assembly and route the seven connectors' leads in 3D to get real lengths.
- Done 2026-11-11: the seven connectors are in `electronics/harnesses.json`, the UART receive pin replaces the expander pair in `hardware/signals.json`, and one WireViz input per connector is generated. Pin mapping proposed 2026-11-11 (section 1); a virtual netlist (`tools/harness_netlist.py`) and a model of the button link (`tools/button_link.py`) are tested without hardware. Datasheet check done 2026-11-11. Placement study r001 built 2026-11-12 (section 10). Next: measured sizes of the S3, display, microphone and battery, and the heights (M5), before anything beyond a lower bound can be said.
- The ground rows are plan-ready (M2 done for TP01 and TP03).

## 10. Placement study r001 (2026-11-12)

A first 3D placement of the button processor against the gamepad board: `cad/assembly/placement-r001.FCStd`, with the pose in `cad/assembly/placement-poses.json`, the top view in `exports/placement/placement-r001-TOP.svg`, and the maths in `scripts/cad/placement.py` (tested in `tests/test_placement.py`). It uses Espressif's DevKitC V4 dimensions drawing (27.94 x 48.26 mm, 2.54 mm pitch, 25.40 mm between the rows, header pins placed from it; recorded in `hardware/devkitc-v4-header.json`) and the surveyed gamepad board with its 83 pads.

What it is: an **XY study**. Heights are not recorded (M5), so the DevKitC is a zero-thickness outline in the gamepad's rear plane and every wire is a straight line. The lengths are lower bounds, before connector housings, strain relief, service loops or routing around parts, and they are not cut lengths.

What it found. For the 15 button wires and the 5 ground returns that end on the DevKitC, the pose of least total length with the whole board inside the gamepad's bounding rectangle (rotations in 90 degree steps, 1 mm grid) puts the DevKitC's centre at (85, 25) mm turned a quarter turn: 436 mm of wire in total, 20 mm on average, longest 59 mm. Free rotation gives only about 6 % less (410 mm), so a square-on placement costs little. By connector: J2F 178 mm (4 buttons and a ground), J2R 110 mm, J2L 64 mm, J2D 45 mm, J2C 39 mm. The two long wires (59 mm each) are the J2F and J2R ground returns, which go to the large ground pad TP01 on the far side of the board from the D-pad and centre buttons; splicing one ground tail per side, as D4 suggests, would shorten them. This is a study, not a decision: where the DevKitC really sits depends on the enclosure, the stick and component heights, and where the S3 goes.

Not placed: the S3 (so the stick wires and the UART link are not measured), the display, the microphone, the battery and the enclosure, because their sizes and header positions are not recorded, and the WROOM-32U module and the DevKitC's own components (the drawing shows a module with a PCB antenna that overhangs the board, which a WROOM-32U does not have). To go further the owner's measurements are needed: the readings in [module-readings.csv](../measurements/templates/module-readings.csv) for the S3, display and microphone, the battery once chosen, and the heights in M5.
