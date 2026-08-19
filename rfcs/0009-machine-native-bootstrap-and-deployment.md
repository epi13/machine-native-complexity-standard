# RFC 0009: Machine-native bootstrap and deployment protocol

- Status: Draft
- Authors: epi13
- Created: 2026-08-19
- Review deadline: open
- Target version: Experimental / post-0.3
- Conflicts disclosed: none

## Summary

This RFC proposes that the main MNCS system own a first-class bootstrap and deployment protocol for acquiring, configuring, verifying, repairing, cloning, and reconciling MNCS components across supported hosts.

The proposal deliberately treats a conventional installer as only one client of a deeper machine-native control surface. A human may select components from a CLI or future graphical interface, while an authorized AI agent may invoke the same underlying protocol through a small, stable, structured interface. The intended result is that an agent can be told a high-level instruction such as "connect this machine to MNCS" or "make this host a Fabric worker" without having to rediscover repository layout, dependency order, platform-specific setup folklore, verification commands, or capability-registration rules.

The protocol is declarative. Callers describe desired state; MNCS discovers current state, resolves a plan, applies only authorized changes, verifies the resulting state, records a receipt, and registers newly available capabilities. Installation, upgrade, repair, role cloning, migration, and uninstall are therefore different reconciliation goals rather than unrelated script collections.

This RFC is initially experimental and non-normative. It does not modify MNCS 0.2 or MNCS 0.3-rc.1 conformance semantics and does not grant bootstrap receipts any automatic conformance, independence, custody, security, or promotion status.

## Motivation

The MNCS family is becoming a composed ecosystem rather than a single package. A new machine or agent may need some combination of the main MNCS tooling, Fabric, Harness, Forge, MNEL, RAVEL, MNCS Language, validators, providers, or later components. Today, the knowledge required to assemble those pieces tends to be distributed across repositories, platform notes, shell commands, service configuration, environment variables, and human memory.

That is tolerable while one operator understands the entire system, but it becomes a structural weakness as MNCS becomes more autonomous and more distributed. In particular:

- a human installer that merely executes fixed scripts does not give an agent a reliable machine-readable model of the system;
- an AI agent should not need to search repositories and infer dependency order before it can participate in MNCS;
- a newly added host should be able to declare a role rather than repeat an undocumented manual setup;
- repair and upgrade should use the same desired-state semantics as first installation;
- component discovery should be capability-driven and version-aware rather than hard-coded into one agent prompt;
- platform support should be explicit and evidence-backed rather than implied by generic shell logic; and
- privileged deployment must remain bounded even when an AI is the caller.

The goal is not "one click install" as an end in itself. The goal is a canonical bootstrap contract that makes the MNCS ecosystem self-describing enough for humans and machines to deploy it safely.

## Architectural principles

### 1. One bootstrap engine, multiple clients

The canonical behavior belongs to the MNCS bootstrap engine and protocol. CLI, future GUI, agent, Harness, Forge, Fabric, and MCP/RPC surfaces are clients. No client receives separate installation semantics.

### 2. Desired state, not shell-script choreography

The caller declares what should be present, absent, enabled, disabled, pinned, or assigned to a role. The engine computes how to move the observed host from its current state to the desired state.

### 3. Discovery precedes mutation

Every mutating operation begins from a structured discovery snapshot that records platform, architecture, runtime/tool availability, existing MNCS components, versions, services, relevant hardware capabilities, and declared blockers.

### 4. Plan before apply

The engine produces an inspectable plan before mutation. The plan identifies component actions, dependency actions, privilege requirements, downloads or repository acquisitions, configuration changes, service operations, expected verification checks, expected capability changes, and rollback boundaries.

### 5. Verification is part of deployment

A component is not considered available merely because files were copied or a package manager returned success. Each component declares verification checks and capability-registration criteria. Failed or unsupported checks remain explicit.

### 6. AI usability is a protocol property

Agent access is not implemented by teaching a model a long setup prompt. The system itself exposes a compact machine-readable bootstrap interface and catalog.

### 7. Least authority

