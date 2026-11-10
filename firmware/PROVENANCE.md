# Reused hardware drivers

Imported on 2026-11-09 from the authoritative existing project `the private original desktop project`:

- `include/Calibration.h`, `include/Layout.h`, `include/Touch.h`, `include/StripeCanvas.h`, `src/Touch.cpp`: reused hardware/calibration and clipped stripe-renderer implementation.
- `include/Display.h`, `src/Display.cpp`: adapted to use the dual-port console and incremental GRAM capture. Capture reads a row per loop and sends bounded chunks to the requesting port while touch/rendering continue.

This is a deliberately separate controller application, not a migration replacement for DeskDisplay. The desktop UI, network worker, credentials and voice transport are not copied. The touch calibration schema and NVS namespace remain compatible with the existing hardware. The partition layout is the same `default_16MB.csv`, so uploading the application does not intentionally erase calibration/NVS. A private full-flash backup is retained regardless.

New files implement the controller bench UI, dual serial console, microphone level measurement and generated pin contract. Library versions and memory settings are taken from the working hardware configuration and pinned in platformio.ini.
