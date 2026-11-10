# First gamepad measurements

Take these with the S3 and its harness disconnected. Use the original gamepad power arrangement. Use DC voltage mode on a powered board; resistance/continuity only after battery and USB are disconnected. Record values in measurements/electrical.csv with power state, reference point, instrument and date.

| Reading | Conditions |
| --- | --- |
| Battery B+ to GND | Original battery; note charger disconnected/connected separately |
| VCC to GND | Gamepad on; repeat gamepad off |
| +5V to GND | Battery only; repeat original USB charging arrangement |
| L-X and L-Y | Each axis minimum, center, maximum |
| R-X and R-Y | Each axis minimum, center, maximum |
| One face-button signal | Released and pressed, identify the exact pad |
| One shoulder signal | Released and pressed, identify the exact pad |
| L-3 and R-3 | Released and pressed |

These readings establish whether observing the powered board is plausible. They do not by themselves prove absence of button scanning or off-state backfeeding. If readings fluctuate, use an oscilloscope/logic analyzer or characterize that group before connecting it.

Do not join S3 3V3 to gamepad VCC, B+ or +5V based on labels. Series resistors are not level shifters. Do not connect either processor's outputs together.

For mechanical modeling, measure PCB width/height/thickness, mounting-hole diameter and centers from a named datum, joystick centers/height/travel, screen module and S3 outlines, battery dimensions, USB position and ribbon reach. Leave unknown values blank. No need to trace every board connection.
