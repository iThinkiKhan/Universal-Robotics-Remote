#include <Arduino.h>
#include <Bluepad32.h>

// Standalone input diagnostic. No GPIO taps, second UART, Wi-Fi or actuator path.
static ControllerPtr controllers[BP32_MAX_GAMEPADS] = {};
static uint32_t reports[BP32_MAX_GAMEPADS] = {};
static uint32_t lastData[BP32_MAX_GAMEPADS] = {};
static uint32_t lastPrint[BP32_MAX_GAMEPADS] = {};
static uint16_t previousButtons[BP32_MAX_GAMEPADS] = {};
static uint16_t previousMisc[BP32_MAX_GAMEPADS] = {};
static uint8_t previousDpad[BP32_MAX_GAMEPADS] = {};
static uint32_t lastHeartbeat = 0;

static void connected(ControllerPtr ctl) {
    for (unsigned i = 0; i < BP32_MAX_GAMEPADS; ++i) {
        if (controllers[i]) continue;
        controllers[i] = ctl;
        reports[i] = lastData[i] = lastPrint[i] = 0;
        previousButtons[i] = previousMisc[i] = previousDpad[i] = 0;
        const auto props = ctl->getProperties();
        Serial.printf("CONNECTED slot=%u model=%s vid=%04x pid=%04x\n", i,
                      ctl->getModelName().c_str(), props.vendor_id, props.product_id);
        return;
    }
    Serial.println("CONNECTED no-free-slot");
}

static void disconnected(ControllerPtr ctl) {
    for (unsigned i = 0; i < BP32_MAX_GAMEPADS; ++i) {
        if (controllers[i] != ctl) continue;
        Serial.printf("DISCONNECTED slot=%u reports=%lu\n", i,
                      static_cast<unsigned long>(reports[i]));
        controllers[i] = nullptr;
    }
}

void setup() {
    Serial.begin(115200);
    Serial.println("\nURR WROOM Bluetooth input diagnostic 0.1.0");
    Serial.printf("Bluepad32=%s; input logging only\n", BP32.firmwareVersion());
    BP32.setup(&connected, &disconnected);
    BP32.enableVirtualDevice(false);
    BP32.enableNewBluetoothConnections(true);
    Serial.println("READY: put the gamepad in SYNC mode; ?=status, f=forget pairing keys");
}

void loop() {
    const bool updated = BP32.update();
    const uint32_t now = millis();
    for (unsigned i = 0; i < BP32_MAX_GAMEPADS; ++i) {
        const auto ctl = controllers[i];
        if (!updated || !ctl || !ctl->isConnected() || !ctl->isGamepad() || !ctl->hasData()) continue;
        ++reports[i];
        lastData[i] = now;
        // Print digital changes immediately; limit axis-only output to 20 Hz.
        const bool digitalChanged = ctl->buttons() != previousButtons[i] ||
                                    ctl->miscButtons() != previousMisc[i] ||
                                    ctl->dpad() != previousDpad[i];
        if (!digitalChanged && reports[i] > 1 && now - lastPrint[i] < 50) continue;
        lastPrint[i] = now;
        previousButtons[i] = ctl->buttons();
        previousMisc[i] = ctl->miscButtons();
        previousDpad[i] = ctl->dpad();
        Serial.printf("INPUT ms=%lu slot=%u n=%lu lx=%ld ly=%ld rx=%ld ry=%ld "
                      "dpad=%02x buttons=%04x misc=%04x brake=%ld throttle=%ld battery=%u\n",
                      static_cast<unsigned long>(now), i, static_cast<unsigned long>(reports[i]),
                      static_cast<long>(ctl->axisX()), static_cast<long>(ctl->axisY()),
                      static_cast<long>(ctl->axisRX()), static_cast<long>(ctl->axisRY()),
                      ctl->dpad(), ctl->buttons(), ctl->miscButtons(),
                      static_cast<long>(ctl->brake()), static_cast<long>(ctl->throttle()), ctl->battery());
    }
    bool status = now - lastHeartbeat >= 2000;
    while (Serial.available()) {
        const char command = Serial.read();
        if (command == '?') status = true;
        if (command == 'f') {
            BP32.forgetBluetoothKeys();
            Serial.println("PAIRING_KEYS_FORGOTTEN");
        }
    }
    if (status) {
        lastHeartbeat = now;
        unsigned count = 0;
        for (unsigned i = 0; i < BP32_MAX_GAMEPADS; ++i) {
            if (!controllers[i] || !controllers[i]->isConnected()) continue;
            ++count;
            Serial.printf("LINK slot=%u reports=%lu age_ms=%lu\n", i,
                          static_cast<unsigned long>(reports[i]),
                          static_cast<unsigned long>(now - lastData[i]));
        }
        Serial.printf("STATUS ms=%lu connected=%u heap=%u\n",
                      static_cast<unsigned long>(now), count, ESP.getFreeHeap());
    }
    delay(1);
}
