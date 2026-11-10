# Controller coordinate frame

The physical controller datum, board outlines and assembly axes have not been measured or agreed. Do not inherit Gladiator's robot-specific front/rear convention. Record the named datum, +X/+Y/+Z, units, mounting-side view and board-to-assembly transforms when physical dimensions are captured.

Firmware touch coordinates are already defined separately: ILI9341 landscape 320x240, rotation 1, origin upper-left. The saved affine touch map remains in the original portrait frame and is converted by firmware/include/Layout.h. This screen coordinate mapping does not establish an enclosure datum.

The 50x30x1.6 mm board in cad/toolchain-smoke is a synthetic software test fixture. Its coordinate system and dimensions are never controller geometry or measurements.
