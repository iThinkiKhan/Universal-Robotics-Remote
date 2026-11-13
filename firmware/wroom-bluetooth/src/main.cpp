#include <Arduino.h>
#include <Bluepad32.h>
#include <atomic>
#include <bt/uni_bt.h>
#include <bt/uni_bt_allowlist.h>
#include <bt/uni_bt_bredr.h>

// Standalone input diagnostic. No GPIO taps, second UART, Wi-Fi or actuator path.
static ControllerPtr controllers[BP32_MAX_GAMEPADS] = {};
static uint32_t reports[BP32_MAX_GAMEPADS] = {};
static uint32_t lastData[BP32_MAX_GAMEPADS] = {};
static uint32_t lastPrint[BP32_MAX_GAMEPADS] = {};
static uint16_t previousButtons[BP32_MAX_GAMEPADS] = {};
static uint16_t previousMisc[BP32_MAX_GAMEPADS] = {};
static uint8_t previousDpad[BP32_MAX_GAMEPADS] = {};
static uint32_t lastHeartbeat = 0;
static btstack_packet_callback_registration_t discoveryHandler = {};
static btstack_context_callback_registration_t diagnosticRequest = {};
static bool discoveryRegistered = false;
static uint32_t bleAdvertisements = 0;
static uint32_t classicDiscoveries = 0;
static uint32_t lastBlePrint = 0;
static btstack_context_callback_registration_t rawScanRequest = {};
static btstack_timer_source_t rawScanTimer = {};
static std::atomic<bool> diagnosticQueued{false};
static std::atomic<bool> rawScanQueued{false};

static void discoveryEvent(uint8_t type, uint16_t, uint8_t* packet, uint16_t) {
    if (type != HCI_EVENT_PACKET) return;
    switch (hci_event_packet_get_type(packet)) {
        case GAP_EVENT_INQUIRY_RESULT:
            ++classicDiscoveries;
            Serial.printf("DISCOVERED cod=%06lx rssi=%d name=%.*s\n",
                          static_cast<unsigned long>(gap_event_inquiry_result_get_class_of_device(packet)),
                          static_cast<int8_t>(gap_event_inquiry_result_get_rssi(packet)),
                          gap_event_inquiry_result_get_name_len(packet),
                          reinterpret_cast<const char*>(gap_event_inquiry_result_get_name(packet)));
            break;
        case GAP_EVENT_ADVERTISING_REPORT:
            ++bleAdvertisements;
            if (millis() - lastBlePrint >= 2000) {
                lastBlePrint = millis();
                Serial.printf("BLE_ADVERTISEMENT count=%lu rssi=%d bytes=%u\n",
                              static_cast<unsigned long>(bleAdvertisements),
                              static_cast<int8_t>(gap_event_advertising_report_get_rssi(packet)),
                              gap_event_advertising_report_get_data_length(packet));
            }
            break;
        case HCI_EVENT_COMMAND_COMPLETE: {
            const uint16_t opcode = hci_event_command_complete_get_command_opcode(packet);
            if (opcode == 0x0401 || opcode == 0x0403 || opcode == 0x0404 || opcode == 0x200b || opcode == 0x200c)
                Serial.printf("HCI_SCAN_COMMAND opcode=%04x status=%u\n", opcode, packet[5]);
            break;
        }
        case HCI_EVENT_COMMAND_STATUS: {
            const uint16_t opcode = hci_event_command_status_get_command_opcode(packet);
            if (opcode == 0x0401 || opcode == 0x0403 || opcode == 0x0404)
                Serial.printf("HCI_SCAN_STATUS opcode=%04x status=%u\n", opcode,
                              hci_event_command_status_get_status(packet));
            break;
        }
        case GAP_EVENT_INQUIRY_COMPLETE:
            Serial.println("INQUIRY_COMPLETE");
            break;
        case HCI_EVENT_CONNECTION_COMPLETE:
            Serial.printf("HCI_CONNECTION status=%u\n", hci_event_connection_complete_get_status(packet));
            break;
        case HCI_EVENT_AUTHENTICATION_COMPLETE:
            Serial.printf("HCI_AUTH status=%u\n", hci_event_authentication_complete_get_status(packet));
            break;
        case HCI_EVENT_DISCONNECTION_COMPLETE:
            Serial.printf("HCI_DISCONNECT reason=%u\n", hci_event_disconnection_complete_get_reason(packet));
            break;
    }
}

// Register and inspect the stack from its own thread.
static void bluetoothDiagnostics(void*) {
    if (!discoveryRegistered) {
        discoveryHandler.callback = &discoveryEvent;
        hci_add_event_handler(&discoveryHandler);
        discoveryRegistered = true;
    }
    Serial.printf("BT_DIAGNOSTIC state=%d working=%u scan=%u classic=%u allowlist=%u "
                  "classic_seen=%lu ble_seen=%lu\n",
                  hci_get_state(), hci_get_state() == HCI_STATE_WORKING,
                  uni_bt_enable_new_connections_is_enabled(), uni_bt_bredr_is_enabled(),
                  uni_bt_allowlist_is_enabled(), static_cast<unsigned long>(classicDiscoveries),
                  static_cast<unsigned long>(bleAdvertisements));
    diagnosticQueued.store(false);
}

static void startRawInquiry(btstack_timer_source_t*) {
    Serial.printf("RAW_CLASSIC_INQUIRY result=%u\n", gap_inquiry_start(8));
}

static void requestRawInquiry(void*) {
    uni_bt_enable_new_connections_unsafe(false);
    btstack_run_loop_remove_timer(&rawScanTimer);
    btstack_run_loop_set_timer_handler(&rawScanTimer, &startRawInquiry);
    btstack_run_loop_set_timer(&rawScanTimer, 1000);
    btstack_run_loop_add_timer(&rawScanTimer);
    rawScanQueued.store(false);
}

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
    Serial.println("\nURR WROOM Bluetooth input diagnostic 0.1.2");
    Serial.printf("Bluepad32=%s; input logging only\n", BP32.firmwareVersion());
    BP32.setup(&connected, &disconnected);
    BP32.enableVirtualDevice(false);
    BP32.enableNewBluetoothConnections(true);
    diagnosticRequest.callback = &bluetoothDiagnostics;
    rawScanRequest.callback = &requestRawInquiry;
    diagnosticQueued.store(true);
    btstack_run_loop_execute_on_main_thread(&diagnosticRequest);
    Serial.println("READY: SYNC gamepad; ?=status, d=BT status, s=rescan, i=raw inquiry, f=forget keys");
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
        if (command == 'd' && !diagnosticQueued.exchange(true))
            btstack_run_loop_execute_on_main_thread(&diagnosticRequest);
        if (command == 'i' && !rawScanQueued.exchange(true))
            btstack_run_loop_execute_on_main_thread(&rawScanRequest);
        if (command == 's') {
            BP32.enableNewBluetoothConnections(false);
            BP32.enableNewBluetoothConnections(true);
            Serial.println("SCAN_RESTART_REQUESTED");
        }
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
