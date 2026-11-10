#pragma once
#include "AxisObserverState.h"
#include "Board.h"
#include "Console.h"

#ifndef URR_AXIS_OBSERVER
#define URR_AXIS_OBSERVER 0
#endif

#if URR_AXIS_OBSERVER
#include <driver/adc.h>
#include <driver/gpio.h>
#include <driver/rtc_io.h>
#include <esp_adc_cal.h>
#endif

class AxisObserver {
public:
    AxisObserverState state;
    static constexpr bool available=URR_AXIS_OBSERVER;
    bool start(uint32_t now) {
#if URR_AXIS_OBSERVER
        static_assert(Board::leftX==5,"Review the single-axis contract before changing its pin");
        static_assert(!Board::gamepadEnabled,"The complete gamepad must remain disabled");
        if(state.active) { Console.println("AXIS error=already_active use_axis_stop_first");return false; }
        if(adc1_config_width(ADC_WIDTH_BIT_12)!=ESP_OK ||
           adc1_config_channel_atten(ADC1_CHANNEL_4,ADC_ATTEN_DB_12)!=ESP_OK) {
            Console.println("AXIS error=adc_configuration");return false;
        }
        // ADC1 configuration selects the analog input. Explicitly disable RTC pulls.
        rtc_gpio_pullup_dis(GPIO_NUM_5);rtc_gpio_pulldown_dis(GPIO_NUM_5);
        calibration=esp_adc_cal_characterize(ADC_UNIT_1,ADC_ATTEN_DB_12,ADC_WIDTH_BIT_12,1100,&characteristics);
        readErrors=0;state.start(now);
        Console.println("AXIS started pin=5 input_only=1 timeout_ms=300000 physical_isolation=0");
        return true;
#else
        Console.println("AXIS unavailable use_bench_axis_test_build");return false;
#endif
    }
    void stop(const char *reason="command") {
#if URR_AXIS_OBSERVER
        if(state.active) {
            state.stop();rtc_gpio_deinit(GPIO_NUM_5);pinMode(Board::leftX,INPUT);
            gpio_pullup_dis(GPIO_NUM_5);gpio_pulldown_dis(GPIO_NUM_5);
        }
#else
        state.stop();
#endif
        Console.printf("AXIS stopped reason=%s physical_isolation=0 disconnect_signal_before_power_changes\n",reason);
    }
    void tick(uint32_t now) {
#if URR_AXIS_OBSERVER
        if(state.expired(now)) { stop("timeout");return; }
        if(state.due(now)) {
            int raw=adc1_get_raw(ADC1_CHANNEL_4);
            if(raw<0 || raw>4095) { ++readErrors;stop("adc_read_error");return; }
            state.accept(uint16_t(raw),esp_adc_cal_raw_to_voltage(raw,&characteristics),now);
        }
        if(state.reportDue(now)) { report(now);state.reportedAt=now; }
#endif
    }
    void report(uint32_t now) const {
        Console.printf("AXIS available=%d active=%d valid=%d pin=5 samples=%lu raw=%u filtered=%u mv_est=%lu min=%u max=%u age_ms=%lu elapsed_ms=%lu errors=%lu calibration=%d\n",
            available,state.active,state.valid,state.samples,state.raw,state.filtered(),state.millivolts,
            state.minimum,state.maximum,state.valid ? uint32_t(now-state.sampledAt) : 0UL,
            state.active ? uint32_t(now-state.started) : 0UL,readErrors,calibration);
    }
private:
    uint32_t readErrors=0;
    int calibration=-1;
#if URR_AXIS_OBSERVER
    esp_adc_cal_characteristics_t characteristics={};
#endif
};
