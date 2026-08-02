# Codex implementation next steps

This document converts the remaining findings from the integrated MNCS, MNCDS, and
MNCS Forge review into bounded follow-on work for a Codex agent. It is a development
roadmap, not a release authorization record. Completing a local task cannot create
independent evaluation, protected custody, external review, governance approval,
certification, or promotion.

## Work completed before this backlog

The repository already has the release-candidate schemas, Python validator, independent
Rust consumer, 74-case shared corpus, graph-impact closure, package and attestation
cross-checks, separated core and experimental CI authority, and a hardened project Forge
integration. The companion Forge repository has bounded subprocess execution,
capability probing, micro-verifier matching and execution, deleted-path identities,
terminal `UNKNOWN` records, heterogeneous bounded batches, and desktop-platform CI.

The small consistency fixes accompanying this roadmap correct the public corpus count,
name the hardened Forge workflow entrypoint, document the existing version-reporting
contract, and make this backlog visible from the documentation navigation.

## Execution rules for Codex

For every task below, Codex must:

1. inspect the current implementation and tests before changing code;
2. preserve `FAIL > UNKNOWN > PASS` and keep MNCS and MNCDS results separate;
3. add negative regression coverage for authority, identity, path, framing, timeout,
   output-bound, and stale-evidence behavior affected by the change;
4. avoid changing frozen normative semantics without an approved RFC or explicit
   release-candidate correction path;
5. retain old records and failed evidence rather than rewriting history;
6. state when a result is same-implementation-family or operator-controlled;
7. run the narrow relevant checks first, followed by the repository's full required
   check where practical; and
8. open a focused draft pull request rather than combining unrelated phases.

## Phase A — Forge implementation stabilization

These tasks belong primarily in `epi13/mncs-forge-mcp`. Corresponding integration
updates belong in this repository only when the public Forge interface changes.

### CODEX-NEXT-001: Remove import-time verifier service replacement

Replace the package-import mutation that swaps `MicroVerifierService` with an explicit,
statically visible implementation selection. Prefer making the hardened service the
normal implementation or importing it directly from the engine.

Acceptance criteria:

- importing `mncs_forge.engine` directly and importing `mncs_forge` first select the
  same service class;
- no module namespace mutation is required to activate hardening;
- CLI and MCP behavior remain identical;
- strict typing, tests, and benchmark smoke checks pass; and
- compatibility notes identify any intentionally retained public import.

### CODEX-NEXT-002: Introduce one bounded strict JSON loader

Create a shared loader for Forge configuration-adjacent records, Provider Protocol
responses, ledger records where applicable, and project-owned provider inputs. It must
reject duplicate keys, non-finite numbers, malformed UTF-8, excessive depth or
collection size, and unsupported root types.

Acceptance criteria:

- duplicate-key and `NaN`/infinity fixtures fail deterministically;
- Provider Protocol framing still requires exactly one non-empty JSON Lines response;
- existing valid provider and ledger fixtures remain compatible;
- error codes distinguish framing, malformed JSON, and limit violations; and
- no ordinary validation or discovery path executes a provider.

### CODEX-NEXT-003: Add ledger and immutable-record recovery

Add a read-only audit and explicit recovery workflow for crashes between immutable
record creation and ledger append.

Acceptance criteria:

- audit reports orphan immutable records, missing referenced records, unterminated
  verifier actions, duplicate identities, and incompatible sequence/linkage;
- recovery never edits or deletes prior ledger entries;
- recovery appends a deterministic recovery or interrupted-state record;
- every started verifier action can be shown to have a terminal result or explicit
  interrupted state; and
- tests simulate termination at each write boundary.

### CODEX-NEXT-004: Bind effective interpreter and toolchain identities

For evaluator-mode execution, record the actual interpreter or executable, version,
provider source/package identity, dependency-lock identity, and relevant toolchain
identity rather than relying only on the configured script path.

Acceptance criteria:

