# Bench firmware 0.1.2

Four touchscreen tabs: Rig, Mic, Touch and Plan. Uses the installed ILI9341/XPT2046/INMP441 wiring. Gamepad axes, expander and control transports are disabled. Audio is processed into amplitude statistics in RAM and discarded; no recording or network speech request is made.

The normal `bench` build keeps the observer unavailable. The separate `bench-axis-test` build adds **only** the input-only GPIO5/ADC1_CH4 observer described in [LX-01](../docs/TEMP_INPUT_TEST.md). It does not start at boot. `axis start` selects the Plan page, samples at 100 Hz and reports at 10 Hz; `axis stop` stops conversions. A five-minute absolute timeout stops the session; repeated start while active is rejected. Raw counts, alpha 1/4 filtered counts and estimated mV from the same raw sample are reported. No calibration is written to NVS.

The Plan page shows the observer's active/disarmed state. Calibration/display patterns stop observation; binary capture is rejected while observation is active. Stop/timeout is not electrical isolation. Remove the external signal before resets, uploads or power changes. Other axes, buttons, expansion, radio and actuator control remain disabled.

Both the CH343 UART connector and native USB CDC accept newline commands at 115200 baud. Text output is mirrored to both. Binary capture replies go only to the requesting connector. Discover the current port with `tools/device.py ports`; configure `URR_BRIDGE_SERIAL` locally or pass `--port`. Native USB may enumerate separately.

Commands: `status`, `selftest`, `mic`, `page 0` through `page 3`, `raw on`, `raw off`, `test`, `capture`, `calibrate`, `cancel`, `axis start`, `axis stop`, `axis status`.

Existing affine touch calibration is loaded from the desktop firmware's NVS namespace. Recalibration only saves after three held targets and a fourth center check succeed. Hold each target at least 200 ms and lift fully; `cancel` preserves the existing mapping. No automatic calibration rewrite occurs on boot.

The microphone worker continuously reads the left I2S channel at 16 kHz. RMS excludes DC and is reported as percent of signed 24-bit full scale; the meter displays -60 to 0 dBFS. This is not a calibrated sound-pressure meter. Zero data, stale windows and I2S initialization/read errors are reported separately. Speak/clap and verify a change before accepting microphone function.

Rendering uses one 24-row canvas and hashes; changed bands are sent as complete pixels without a visible erase pass. Each loop renders at most one band. GRAM capture reads at most one row and transmits at most 96 bytes per loop, with a 45-second overall deadline. Touch and rendering continue during capture; other console commands wait. A capture scans the updating display and may therefore include values from different moments.

Build from the repository root:

```powershell
python tools/generate_hardware.py --check
& "$env:USERPROFILE\.platformio\penv\Scripts\platformio.exe" run -d firmware
```

PlatformIO also runs the registry check automatically before every build/upload, so stale generated pin assignments stop the build.

Upload only after the backup check in docs/RECOVERY.md:

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\platformio.exe" run -d firmware -e bench -t upload --upload-port YOUR_PORT
```

`selftest` checks flash/PSRAM sizes, a 64 KiB PSRAM pattern, display ID, valid saved touch mapping, recent nonzero microphone data, I2S read errors, disabled gamepad policy, disarmed observer and coordinate rotation. Run it after `axis stop`; an armed observer intentionally fails the disarmed-baseline check. These do not establish gamepad electrical compatibility or physical edge-touch accuracy. A display capture is controller GRAM, not a camera photograph.
