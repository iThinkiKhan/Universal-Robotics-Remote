# Contributing

Read README.md, STATUS.md, docs/PROJECT_PLAN.md and the engineering records relevant to your change. Discuss substantial work in an issue, state the intended result and files involved, then use a branch or fork and open a pull request. Coordinate overlapping edits and preserve others' changes.

Measurements, native CAD and registries own technical facts. Record measurement method, conditions, units, datum and uncertainty when known. Leave unknown values blank. A photograph or silkscreen label does not establish dimensions or electrical compatibility.

Run the privacy check, generated-file check and unit tests shown in README. Build pinned firmware when firmware or hardware configuration changes. CAD changes require native reopening, geometry/units/datum validation and a review image. Distinguish live, simulated and compile-only results. A successful build does not authorize operating hardware.

Review staged content and embedded metadata before pushing. Exclude credentials, device backups, local configuration, host administration and internal coordination files. A pull request should describe the problem, resulting behavior, validation and remaining uncertainty. Keep public engineering status and decisions current when they change.

Preserve the gamepad PCB, daughterboards and ribbons. Proposed GPIOs remain disabled until compatibility is measured. No actuator commands should be enabled before receiver failsafe, arming, link-loss timeout and deadman behavior are designed and tested. No printable enclosure or G-code is currently released.
