# Remote Water Resilience Controller

The Remote Water Resilience Controller is a development-only MNCS case study for a composed,
fault-aware supervisory control system. It deliberately advances beyond the EdgeStream
component study by separating machine proposal authority from readable safety authority and
by evaluating state, recovery, audit continuity, system dependencies, and multi-objective
utility together.

The bounded digital twin contains one tank, one duty pump, one standby pump, variable demand,
power interruption, degraded telemetry, checkpoint restart, and a hash-chained intent
journal. A deterministically generated table planner proposes pump states. A compact safety
kernel independently enforces high-high shutdown, low-low response, telemetry hold,
power-loss shutdown, pump ordering, minimum dwell, sequence, and intent-expiry rules.

The current repository evidence is a transparent development epoch. The experimental
contract profile and combined assurance case remain `UNKNOWN` for formal MNCS and MNCDS
status. Protected holdout evaluation, independent review, cross-host reproduction, release
binding, and operational evidence are explicitly deferred rather than simulated or implied.

The implementation cannot emit industrial control traffic and must not be connected to live
equipment. Its utility is in commissioning-oriented sequence review, operator-training
simulation, fault injection, planner comparison, and continued development of machine-native
composition and lifecycle evidence.

Run the complete development study from the repository root:

```bash
make remote-water-study
```

The case-study source and records are under `case-studies/remote-water-control/`.
