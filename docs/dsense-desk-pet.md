# dSense Desk Pet case study

The dSense Desk Pet case study is a physical Arduino Uno experiment in recursive embedded cognition and machine-native representation.

Its light, piezo, button, timing, OLED, RGB, buzzer, state, and prediction signals participate in a
bounded feedback system. The pet exposes expressive behavior and an on-device introspection menu,
while its compact execution state remains replaceable as one firmware image.

## Why it belongs in the case-study corpus

The study records two unfavorable observations instead of hiding them:

- the first acoustic detector fired near its refractory limit in both quiet and stimulated
  segments, saturating novelty; and
- the later human-readable interface exceeded the Uno's available program storage.

Those failures recursively changed the next development epochs. Acoustic state was split into
baseline, onset, sustained presence, self-sound, and external energy. Human labels and CSV
formatting were then moved off the microcontroller into readable host tooling, while the OLED and
serial link adopted compact icon/numeric and binary representations.

The repository contains the failing baseline, frozen V5 candidates, a canonical telemetry extract tied to the original capture hash, reproducible analysis, a readable contract, preregistered hardware gates, a threat model, and a bounded assurance case.

## Status

Offline evidence and framing checks pass. The final AVR compile and physical V5 response protocol
have not yet been captured as repository-bound evidence. Formal MNCS and MNCDS status therefore
remain `UNKNOWN`, and promotion is unauthorized.
