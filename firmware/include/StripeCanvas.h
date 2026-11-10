#pragma once
#include <Adafruit_GFX.h>
#include <algorithm>
#include "Layout.h"

// Full logical screen, backed by one 24-row band (15,360 bytes). Rendering the
// same scene into each band avoids a framebuffer, allocations and erase flicker.
class StripeCanvas: public Adafruit_GFX {
public:
    static constexpr int rows=24;
    uint16_t pixels[Layout::width*rows];
    StripeCanvas():Adafruit_GFX(Layout::width,Layout::height) {}
    bool intersects(int y,int h) const { return y<top+rows && y+h>top; }
    void band(int y,uint16_t background) { top=y; std::fill(pixels,pixels+Layout::width*rows,background); }
    void drawPixel(int16_t x,int16_t y,uint16_t color) override {
        if(x>=0 && x<Layout::width && y>=top && y<top+rows) pixels[(y-top)*Layout::width+x]=color;
    }
    void writeFastHLine(int16_t x,int16_t y,int16_t w,uint16_t color) override { writeFillRect(x,y,w,1,color); }
    void writeFastVLine(int16_t x,int16_t y,int16_t h,uint16_t color) override { writeFillRect(x,y,1,h,color); }
    void writeFillRect(int16_t x,int16_t y,int16_t w,int16_t h,uint16_t color) override {
        if(w<=0 || h<=0) return;
        int left=std::max(0,int(x)),right=std::min(Layout::width,int(x)+w);
        int first=std::max(top,int(y)),last=std::min(top+rows,int(y)+h);
        if(left>=right || first>=last) return;
        for(int row=first;row<last;++row) std::fill(pixels+(row-top)*Layout::width+left,pixels+(row-top)*Layout::width+right,color);
    }
    uint32_t hash() const {
        uint32_t value=2166136261u;
        for(uint16_t p:pixels) { value^=p; value*=16777619u; }
        return value;
    }
private:
    int top=0;
};
