# J3 power distribution — proposed terminal netlist

Approved on 2026-11-13 with [the power design](../POWER_SYSTEM.md). Each row names all terminals joined by an external conductor or splice. Names refer to electrical functions on the specimen. Physical contact numbers, colors, wire sizes and lengths remain open.

| Net | External terminals joined | Implementation |
|---|---|---|
| PACK_POS | BAT2 external positive, F1 pack side | Keep the unfused length short. Use a mating socket to preserve the removable pack. |
| PACK_FUSED | F1 carrier side, CHG1 B+ | Carries both discharge and charging current. |
| PACK_NEG | BAT2 external negative, CHG1 B− | Battery-side return. No external jumper to system ground. |
| PROTECTED_POS | CHG1 OUT+, SW1 common | Pack voltage at the charger board's load output. |
| RUN | SW1 ON throw, PAD1 battery positive via original donor pigtail, REG1 VIN | Split at the carrier. Only the gamepad branch passes through the donor plug. |
| GND | CHG1 OUT−, PAD1 battery return via donor pigtail, REG1 GND, MCU1 GND, WRM1 GND | Common system return. Pair a return with each load feed. The existing signal references meet system ground at the boards. |
| ESP_3V3 | REG1 VOUT, MCU1 verified 3V3 input, WRM1 3V3 input | Two removable power leads, one per ESP board. S3 peripherals retain their existing supply wiring. |

SW1's unused throw is insulated. CHG1 takes USB input through its own USB-C receptacle. The original gamepad USB receptacle has no external opening for normal use. The ESP USB receptacles are service connections. REG1 output selection follows the purchased board's actual configuration pads.

**Donor connector drawing convention.** Record the unplugged donor's mating face with the latch up and the wires pointing away from the viewer. Mark the contacts left to right on a photo and identify positive and return by signed voltage comparison to the original lead before reusing it. Verify any additional contact's function and preserve a required sense connection separately. Until then the diagram assigns functions only. A board-side view faces the opposite way.
