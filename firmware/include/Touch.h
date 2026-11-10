#pragma once
#include <SPI.h>
#include "Board.h"
#include "Calibration.h"

struct TouchSample {
    RawPoint raw;
    int z1 = 0, z2 = 0;
    bool down = false;
    int irq = 1;
};
class Touch {
public:
    void begin();
    TouchSample sample();
    bool load();
    bool save(const Calibration &value);
    Calibration calibration;
    bool calibrated = false;
private:
    SPIClass bus{HSPI};
    uint16_t adc(uint8_t command);
};
