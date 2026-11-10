#pragma once
#include <stdint.h>

// Pure diagnostic state; all times use unsigned elapsed arithmetic across rollover.
struct AxisObserverState {
    static constexpr uint32_t samplePeriodMs=10, reportPeriodMs=100, sessionLimitMs=300000;
    bool active=false, valid=false;
    uint32_t started=0, sampledAt=0, reportedAt=0, samples=0, millivolts=0;
    uint16_t raw=0, minimum=4095, maximum=0;
    int32_t filteredQ8=0;
    void start(uint32_t now) { *this=AxisObserverState();active=true;started=reportedAt=now; }
    void stop() { active=false; }
    bool expired(uint32_t now) const { return active && uint32_t(now-started)>=sessionLimitMs; }
    bool due(uint32_t now) const { return active && !expired(now) && (!valid || uint32_t(now-sampledAt)>=samplePeriodMs); }
    void accept(uint16_t value,uint32_t mv,uint32_t now) {
        if(!due(now)) return;
        raw=value>4095 ? 4095 : value;millivolts=mv;
        if(!valid) filteredQ8=int32_t(raw)*256;
        else filteredQ8+=(int32_t(raw)*256-filteredQ8)/4;
        if(raw<minimum) minimum=raw;
        if(raw>maximum) maximum=raw;
        valid=true;sampledAt=now;++samples;
    }
    uint16_t filtered() const { return uint16_t((filteredQ8+128)/256); }
    bool reportDue(uint32_t now) const { return active && valid && uint32_t(now-reportedAt)>=reportPeriodMs; }
};
