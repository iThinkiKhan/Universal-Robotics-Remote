#pragma once
#include <Arduino.h>

// Mirror diagnostics to the existing CH343/UART cable and native USB CDC.
class BenchConsole : public Print {
public:
    using Print::write;
    size_t write(uint8_t value) override { return write(&value,1); }
    size_t write(const uint8_t *data,size_t size) override {
        size_t sent=Serial0.write(data,size);
        if(Serial) Serial.write(data,size);
        return sent;
    }
};
extern BenchConsole Console;
