# Remote Water Resilience Controller

This case study is an executable, development-only digital twin and supervisory controller
for a bounded remote water system. A deterministically generated table planner may propose
commands, but a compact readable safety kernel owns authorization. The code has no industrial
protocol or actuator output and must not be connected to live equipment.

## Epoch-2 evidence hardening

The second development epoch adds:

- terminal-state normalization using baseline-equivalent stored-water inventory;
- per-scenario limits for adjusted energy, starts, reserve, unmet demand, and overflow;
- explicit counts for accepted, modified, held, and rejected planner proposals;
- combined outage/stale, restart/degraded, near-empty, demand-model-error, and repeated
  checkpoint-corruption scenarios;
- sixteen deterministic randomized development scenarios;
- an evaluator-lock workflow that generates exact scenarios after commit and compares fresh
  x64 and ARM64 GitHub-hosted virtual machines;
- a separate EdgeStream telemetry integration study that does not merge component claims.

The generated planner identity is `mncs.remote-water.generated-table.v2`. Its duty-start
boundary was raised from 50% to 55% so finite-horizon pump-start reductions cannot rely on a
materially lower terminal reserve.

## Terminal inventory normalization

Raw energy remains reported. A second comparison normalizes the candidate to the baseline's
terminal stored-water inventory:

```text
candidate adjusted kWh = candidate kWh
  - (candidate final liters - baseline final liters)
  * duty pump kW / (duty pump liters/second * 3600)
```

This prevents a controller from appearing efficient merely because it ends with less stored
water. It remains a development accounting method, not a hydraulic or pump-curve model.

## Safety authority evidence

Every authorized intent now records the original proposal, final command, safety disposition,
and reasons. Scenario evidence aggregates:

- `accepted_unchanged`
- `modified`
- `held`
- `rejected`

The safety kernel remains separately maintained and retains final authority over generated
planner output.

## Run

From the repository root:

```bash
make remote-water-test
make remote-water-study
make edgestream-water-integration
```

A local protected-at-execution campaign can be run with a seed:

```bash
make -C case-studies/remote-water-control protected PROTECTED_SEED=123456789
```

GitHub Actions generates the runtime seed only after the candidate and evaluator lock are
committed, then runs the same undisclosed scenario set on x64 and ARM64. This improves evidence
separation, but it is not an independent third-party holdout.

## Development result versus formal claim

The checked-in development run can pass its hard gates and selection objective. Formal
`MNCS-L5` and `MNCDS-D3` status remain `UNKNOWN` because independent domain review, independent
holdout control, release authority, physical-system evidence, monitoring, rollback operations,
and lifecycle evidence remain incomplete.

## Repository layout

```text
contract/                         experimental contract adequacy record
generator/                        readable generation specification
machine/                          deterministic generated planner table
src/water_control/                controller, safety kernel, journal, checkpoint, simulator
                                 and scenario definitions
tests/                            invariant, recovery, corruption, comparison, and objective tests
tools/run_study.py                repository-visible development evaluator
tools/run_protected_evaluation.py evaluator-locked runtime scenario campaign
tools/compare_protected_results.py cross-architecture evidence comparison
protected-evaluator-lock.json     frozen evaluator and candidate identities
evidence/results/                 deterministic checked-in development observations
preregistration.json              frozen epoch-2 protocol and thresholds
threat-model.json                 threat paths, mitigations, and residual UNKNOWNs
assurance-case.json               composed review-required assurance record
```
