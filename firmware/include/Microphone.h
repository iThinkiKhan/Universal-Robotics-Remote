#pragma once
#include <Arduino.h>

struct MicSnapshot {
    bool initialized=false;
    uint32_t samples=0,windowSamples=0,nonzero=0,clipped=0,errors=0,at=0;
    float rmsPercent=0,peakPercent=0,dcPercent=0;
};

class Microphone {
public:
    bool begin();
    bool snapshot(MicSnapshot &out);
private:
    QueueHandle_t queue=nullptr;
    static void entry(void *arg);
    void run();
};
