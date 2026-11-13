#include <Arduino.h>
#include <Bluepad32.h>
#include <atomic>
#include <bt/uni_bt.h>
#include <bt/uni_bt_allowlist.h>
#include <bt/uni_bt_bredr.h>
extern "C" {
#include <parser/uni_hid_parser_wii.h>
}
#include <uni_hid_device.h>

// Standalone Bluetooth input test for the GH-Wii U002 clone. Input logging only: no GPIO taps,
// second UART, Wi-Fi or actuator path.
//
// What this clone needs (observed on one unit, 2026-11-13; see README):
//   * limited inquiry (LIAC) while the gamepad is in SYNC mode;
//   * the library's name and SDP queries skipped (they time out), so the Wii decoder is chosen
//     by an address-scoped profile;
//   * its trimmed 12-byte memory-read reply is not usable by the library, so the setup that
//     the library would do is done here: player-1 LED, then data reporting mode 0x3d.
//   Any other data reporting mode made this unit stop responding after one acknowledgment.
static const char* VERSION = "0.1.15";

static btstack_packet_callback_registration_t discoveryHandler = {};
static btstack_context_callback_registration_t diagnosticRequest = {};
static bool discoveryRegistered = false;
static uint32_t classicDiscoveries = 0;
static std::atomic<bool> diagnosticQueued{false};
static btstack_context_callback_registration_t inquiryModeRequest = {};
static btstack_timer_source_t inquiryModeTimer = {};
static std::atomic<bool> inquiryModeQueued{false};
static uint32_t currentInquiryLap = GAP_IAC_GENERAL_INQUIRY;

static std::atomic<bool> cloneProfileEnabled{false};
static std::atomic<bool> cloneProfileQueued{false};
static bd_addr_t cloneTarget = {};
static bd_addr_t pendingCloneTarget = {};
static btstack_context_callback_registration_t cloneProfileRequest = {};
static uni_error_t (*previousDiscovery)(bd_addr_t, const char*, uint16_t, uint8_t) = nullptr;

static bool collectingTarget = false;
static char targetText[18] = {};
static unsigned targetLength = 0;
static bool targetOverflow = false;

// Setup sequence sent after the clone's memory-read reply: step 0 LED, step 1 report mode.
static btstack_context_callback_registration_t setupRequest = {};
static std::atomic<uint32_t> setupStartMs{0};
static std::atomic<unsigned> setupStep{0};
static std::atomic<bool> setupQueued{false};
static const uint32_t SETUP_DELAY_MS[] = {500, 2500, 3500};
static const unsigned SETUP_STEPS = sizeof(SETUP_DELAY_MS) / sizeof(SETUP_DELAY_MS[0]);

// Decoded input state (Wii U Pro extension data inside report 0x3d). Layout assumed from the
// public Wii U Pro format; axis values are raw 12-bit counts, uncalibrated.
static uint32_t inputReports = 0;
static uint32_t lastReportMs = 0;
static uint32_t lastPrintMs = 0;
static bool streamStaleReported = false;
static uint16_t lastAxis[4] = {};
static uint8_t lastButtons[3] = {};
static uint32_t lastHeartbeat = 0;

static void sendSetupStep(void*) {
    auto* device = uni_hid_device_get_instance_for_address(cloneTarget);
    const unsigned step = setupStep.load();
    if (device) {
        if (step == 0) {
            // Player-1 LED exactly as Bluepad32 sends it (seat 1 << 4, no rumble).
            const uint8_t led[] = {0xa2, 0x11, 0x10};
            uni_hid_device_send_intr_report(device, led, sizeof(led));
            Serial.println("SETUP player_led=1");
        } else if (step == 1) {
            // Data reporting mode 0x3d, continuous: 21 extension bytes per report.
            const uint8_t mode[] = {0xa2, 0x12, 0x04, 0x3d};
            uni_hid_device_send_intr_report(device, mode, sizeof(mode));
            Serial.println("SETUP report_mode=3d continuous=1");
        } else if (step == 2) {
            // The library deletes a device that has not reached "ready" when its one-shot
            // connection timer fires (about 13-17 s). Our setup replaces the library's, so
            // declare the device ready ourselves; this also removes that timer.
            Serial.printf("SETUP mark_ready=%d\n", uni_hid_device_set_ready_complete(device));
        }
    }
    setupStep.store(step + 1);
    setupQueued.store(false);
}

