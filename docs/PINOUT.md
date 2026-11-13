# Pin assignments

Generated from hardware/signals.json. Proposed pins are not connection instructions.

Registry SHA-256: `00b717d0bf03229471ff0018831e78b9eabca1b10f108171174f4f4946f82484`

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
| L-3 | 21 | gamepad | proposed |
| R-3 | 1 | gamepad | proposed |
| button_link_rx | 18 | button_link | proposed |

GPIO4 stays INPUT. Gamepad and button-link pins are never initialized in the bench profile.
GPIO14/38/48 remain unallocated; unallocated does not prove exposed or free. GPIO38 and 48 may carry an on-board RGB LED, so they are not used for wired inputs.

## Button processor: ESP32-DevKitC V4 carrying an ESP32-WROOM-32U (owner-reported 2026-11-11) (proposed)

Proposed pins, movable for wiring convenience. Owner adopted the button processor on 2026-11-11 and delegated the pin choice (movable for wiring convenience). Checked on 2026-11-11 against Espressif's DevKitC V4 header tables and the WROOM-32U datasheet v2.8 (hardware/devkitc-v4-header.json): all pins used are on the headers, none is a strapping pin (GPIO0, 2, 5, 12, 15), a flash pin (6 to 11) or a console pin (1, 3), and GPIO16 and 17 are free on this module. GPIO14 is left spare because a pulse at boot is community-reported (not confirmed by Espressif). GPIO16 is left spare as the UART2 receive pin for an optional return link. GPIO34, 35, 36 and 39 are input-only with no internal pull-up, so they carry buttons that the gamepad pulls up itself (about 3.0 V released, above the 0.75 x VDD = 2.5 V input-high level); if the button check (M4) shows a line floating when released, move it to a pin with an internal pull-up. Internal pull-ups stay off until then.

UART TX to the S3 `button_link_rx` (GPIO18): WROOM GPIO17. Common ground required.

| WROOM GPIO | Signal | Connector | Note |
| --- | --- | --- | --- |
| 4 | K_POW | J2C | POWER key, held: its voltage is unmeasured and may be battery voltage (M8). Nothing is wired to this pin until M8 clears it. |
| 13 | L-LEFT | J2D |  |
| 14 | spare |  | pulses at boot; avoid for a wired line |
| 16 | spare |  | UART2 RX, for an optional return link from the S3 |
| 18 | H | J2C |  |
| 19 | K-- | J2C |  |
| 21 | K-+ | J2C |  |
| 22 | R-2 | J2R |  |
| 23 | R-1 | J2R |  |
| 25 | L-UP | J2D |  |
| 26 | L-RIGHT | J2D |  |
| 27 | L-DOWN | J2D |  |
| 32 | L-1 | J2L |  |
| 33 | L-2 | J2L |  |
| 34 | R-DOWN | J2F | input-only, no internal pull-up |
| 35 | R-LEFT | J2F | input-only, no internal pull-up |
| 36 | R-UP | J2F | input-only, no internal pull-up |
| 39 | R-RIGHT | J2F | input-only, no internal pull-up |

## Candidate harnesses

### J1L — Left stick signals (proposed, goes to S3)

Candidate numbering only. No power rail. Do not assemble until connector orientation and electrical compatibility are resolved.

| Candidate position | Signal | S3 GPIO |
| --- | --- | --- |
| 1 | L-X | 5 |
| 2 | L-Y | 6 |
| 3 | L-3 | 21 |
| 4 | GND | TBD / not a GPIO |

### J1R — Right stick signals (proposed, goes to S3)

Candidate numbering only. No power rail. Do not assemble until connector orientation and electrical compatibility are resolved.

| Candidate position | Signal | S3 GPIO |
| --- | --- | --- |
| 1 | R-X | 7 |
| 2 | R-Y | 2 |
| 3 | R-3 | 1 |
| 4 | GND | TBD / not a GPIO |

### J2F — Face buttons (proposed, goes to WROOM-32U)

Candidate numbering only. Button functions are inferred from silkscreen until the button check (M4). WROOM input pins are not assigned.

| Candidate position | Signal | S3 GPIO |
| --- | --- | --- |
| 1 | R-UP | WROOM input, not assigned |
| 2 | R-RIGHT | WROOM input, not assigned |
| 3 | R-DOWN | WROOM input, not assigned |
| 4 | R-LEFT | WROOM input, not assigned |
| 5 | GND | TBD / not a GPIO |

### J2R — Right shoulder buttons (proposed, goes to WROOM-32U)

Candidate numbering only. Taps free round test pads, not the shoulder ribbon joints. WROOM input pins are not assigned.

| Candidate position | Signal | S3 GPIO |
| --- | --- | --- |
| 1 | R-1 | WROOM input, not assigned |
| 2 | R-2 | WROOM input, not assigned |
| 3 | GND | TBD / not a GPIO |

### J2D — D-pad (proposed, goes to WROOM-32U)

Candidate numbering only. Button functions are inferred from silkscreen until the button check (M4). WROOM input pins are not assigned.

| Candidate position | Signal | S3 GPIO |
| --- | --- | --- |
| 1 | L-UP | WROOM input, not assigned |
| 2 | L-RIGHT | WROOM input, not assigned |
| 3 | L-DOWN | WROOM input, not assigned |
| 4 | L-LEFT | WROOM input, not assigned |
| 5 | GND | TBD / not a GPIO |

### J2L — Left shoulder buttons (proposed, goes to WROOM-32U)

Candidate numbering only. Taps free round test pads, not the shoulder ribbon joints. WROOM input pins are not assigned.

| Candidate position | Signal | S3 GPIO |
| --- | --- | --- |
| 1 | L-1 | WROOM input, not assigned |
| 2 | L-2 | WROOM input, not assigned |
| 3 | GND | TBD / not a GPIO |

### J2C — Centre buttons (proposed, goes to WROOM-32U)

Candidate numbering only. A fifth position is reserved in the connection list for POWER (K_POW); it is not in this registry until its voltage is measured (M8). K-- pad is unsettled between TP69 and TP70.

| Candidate position | Signal | S3 GPIO |
| --- | --- | --- |
| 1 | K-+ | WROOM input, not assigned |
| 2 | K-- | WROOM input, not assigned |
| 3 | H | WROOM input, not assigned |
| 4 | GND | TBD / not a GPIO |

### J3 — Power (unresolved)

Approved power distribution uses the original gamepad donor plug plus two removable 3V3 branches. See electronics/power/netlist.md. Physical pin numbering, viewing directions and lengths await measurement.
