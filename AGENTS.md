# MNCS repository agent guidance

## MNCS Forge

- The empirical Forge project configuration and study providers live in the dedicated
  `mncs-reference-studies` repository. Use that configuration for empirical study work.
  This standards repository has no Forge configuration that ordinary core validation
  depends on.
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

## Provider-neutral structural evidence

- Use Forge to inspect declared providers, capabilities, availability, limitations, and
  capability blockers before claiming structural, control-flow, or data-flow evidence.
- Use an appropriate declared provider when a change requires that evidence. Joern is
  one optional legacy provider and is not the standard or default.
- Source reading is review, not independent structural verification. Do not substitute
  grep, line counts, or manual inspection for a missing analyzer capability.
- If no suitable provider is available, preserve the limitation and report `UNKNOWN` or
  a blocker, never `PASS`.
- When comparative structural evidence is claimed, run the same declared provider and
  method before and after the graph-sensitive change and report failures, unsupported
  constructs, limitations, and uncertainty.
- Never rewrite historical Joern outputs or frozen baselines merely because the default
  development interface changed.
