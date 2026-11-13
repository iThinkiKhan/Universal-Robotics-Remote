# Protected-output power verification plan

Use the [approved circuit](../POWER_SYSTEM.md), its [terminal netlist](netlist.md) and the [measurement worksheet](../../measurements/templates/power-verification-20261113.csv). All physical results are pending.

## Before connecting the remote

With all power removed, identify B+/B− and OUT+/OUT− on the HiLetgo, confirm the switch common and ON throw, and verify the donor connector mating view. Use voltage mode with an isolated pack/pigtail to establish polarity. Preserve all required sense contacts. Verify the shared regulator output setting with boards disconnected and a bench supply at nominal cell voltage. Confirm the exact S3 carrier supports external regulated 3.3 V. Unplug any old L-X probe before changing supplies.

## Sizing tests

Use a current-limited supply and dummy load to check REG1 near full, nominal and low cell voltages. Apply load steps within the module rating and measure at each ESP header. A proposed rail target is 3.135–3.465 V within every attached component's limits. A DMM captures static voltage; use a scope to assess transient dips. Check both ESPs and the lit display together, gamepad active and sleeping, and motors if used. Use a rated temporary path in place of SW1 for initial characterization. Compare load current and switching surge with the actual contact ratings before applying them to SW1. Switch and cable drop, regulator temperature and protection margin determine component sizing.

## Charge and service checks

In OFF, the fuse and B pair still connect the pack to the HiLetgo and the handheld load positive is open. Confirm branch voltage decay and off current. Verify approximately 500 mA constant current, pack-approved CV voltage, taper and termination with the loads off. Record temperature and charge conditions. Verify routine USB connection only at CHG1. The circuit also allows USB with SW1 on, so unplug charging USB before selecting ON. For PC USB programming, remove the target board's 3V3 feed and inter-board signal leads before connecting it.

With the ESP and gamepad signal connections separated, record stick response when gamepad VCC actually falls and whether its own power key restores it. Rail decay and sleep can leave one side of an input powered. Confirm the permanent signal interface for that condition before joining it. No circuit continuity check or repository test establishes this hardware behavior.
