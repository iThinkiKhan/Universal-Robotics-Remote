# Staged project plan

The next bounded experiment is [LX-01](TEMP_INPUT_TEST.md). Complete its S3-only reference and supervised single-axis gates before expanding inputs. Its temporary signal-break procedure is not the permanent power-off-safe interface design.

## 0. Recover and identify
Record chip, flash, PSRAM, bridge identity, security state and the existing interface. Read all flash; verify against the device; hash the image. Retain a recovery procedure. Inspect original source without exposing its secrets.

Exit: verified private backup, repeatable serial identification, documented source provenance.

## 1. Make the S3 a dependable bench instrument
Build a local diagnostics UI with display identification, saved touch mapping, microphone level/sample health, heap, uptime and PSRAM checks. Support UART bridge and native USB. Keep gamepad pins high impedance and all control/radio functions absent. Capture hardware evidence and run a bounded soak.

Exit: physical display confirmed by the project owner, display register and memory capture pass, real touch events observed, nonzero microphone samples and a response-to-sound check, firmware self-test pass, no resets during the recorded soak. A build alone does not close this milestone.

## 2. Establish the gamepad's interface
Use its original battery/charging arrangement with the S3 electrically disconnected. Record logic and USB rail voltages, joystick extrema/centers, one face and shoulder button's released/pressed voltages, and power-state behavior. Check continuity only with every source disconnected.

Exit: input voltage ranges and button topology established, power/off-state backfeeding handled, common-ground and observer strategy documented. Then enable one measured input group at a time.

## 3. Harness and electronics
Choose locking connector part numbers, view/orientation, pin 1, wire colors, lengths and strain relief. Generate WireViz documentation from canonical assignments. Create a KiCad system schematic with the original PCB as a black-box module. Consider an MCP23017 only after independent button inputs and voltage compatibility are established.

Exit: reconciled schematic/harness/firmware mappings; point-to-point continuity and powered checks recorded for each installed connection.

## 4. Controller application and transport
Define actual target devices and protocol requirements. Add joystick calibration/deadzones, debounced button events, profile selection, telemetry and transport abstraction. Specify sequence numbers, freshness, neutral state, receiver timeout, arming and deadman behavior before enabling actuators. Voice remains a separate optional feature.

Exit: bench receiver tests including stale/duplicate packets, reboot, disconnect and stuck inputs; no uncontrolled actuator motion.

## 5. Mechanical integration
Measure board outlines/holes, component heights, joystick travel, ribbons, screen window, USB access, battery and antenna clearance. Model parts in FreeCAD and check the assembly. Prototype mounting and cable routing before final shell design. Deliver models for the project owner to slice.

## Shared working record
- `hardware/`: canonical electrical signals and component registry.
- `measurements/`: recorded readings, physical dimensions and source photos.
- `electronics/`: physical harness definitions and future KiCad files.
- `firmware/`: controller diagnostics and later application.
- `cad/`: measurement-led native CAD.
- `exports/`: derived STEP files, drawings and review assets.
- `scripts/cad/`: portable photo and board-survey tools; firmware utilities retain tools/.
- `evidence/`: dated build logs, captures and live checks.
- `docs/`: engineering decisions, guidance, validation and plan; root STATUS.md and HISTORY.md summarize progress.

Each electrical connection progresses through proposed → installed → measured → verified, with evidence. A drawing does not change its physical status. Coordinate changes through issues and pull requests; do not create competing copies of the assignments.