static uint16_t axis12(const uint8_t* ext, unsigned index) {
    return static_cast<uint16_t>(ext[index] | ((ext[index + 1] & 0x0f) << 8));
}

static void handleInputReport(const uint8_t* report) {
    const uint8_t* ext = report + 1;
    const uint32_t now = millis();
    ++inputReports;
    lastReportMs = now;
    streamStaleReported = false;
    uint16_t axes[4] = {axis12(ext, 0), axis12(ext, 2), axis12(ext, 4), axis12(ext, 6)};  // LX RX LY RY
    const uint8_t buttons[3] = {ext[8], ext[9], ext[10]};
    const bool buttonsChanged = memcmp(buttons, lastButtons, sizeof(buttons)) != 0;
    bool axesMoved = false;
    for (unsigned i = 0; i < 4; ++i)
        if (abs(static_cast<int>(axes[i]) - static_cast<int>(lastAxis[i])) > 2) axesMoved = true;
    if (inputReports > 1 && !buttonsChanged && !(axesMoved && now - lastPrintMs >= 50)) return;
    lastPrintMs = now;
    memcpy(lastAxis, axes, sizeof(axes));
    memcpy(lastButtons, buttons, sizeof(buttons));
    Serial.printf("INPUT n=%lu ms=%lu lx=%u ly=%u rx=%u ry=%u b=%02x,%02x,%02x\n",
                  static_cast<unsigned long>(inputReports), static_cast<unsigned long>(now),
                  axes[0], axes[2], axes[1], axes[3], buttons[0], buttons[1], buttons[2]);
}

// Report parser installed for the profiled clone only. Runs on the Bluetooth thread.
static void cloneReport(uni_hid_device_t* device, const uint8_t* report, uint16_t length) {
    if (length < 1) return;
    switch (report[0]) {
        case 0x3d:
            if (length >= 12) handleInputReport(report);
            break;
        case 0x21:
            // The clone's read reply is trimmed to its real size (12 bytes), which the library
            // rejects, so the library's own setup never runs. Start ours instead.
            Serial.printf("SETUP read_reply len=%u\n", length);
            setupStep.store(0);
            setupStartMs.store(millis());
            break;
        case 0x20:
        case 0x22:
            // Status and acknowledgment reports drive the library's own extension init and
            // identity read, so they must still reach its parser. Not logged.
            uni_hid_parser_wii_parse_input_report(device, report, length);
            break;
        default:
            Serial.printf("UNEXPECTED_REPORT id=%02x len=%u\n", report[0], length);
            break;
    }
}

static uni_error_t cloneDiscovery(bd_addr_t address, const char* name, uint16_t cod, uint8_t rssi) {
    if (previousDiscovery) {
        const auto result = previousDiscovery(address, name, cod, rssi);
        if (result != UNI_ERROR_SUCCESS) return result;
    }
    if (!cloneProfileEnabled.load() || bd_addr_cmp(address, cloneTarget) != 0)
        return UNI_ERROR_SUCCESS;
    if (uni_hid_device_get_instance_for_address(address)) return UNI_ERROR_SUCCESS;
    auto* device = uni_hid_device_create(address);
    if (!device) return UNI_ERROR_NO_SLOTS;
    uni_hid_device_set_cod(device, cod);
    uni_hid_device_set_name(device, "GH-Wii U002 compatibility test");
    // These select the decoder path; they are not identity values returned by the clone.
    uni_hid_device_set_vendor_id(device, 0x057e);
    uni_hid_device_set_product_id(device, 0x0330);
    uni_hid_device_guess_controller_type_from_pid_vid(device);
    device->report_parser.parse_input_report = &cloneReport;
    device->sdp_query_type = SDP_QUERY_NOT_NEEDED;
    uni_bt_conn_set_state(&device->conn, UNI_BT_CONN_STATE_REMOTE_NAME_FETCHED);
    setupStartMs.store(0);
    setupStep.store(0);
    inputReports = 0;
    Serial.println("WII_PROFILE_APPLIED assumed_vid=057e assumed_pid=0330 name_query=skip sdp=skip");
    return UNI_ERROR_SUCCESS;
}

