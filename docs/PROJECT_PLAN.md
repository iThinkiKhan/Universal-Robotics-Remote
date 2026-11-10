# Staged project plan

## End product — integrated electromechanical design

The deliverable is **not only a case-fit 3D reconstruction**. It is a **design-ready, editable controller assembly**, with common identity and verified interface mappings across KiCad, WireViz and FreeCAD. The model must support designing the circuitry, harnesses, physical routing and eventual enclosure **from the same engineering records**. See [integration acceptance criteria and ownership in issue #5](https://github.com/iThinkiKhan/Universal-Robotics-Remote/issues/5).

- **KiCad / electronics:** full controller-level functional schematic (original GH-Wii U002 as a characterized black box with verified external pads; S3, touchscreen, microphone, connectors, power and any designed interface PCB). Unknown original internal nets are explicitly unknown.
- **Harness / WireViz:** **every** inter-module cable and original retained ribbon assembly, tracked by unique contact/connector/wire/harness IDs; mating view and pin 1, keying, part numbers, signal nets, colors/gauges, physical lengths, branches, service loops, strain relief and continuity-test endpoints. Render drawings, parts list and cut/termination list from canonical data.
- **FreeCAD / StepUp:** editable physical assembly with measured board geometry, separate daughterboards, actual connector positions and orientations, all modules, battery, access and keepouts, plus **3D routed cable bundles/wires** with bend/clearance constraints and fastening. The case must be designed around this assembly, not the other way around.
- **Cross-domain traceability:** a signal can be followed from an original PCB pad through a named connector/contact and individual wire to a named destination pin, and its cable location can be inspected in 3D. Part/connector/pin IDs and coordinate transforms are consistent. Software checks catch stale or conflicting representations. Where tool interchange is not automatic, provide explicit exchange scripts and review gates instead of claiming synchronization.
- **Fabrication and maintenance:** editable native design files, BOMs, harness build sheets, point-to-point test records, geometry/clearance reviews and versioned evidence. Every fact is marked proposed, measured, installed or verified as appropriate; no dimension or connection is invented to make a design look complete.

`hardware/signals.json` and `electronics/harnesses.json` remain current electrical assignment/harness authorities; `measurements/` records physical evidence; `cad/` and future KiCad files are native editable sources; `exports/` contains generated views. Extend the existing schema and generation/validation pipeline without maintaining parallel conflicting pin tables. Work is coordinated through issues and non-overlapping agent branches. The join between KiCad/FreeCAD and the harness routing is a work item, **not an already existing automatic capability**.

### Integrated model acceptance gate

Before calling the controller model **build-ready**, demonstrate: (1) every used connector pin maps consistently across schematic, harness and physical assembly; (2) every wire has named termination and length/cable-route rationale; (3) all assembled boards and connectors have measured or explicitly provisional geometry and pose; (4) the electrical schematic and hardware registry agree; (5) generated artifacts and BOM reconcile; (6) cable routing/clearances, strain relief, USB access and serviceability have been checked; and (7) native documents reopen editable with traceable source revisions. Unverified electrical interfaces and mechanical dimensions remain tagged unresolved and block fabrication release.

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
Choose locking connector part numbers, mating/pin 1 views, unique contact identifiers, wire colors/gauges, lengths/branches and strain relief. Model **all** controller wiring, not just J1, including existing ribbons and new removable interconnects. Generate WireViz drawings, cut/termination and continuity-test sheets from canonical assignments. Create an **editable KiCad controller-level schematic** with the original PCB as a characterized black-box module, all physical connectors, power architecture, and a proposed interface PCB where required. Consider an MCP23017 only after independent button inputs and voltage compatibility are established.

Exit: reconciled schematic / harness / BOM / firmware mappings; all terminal identities accounted for; point-to-point continuity and powered checks recorded for each installed connection; unknown electrical behavior marked and gated.

## 4. Controller application and transport
Define actual target devices and protocol requirements. Add joystick calibration/deadzones, debounced button events, profile selection, telemetry and transport abstraction. Specify sequence numbers, freshness, neutral state, receiver timeout, arming and deadman behavior before enabling actuators. Voice remains a separate optional feature.

Exit: bench receiver tests including stale/duplicate packets, reboot, disconnect and stuck inputs; no uncontrolled actuator motion.

## 5. Mechanical and harness integration
Measure board outlines/holes, connector locations/orientations, component heights, joystick travel, ribbon reach, screen window, USB access, battery and antenna clearance. Model **all physical modules and connector placements** in the same FreeCAD assembly coordinate system. Route 3D representations of wires and cable bundles between their actual contacts, recording required length/slack, bends, fastening, strain relief and enclosure clearances. Link these routes to the canonical harness IDs; review any ECAD/MCAD export and coordinate transforms. Prototype mounting and cable routing before final shell design. Deliver native editable assemblies and models for the owner to review and slice.

Exit: the whole controller—including its wiring—can be examined in 3D, and each routed cable can be traced to a schematic net, harness drawing, contact and build sheet. Enclosure geometry derives from this assembly, not an isolated PCB envelope.

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
