# EdgeStream to Remote Water Integration Study

This development-only study evaluates a narrow telemetry-envelope boundary between the
EdgeStream case study and the Remote Water Resilience Controller. It does not merge either
component's evidence graph, claim, evaluator, or release identity.

The integration runner refuses to execute unless:

- the checked-in EdgeStream development summary is `PASS`;
- the checked-in Remote Water development summary is `PASS`;
- the two evidence roots, component identities, and evaluator identities remain distinct;
- neither component's formal claim is promoted by the integration result.

The adapter accepts a normalized JSON envelope with a sequence number, observation and
receipt times, tank level, demand, power state, and quality. It maps that envelope into the
Remote Water telemetry model and executes the readable safety authority boundary. No C
binary is imported into Python and no industrial protocol or actuator output is present.

Run from the repository root:

```bash
python case-studies/edgestream-remote-water-integration/tools/run_study.py
```

The result is written to `evidence/results/integration-summary.json`. A passing integration
result means only that the declared envelope and evidence-boundary checks passed in the
captured development environment.