static void enableCloneProfile(void*) {
    bd_addr_copy(cloneTarget, pendingCloneTarget);
    cloneProfileEnabled.store(true);
    cloneProfileQueued.store(false);
    Serial.println("WII_PROFILE_ARMED target_scoped=1 metadata_is_assumed=1");
}

static void finishTargetCommand() {
    collectingTarget = false;
    targetText[targetLength] = '\0';
    unsigned bytes[6] = {};
    if (targetOverflow || targetLength != 17 ||
        sscanf(targetText, "%2x:%2x:%2x:%2x:%2x:%2x", &bytes[0], &bytes[1], &bytes[2],
               &bytes[3], &bytes[4], &bytes[5]) != 6) {
        Serial.println("WII_PROFILE_INVALID_ADDRESS");
        return;
    }
    if (cloneProfileEnabled.load() || cloneProfileQueued.exchange(true)) {
        Serial.println("WII_PROFILE_ALREADY_ARMED_OR_PENDING reset_to_change_target");
        return;
    }
    for (unsigned i = 0; i < 6; ++i) pendingCloneTarget[i] = static_cast<uint8_t>(bytes[i]);
    btstack_run_loop_execute_on_main_thread(&cloneProfileRequest);
}

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
        case HCI_EVENT_CONNECTION_COMPLETE:
            Serial.printf("HCI_CONNECTION status=%u\n", hci_event_connection_complete_get_status(packet));
            break;
        case HCI_EVENT_AUTHENTICATION_COMPLETE:
            Serial.printf("HCI_AUTH status=%u\n", hci_event_authentication_complete_get_status(packet));
            break;
        case HCI_EVENT_DISCONNECTION_COMPLETE:
            Serial.printf("HCI_DISCONNECT reason=%u reports=%lu\n",
                          hci_event_disconnection_complete_get_reason(packet),
                          static_cast<unsigned long>(inputReports));
            setupStartMs.store(0);
            setupStep.store(0);
            break;
    }
}

// Register and inspect the stack from its own thread.
static void bluetoothDiagnostics(void*) {
    if (!discoveryRegistered) {
        auto* platform = get_arduino_platform();
        previousDiscovery = platform->on_device_discovered;
        platform->on_device_discovered = &cloneDiscovery;
        discoveryHandler.callback = &discoveryEvent;
        hci_add_event_handler(&discoveryHandler);
        discoveryRegistered = true;
    }
    Serial.printf("BT_DIAGNOSTIC state=%d working=%u scan=%u classic=%u allowlist=%u "
                  "classic_seen=%lu lap=%06lx\n",
                  hci_get_state(), hci_get_state() == HCI_STATE_WORKING,
                  uni_bt_enable_new_connections_is_enabled(), uni_bt_bredr_is_enabled(),
                  uni_bt_allowlist_is_enabled(), static_cast<unsigned long>(classicDiscoveries),
                  static_cast<unsigned long>(currentInquiryLap));
    diagnosticQueued.store(false);
}

static void startInquiryMode(btstack_timer_source_t*) {
    gap_inquiry_set_lap(currentInquiryLap);
    uni_bt_enable_new_connections_unsafe(true);
    Serial.printf("INQUIRY_MODE lap=%06lx scanning=1\n", static_cast<unsigned long>(currentInquiryLap));
    inquiryModeQueued.store(false);
}

