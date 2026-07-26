# Conformance levels

Levels are cumulative. A manifest MUST claim exactly one level and meet every lower
level. A failed candidate MAY retain a valid evidence bundle with `final_status:
FAIL`, but it MUST NOT claim acceptance.

## MNCS-L1 — Behavioral Conformance

L1 requires a readable functional contract; readable reference implementation or
executable oracle; semantic or differential evaluation; generated edge cases;
deterministic result accounting; strict compiler or language-tool warnings; and
declared limitations.

## MNCS-L2 — Safety Conformance

L2 adds appropriate memory or runtime-safety evaluation; integer, bounds, and
overflow evaluation; malformed-input evaluation; property testing or fuzzing;
known-bad mutation detection; resource-limit enforcement; and specified failure-state
behavior.

## MNCS-L3 — Structural Conformance

L3 adds declared structural invariants; tool-neutral invariant evidence;
sensitive-operation ownership; state-transition restrictions; forbidden-path
evaluation; explicit PASS, FAIL, and UNKNOWN; stated assumptions and bounds; and
witnesses or evidence references where available.

## MNCS-L4 — Performance Conformance

L4 adds repeated measurements; representative corpora; randomized or alternating
order; semantic checksums; a noise policy; worst-corpus regression limits; platform,
compiler, and build metadata; binary-size and memory reporting; a predeclared useful
benefit threshold; and separate fields for measurement validity and performance
victory.

## MNCS-L5 — Regeneration and Audit Conformance

L5 adds locked generator and evaluator versions; complete input and tool hashes; an
immutable evidence index; a reproduction command; a rollback-capable readable
implementation; independent or holdout reevaluation; and evidence that the certified
implementation was not silently modified.

The validator computes the required gate set from the claimed level. Missing or
UNKNOWN required gates prevent PASS.
