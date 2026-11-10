#include "Board.h"
#include "Console.h"
#include "Display.h"
#include "Touch.h"
#include "Layout.h"
#include "Microphone.h"
#include "StripeCanvas.h"
#include <esp_system.h>

BenchConsole Console;
Display display;
Touch touch;
Microphone microphone;
MicSnapshot mic;
constexpr char version[]="0.1.1-bench";
constexpr uint16_t bg=0x0862,panelColor=0x10C4,muted=0x94B3,accent=0xFFE0,cyan=0x07FF;
uint32_t readyAt=0,taps=0,paints=0,lastPaint=0,maxPaintUs=0,loopMaxUs=0;
uint32_t touchEvents=0,lastTouchAt=0;
RawPoint lastRaw,lastPoint;
bool dirty=true,rawLogging=false,patternMode=false,calibrating=false;
StripeCanvas canvas;
uint32_t stripeHashes[10]={};
bool stripeValid[10]={},painting=false;
int paintBand=0;
int page=0,calStep=0;
Calibration candidate;
RawPoint calibrationRaw[3];
constexpr RawPoint targets[]={{32,44},{288,44},{160,180},{160,112}};

void line(int y,const char *text,uint16_t color=ILI9341_WHITE,int size=1) {
    auto &t=canvas;t.setTextSize(size);t.setTextColor(color);t.setCursor(14,y);t.print(text);
}
void heading() {
    auto &t=canvas;
    t.fillRect(0,0,4,194,accent);
    line(12,"UNIVERSAL",accent,2);line(34,"CONTROLLER / BENCH 01",muted);
    t.drawFastHLine(14,51,292,panelColor);
    const char *labels[]={"RIG","MIC","TOUCH","PLAN"};
    for(int i=0;i<4;++i) {
        t.fillRect(i*80,198,78,42,i==page ? accent : panelColor);
        t.setTextSize(1);t.setTextColor(i==page ? bg : ILI9341_WHITE);
        t.setCursor(i*80+24,215);t.print(labels[i]);
    }
}
void drawScene() {
    heading();
    auto &t=canvas;
    char text[64];
    if(page==0) {
        line(61,"S3 / N16R8",ILI9341_WHITE,2);
        snprintf(text,sizeof(text),"DISPLAY  %s",display.identified?"ILI9341 VERIFIED":"ID UNCONFIRMED");line(88,text,cyan);
        snprintf(text,sizeof(text),"TOUCH    %s",touch.calibrated?"SAVED MAP LOADED":"CALIBRATION NEEDED");line(104,text);
        snprintf(text,sizeof(text),"MIC      %s",mic.initialized&&mic.nonzero?"STREAMING":"CHECK MIC PAGE");line(120,text);
        snprintf(text,sizeof(text),"UP %lus  HEAP %uK  PSRAM %uM",millis()/1000,ESP.getFreeHeap()/1024,(ESP.getPsramSize()+524288)/1048576);line(143,text,muted);
        line(164,"GAMEPAD NOT CONNECTED",accent);line(179,"CONTROL LINK: DISABLED",muted);
    } else if(page==1) {
        line(61,"MICROPHONE",ILI9341_WHITE,2);
        snprintf(text,sizeof(text),"16kHz / LEFT / %s",mic.initialized?"I2S READY":"I2S ERROR");line(88,text,cyan);
        t.drawRect(14,108,292,18,muted);
        // Meter uses -60..0 dBFS so normal speech/noise remains visible.
        float db=mic.rmsPercent>0 ? 20*log10f(mic.rmsPercent/100) : -60;
        int meter=constrain(int((db+60)*290/60),0,290);
        t.fillRect(15,109,meter,16,accent);
        snprintf(text,sizeof(text),"RMS %.3f%%  PEAK %.3f%%",mic.rmsPercent,mic.peakPercent);line(136,text);
        snprintf(text,sizeof(text),"SAMPLES %lu  ERRORS %lu",mic.samples,mic.errors);line(152,text,muted);
        line(173,"Speak or clap: meter should respond.",cyan);
    } else if(page==2) {
        line(61,"TOUCH / LIVE",ILI9341_WHITE,2);
        snprintf(text,sizeof(text),"MAP %s / EVENTS %lu",touch.calibrated?"LOADED":"MISSING",touchEvents);line(89,text,cyan);
        snprintf(text,sizeof(text),"RAW %d,%d  SCREEN %d,%d",lastRaw.x,lastRaw.y,lastPoint.x,lastPoint.y);line(111,text);
        line(132,"Tap targets and edges; watch coordinates.",muted);
        t.drawRect(14,153,292,33,accent);line(165,"TAP HERE TO RECALIBRATE",accent);
    } else {
        line(61,"NEXT: INPUT HARNESS",ILI9341_WHITE,2);
        line(91,"1  Measure gamepad rails and axes");
        line(109,"2  Verify buttons and power states");
        line(127,"3  Fit removable signal harness");
        line(150,"Axes / expander pins are uninitialized.",accent);
        line(173,"No radio commands in bench firmware.",muted);
    }
}
void paint() {
    if(patternMode || calibrating) return;
    uint32_t started=micros();
    if(dirty) {
        for(bool &valid:stripeValid) valid=false;
        paintBand=0;painting=true;dirty=false;
    }
    if(!painting) {
        if(millis()-lastPaint<250) return;
        paintBand=0;painting=true;
    }
    canvas.band(paintBand*StripeCanvas::rows,bg);canvas.setTextWrap(false);drawScene();
    uint32_t hash=canvas.hash();
    if(!stripeValid[paintBand] || stripeHashes[paintBand]!=hash) {
        display.panel.drawRGBBitmap(0,paintBand*StripeCanvas::rows,canvas.pixels,Layout::width,StripeCanvas::rows);
        stripeHashes[paintBand]=hash;stripeValid[paintBand]=true;
    }
    if(++paintBand==10) { painting=false;lastPaint=millis();++paints; }
    maxPaintUs=max(maxPaintUs,uint32_t(micros()-started));
}
void calibrationTarget() {
    auto &t=display.panel;t.fillScreen(bg);
    t.setTextColor(accent);t.setTextSize(1);t.setCursor(14,6);t.print("TOUCH CALIBRATION");
    t.setTextColor(muted);t.setCursor(14,20);t.print("Hold target then lift. Serial: cancel");
    RawPoint p=targets[calStep];
    t.drawCircle(p.x,p.y,10,cyan);t.drawFastHLine(p.x-16,p.y,33,accent);t.drawFastVLine(p.x,p.y-16,33,accent);
}
void startCalibration() {
    calibrating=true;patternMode=false;calStep=0;candidate=Calibration();calibrationTarget();
    Console.println("CALIBRATION hold 3 targets then center; existing NVS kept until verification; cancel to exit");
}
void reportMic() {
    Console.printf("MIC initialized=%d samples=%lu window=%lu nonzero=%lu rms_pct=%.5f peak_pct=%.5f dc_pct=%.5f clipped=%lu errors=%lu age_ms=%lu\n",
        mic.initialized,mic.samples,mic.windowSamples,mic.nonzero,mic.rmsPercent,mic.peakPercent,
        mic.dcPercent,mic.clipped,mic.errors,mic.at ? millis()-mic.at : 0UL);
}
void status() {
    Console.printf("RIG version=%s registry=%s uptime_ms=%lu ready_ms=%lu reset=%d flash=%u psram=%u heap=%u min_heap=%u\n",
        version,Board::registryHash,millis(),readyAt,esp_reset_reason(),ESP.getFlashChipSize(),ESP.getPsramSize(),ESP.getFreeHeap(),ESP.getMinFreeHeap());
    Console.printf("DISPLAY identified=%d calibrated=%d page=%d paints=%lu max_paint_us=%lu max_loop_us=%lu\n",
        display.identified,touch.calibrated,page,paints,maxPaintUs,loopMaxUs);
    Console.printf("TOUCH events=%lu raw=%d,%d screen=%d,%d taps=%lu last_ms=%lu\n",
        touchEvents,lastRaw.x,lastRaw.y,lastPoint.x,lastPoint.y,taps,lastTouchAt);
    Console.printf("POLICY gamepad_enabled=%d radio_control=0 backlight_gpio=INPUT uart=43,44\n",Board::gamepadEnabled);
    reportMic();
}
void selftest() {
    int passed=0,failed=0;
    auto check=[&](bool ok,const char *name) { Console.printf("%s %s\n",ok?"PASS":"FAIL",name);ok?++passed:++failed; };
    check(ESP.getFlashChipSize()==16777216,"flash_16MB");
    check(ESP.getPsramSize()>=8000000,"psram_8MB");
    auto *memory=static_cast<uint32_t *>(ps_malloc(65536));
    bool memoryOk=memory;
    if(memory) {
        for(uint32_t i=0;i<16384;++i) memory[i]=0xA55A0000^i;
        for(uint32_t i=0;i<16384;++i) if(memory[i]!=(0xA55A0000^i)) { memoryOk=false;break; }
        free(memory);
    }
    check(memoryOk,"psram_64KB_pattern");
    check(display.identified,"ili9341_register_id");
    check(touch.calibrated && touch.calibration.valid(),"saved_touch_map");
    check(mic.initialized && mic.samples>16000 && mic.nonzero>0 && millis()-mic.at<1500,"mic_live_nonzero_samples");
    check(mic.errors==0,"mic_read_errors_zero");
    check(!Board::gamepadEnabled,"gamepad_disabled");
    const RawPoint p=Layout::landscape(Layout::portrait({110,70}));
    check(p.x==110 && p.y==70,"touch_rotation_round_trip");
    Console.printf("SELFTEST passed=%d failed=%d\n",passed,failed);
}
void command(const char *s,bool usb) {
    if(!strcmp(s,"status")) status();
    else if(!strcmp(s,"mic")) reportMic();
    else if(!strcmp(s,"selftest")) { display.report();selftest(); }
    else if(!strcmp(s,"capture")) {
        if(calibrating) Console.println("ERROR finish/cancel calibration before capture");
        else { rawLogging=false;if(!display.startCapture(usb)) Console.println("ERROR capture allocation failed"); }
    }
    else if(!strcmp(s,"test")) { patternMode=true;display.pattern(); }
    else if(!strcmp(s,"calibrate")) startCalibration();
    else if(!strcmp(s,"cancel")) { calibrating=patternMode=false;dirty=true; }
    else if(!strcmp(s,"raw on")) rawLogging=true;
    else if(!strcmp(s,"raw off")) rawLogging=false;
    else if(strlen(s)==6 && !strncmp(s,"page ",5) && s[5]>='0' && s[5]<='3') {
        page=s[5]-'0';calibrating=patternMode=false;dirty=true;
    } else Console.println("Commands: status | selftest | mic | page 0..3 | raw on/off | test | capture | calibrate | cancel");
}
struct Parser {
    char buffer[96]={};size_t used=0;bool overflow=false;
    void poll(Stream &stream,bool usb) {
        for(int budget=0;budget<96 && stream.available();++budget) {
            char c=stream.read();if(c=='\r') continue;
            if(c=='\n') {
                if(overflow) Console.println("ERROR command too long; discarded");
                else { buffer[used]=0;if(used) command(buffer,usb); }
                used=0;overflow=false;
                if(display.capturing()) break;
            } else if(!overflow && used<sizeof(buffer)-1) buffer[used++]=c;
            else overflow=true;
        }
    }
} uartParser,usbParser;
void pollTouch() {
    static uint32_t lastSample=0,lastRawLog=0,heldSince=0;
    static bool wasDown=false;static RawPoint heldPoint;
    if(millis()-lastSample<20) return;
    lastSample=millis();TouchSample s=touch.sample();
    if(s.down) {
        lastRaw=s.raw;lastPoint=touch.calibrated?Layout::landscape(touch.calibration.map(s.raw)):RawPoint(-1,-1);
        lastTouchAt=millis();++touchEvents;
        if(!wasDown) { heldSince=millis();heldPoint=s.raw;++taps; }
        else heldPoint=s.raw;
    }
    if(rawLogging && !display.capturing() && millis()-lastRawLog>=100) {
        Console.printf("RAW irq=%d down=%d x=%d y=%d z1=%d z2=%d screen=%d,%d\n",
            s.irq,s.down,s.raw.x,s.raw.y,s.z1,s.z2,lastPoint.x,lastPoint.y);lastRawLog=millis();
    }
    if(wasDown && !s.down) {
        if(calibrating && millis()-heldSince>=200) {
            if(calStep<3) {
                calibrationRaw[calStep]=heldPoint;++calStep;
                if(calStep==3) {
                    RawPoint portrait[3];for(int i=0;i<3;++i) portrait[i]=Layout::portrait(targets[i]);
                    if(!candidate.solve(calibrationRaw,portrait)) { Console.println("CALIBRATION geometry rejected; retry");calStep=0; }
                }
                calibrationTarget();
            } else {
                RawPoint mapped=Layout::landscape(candidate.map(heldPoint));
                if(abs(mapped.x-targets[3].x)<=12 && abs(mapped.y-targets[3].y)<=12 && touch.save(candidate)) {
                    calibrating=false;dirty=true;Console.println("CALIBRATION verified and saved");
                } else { calStep=0;calibrationTarget();Console.println("CALIBRATION verification/save failed; existing mapping retained"); }
            }
        } else if(!calibrating && touch.calibrated) {
            int selected=Layout::tab(lastPoint);
            if(selected>=0) { page=selected;patternMode=false;dirty=true; }
            else if(!display.capturing() && page==2 && Layout::inside(lastPoint,14,153,292,33)) startCalibration();
        }
    }
    wasDown=s.down;
}
void setup() {
    Serial.begin(115200);Serial.setTxTimeoutMs(10);
    Serial0.setTxBufferSize(2048);Serial0.begin(115200,SERIAL_8N1,Board::uartRx,Board::uartTx);
    display.begin();touch.begin();
    if(!microphone.begin()) Console.println("ERROR microphone task creation failed");
    while(dirty || painting) paint();
    readyAt=millis();status();
}
void loop() {
    uint32_t started=micros();
    microphone.snapshot(mic);
    // Defer console commands during binary transfer, while touch/UI remain live.
    if(!display.capturing()) { uartParser.poll(Serial0,false);if(!display.capturing()) usbParser.poll(Serial,true); }
    pollTouch();paint();display.captureTick();
    loopMaxUs=max(loopMaxUs,uint32_t(micros()-started));
    delay(2);
}
