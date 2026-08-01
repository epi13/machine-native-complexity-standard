# MNCS Forge MCP integration

> Experimental, non-normative integration. MNCS Forge is not required for MNCS
> conformance and is not an accredited certification system.

[MNCS Forge](https://github.com/epi13/mncs-forge-mcp) is a separate local stdio MCP
server and CLI that is the default Codex development and evidence-control interface for
this repository.
It makes authority paths, candidate lineage, development epochs, declared checks,
selection, freeze, evaluator mode, evidence gaps, and claim blockers explicit.

Forge is not Joern, a universal Code Property Graph implementation, or a structural
analyzer. Joern is one optional legacy provider. Compilers, analyzers, mutation tools,
sanitizers, benchmarks, and runtime harnesses remain replaceable providers. Forge does
not copy validator conformance decisions, and it never fills a missing analysis
capability with source reading, grep, or line counts.

## Interface and authority separation

| Layer | Purpose | Authority |
| --- | --- | --- |
| MCP | Interactive Codex tools, resources, and workflow prompts | Project configuration and Forge mode |
| Provider Protocol 0.1 | Deterministic analyzer request/response interface | Declared provider identity and bounded result |
| MNCS / MNCDS CLI | Offline validation and result derivation | Public schemas, commands, and validator rules |
| Analyzer or harness | Replaceable structural, behavioral, safety, resource, or performance evidence | Its declared scope, method, environment, and limitations |

Forge `0.1.0a2` adds explicit provider listing, bounded Provider Protocol capability
probing, executable/provider identity checks, and required-capability blockers. An
optional unavailable provider is reported as an informational UNKNOWN. A required but
unavailable or unsupported capability is a blocker and remains UNKNOWN.

Ordinary MNCS validation never launches Forge. Forge is not a normative dependency and
core CI does not fetch or execute mutable Forge `main`.

Forge cannot create independent evaluation, protected custody, witnessing, operational
evidence, or governance approval. A local result does not promote MNCS, MNCDS, an RFC, or
a case study. `REVIEW_REQUIRED` is a workflow disposition, not an MNCS result. `FAIL`
dominates `UNKNOWN`, and `UNKNOWN` dominates `PASS`; absent or unsupported evidence
remains `UNKNOWN`. MNCS implementation and MNCDS development-process results remain
separate.

## Declared project workflows

The committed configuration exposes project-scoped development workflows for tooling
inspection, the MNCS/MNCDS release-candidate check, the release-candidate corpus,
Python/Rust consumer comparison, the recursive analyzer study, full core `make check`,
and RAVEL 0.4 as an optional case-study regression check rather than a release gate.

Each workflow uses `scripts/forge_workflow.py`, which executes a fixed argv array without
a shell, captures bounded output, records command/environment/executable/output
identities, and distinguishes PASS, FAIL, UNKNOWN, timeout, crash, output limit, and
unsupported executable. Wrapper PASS means only that the declared development command
completed successfully; its conformance status remains UNKNOWN.

```bash
mncs-forge --config "$PWD/mncs-forge.toml" providers list
mncs-forge --config "$PWD/mncs-forge.toml" providers blockers
mncs-forge --config "$PWD/mncs-forge.toml" check development tooling-inspect
mncs-forge --config "$PWD/mncs-forge.toml" check development release-candidate-check
```

No provider is enabled by default. See the [provider transition](provider-transition.md)
before adding one.

## EdgeStream compatibility workflow

The repository-root `mncs-forge.toml` also retains the current EdgeStream candidate,
generated output, contract, reference, evaluators,
preregistration/acceptance policy, development evidence, and MNCDS record. Its protected
path list is empty because the case study has no protected holdout. It does not rewrite
or promote historical evidence.

After installing the separate repository, start a new Codex session so the MCP tool
inventory and configuration are reloaded:

```bash
/path/to/mncs-forge-mcp/scripts/install-codex-mcp.sh \
  "$PWD/mncs-forge.toml"
mncs-forge --config "$PWD/mncs-forge.toml" inspect
mncs-forge --config "$PWD/mncs-forge.toml" status
mncs-forge --config "$PWD/mncs-forge.toml" blockers promotion
mncs-forge --config "$PWD/mncs-forge.toml" check development \
  edgestream-read-only-inspect
```

The inspection workflow only confirms that expected visible files exist. It is not proof
of schema validity, correctness, independence, or custody. A future controlled epoch
would begin with explicit identities:

```bash
mncs-forge --config "$PWD/mncs-forge.toml" epoch begin \
  --generator future-generator-id --evaluator development-evaluator-id
```

That command creates new local `.mncs-forge/` state and should not be run during a
read-only review. Evaluator mode is a separate `--mode evaluator` process, requires a
newly selected and frozen candidate, verifies frozen identities, and must not be used as
repair feedback for the same development epoch. The development MCP inventory does not
expose the final-evaluation tool; use a separately configured evaluator session.

See the [post-Wave-Five roadmap](post-wave-five-roadmap.md) for physical-machine,
external-actor, and governance gaps that Forge cannot resolve locally.
