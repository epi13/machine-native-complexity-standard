# Acceptance policy

The complete conceptual policy is:

```text
behavioral_pass
AND holdout_pass
AND safety_pass
AND resource_bounds_pass
AND compiler_matrix_pass
AND required_invariants_pass
AND measurement_valid
AND useful_benefit_threshold_met
AND worst_case_regression_within_policy
AND provenance_complete
```

The claimed cumulative level selects which gates are REQUIRED. Each gate is PASS,
FAIL, or UNKNOWN. Any required FAIL yields FAIL. Otherwise any required UNKNOWN
yields UNKNOWN. Only all required PASS yields PASS.

The policy MUST declare whether UNKNOWN is rejected or routed to manual review.
Manual review MAY create new evidence or an explicit exception record, but MUST NOT
rewrite UNKNOWN as provider PASS. Objectives MUST precede generation.
In schema 0.1.1 acceptance policy declares what must be true; it MUST NOT contain
authoritative observed PASS values. It declares the conformance level, cumulative
required gate names, `on_unknown`, conflict policy, objective/unit/direction,
threshold, minimum sample count, noise policy, and worst-regression limit.

Observed results are separate indexed records. Validators aggregate each required
gate deterministically with FAIL taking precedence over UNKNOWN and UNKNOWN taking
precedence over PASS. An empty evidence set derives UNKNOWN and is invalid for a
required gate. The claimed-level aggregate becomes the computed final result.

Requirements are cumulative and conditional. Lower levels MUST NOT add placeholder
higher-level evidence merely to report UNKNOWN.