Discovery and planning should generally require less authority than mutation. An AI caller receives only the deployment permissions granted to it. The bootstrap service must not turn arbitrary model output into unrestricted root shell execution.

### 8. Platform claims require evidence

Linux and Windows adapters may be implemented and validated as hardware becomes available. The `darwin`/macOS platform identifier is reserved from the beginning so manifests remain stable, but macOS support MUST remain explicitly `unsupported` or `unverified` until it is implemented and tested on owned or otherwise controlled Apple hardware. Absence of test hardware must not be papered over by presumed compatibility.

### 9. Role cloning is semantic, not disk cloning

MNCS clones a machine's declared role and reproducible configuration, not its secrets, machine identity, transient state, or hardware-specific values.

### 10. Reconciliation is idempotent

Applying an already-satisfied desired state should make no material changes. Repeated reconcile operations should converge.

## Terminology

**Bootstrap engine** — the implementation that discovers state, resolves plans, applies authorized actions, verifies results, and emits receipts.

**Component catalog** — the machine-readable inventory of MNCS components and their deployment contracts.

**Component descriptor** — versioned metadata for one deployable component, including acquisition methods, dependencies, supported platforms, configuration inputs, verification, capability outputs, and removal behavior.

**Desired-state manifest** — a caller-supplied declaration of the target MNCS state for a host or role.

**Observed-state record** — the discovered state of a target host at a point in time.

**Plan** — a deterministic or reproducibly explainable sequence/DAG of proposed deployment actions derived from desired and observed state.

**Apply receipt** — a record of actions attempted, actions completed, failures, changes, rollback results, and post-apply verification.

**Role** — a reusable desired-state profile such as `fabric-worker`, `controller`, `forge-host`, `validator-only`, or a future custom composition.

**Semantic clone** — materializing a role/profile derived from another host while excluding host identity, secrets, ephemeral state, and hardware-bound configuration unless explicitly mapped.

## Proposed protocol

The minimal bootstrap surface SHOULD expose the following operations independently of transport:

```text
mncs.bootstrap.discover
mncs.bootstrap.catalog
mncs.bootstrap.plan
mncs.bootstrap.apply
mncs.bootstrap.verify
mncs.bootstrap.reconcile
```

Optional lifecycle operations MAY include:

```text
mncs.bootstrap.export_role
mncs.bootstrap.clone_role
mncs.bootstrap.rollback
mncs.bootstrap.remove
mncs.bootstrap.receipt
```

A CLI may map these to commands such as:

```text
mncs bootstrap discover --json
mncs bootstrap catalog --json
mncs bootstrap plan desired-state.json --json
mncs bootstrap apply plan.json --json
mncs bootstrap verify --json
mncs reconcile desired-state.json --json
mncs role export fabric-worker-02 > fabric-worker-role.json
mncs role clone fabric-worker-02 --onto node-07
```

The exact CLI is non-normative. The protocol objects and state transitions are the important boundary.

## Bootstrap state machine

A deployment transaction SHOULD progress through explicit phases:

```text
UNKNOWN
  -> DISCOVERED
  -> PLANNED
  -> AUTHORIZED
  -> APPLYING
  -> VERIFYING
  -> SATISFIED | DEGRADED | FAILED
```

A transaction may additionally enter `ROLLING_BACK` and end in `ROLLED_BACK` or `ROLLBACK_INCOMPLETE`.

`SATISFIED` means the declared desired state and required verification checks were satisfied within the transaction's stated support boundary. It does not mean MNCS conformance, security certification, independence, or promotion.

`DEGRADED` means useful state was achieved but one or more declared optional or non-blocking properties remain unmet. Missing required verification MUST NOT be silently treated as success.

## Desired-state manifest

A desired-state manifest SHOULD be host-independent where possible and SHOULD contain at least:

- manifest schema/version;
- target role or explicit component set;
- component presence/absence requirements;
- version/channel/pinning constraints;
- optional feature selections;
- configuration references or non-secret values;
- platform constraints when needed;
- capability requirements;
- policy constraints such as network allowance, privilege ceiling, or allowed acquisition sources; and
- verification requirements.

