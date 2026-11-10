# Synthetic ECAD/MCAD toolchain fixture

This is a software validation board, **not controller geometry or a fabrication/print design**. It is deliberately 50x30x1.6 mm, with two 3.2 mm holes and one standard library pin header. None of those values are measurements of the project owner's gamepad, display or S3.

The native FreeCAD review contains the imported populated PCB, a blue test block clear by 3 mm, and a red block intentionally contained inside the PCB volume (toggle the PCB's visibility to see it). The 16 mm3 collision is an expected test case, not an accepted enclosure design. See `fixture.json`, ../../exports/toolchain-smoke/validation.json and ../../docs/ECAD_MCAD.md.

Reference model: installed KiCad Packages3D `Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x04_P2.54mm_Vertical.step`, SHA-256 `a74079b8d06bda78847623b39ee1855ffd1d9a8c1e896b349e4f1dc2056d44d9`. Upstream: https://gitlab.com/kicad/libraries/kicad-packages3D. Machine inventory remains private. See ../../THIRD_PARTY.md for upstream attribution.

Rebuild in an isolated build directory with `~/bin/ecad-smoke-test`. STEP and preview exports are under exports/toolchain-smoke. No STL, slicer configuration or G-code is generated.
