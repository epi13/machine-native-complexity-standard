# MNCS repository agent guidance

## Joern graph-sensitive workflow

Use real Joern analysis before and after source edits involving control flow,
reachability, calls, control dependencies, dominance, post-dominance, data flow,
state transitions, authentication, authorization, input validation, error handling,
or cleanup. Manual source reading is not a substitute. Create a baseline, repeat the
same focused queries after editing, compare the post snapshot, run verification, and
report commands, graph findings, failures, unsupported features, and uncertainty.

## MNCS Forge

- Use the separately installed MNCS Forge MCP server only when a validated
  `mncs-forge.toml` declares the project authority and workflow.
- Forge is an optional, experimental, non-normative development control plane. It does
  not replace MNCS/MNCDS validation and is not required for conformance.
- Candidate generation and writes must stay within declared candidate/generated paths.
  Contracts, references, evaluators, policies, protected data, and historical evidence
  remain protected authorities.
- Keep MNCS, MNCDS, evidence-class, and promotion statuses separate. Missing or
  unsupported evidence remains `UNKNOWN`; `FAIL` dominates `UNKNOWN`, which dominates
  `PASS`.
- Do not use final evaluation as repair feedback for the same candidate epoch.
- A local Forge result cannot create independence, protected custody, witnessing,
  operational evidence, governance approval, certification, or promotion.
