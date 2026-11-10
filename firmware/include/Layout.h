#pragma once
#include "Calibration.h"

namespace Layout {
constexpr int width=320, height=240, navTop=198;
constexpr uint8_t rotation=1;
// NVS calibration remains in the original rotation-0 portrait coordinate space.
// ILI9341 rotation 1 (MV) maps that space to (portrait Y, 239 - portrait X).
constexpr RawPoint landscape(RawPoint p) { return {p.y,239-p.x}; }
constexpr RawPoint portrait(RawPoint p) { return {239-p.y,p.x}; }
constexpr bool inside(RawPoint p,int x,int y,int w,int h) {
    return p.x>=x && p.x<x+w && p.y>=y && p.y<y+h;
}
constexpr int tab(RawPoint p) { return inside(p,0,navTop,width,height-navTop)?p.x/80:-1; }
}
