#include "Touch.h"
#include <Preferences.h>
#include <algorithm>

void Touch::begin() {
    pinMode(Board::tftCs, OUTPUT); digitalWrite(Board::tftCs, HIGH);
    pinMode(Board::touchCs, OUTPUT); digitalWrite(Board::touchCs, HIGH);
    pinMode(Board::touchIrq, INPUT_PULLUP);
    bus.begin(Board::touchSck, Board::touchMiso, Board::touchMosi, Board::touchCs);
    load();
}
uint16_t Touch::adc(uint8_t command) {
    bus.transfer(command);
    return (bus.transfer16(0) >> 3) & 4095;
}
TouchSample Touch::sample() {
    TouchSample s;
    s.irq = digitalRead(Board::touchIrq);
    bus.beginTransaction(SPISettings(500000, MSBFIRST, SPI_MODE0));
    digitalWrite(Board::touchCs, LOW);
    int x[5], y[5];
    // Settle after each mux change, then median-filter five samples.
    adc(0xD1); for (int &v : x) v = adc(0xD1);
    adc(0x91); for (int &v : y) v = adc(0x91);
    adc(0xB1); s.z1 = adc(0xB1);
    adc(0xC1); s.z2 = adc(0xC1);
    adc(0x90); // Power down ADC and restore PENIRQ after every transaction.
    digitalWrite(Board::touchCs, HIGH);
    bus.endTransaction();
    std::sort(x, x+5); std::sort(y, y+5);
    s.raw = {x[2],y[2]};
    s.down = s.irq == 0 && s.z1 > 100 && s.z2 >= s.z1 && s.z2 < 4090 &&
        x[2] > 40 && x[2] < 4055 && y[2] > 40 && y[2] < 4055 &&
        x[4]-x[0] < 150 && y[4]-y[0] < 150;
    return s;
}
bool Touch::load() {
    Preferences p;
    if (!p.begin("desk-touch", true)) return false;
    Calibration candidate;
    bool ok = p.getBytesLength("affine") == sizeof(candidate) &&
        p.getBytes("affine", &candidate, sizeof(candidate)) == sizeof(candidate) && candidate.valid();
    p.end();
    if (ok) calibration = candidate;
    return calibrated = ok;
}
bool Touch::save(const Calibration &value) {
    if (!value.valid()) return false;
    Preferences p;
    if (!p.begin("desk-touch", false)) return false;
    bool ok = p.putBytes("affine", &value, sizeof(value)) == sizeof(value);
    p.end();
    if (ok) { calibration = value; calibrated = true; }
    return ok;
}
