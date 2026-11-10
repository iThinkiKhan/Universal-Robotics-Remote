#pragma once
#include <Adafruit_ILI9341.h>
#include "Board.h"

class Display {
public:
    SPIClass bus{FSPI};
    Adafruit_ILI9341 panel{&bus, Board::tftDc, Board::tftCs, Board::tftReset};
    bool identified = false;
    void begin();
    void report();
    void pattern();
    bool startCapture(bool usb);
    void captureTick();
    bool capturing() const { return frame!=nullptr; }
private:
    uint8_t *frame=nullptr;
    int captureRow=0;
    size_t captureOffset=0;
    uint32_t captureStarted=0;
    bool captureUsb=false,captureHeader=false;
};
