#include "AxisObserverState.h"
#include <cassert>
#include <cstdint>

int main() {
    AxisObserverState s;
    assert(!s.active && !s.due(100));
    s.start(100);assert(s.due(100));s.accept(1000,800,100);
    assert(s.valid && s.samples==1 && s.filtered()==1000 && s.minimum==1000);
    s.accept(3000,2400,105);assert(s.samples==1); // no early samples
    s.accept(3000,2400,110);assert(s.filtered()==1500 && s.maximum==3000);
    assert(!s.reportDue(199) && s.reportDue(200));
    assert(!s.expired(300099) && s.expired(300100) && !s.due(300100));
    s.stop();s.accept(2000,1500,400000);assert(s.samples==2);
    s.start(UINT32_MAX-5);s.accept(4095,3000,UINT32_MAX-5);
    assert(s.due(4));s.accept(0,0,4);assert(s.samples==2 && s.minimum==0 && s.maximum==4095);
    assert(s.expired(uint32_t(UINT32_MAX-5+uint32_t(300000))));
    s.start(0);assert(!s.valid && s.samples==0 && s.minimum==4095);
    for(uint32_t t=0;t<1000;t+=10) s.accept(4000,2900,t);
    assert(s.filtered()==4000 && s.samples==100);
}
