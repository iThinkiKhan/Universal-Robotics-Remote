#include "Display.h"
#include "Layout.h"
#include "Console.h"

void Display::begin() {
    pinMode(Board::backlight, INPUT);
    pinMode(Board::touchCs, OUTPUT); digitalWrite(Board::touchCs, HIGH);
    bus.begin(Board::tftSck, Board::tftMiso, Board::tftMosi, Board::tftCs);
    // ILI9341 confirmed on this module by repeated indexed D3 reads (93 41).
    panel.begin(Board::displayHz);
    panel.setRotation(Layout::rotation);
    panel.setTextWrap(false);
    report();
}

bool Display::startCapture(bool usb) {
    if(frame) return false;
    frame=static_cast<uint8_t *>(ps_malloc(Layout::width*Layout::height*3));
    if(!frame) return false;
    captureRow=0;captureOffset=0;captureHeader=false;captureUsb=usb;captureStarted=millis();
    return true;
}
void Display::captureTick() {
    if(!frame) return;
    // Scanned GRAM readback, not a simultaneous photograph: UI/touch keep running.
    // Read at most one row per loop; never hold the UI for a complete UART transfer.
    if(millis()-captureStarted>45000 || (captureUsb && !Serial)) {
        free(frame);frame=nullptr;return;
    }
    if(captureRow<Layout::height) {
        panel.setSPISpeed(1000000);
        panel.startWrite();panel.setAddrWindow(0,captureRow,Layout::width,1);
        panel.writeCommand(0x2E);panel.spiRead();
        uint8_t *row=frame+captureRow*Layout::width*3;
        for(int i=0;i<Layout::width*3;++i) row[i]=panel.spiRead();
        panel.endWrite();panel.setSPISpeed(Board::displayHz);++captureRow;return;
    }
    int room=captureUsb ? Serial.availableForWrite() : Serial0.availableForWrite();
    if(room<96) return;
    Print &out=captureUsb ? static_cast<Print &>(Serial) : static_cast<Print &>(Serial0);
    if(!captureHeader) { out.printf("FRAME %d %d RGB888\n",Layout::width,Layout::height);captureHeader=true;return; }
    constexpr size_t total=Layout::width*Layout::height*3;
    if(captureOffset<total) {
        size_t count=min(size_t(96),total-captureOffset);
        captureOffset+=out.write(frame+captureOffset,count);
    } else {
        out.println("\nEND FRAME");free(frame);frame=nullptr;
    }
}

void Display::report() {
    uint8_t id[4];
    Console.print("ILI9341 indexed D3:");
    for (int i = 0; i < 4; ++i) {
        id[i] = panel.readcommand8(0xD3, i);
        Console.printf(" %02X", id[i]);
    }
    identified = id[2] == 0x93 && id[3] == 0x41;
    Console.printf(" => %s\n", identified ? "ILI9341 ID MATCH" : "CONTROLLER UNCONFIRMED");
    Console.printf("Display status=%02X pixel-format=%02X MADCTL=%02X\n",
        panel.readcommand8(0x0A), panel.readcommand8(0x0C), panel.readcommand8(0x0B));
}

void Display::pattern() {
    auto &t = panel;
    t.fillScreen(ILI9341_BLACK);
    t.drawRect(0, 0, 320, 240, ILI9341_WHITE);
    t.setTextColor(ILI9341_WHITE); t.setTextSize(2); t.setCursor(12, 12);
    t.print("DISPLAY TEST");
    t.setTextSize(1); t.setCursor(12, 38);
    t.print(identified ? "ILI9341 ID confirmed" : "ILI9341 candidate - ID unknown");
    const uint16_t colors[] = {ILI9341_RED, ILI9341_GREEN, ILI9341_BLUE,
                              ILI9341_CYAN, ILI9341_MAGENTA, ILI9341_YELLOW};
    const char *names[] = {"RED", "GREEN", "BLUE", "CYAN", "MAGENTA", "YELLOW"};
    for (int i = 0; i < 6; ++i) {
        t.fillRect(12+i*49,58,47,68,colors[i]);
        t.setCursor(14+i*49,84); t.setTextColor(ILI9341_BLACK); t.print(names[i]);
    }
    for (int x = 0; x < 294; ++x) {
        uint8_t v = x * 255 / 293;
        t.drawFastVLine(12+x,136,24,t.color565(v,v,v));
    }
    t.drawRect(12,174,40,40,ILI9341_WHITE);
    t.drawLine(12,174,51,213,ILI9341_WHITE);
    t.drawCircle(284,194,20,ILI9341_WHITE);
    t.setTextColor(ILI9341_WHITE); t.setCursor(64,182); t.print("320 x 240 / LANDSCAPE");
    t.setCursor(64,198); t.print("SPI 10 MHz / TOUCH TEST");
    t.setCursor(12,226); t.print("TL origin                            BR corner");
}