Illustrative shape:

```json
{
  "schema": "mncs.bootstrap.desired-state/0.1-experimental",
  "role": "fabric-worker",
  "components": {
    "fabric": {"state": "present", "channel": "stable"},
    "harness": {"state": "present"},
    "forge": {"state": "absent"}
  },
  "requires_capabilities": ["fabric.worker"],
  "policy": {
    "network": "acquisition-only",
    "privilege": "prompt-or-authorized-helper"
  }
}
```

Secrets SHOULD be referenced through a secret-provider binding or local protected store rather than serialized directly into reusable role manifests.

## Component catalog and descriptor contract

The main MNCS system SHOULD expose a canonical catalog that tells clients what can be deployed without requiring repository-specific inference.

A component descriptor SHOULD include:

- stable component identifier;
- display/human description;
- descriptor version;
- component version/channel information;
- source authority and acquisition methods;
- integrity/provenance metadata where available;
- supported/unsupported/unverified platform and architecture combinations;
- dependencies and conflicts;
- required external runtimes or packages;
- configuration inputs and whether each is secret, host-bound, role-level, or optional;
- install/configure/upgrade/remove adapters;
- verification checks;
- capabilities exposed after successful verification;
- services/endpoints registered after deployment;
- rollback or removal semantics;
- data retention/preservation rules; and
- known limitations.

Descriptors MUST distinguish `unsupported`, `unverified`, and `supported`. A platform that has never been exercised is not `supported` merely because the implementation is likely portable.

## Acquisition and execution boundary

A descriptor may identify Git repositories, signed releases, local packages, system packages, or other acquisition providers. The catalog is provider-neutral; GitHub is not a required protocol dependency.

The bootstrap engine SHOULD prefer pinned/content-addressed or otherwise integrity-verifiable inputs when available. Remote catalog data MUST NOT be interpreted as unconstrained shell text solely because an AI requested installation.

Privileged actions SHOULD pass through a constrained deployment adapter or privileged helper with an explicit action vocabulary. Where arbitrary command execution is temporarily unavoidable, the plan and receipt must expose it distinctly so later MNCS hardening can replace it with a structured adapter.

## AI-facing bootstrap entry point

An AI agent should be able to begin with very little MNCS-specific context. A recommended interaction is:

```text
Agent instruction: "Connect this machine to MNCS as a Fabric worker."

1. discover()
2. catalog()
3. resolve desired role/component requirements
4. plan(desired_state)
5. request or consume already-granted authorization for the bounded plan
6. apply(plan)
7. verify()
8. receive capability registry delta
9. continue through normal Harness/Fabric routing
```

The bootstrap surface SHOULD be small enough that it can be exposed before the rest of the MNCS tool family is available. It is intentionally different from giving an agent every registered MNCS tool during initial bootstrap.

Transport MAY be CLI/stdio JSON, local RPC, MCP, or a later MNCS-native protocol. The transport MUST NOT redefine the underlying deployment semantics.

Structured responses SHOULD include stable machine-readable error codes, blockers, next permitted actions, and capability deltas. Human prose MAY accompany these objects but MUST NOT be the only representation an AI must parse.

## Human-facing installer

A conventional installer remains valuable. It SHOULD be a thin client over the same discovery, catalog, planning, apply, and verification operations.

A human workflow may present:

- detected host information;
- selectable MNCS components or roles;
- dependency implications;
- privilege/network requirements;
- plan preview;
- progress/status;
- verification results; and
- rollback/repair options.

The human interface MUST NOT have a separate hidden path that leaves the machine in a state the machine-readable protocol cannot describe.

## Reconciliation, repair, and upgrade

The core operation is reconciliation:

```text
reconcile(observed_state, desired_state) -> plan -> apply -> verify
```

Therefore:

- first install reconciles `absent` to `present`;
- repair reconciles drifted/broken state to declared state;
- upgrade changes version constraints and reconciles;
- uninstall changes desired state to `absent` and reconciles;
- migration changes target role or host bindings and reconciles; and
- role cloning derives a desired state from a source role and reconciles it onto a new host.