- drift in the resolved interpreter or pinned dependency identity invalidates the
  frozen execution and remains `UNKNOWN` or `FAIL` according to the declared rule;
- development mode may remain less strict but must disclose weaker binding;
- evaluator records expose identities without leaking environment values; and
- Windows, macOS, and Linux tests cover interpreter resolution.

### CODEX-NEXT-005: Define separate and aggregate output bounds

Replace ambiguous single-stream interpretation with explicit stdout, stderr, witness,
result, and aggregate retained-output limits.

Acceptance criteria:

- configuration schema and documentation define each limit;
- both POSIX and Windows runners enforce per-stream and aggregate caps;
- exceeding a cap terminates execution and preserves required facts as `UNKNOWN`;
- redaction occurs before disclosed excerpts and status-only result identity; and
- boundary tests cover exact-limit, one-byte-over, and simultaneous-stream output.

### CODEX-NEXT-006: Decompose the Forge engine

Refactor the large `Forge` coordinator behind a compatibility facade. Suggested
services are authority, provider, epoch, candidate, workflow, verifier, evaluation,
evidence, and bundle services.

Acceptance criteria:

- CLI and MCP continue to call one public facade;
- policy is not duplicated between services or interfaces;
- final evaluation remains unavailable from a development-mode MCP inventory;
- provider and workflow authority checks remain centralized; and
- tests prove the refactor does not broaden writable paths, executable selection, or
  result disclosure.

### CODEX-NEXT-007: Add scalable ledger verification and optional anchoring

Avoid rereading and rehashing the entire ledger on every append while preserving a
full-verification command.

Acceptance criteria:

- append verifies a trusted local head plus the new tail under the existing lock;
- periodic checkpoints can be independently recomputed from the full ledger;
- stale, replaced, or inconsistent head state is rejected;
- external timestamping or signatures are optional and never mislabeled as protected
  custody or governance approval; and
- migration from the current ledger format is explicit and lossless.

## Phase B — MNCDS and validator maintainability

### CODEX-NEXT-008: Modularize MNCDS validation

Split the current MNCDS validator into focused modules for roles, lineage, partitions,
selection, reproducibility, independence, release controls, and aggregate result
reconciliation while retaining the existing public API and CLI.

Acceptance criteria:

- the existing corpus produces byte-equivalent machine-readable categories and issue
  codes unless a separately documented defect is corrected;
- profile ordering and `FAIL > UNKNOWN > PASS` remain unchanged;
- no module can silently promote developer-withheld evidence to protected custody;
- property or mutation tests cover lineage cycles, authority conflicts, contaminated
  holdouts, and required `UNKNOWN`; and
- the compatibility facade remains the documented import path.

### CODEX-NEXT-009: Establish one release-metadata source of truth

Create a machine-readable release metadata record for current normative family,
release-candidate families, corpus size, supported schema versions, package format,
consumer agreement, Forge integration version, and release-gate state. Generate or
validate repeated documentation statements from it.

Acceptance criteria:

- `mncs version --json`, release documentation, and corpus summaries agree;
- CI fails when the documented corpus count or current RC identifier drifts;
- historical version documents remain frozen;
- generated text is clearly marked or validation-only tooling leaves authored prose
  intact; and
- package-format and standard-version identifiers remain separate concepts.

## Phase C — New bounded verification capability

### CODEX-NEXT-010: Add micro-verifiers by uncertainty class

Add narrow verifier families rather than one universal analyzer. Candidate families
include compiler diagnostic normalization, symbol/interface change impact, concurrency
and lock-order evidence, unsafe FFI boundaries, resource-bound extraction, benchmark
protocol validity, mutation-survival summaries, sanitizer normalization,
deterministic-build comparison, and schema-to-code binding.

Acceptance criteria for each verifier:

- one bounded claim, explicit assumptions, limitations, cost, timeout, scope, input
  kinds, and uncertainty classes;
- no caller-controlled argv, executable, environment, shell, or working directory;
- strict positive, negative, unsupported, timeout, crash, stale, and output-limit
  fixtures;
