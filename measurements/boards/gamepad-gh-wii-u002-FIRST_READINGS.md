# GH-Wii U002 — first mechanical readings

Reference: [3081.jpg](../photos/gamepad-gh-wii-u002/originals/3081.jpg), button-contact side facing you, USB at the top. The [illustrated checklist](../photos/gamepad-gh-wii-u002/first-readings.html) marks reference hole A. Keep the board unpowered; retain all ribbons and daughterboards.

Please provide just these four values in millimetres first:

| ID | Reading | What to include/exclude |
| --- | --- | --- |
| W | Maximum main-PCB width | Green main board only; exclude separate joystick boards, ribbons and wires |
| H | Maximum main-PCB height | Include its green USB tongue; exclude metal socket overhang |
| T | Bare PCB thickness | Exposed substrate edge; exclude components and solder |
| A | Diameter of reference hole A | Round through-hole immediately left of the USB tongue in photo 3081; function not assumed |

Record the instrument and approximate precision if known; an uncertain reading stays marked uncertain. The authoritative record is gamepad-gh-wii-u002.json. Unknown values remain null.

W/H/T will establish a measured bounding envelope. This is an irregular board, so a rectangular envelope is not its outline or a validated enclosure fit. Hole diameter alone will not place/cut a hole in CAD.

Next pass: selected hole-center coordinates from an agreed datum, the outline's steps/cutouts, USB overhang and component heights. A flat, straight-on photograph with a ruler in the PCB plane will help outline tracing; the current handheld photos are not dimensionally rectified.

Treat both joystick daughterboards and both shoulder boards as separate components. Their floating positions in the loose photos are not mounting coordinates. If retaining the original stick spacing, measure it in the original shell; otherwise choose that spacing during the enclosure layout.
