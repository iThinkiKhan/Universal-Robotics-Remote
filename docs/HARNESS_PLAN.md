# Harness package: proposal for owner review (2026-11-10)

**Status: proposal.** `hardware/signals.json` and `electronics/harnesses.json` remain the authority for signals and harness pins, as the [project plan](PROJECT_PLAN.md) and issue 5 require. This package adds three things without creating a competing pin table: where each connection lands on the board (pad IDs from the [pad table](../measurements/boards/gamepad-gh-wii-u002-pads.csv)), what has to be decided or measured before a permanent harness is built, and what can safely be ordered now. J1 pin numbers below are the registry's; J2 and J3 are not in the registry yet.

Files: [connection list](../electronics/harness-sources-proposed.csv), [ordering list](../electronics/harness-procurement-proposed.csv), [continuity sheet](../measurements/templates/harness-continuity-sheet.csv), and the [pad map](../exports/boards/gamepad-gh-wii-u002/gamepad-gh-wii-u002-pad-map-REAR.png). Every row is checked against the pad table and the registry by `tests/test_harness_package.py`.

## 1. The important connections

| Group | Connection | Lands on (pad IDs) | Status |
| --- | --- | --- | --- |
| **J1** | Right stick X, Y and click, to the S3 | TP11, TP10, TP12 (labelled 1.2 mm test pads) | **plan-ready**, electrical use gated by LX-01 |
| **J1** | Left stick X, Y and click | unlabeled pads TP29 to TP32, or ribbon pads TP33/35/37 | **blocked** by M1 |
| **J1** | Ground reference | candidates TP01, TP54 | **blocked** by M2 |
| **J2** | Shoulder buttons L1, L2, R1, R2 and their grounds | SW1 pads TP42 to TP45, SW2 pads TP38 to TP41 | **blocked** by D3 and M4 |
| **J2** | Face buttons and D-pad | front-side contacts; no rear pad confirmed | **blocked** by M4 |
| **J3** | Gamepad power | B+ TP02, GND TP01, VCC, +5V TP07 | **hold**: no power harness until backfeed is qualified |
| none | SDA, SCL | TP05, TP06 | **hold**: do not connect |
| retained | Both stick ribbons, both shoulder ribbons, battery lead, motor leads, USB | TP14 to TP18, TP33 to TP37, TP38 to TP45, TP48 to TP53, TP46 and TP47 | **stay intact**; recorded where they land |

The S3 side (display, touch and microphone) is wired on the bench today. It is not part of this package yet because the connector positions and lengths depend on the enclosure layout (D5, M5); it joins the registry harness work once that exists.

**What this means in practice:** of the connections you listed, three are ready to plan today (R-X, R-Y, R-3), and even those stay behind the LX-01 gates before anything is connected. The left stick and the grounds need one measurement each. Buttons need decisions and measurements. Power waits for backfeed qualification.

## 2. Facts from the physical model that drive the build

- Every pad is on the **rear (component) side**, positions traced at about ±0.4 mm. The three right-stick test pads are 1.2 mm round, at least 2.8 mm apart. Ribbon rows are 1.3 mm pads at about 2.0 mm pitch and are **already occupied** by the retained ribbons. Shoulder pads are about 1.5 by 2.4 mm ovals at about 2.1 mm pitch. Power and bus pads are 1.8 to 3.0 mm.
- The original board, daughterboards and ribbons stay intact; no trace cuts and no desoldering of ribbons.
- The 3D model (survey r004) carries every pad, so routing can be studied as soon as the S3, display and battery positions are known.
- Holes B, C, D and E lie near the bottom edge close to the right-stick pads. Whether any is usable as a strain-relief anchor is a mechanical review question, not a decision here.

## 3. Proposed build principles

1. **Tap, do not replace.** Solder thin flexible leads (30 AWG silicone) to the labelled test pads. Do not solder onto a ribbon-occupied pad without decision D3.
2. **One removable connector** between the gamepad-side tails and the S3 or interface-board end, so the gamepad can be separated for service. The gamepad end is soldered wire with strain relief and adhesive-lined shrink.
3. **J1 carries signals only.** No power rail. J3 is physically distinct and keyed differently when it exists.
4. **Label every wire** with its ID (`J1-W03` means J1 pin 3) and record continuity before connecting anything, using the continuity sheet.
5. **Lengths come from the routed 3D assembly**, with the service loop set in the routing review. Prototype leads are cut long and recorded.
6. **Connection order follows LX-01:** signal last when connecting, signal first when removing, with both boards powered. A resistor-only interface is not power-off safe, so a permanent harness waits for a reviewed protective interface.
7. **Colour code** (proposed, not final): black for ground, a distinct colour per signal on J1, and red reserved for power on J3 only.

## 4. Connector options (needs D1)