Reconciliation SHOULD expose drift rather than silently overwriting local changes.

## Semantic role cloning

Role cloning is first-class because an MNCS cluster frequently wants another machine that is functionally equivalent to an existing node without duplicating unsafe identity.

An exported role SHOULD classify fields as:

- reproducible role state;
- host-bound state;
- secret reference;
- ephemeral state;
- hardware-derived state; and
- operator override.

By default, cloning MUST exclude:

- private keys and raw secrets;
- machine/host UUIDs;
- ephemeral caches and logs;
- active process state;
- hardware-specific accelerator IDs or device paths; and
- credentials whose policy forbids reuse.

The clone planner then resolves new host bindings and reports any missing mappings.

## Capability registration

Successful verification SHOULD produce a capability delta describing what the host can now provide. Examples may include `fabric.worker`, `forge.control`, `mncs.validator`, a particular provider capability, or later MNEL/MNCS Language functions.

The Harness/router may use this registry to decide what tools or roles can be exposed to agents. Installation therefore does not merely copy software; it changes a verified capability graph.

Capability registration MUST depend on verification, not acquisition alone.

## Platform model

The protocol SHOULD separate platform-independent desired state from platform adapters.

Initial platform identifiers are expected to include:

```text
linux
windows
darwin   # reserved, unverified until tested
```

Linux distribution details and Windows version/edition distinctions belong in the discovered environment and adapter matching rules rather than in component names.

A future macOS implementation should be added without changing existing manifest semantics. Until tested, the reserved adapter reports a structured blocker rather than attempting generic Unix installation by assumption.

## Security and authority model

Ease of AI access does not imply unrestricted AI authority.

The bootstrap system SHOULD separate at least:

1. discovery authority;
2. catalog/read authority;
3. planning authority;
4. acquisition/network authority;
5. unprivileged mutation authority;
6. privileged mutation authority;
7. secret-binding authority; and
8. rollback/removal authority.

Authorization may be supplied by an interactive operator, local policy, a bounded capability token, Harness policy, or another approved mechanism. The apply receipt must record the authorization class without embedding reusable secrets.

Plans SHOULD identify operations that:

- require elevation;
- change firewall/network exposure;
- install or enable persistent services;
- modify startup behavior;
- create users/groups;
- change filesystem ownership/permissions;
- retrieve remote artifacts;
- bind credentials/secrets; or
- remove user data.

High-impact changes should be visible before application and should be separately policy-gateable.

## Receipts and evidence boundary

Each apply/verify transaction SHOULD emit an immutable or content-addressable receipt where practical. The receipt may contain:

- observed-state identity;
- desired-state identity;
- catalog/descriptor identities;
- plan identity;
- authorization class;
- attempted/completed/skipped/failed actions;
- acquired artifact identities;
- verification results;
- rollback results;
- final observed state identity;
- capability delta; and
- timestamps/environment identity.

These receipts are operational evidence. They do not by themselves prove MNCS conformance, protected execution, organizational independence, provenance correctness, or security. Existing MNCS evidence-assurance rules continue to govern stronger claims.

## Ownership boundary within the MNCS family

The bootstrap protocol and canonical cross-family catalog belong to the main MNCS system because they describe how the family is discovered and composed.

Individual component repositories remain authoritative for their component-specific deployment facts and verification logic. The main catalog SHOULD consume versioned descriptors rather than duplicating implementation knowledge indefinitely.

This permits a component to evolve without requiring the bootstrap engine to hard-code its internals, while preserving one canonical entry surface for humans and agents.

## Schema and validator changes

This RFC initially requires no change to frozen normative MNCS schemas or validators.

A follow-on implementation SHOULD define experimental schemas for:

- component descriptors;
- component catalogs;
- observed-state records;
- desired-state manifests;
- plans;
- apply/verify receipts;
- role exports; and
- capability deltas.

Those schemas should have an independent experimental validator before any proposal to make them normative.

