# WROOM Bluetooth input test

Standalone diagnostic for an original ESP32-WROOM-32U on a DevKitC V4. It tests
whether the intact GH-Wii U002 pairs and reports usable sticks and buttons.
Compatibility with this particular third-party board is not established yet.

Bluepad32 lists Wii U Pro controllers and compatible clones as supported, using
Bluetooth BR/EDR (Classic). The original ESP32 supports that protocol; the S3
does not. If this test succeeds, the proposed architecture is:

`original gamepad -> Bluetooth -> WROOM -> UART -> S3 display application`

That could replace the proposed stick/button taps while keeping the original
gamepad processor active. This experiment does not change the signal registry or
approve a replacement harness, power circuit, UART protocol or actuator path.

## Build

```sh
pio run -d firmware/wroom-bluetooth -e wroom-bluetooth
```

The environment pins Espressif32 7.0.1 and the official Arduino + Bluepad32 4.1.0
release archive (SHA-256
`2b4916baba6c8d4e40b0330e12dd6a21ca7b95540337e6c2d2713831ccf3c394`).
The target is `esp32dev`, with a large application partition. Use only the original
ESP32 WROOM, not the S3 bench board. Preserve and verify a full flash backup before
uploading replacement firmware; keep backups and raw identity logs private.

## Physical test

Use the WROOM's USB connection and its attached external antenna. Keep GPIO
headers disconnected. Power the gamepad with its existing battery arrangement.
This test requires no electrical connection to the gamepad or S3.

After a verified backup and upload, monitor the WROOM console at 115200 baud.
Wait for `READY`, then press the gamepad's original SYNC switch. Confirm its
pairing indication. Record discovery, connection, model and whether input reports
arrive; a connection alone does not prove a working decoder.

Move each stick separately, then exercise the D-pad, face buttons, shoulders,
stick clicks, Plus, Minus and Home. The console prints all four axes, digital
bitmasks, trigger values, battery field, update count and link age. Record physical
button labels against returned bit positions rather than assuming Nintendo labels
match Bluepad32's normalized A/B/X/Y names. POWER may turn off the controller
instead of producing an input report. Battery zero means unknown in this API.

Confirm continued operation beyond the previously observed unpaired shutdown,
then power the controller off and verify a `DISCONNECTED` event. Reconnect and
repeat a few inputs. Measure report intervals and reconnect behavior separately
before designing a receiver timeout. A short trial is not a range, latency or
failsafe qualification.

The application prints input diagnostics only. It initializes no gamepad GPIOs,
secondary UART or Wi-Fi, and sends no application rumble or LED commands. Bluepad32
still performs the controller-protocol setup required for a connection. Pairing
keys persist across resets; console `f` explicitly forgets them, `?` prints status.

## Sources

- [Bluepad32 supported controllers](https://bluepad32.readthedocs.io/en/latest/supported_gamepads/#nintendo-wii-u-pro-controller)
- [Bluepad32 Arduino platform instructions](https://bluepad32.readthedocs.io/en/latest/plat_arduino/)
- [Official core release](https://github.com/ricardoquesada/esp32-arduino-lib-builder/releases/tag/4.1.0)
- [Espressif Bluetooth overview](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/bluetooth/)