static void selectInquiryMode(void* context) {
    currentInquiryLap = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(context));
    uni_bt_enable_new_connections_unsafe(false);
    gap_inquiry_stop();
    btstack_run_loop_remove_timer(&inquiryModeTimer);
    btstack_run_loop_set_timer_handler(&inquiryModeTimer, &startInquiryMode);
    btstack_run_loop_set_timer(&inquiryModeTimer, 1000);
    btstack_run_loop_add_timer(&inquiryModeTimer);
}

// The library never reaches "ready" for the profiled clone, so these are not expected to fire.
static void libraryConnected(ControllerPtr) { Serial.println("LIBRARY_CONNECTED (ready)"); }
static void libraryDisconnected(ControllerPtr) { Serial.println("LIBRARY_DISCONNECTED"); }

void setup() {
    Serial.begin(115200);
    Serial.printf("\nURR WROOM Bluetooth input diagnostic %s\n", VERSION);
    Serial.printf("Bluepad32=%s; input logging only\n", BP32.firmwareVersion());
    BP32.setup(&libraryConnected, &libraryDisconnected);
    BP32.enableVirtualDevice(false);
    BP32.enableNewBluetoothConnections(true);
    diagnosticRequest.callback = &bluetoothDiagnostics;
    inquiryModeRequest.callback = &selectInquiryMode;
    cloneProfileRequest.callback = &enableCloneProfile;
    setupRequest.callback = &sendSetupStep;
    diagnosticQueued.store(true);
    btstack_run_loop_execute_on_main_thread(&diagnosticRequest);
    Serial.println("READY: ?=status d=BT l=LIAC g=GIAC s=rescan f=forget w<address>=Wii profile");
}

void loop() {
    const uint32_t now = millis();
    // Send the clone's setup steps, one at a time, on the Bluetooth thread.
    const uint32_t started = setupStartMs.load();
    const unsigned step = setupStep.load();
    if (started && step < SETUP_STEPS && now - started >= SETUP_DELAY_MS[step] && !setupQueued.exchange(true))
        btstack_run_loop_execute_on_main_thread(&setupRequest);

    // Report if an established stream goes quiet.
    if (inputReports > 0 && !streamStaleReported && now - lastReportMs > 1000) {
        streamStaleReported = true;
        Serial.printf("STREAM_STALE age_ms=%lu reports=%lu\n",
                      static_cast<unsigned long>(now - lastReportMs),
                      static_cast<unsigned long>(inputReports));
    }

    bool status = now - lastHeartbeat >= 5000;
    while (Serial.available()) {
        const char command = Serial.read();
        if (collectingTarget) {
            if (command == '\n') finishTargetCommand();
            else if (command != '\r') {
                if (targetLength < sizeof(targetText) - 1) targetText[targetLength++] = command;
                else targetOverflow = true;
            }
            continue;
        }
        if (command == 'w') {
            collectingTarget = true;
            targetLength = 0;
            targetOverflow = false;
            continue;
        }
        if (command == '?') status = true;
        if (command == 'd' && !diagnosticQueued.exchange(true))
            btstack_run_loop_execute_on_main_thread(&diagnosticRequest);
        if ((command == 'l' || command == 'g') && !inquiryModeQueued.exchange(true)) {
            const uint32_t lap = command == 'l' ? GAP_IAC_LIMITED_INQUIRY : GAP_IAC_GENERAL_INQUIRY;
            inquiryModeRequest.context = reinterpret_cast<void*>(static_cast<uintptr_t>(lap));
            btstack_run_loop_execute_on_main_thread(&inquiryModeRequest);
        }
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
        Serial.printf("STATUS ms=%lu reports=%lu last_report_age_ms=%lu heap=%u\n",
                      static_cast<unsigned long>(now), static_cast<unsigned long>(inputReports),
                      static_cast<unsigned long>(inputReports ? now - lastReportMs : 0),
                      ESP.getFreeHeap());
    }
    delay(1);
}
