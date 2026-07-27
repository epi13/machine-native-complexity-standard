# EdgeStream design

The readable reference uses bytewise little-endian decoding and a bitwise CRC-32. The
machine candidate is regenerated from the reference and replaces the CRC loop with a
specialized 256-entry table. The transformation is intentionally narrow: all state,
classification, JSON output, and checkpoint behavior remain shared and are tested for
byte-identical behavior.

The study is more demanding than the preliminary HTTP decoder because correctness spans
long-lived per-device state, rolling aggregation, sequence rollover, explicit event time,
alarm transitions, bounded admission, persistence, recovery, and injected checkpoint
failures.

The required structural provider is a bounded local source checker. Joern is optional and
was unavailable in the captured run, so Joern-specific evidence is recorded as UNKNOWN
and is not silently converted to PASS.