## Security, privacy, and vendor-neutrality impact

The proposal reduces reliance on undocumented privileged scripts and makes deployment authority explicit, but it also creates a powerful control surface. A compromised bootstrap service could become a cluster-wide software supply-chain mechanism. For that reason, catalog authority, artifact integrity, authorization, secret handling, and privileged helpers must be treated as security boundaries rather than convenience code.

The protocol is vendor-neutral. A descriptor can acquire from Git, a release registry, a local mirror, system packages, removable media, or another provider. GitHub, a specific package manager, MCP, and any particular model vendor are implementation options, not protocol requirements.

Privacy-sensitive environment discovery should collect only facts needed for planning and verification. A discovery record intended to leave the host should be redactable without changing the local planner's ability to operate.

## Compatibility and migration

Existing manual installation remains valid. Early adoption can proceed incrementally:

1. catalog current MNCS components and document existing setup methods;
2. add read-only discovery and catalog commands;
3. add plan generation without mutation;
4. wrap known-safe existing setup procedures behind deployment adapters;
5. add verification and capability registration;
6. add transactional apply/rollback where feasible;
7. add role export/clone;
8. migrate component repositories toward self-described versioned descriptors; and
9. later add a human GUI if useful.

No existing component is required to become deployable through the protocol immediately.

## Alternatives

### Traditional monolithic installer

A monolithic installer is easy for humans initially but tends to encode platform and repository assumptions in one procedural program. It also gives agents no durable semantics for repair, cloning, capability discovery, or reconciliation.

### One install script per repository

This keeps ownership local but forces every caller to know repository topology and dependency order. Cross-family desired state remains unsolved.

### Let agents infer setup from documentation

This maximizes short-term flexibility but makes successful deployment dependent on model interpretation and stale prose. It is not a reliable machine-native interface.

### Containerize everything

Containers can simplify some dependencies but do not remove host integration, accelerators, USB/network topology, privileged services, secrets, hardware discovery, or cross-platform concerns. Containers may be an acquisition/execution adapter, not the bootstrap architecture.

## Test and evidence plan

Before the bootstrap protocol is considered stable, an implementation should demonstrate at least:

- deterministic schema validation for all protocol objects;
- repeated idempotent reconcile on an already-satisfied host;
- fresh installation from a minimal supported host state;
- partial installation of selected components;
- failed dependency resolution without partial silent success;
- interrupted apply with bounded recovery/rollback behavior;
- drift detection and repair;
- upgrade and downgrade/pin behavior where supported;
- clean removal with explicit preservation of user/evidence data;
- semantic clone onto a second host without secret or machine-identity duplication;
- capability registration only after verification;
- denied privileged actions when authority is absent;
- malicious/invalid component descriptor rejection;
- acquisition integrity mismatch rejection;
- structured unsupported-platform behavior; and
- explicit `darwin` unverified/unsupported behavior until real hardware validation exists.

Cross-host tests should eventually cover the actual Windows and Linux machines in the MNCS environment. Evidence should distinguish same-operator functional reproduction from independent evaluation.

## Unresolved questions

- Whether the canonical bootstrap engine should initially ship inside the existing `mncs` Python package or as a closely coupled implementation package exposed by the main MNCS distribution.
- Whether component descriptors should be signed by repository release automation, pinned by the main catalog, or both.
- Which minimal privilege-helper design gives enough cross-platform capability without becoming a general root command executor.
- Whether long-running apply transactions need a local daemon or can remain process-scoped initially.
- How much host inventory should be retained in portable receipts versus locally redacted discovery state.
- Which capability-registry authority ultimately owns cluster-wide registration: bootstrap itself, Harness, Fabric, or a shared registry with explicit ownership boundaries.
- Whether role exports should be content-addressed immutable artifacts or named mutable profiles layered over immutable snapshots.

These questions do not block the architectural direction: MNCS should expose one declarative bootstrap/deployment protocol whose human installer is only one client and whose machine-facing surface is intentionally simple enough for an authorized AI to use directly.