| | JST GH | Hirose DF13 |
| --- | --- | --- |
| Pitch and positions | 1.25 mm, 8-position housing GHR-08V-S | 1.25 mm, 8-position housing DF13-8S-1.25C |
| Contact | SSHL-002T-P0.2, AWG 30 to 26 (SSHL-003 does **not** fit GH) | DF13-2630SCF, AWG 26 to 30 |
| Board-side header | SM08B-GHS-TB (side-entry SMT) | DF13A-8P-1.25H (right-angle SMT) |
| Retention | positive latch (commonly stated; **verify**) | not confirmed by my search; **verify** |
| Pre-crimped assemblies | yes (Farnell lists GHR-08V-S assemblies, 28 AWG) | yes (distributors list DF13 assemblies) |

**Recommendation for the owner to approve or reject:** use JST GH, 8 positions, for J1, because it is small, keyed, latching and available as pre-crimped leads, which avoids buying a crimper before the family is final. DF13 is the fallback. Both are cheap enough to evaluate side by side with the evaluation lots (B09 to B12) before D1.

I verified the part numbers and wire ranges from distributor and manufacturer datasheets, but one catalog source gave the GH wire range and I could not confirm it directly from JST. Check each "verify before ordering" note in the ordering list.

Sources: [JST GH datasheets via Farnell](https://www.farnell.com/datasheets/4803940.pdf), [Hirose DF13 catalog via Mouser](https://www.mouser.lt/datasheet/3/731/1/DF13_Catalog_en_DF13_CAT.pdf), [30 AWG silicone wire example](https://adafruit.com/products/2051).

## 5. Decisions only the owner can make

- **D1. Connector family** for the removable harness interfaces (recommendation above).
- **D2. Interface architecture:** wire J1 straight to the S3 header, or through a small interface board with per-channel protection near the S3. The plan requires a qualified protective interface before a permanent harness; a board is the cleaner way to provide it, but it is a design task.
- **D3. Shoulder-button tap strategy:** piggyback on the ribbon's own pads, tap at the shoulder boards, or put an inline connector in the retained ribbon. The last one modifies a retained assembly and needs your explicit approval.
- **D4. Ground return:** which pad is the reference and how many returns are used (one per group reduces noise). Depends on M2.
- **D5. Layout:** where the S3, display and battery sit in the enclosure, or the measured envelopes so I can place them. This sets every length.
- **D6. Whether a permanent gamepad power harness is wanted at all.** The alternative is to leave the gamepad on its own battery and never connect its power to the S3.

## 6. Measurements still needed

- **M1. Read the printed labels** beside the four unlabeled round pads (TP29 to TP32) next to the left-stick ribbon. This unlocks L-X, L-Y and L-3.
- **M2. Ground identity,** with every source disconnected: continuity between TP01, TP54, the ribbon GND pads (TP17, TP36), the shoulder GND pads and the battery negative pad (TP48).
- **M3. Spot-checks** with the caliper of three pad centres and the far-end diagonal, to tighten the traced positions.
- **M4. Button behaviour:** released and pressed voltage for L1, L2, R1, R2 and each face and D-pad contact, and whether they are direct switches or a matrix.
- **M5. Heights and envelopes:** component heights near the pads, ribbon free lengths and exit directions, joystick travel, the S3, display and battery envelopes, USB access.
- **M6. Battery pack:** dimensions (DIM05 to DIM07), connector pin count and wire colours, the third wire's function.
- **M7. S3 end:** which header positions are used and whether the connector is socketed or soldered.

## 7. What to order

The full list is in the [ordering list](../electronics/harness-procurement-proposed.csv).

- **Buy now (12 lines):** 30 AWG silicone wire, fine solder and flux, heat-shrink, Kapton tape, 10 kOhm resistors and 100 nF capacitors for LX-01, micro test hooks, wire labels, and a small **evaluation lot** of GH and DF13 leads and headers. None of it commits a design decision, and all of it is needed for the measurements and the first prototype.
- **Buy after a decision (7 lines):** final connectors, the crimp tool, interface-board parts, S3-side connectors, sleeving, cut-to-length wire and any shoulder-tap hardware. Each names the decision it waits for.
- **Hold (3 lines):** any gamepad power connector, anything on SDA or SCL, and any actuator or radio connector.

## 8. Test and acceptance

Use the [continuity sheet](../measurements/templates/harness-continuity-sheet.csv) for every wire, with all sources disconnected: continuity end to end, no continuity to the neighbouring pad (they sit at 2 mm pitch), insulation, and a pull test. Then follow LX-01 G1 to G3 for the electrical connection.

Against issue 5's acceptance milestone, this package covers the "trace a signal from a pad to a named contact" step for three signals and makes every unresolved step visible. It does not yet provide routed 3D cables, WireViz drawings, a KiCad schematic or a cut list; those need D1, D2 and D5 first.

## 9. What happens next

- With D5, I model the S3, display and battery in the FreeCAD assembly and route the J1 leads in 3D to get real lengths.
- With D1 and D2, the harness registry and WireViz data can be extended from the connection list.
- With M1 and M2, the left stick and ground rows move from blocked to plan-ready.
