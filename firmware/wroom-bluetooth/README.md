# WROOM Bluetooth input test

Standalone test for an original ESP32-WROOM-32U on a DevKitC V4. It checks whether the
intact GH-Wii U002 gamepad pairs with the WROOM and streams usable sticks and buttons
over Bluetooth Classic. The result below applies to **one bench unit**; other units of
this third-party board have not been tested.

If this approach is adopted, the proposed architecture is:

`original gamepad -> Bluetooth -> WROOM -> UART -> S3 display application`

That could replace the proposed stick/button taps while keeping the original gamepad
processor active. This test does not change the signal registry or approve a replacement
harness, power circuit, UART protocol or actuator path.

## Result on the bench unit (observed, one unit, 2026-11-13)

The WROOM pairs with the gamepad and receives a continuous input stream of about 110
reports per second. The link ran for more than 80 seconds on the gamepad's own battery
with no dropout (a short trial, not a range, latency or failsafe qualification).

What this clone needs, none of which Bluepad32 does by itself:

- **Limited inquiry (LIAC).** The gamepad answers inquiry only in this mode while in SYNC.
- **Name and SDP queries skipped.** They time out, so the Wii decoder is selected by an
  address-scoped profile (`w<address>`) instead of by remote identity.
- **The library's setup is replaced.** The clone answers the extension identity read with
  a 12-byte report trimmed to its real size; Bluepad32 rejects anything shorter than 22
  bytes. The firmware holds that reply back and does the setup itself: player-1 LED, then
  data reporting mode `0x3d`.
- **Only mode `0x3d` works.** Every other data reporting mode tried (`0x30`, `0x31`,
  `0x34`, with and without the continuous flag, and a zero-padded request) was
  acknowledged once and the gamepad then stopped responding at the radio level. With no
  reporting request at all it answers status polls but sends no input, consistent with a
  Wii U Pro Controller reporting through its extension.
- **The device is declared ready by the firmware.** Bluepad32 deletes a device that has
  not reached "ready" about 13 to 17 seconds after discovery, so the firmware calls the
  library's ready function once setup completes.

The reported identity is **assumed**: the profile selects the Wii parser by assuming a
Wii U Pro Controller (VID `057e` / PID `0330`). The clone returned only the extension ID
`0000A4200120` and never answered the name or SDP queries.

Decoding follows the public Wii U Pro format and is **not yet verified**: four 12-bit
little-endian axes and three button bytes. Axis values are raw counts (about 2047 at rest)
and uncalibrated. Button bytes read `ff,ff,cf` with nothing pressed. Button-to-bit mapping
has not been measured: on this bench unit the left stick and left shoulder buttons are
disconnected and the front buttons are bare PCB.

## Build

```sh
pio run -d firmware/wroom-bluetooth -e wroom-bluetooth
```

The environment pins Espressif32 7.0.1, esptool 4.9.0, and the official Arduino + Bluepad32
4.1.0 release archive (SHA-256
`2b4916baba6c8d4e40b0330e12dd6a21ca7b95540337e6c2d2713831ccf3c394`). The target is
`esp32dev`, with a large application partition. Use only the original ESP32 WROOM, not
the S3 bench board. Preserve and verify a full flash backup before uploading replacement
firmware; keep backups and raw identity logs private. If automatic download-mode entry
fails, hold BOOT, tap EN/RESET, then release BOOT. Connect without another reset
(`--before no_reset`) for the read and upload.

## Physical test

Use the WROOM's USB connection and its attached external antenna. Keep GPIO headers
disconnected. This test requires no electrical connection to the gamepad or S3, and the
gamepad may run from its own battery or its USB charge path.

1. Monitor the WROOM console at 115200 baud and wait for `READY`.
2. Enter the gamepad's address, supplied privately at runtime, as `w<address>` followed by
   a newline. Do not put device identities in source or logs that are committed.
3. Send `l` to select limited inquiry, then put the gamepad into SYNC mode (original SYNC
   switch, indicator flashing).
4. The console should print `SETUP read_reply`, `SETUP player_led=1`,
   `SETUP report_mode=3d`, `SETUP mark_ready=1`, then `INPUT` lines.

`INPUT` lines are printed only when a button byte changes or an axis moves by more than
two counts (at most 20 per second): `INPUT n= ms= lx= ly= rx= ry= b=xx,xx,xx`. A
`STREAM_STALE` line means no report arrived for a second. Record physical button labels
against returned bit positions rather than assuming Nintendo labels. The application
initializes no gamepad GPIOs, secondary UART or Wi-Fi, and its only output to the gamepad
is the player LED and data-mode requests above.

Console commands: `?` status, `d` Bluetooth stack state, `l` limited inquiry (LIAC
`0x9e8b00`), `g` general inquiry (GIAC `0x9e8b33`), `s` restart scanning, `f` forget
pairing keys, `w<address>` arm the profile for one device until reset. Inquiry selection
and the profile are temporary and reset with the board.

The gamepad often needs a power-cycle (unplug and replug, or battery out and in) between
attempts: after a dropped link it can keep answering inquiries while refusing connections.

## Sources

- [Bluepad32 supported controllers](https://bluepad32.readthedocs.io/en/latest/supported_gamepads/#nintendo-wii-u-pro-controller)
- [Bluepad32 Arduino platform instructions](https://bluepad32.readthedocs.io/en/latest/plat_arduino/)
- [Official core release](https://github.com/ricardoquesada/esp32-arduino-lib-builder/releases/tag/4.1.0)
- [Espressif Bluetooth overview](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/bluetooth/)
- [xwiimote Wii-family pairing observations](https://github.com/xwiimote/xwiimote/blob/master/doc/DEV_REMOTE)
