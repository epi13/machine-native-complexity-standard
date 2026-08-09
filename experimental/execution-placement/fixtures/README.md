# Execution-placement fixture corpus

`valid/sequential-offload.json` is a generic, non-normative constrained-provider
observation. `tests/test_execution_placement.py` treats it as an immutable seed and
applies deterministic mutations for the adversarial corpus. The mutation matrix keeps
the complete record shape while exercising the following cases:

1. CPU-only success;
2. full accelerator success with an execution probe;
3. witnessed sequential CPU offload;
4. AUTO selecting offload under a budget;
5. AUTO bounded OOM recovery to CPU;
6. absent optional metrics;
7. accelerator discovery without a real probe (`UNKNOWN`);
8. sequential-offload configuration without a placement witness (`UNKNOWN`);
9. exact-cap success and cap exceedance (`FAIL`);
10. partial resource observation (`UNKNOWN`);
11. explicit CPU paired with accelerator execution;
12. explicit accelerator paired with CPU execution;
13. undeclared AUTO fallback;
14. stale environment identity;
15. changed runtime identity;
16. sequential offload confused with permanent accelerator residency;
17. reduced precision without its required probe;
18. runtime crash during a transition;
19. conformance claimed from placement evidence; and
20. independent operation claimed from local execution.

The test matrix is intentionally mutation-style and dependency-free. It does not use
GPU hardware or turn an observation into a universal performance claim.
