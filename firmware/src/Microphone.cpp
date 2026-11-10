#include "Microphone.h"
#include "Board.h"
#include <driver/i2s.h>
#include <cmath>

bool Microphone::begin() {
    queue=xQueueCreate(1,sizeof(MicSnapshot));
    if(!queue) return false;
    if(xTaskCreatePinnedToCore(entry,"mic-diagnostics",4096,this,2,nullptr,0)!=pdPASS) {
        vQueueDelete(queue);queue=nullptr;return false;
    }
    return true;
}
bool Microphone::snapshot(MicSnapshot &out) {
    return queue && xQueuePeek(queue,&out,0)==pdTRUE;
}
void Microphone::entry(void *arg) { static_cast<Microphone *>(arg)->run(); }
void Microphone::run() {
    MicSnapshot s;
    i2s_config_t cfg={};
    cfg.mode=i2s_mode_t(I2S_MODE_MASTER|I2S_MODE_RX);
    cfg.sample_rate=16000;cfg.bits_per_sample=I2S_BITS_PER_SAMPLE_32BIT;
    cfg.channel_format=I2S_CHANNEL_FMT_ONLY_LEFT;
    cfg.communication_format=I2S_COMM_FORMAT_STAND_I2S;
    cfg.intr_alloc_flags=ESP_INTR_FLAG_LEVEL1;cfg.dma_buf_count=6;cfg.dma_buf_len=256;
    i2s_pin_config_t pins={};pins.mck_io_num=I2S_PIN_NO_CHANGE;
    pins.bck_io_num=Board::micSck;pins.ws_io_num=Board::micWs;
    pins.data_out_num=I2S_PIN_NO_CHANGE;pins.data_in_num=Board::micSd;
    esp_err_t installed=i2s_driver_install(I2S_NUM_0,&cfg,0,nullptr);
    if(installed!=ESP_OK || i2s_set_pin(I2S_NUM_0,&pins)!=ESP_OK) {
        if(installed==ESP_OK) i2s_driver_uninstall(I2S_NUM_0);
        s.errors=1;xQueueOverwrite(queue,&s);vTaskDelete(nullptr);return;
    }
    s.initialized=true;
    int32_t raw[256];
    uint32_t n=0,nonzero=0,clipped=0,start=millis();
    double sum=0,squares=0,peak=0;
    for(;;) {
        size_t bytes=0;
        esp_err_t result=i2s_read(I2S_NUM_0,raw,sizeof(raw),&bytes,pdMS_TO_TICKS(100));
        if(result!=ESP_OK) ++s.errors;
        for(size_t i=0;i<bytes/sizeof(raw[0]);++i) {
            // Signed 24-bit INMP441 data occupies the high 24 bits of the slot.
            int32_t value=raw[i]>>8;
            double normalized=double(value)/8388608.0;
            sum+=normalized;squares+=normalized*normalized;
            peak=fmax(peak,fabs(normalized));++n;if(value!=0) ++nonzero;
            if(fabs(normalized)>=0.99) ++clipped;
        }
        if(uint32_t(millis()-start)>=250) {
            s.samples+=n;s.windowSamples=n;s.nonzero=nonzero;s.clipped=clipped;s.at=millis();
            double mean=n ? sum/n : 0;
            s.dcPercent=100*mean;
            s.rmsPercent=100*sqrt(fmax(0.0,n ? squares/n-mean*mean : 0));
            s.peakPercent=100*peak;xQueueOverwrite(queue,&s);
            n=nonzero=clipped=0;sum=squares=peak=0;start=millis();
        }
    }
}
