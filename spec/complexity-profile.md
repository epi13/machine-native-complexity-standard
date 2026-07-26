# Complexity profile

MNCS rejects a single universal complexity score. A profile reports throughput,
latency, worst-case performance, memory, binary size, source size, changed lines,
CFG-node count, cyclomatic complexity, state count, branch count, portability,
generation cost, validation cost, conformance level, unresolved UNKNOWN count, and
operational criticality. Units and measurement methods belong in evidence.

Candidate A **Pareto-dominates** B when they meet the same contract, A is no worse
on every compared evidence/benefit/complexity dimension, and A is strictly better on
at least one. If each is better on some dimension, they are incomparable. MNCS does
not invent arbitrary hidden weights.

A candidate SHOULD normally be rejected when another candidate meets the same
contract, has equal or stronger correctness and safety evidence, provides equal or
better declared benefit, and has lower complexity or lifecycle cost.

Complexity itself MUST NOT count as a benefit.
