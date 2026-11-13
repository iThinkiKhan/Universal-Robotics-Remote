# Engineering decisions

## 2026-11-10 — One bounded observer experiment before a custom harness
Use the LX-01 model and test plan for a single input-only L-X/ADC1 observer. The dedicated profile is disarmed at boot and starts only by command after the bench preparation gate. The complete gamepad and control link stay disabled. The resistor/capacitor circuit has no powered-off-input protection: use a removable signal break, signal-last connection while both boards are powered, and signal-first removal before power/reset changes. Qualify a permanent protective interface separately before any final harness. Keep actual readings and unmeasured mechanical dimensions explicit; software compilation does not complete the physical test.

## 2026-11-10 — Measured envelope before board outline
W/H/T define a rectangular bounding envelope only. Hole A's diameter does not locate its center. Do not cut holes, infer the irregular contour from perspective photographs or claim enclosure fit before the missing measurements are recorded.

## 2026-11-10 — Verify ECAD/MCAD datums per board
Use direct StepUp board import for enclosure work. Native KiCad STEP exports require explicit datum/stackup alignment. The synthetic fixture's measured export translation is a test observation, not a universal correction.

## 2026-11-09 — Establish the bench baseline first
- Reuse the established S3, ILI9341, XPT2046 and INMP441 assembly; preserve recovery data separately.
- Keep the GH-Wii U002 PCB, contacts, daughterboards and ribbons intact. Represent unknown circuitry as a black-box module.
- Exercise established display/touch/microphone wiring before adding gamepad inputs or control protocols.
- Own GPIO assignments in hardware/signals.json and generate the firmware header and pin table.
- Proposed joystick reservations are L-X5, L-Y6, R-X7, R-Y2. They remain disabled pending interface measurements. GPIO3 is a strap and is excluded.
- Reserve GPIO18/21 for possible future I2C and GPIO43/44 for UART0; do not activate new interfaces by assumption.
- Proposed J1 is an observer signal bundle with four axes, two stick clicks, ground and spare. It carries no power rail. Connector family, mating orientation, numbering, wire specification and electrical compatibility remain unresolved.
- Add actuator transport only after failsafe, arming, freshness, link-loss and deadman requirements are tested.

## 2026-11-13 — Single-pack controller power

The owner approved the MakerFocus 103665 pack, HiLetgo protected-output distribution, existing EGSCST load switch, donor gamepad battery lead and shared XL63020 3.3 V regulator. Charge with the handheld off. Bench sizing and assembly verification follow the [approved design](../electronics/POWER_SYSTEM.md).

## 2026-11-13 - Enclosure: original shell kept, add-on pod (owner)
The owner chose to keep the gamepad whole in its original shell and to house the display, both ESP boards, battery, charger, regulator, switch and microphone in a printed add-on pod. Signal wiring is left out of the enclosure work while a Bluetooth link is explored. Evidence: owner's reply in chat, 2026-11-13, to the concept `cad/enclosure/pod-r001`. Open: where the pod fixes to the shell and the shell's dimensions there, measured heights of the DevKitC, charger and regulator, the switch body, the direction of the 28 mm Dupont allowance. `pod-r001` remains a concept, not a printable part.
