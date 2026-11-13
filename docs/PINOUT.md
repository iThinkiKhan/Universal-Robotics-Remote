# Pin assignments

Generated from hardware/signals.json. Proposed pins are not connection instructions.

Registry SHA-256: `7ff4202bcb600d0520df1c742b030e98bf1aae6eefd5dbf9a6a4c3875669690a`

| Signal | GPIO | Group | State |
| --- | --- | --- | --- |
| tft_sck | 12 | display | installed |
| tft_mosi | 11 | display | installed |
| tft_miso | 13 | display | installed |
| tft_cs | 10 | display | installed |
| tft_dc | 9 | display | installed |
| tft_reset | 8 | display | installed |
| touch_sck | 39 | touch | installed |
| touch_mosi | 40 | touch | installed |
| touch_miso | 41 | touch | installed |
| touch_cs | 42 | touch | installed |
| touch_irq | 47 | touch | installed |
| mic_sck | 15 | microphone | installed |
| mic_ws | 16 | microphone | installed |
| mic_sd | 17 | microphone | installed |
| backlight_reserved | 4 | backlight | reserved |
| uart_tx | 43 | console | installed |
| uart_rx | 44 | console | installed |
| L-X | 5 | gamepad | proposed |
| L-Y | 6 | gamepad | proposed |
| R-X | 7 | gamepad | proposed |
| R-Y | 2 | gamepad | proposed |
| L-3 | TBD | gamepad | proposed |
| R-3 | TBD | gamepad | proposed |
| expander_sda | 18 | expansion | proposed |
| expander_scl | 21 | expansion | proposed |

GPIO4 stays INPUT. Gamepad and expander pins are never initialized in the bench profile.
GPIO1/14/38/48 remain unallocated pending exact development-board inspection; unallocated does not prove exposed or free.

## Candidate harnesses

### J1 — Joystick observer signals (proposed)

Candidate numbering only. No power rail. Do not assemble until connector orientation and electrical compatibility are resolved.

| Candidate position | Signal | GPIO |
| --- | --- | --- |
| 1 | L-X | 5 |
| 2 | L-Y | 6 |
| 3 | R-X | 7 |
| 4 | R-Y | 2 |
| 5 | L-3 | TBD / not a GPIO |
| 6 | R-3 | TBD / not a GPIO |
| 7 | GND | TBD / not a GPIO |
| 8 | SPARE | TBD / not a GPIO |

### J2 — Buttons and shoulders (unresolved)

Inventory signals and determine direct switch vs scanned matrix first; connector count and size TBD.

### J3 — Power (unresolved)

Approved power distribution uses the original gamepad donor plug plus two removable 3V3 branches. See electronics/power/netlist.md. Physical pin numbering, viewing directions and lengths await measurement.
