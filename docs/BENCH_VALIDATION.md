# Bench validation scope

Bench firmware0.1.1 passed9 live display/touch/microphone self-tests and a bounded five-minute soak. The owner confirmed smooth, responsive touch and microphone response after the refresh/capture fix. Repeated capture kept the recorded maximum loop at26.369 ms; the earlier synchronous capture blocked for22.426 seconds.

Public `tests/fixtures/soak/` contains selected original timing/status records with private context excluded. Host regression tests reject the blocking case and accept the bounded capture interval. Full logs, recovery checks and device identity remain private. These checks do not qualify battery life, radio safety, enclosure fit or long-term operation. LCD memory capture does not prove the physical panel is illuminated.
