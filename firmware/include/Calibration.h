#pragma once
#include <cmath>
#include <cstdint>

struct RawPoint {
    int x, y;
    constexpr RawPoint(int xValue=0,int yValue=0): x(xValue),y(yValue) {}
};
struct Calibration {
    uint32_t version = 1;
    float ax = 0, bx = 0, cx = 0, ay = 0, by = 0, cy = 0;
    bool valid() const {
        return version == 1 && std::isfinite(ax) && std::isfinite(bx) &&
            std::isfinite(cx) && std::isfinite(ay) && std::isfinite(by) &&
            std::isfinite(cy) && std::fabs(ax*by-bx*ay) > 0.00001f &&
            std::fabs(ax) < 2 && std::fabs(bx) < 2 && std::fabs(ay) < 2 &&
            std::fabs(by) < 2 && std::fabs(cx) < 2000 && std::fabs(cy) < 2000;
    }
    RawPoint map(RawPoint r) const {
        return {int(std::lround(ax*r.x+bx*r.y+cx)), int(std::lround(ay*r.x+by*r.y+cy))};
    }
    bool solve(const RawPoint *r, const RawPoint *s) {
        float d = float(r[0].x)*(r[1].y-r[2].y) + float(r[1].x)*(r[2].y-r[0].y) + float(r[2].x)*(r[0].y-r[1].y);
        if (std::fabs(d) < 100000) return false;
        auto fit = [&](bool y, float &a, float &b, float &c) {
            float v[3]; for (int i=0;i<3;++i) v[i] = y ? s[i].y : s[i].x;
            a = (v[0]*(r[1].y-r[2].y)+v[1]*(r[2].y-r[0].y)+v[2]*(r[0].y-r[1].y))/d;
            b = (v[0]*(r[2].x-r[1].x)+v[1]*(r[0].x-r[2].x)+v[2]*(r[1].x-r[0].x))/d;
            c = v[0]-a*r[0].x-b*r[0].y;
        };
        fit(false,ax,bx,cx); fit(true,ay,by,cy);
        return valid();
    }
};