- a declared dependency envelope with completeness status; and
- a narrow `PASS` that cannot be interpreted as whole-program correctness or MNCS
  conformance.

### CODEX-NEXT-011: Add an adversarial provider sandbox profile

Define an optional container or host-sandbox profile for providers that are not trusted
with ambient host permissions. Forge itself must continue to state that its ordinary
runner is not an OS or network sandbox.

Acceptance criteria:

- the sandbox profile is explicit, optional, and separately identified;
- filesystem, process, and network policies are tested with adversarial fixtures;
- unsupported sandbox availability remains `UNKNOWN` rather than falling back silently;
- provider output and identities remain compatible with Provider Protocol records; and
- documentation distinguishes trusted-provider execution from adversarial isolation.

## Phase D — Empirical Forge evaluation

### CODEX-NEXT-012: Run a preregistered Forge effectiveness study

Compare no-Forge development, Forge orchestration only, Forge plus micro-verifiers, and
legacy analyzer-assisted workflows where the language and analyzer support the task.

Measure task completion, escaped defects, false `PASS`, retained `UNKNOWN`, verifier hit
rate, useful findings, retries, elapsed and subprocess time, token and output volume,
crashes, timeouts, stale-evidence detection, and human-review effort.

Acceptance criteria:

- tasks, partitions, metrics, stopping rules, and analysis are frozen before the final
  partition is opened;
- raw observations, failures, unsupported cases, and `UNKNOWN` results are retained;
- the study separates architectural cleanliness from measured performance;
- same-operator results are labeled operator-controlled; and
- no benchmark result is used as same-epoch repair feedback for the final partition.

## Phase E — External and governance gates

Codex can prepare records, templates, issue maps, checklists, and exact artifact
identities for these tasks. Codex cannot satisfy the gate or name an authority that has
not legitimately accepted the role.

### CODEX-NEXT-013: Prepare RFC 0004 and RFC 0005 decision packets

Assemble exact text, schema, corpus, implementation, migration, security-review,
conflict-disclosure, and dissent records for non-conflicted human review. Final approval
must remain open until recorded by eligible governance participants.

### CODEX-NEXT-014: Prepare independent contract-domain review

Create a reviewer packet covering intended use, exclusions, state and error behavior,
adversarial behavior, external effects, safety/security invariants, limits, environment
assumptions, compatibility, oracle limits, and unresolved ambiguities. The review itself
must come from an eligible external domain reviewer.

### CODEX-NEXT-015: Prepare external security and privacy review

Freeze the reviewed commit and artifacts; provide the threat model, parser and archive
bounds, identity and downgrade rules, provider and Forge trust boundaries, privacy
handling, known limitations, regression corpus, and finding template. External
acceptance or rejection must be recorded without relabeling internal review.

### CODEX-NEXT-016: Prepare externally controlled MNCDS evaluation

Produce a reproducible evaluation kit that lets an external custodian freeze candidate,
evaluator, thresholds, partitions, and policy before opening a fresh final partition.
The external actor must control custody and operation; local machines, languages, or
executables cannot manufacture organizational independence.

### CODEX-NEXT-017: Prepare bootstrap governance and release authority records

Prepare roster, succession, inactivity, emergency-access, conflict, namespace,
release-authorization, signing-custody, and exact-artifact templates. Leave every
assignment `OPEN` until a legitimate public decision records the responsible person or
body.

## Suggested PR order

1. Forge service activation and strict JSON parsing.
2. Ledger recovery and explicit output-limit semantics.
3. Evaluator interpreter/toolchain binding.
4. Forge engine decomposition and scalable ledger checkpoints.
5. MNCDS modularization and release-metadata validation.
6. One micro-verifier family per focused PR.
7. Sandbox profile and preregistered effectiveness study.
8. External-review and governance preparation packets.

Each pull request should reference the applicable `CODEX-NEXT-*` identifier and state
which acceptance criteria were demonstrated, which remain `UNKNOWN`, and whether an
external actor is still required.
