# Machine-native bootstrap and deployment

> Experimental design note accompanying RFC 0009. This document describes an implementation shape; it does not change MNCS conformance semantics.

## Purpose

MNCS needs a canonical way to turn a host with little or no MNCS state into a verified participant in the MNCS family. That mechanism should be easy for a human to use, but it should be designed primarily as a machine-readable deployment protocol rather than as a graphical installer or collection of shell scripts.

The core idea is simple:

```text
current host state
        +
desired MNCS state
        +
component catalog
        +
authorization policy
        |
        v
    plan / reconcile
        |
        v
       apply
        |
        v
      verify
        |
        v
verified capability delta + receipt
```

A human installer, CLI, AI agent, Harness task, Fabric controller, or later MNCS-native control process should all invoke this same engine.

## Design objective

The ideal AI-facing instruction should be high-level:

```text
Connect this machine to MNCS as a Fabric worker.
```

The agent should not have to know:

- which repositories must be cloned;
- which repository owns each install step;
- dependency ordering;
- which Python/Node/Rust/system packages are required;
- where services should be installed;
- which platform-specific commands are correct;
- how to verify that the deployment actually works; or
- which capabilities should become visible to Harness/Fabric after installation.

Those facts belong in the bootstrap system and component descriptors.

## Layered architecture

### Layer 0: bootstrap entry surface

This is the smallest stable interface an agent needs before the rest of MNCS exists.

Recommended operations:

```text
discover
catalog
plan
apply
verify
reconcile
```

Optional operations:

```text
export_role
clone_role
rollback
remove
receipt
```

The interface should be transport-neutral. CLI JSON, stdio RPC, MCP, local socket RPC, or a future MNCS-native protocol can expose the same calls.

### Layer 1: bootstrap engine

The engine owns:

- state discovery;
- descriptor/catalog loading;
- dependency resolution;
- desired-state normalization;
- plan construction;
- authorization checks;
- execution/adapters;
- rollback boundaries;
- verification;
- capability registration; and
- receipts.

The engine should be deterministic where practical and explain nondeterministic/provider choices explicitly when not.

### Layer 2: platform adapters

Platform adapters translate generic deployment actions into bounded host operations.

Initial namespace:

```text
platform/linux
platform/windows
platform/darwin   # identifier reserved; no support claim until tested
```

Linux adapters may further detect package manager, service manager, distribution family, architecture, container/VM context, and hardware interfaces. Windows adapters may detect edition/version, PowerShell/runtime availability, service capabilities, and package providers.

The Darwin/macOS adapter should exist only as a reserved identity and structured blocker until actual Apple hardware is available for implementation and validation. Generic Unix similarity is not sufficient evidence of support.

### Layer 3: component adapters/descriptors

Each MNCS component describes how it can be acquired, configured, verified, removed, and what verified capabilities it exposes.

Examples include:

```text
mncs-core
mncs-validator
fabric
harness
forge
mnel
ravel
mncs-language
mncs-commons
rights-provenance
lineage
```

The exact catalog evolves. Component identity should remain stable even if the acquisition mechanism changes.

### Layer 4: clients

Clients include:

- `mncs` CLI;
- a future human installer UI;
- AI agents;
- Harness routing;
- Fabric fleet operations;
- Forge development workflows; and
- future autonomous MNCS services.

Clients are intentionally thin. They do not reimplement deployment rules.

## Suggested CLI shape

The CLI is not the protocol, but it is a useful reference surface.

```bash
# Read-only discovery
mncs bootstrap discover
mncs bootstrap discover --json

# What can this bootstrap engine deploy?
mncs bootstrap catalog
mncs bootstrap catalog --json

# Human-friendly role installation
mncs bootstrap install --role fabric-worker

# Explicit components
mncs bootstrap install fabric harness

# Preview without mutation
mncs bootstrap plan desired-state.json

# Reconcile current host to desired state
mncs reconcile desired-state.json

# Verify currently installed MNCS state
mncs bootstrap verify

# Export reusable role semantics
mncs role export --host fabric-worker-02 --output role.json

# Apply the same role to another host while resolving host-specific values
mncs role clone fabric-worker-02 --onto node-07
```

All commands should support structured output suitable for agents.

## Machine-facing response contract

Human-readable text is useful, but agents should never need to scrape it. A call should return an object shaped roughly like:

```json
{
  "schema": "mncs.bootstrap.result/0.1-experimental",
  "operation": "plan",
  "status": "ready",
  "target": "local",
  "blockers": [],
  "warnings": [],
  "required_authority": ["network.acquire", "host.service.manage"],
  "next_actions": ["apply"],
  "artifacts": {
    "observed_state": "sha256:...",
    "desired_state": "sha256:...",
    "plan": "sha256:..."
  }
}
```

Stable error codes should distinguish problems such as:

```text
PLATFORM_UNSUPPORTED
PLATFORM_UNVERIFIED
DEPENDENCY_UNSATISFIED
VERSION_CONFLICT
ACQUISITION_FAILED
INTEGRITY_MISMATCH
AUTHORITY_REQUIRED
AUTHORITY_DENIED
SECRET_BINDING_REQUIRED
APPLY_INTERRUPTED
VERIFY_FAILED
ROLLBACK_INCOMPLETE
DRIFT_DETECTED
```

## Discovery model

Discovery should collect only what deployment needs. Useful categories include:

### Host identity

- host-local identifier;
- platform and platform version;
- CPU architecture;
- virtualization/container context where relevant.

Portable receipts should avoid exposing sensitive identifiers unless necessary.

### Runtime/tool availability

- Python and relevant interpreter versions;
- Git availability;
- Rust/Cargo if needed;
- Node/npm if needed;
- package/service managers;
- required compilers or provider runtimes.

### Hardware capabilities

- CPU features;
- memory/resource summary;
- GPU/accelerator availability where relevant;
- USB/network interfaces when they affect Fabric roles;
- architecture-specific constraints.

### Existing MNCS state

- installed components;
- versions and sources;
- service status;
- configuration identities;
- known role membership;
- capability registry entries;
- drift from previously declared state.

Discovery facts should carry source and confidence when ambiguity is possible rather than pretending inference is certainty.

## Desired-state model

A user or agent should be able to describe either a role or explicit component set.

Role-based:

```json
{
  "schema": "mncs.bootstrap.desired-state/0.1-experimental",
  "role": "fabric-worker"
}
```

Explicit:

```json
{
  "schema": "mncs.bootstrap.desired-state/0.1-experimental",
  "components": {
    "fabric": {"state": "present", "channel": "stable"},
    "harness": {"state": "present"},
    "forge": {"state": "absent"}
  }
}
```

Policy can be layered without changing component semantics:

```json
{
  "policy": {
    "network": "acquisition-only",
    "privilege": "bounded-helper",
    "allow_persistent_services": true,
    "allow_firewall_changes": false,
    "allow_unverified_sources": false
  }
}
```

## Component descriptor model

A descriptor is the bridge between family-level orchestration and component-level authority.

Illustrative fields:

```json
{
  "schema": "mncs.bootstrap.component/0.1-experimental",
  "id": "fabric",
  "version": "0.2.0a19",
  "source": {
    "type": "git",
    "authority": "epi13/mncs-fabric"
  },
  "platforms": {
    "linux/x86_64": "supported",
    "windows/x86_64": "supported",
    "darwin/*": "unverified"
  },
  "depends_on": ["python>=3.11"],
  "configuration": [],
  "verify": [
    {"id": "service-health", "required": true}
  ],
  "capabilities": ["fabric.worker"]
}
```

In a mature implementation, executable adapter references should be separated from descriptive metadata so a catalog cannot smuggle unrestricted commands into a privileged process.

## Planning as a DAG

The planner should build a dependency graph rather than a single opaque script.

Example:

```text
inspect-python
      |
      v
install-fabric-package -----> write-config
      |                           |
      |                           v
      +--------------------> install-service
                                  |
                                  v
                              start-service
                                  |
                                  v
                             verify-health
                                  |
                                  v
                       register fabric.worker
```

Each action can declare:

- action identifier;
- component owner;
- preconditions;
- inputs;
- expected changes;
- authority required;
- reversibility;
- rollback action;
- verification dependency; and
- whether failure blocks subsequent actions.

The plan should be serializable and content-identifiable so the operator can authorize the exact plan that is later applied.

## Authorization and AI safety

A machine-native installer is powerful. Its simplicity for AI should come from structured semantics, not from removing guardrails.

A useful authority split is:

```text
bootstrap.read
bootstrap.plan
network.acquire
host.files.write
host.service.manage
host.packages.install
host.network.modify
secret.bind
bootstrap.remove
bootstrap.rollback
```

An AI may receive `bootstrap.read` and `bootstrap.plan` by default while a local operator or Harness policy authorizes the exact mutating plan. On a dedicated autonomous node, policy may pre-authorize a bounded role deployment.

The privileged helper should accept structured operations such as "install this verified package", "write this file with these permissions", or "enable this declared service" rather than arbitrary natural-language-generated root commands.

If a temporary adapter must execute shell/PowerShell commands, those commands should be explicit in the plan and receipt and treated as technical debt to be converted into structured operations.

## Apply transactions

Application should track transaction state persistently enough to recover from interruption.

Minimum behavior:

1. confirm the plan identity still matches the authorized plan;
2. confirm preconditions have not materially changed;
3. acquire and verify inputs;
4. execute actions in dependency order;
5. checkpoint completed reversible actions;
6. stop on blocking failure;
7. execute rollback when policy requires and rollback exists;
8. rediscover affected state;
9. verify required postconditions; and
10. emit receipt and capability delta.

The engine should not claim atomicity where the operating system cannot provide it. `ROLLBACK_INCOMPLETE` is preferable to pretending a partially changed machine was restored.

## Verification and capability registration

Acquisition success is not deployment success.

Every component should define checks appropriate to its function, for example:

- executable imports/starts;
- service starts and remains healthy;
- local protocol handshake succeeds;
- expected endpoint responds;
- configuration parses;
- required provider is discoverable;
- component reports expected version/identity;
- minimal self-test passes.

Only after required checks succeed should new capabilities enter the host capability registry.

This enables a useful bootstrap transition:

```text
agent sees only bootstrap tools
        |
        v
installs/verifies Harness + Fabric
        |
        v
capability registry changes
        |
        v
router can expose appropriate MNCS tools
```

The installer therefore participates in capability gating instead of bypassing it.

## Repair and drift

Once desired state is stored, the same engine becomes a repair mechanism.

```bash
mncs reconcile
```

may mean:

> Compare the host's current discovered state to the last accepted desired-state declaration, show drift, and return the host to that state within current policy.

Drift examples include:

- missing package;
- changed service configuration;
- component version outside allowed range;
- disabled service;
- lost capability registration;
- missing runtime dependency;
- changed endpoint/port;
- broken verification result.

Operator modifications should be surfaced, not silently erased.

## Upgrade model

Upgrade is a desired-state change.

```json
{
  "components": {
    "fabric": {
      "state": "present",
      "version": ">=0.2,<0.3"
    }
  }
}
```

Changing the constraint triggers a new plan. This avoids maintaining a separate upgrade engine with different semantics.

## Semantic cloning

A semantic clone reproduces role intent, not machine contents.

Suppose `fabric-worker-02` has:

```text
Fabric worker
Harness runtime
Qwen-compatible local model provider
USB-linked worker transport
specific evidence directories
specific service policy
```

An export should classify every field. A clone to `node-07` might preserve:

- required components;
- role-level settings;
- model/provider requirements;
- evidence layout policy;
- service behavior;
- verification requirements.

It should regenerate or remap:

- host ID;
- service instance identity;
- credentials;
- tunnel/API keys;
- hardware device IDs;
- local IP/interface names;
- machine-specific model paths where discovery resolves alternatives.

This makes fleet expansion much safer than imaging a disk or copying dotfiles.

## Catalog federation

The main MNCS catalog should be the canonical discovery surface, but it should not permanently duplicate every implementation detail.

A likely model is:

```text
main MNCS catalog
   |
   +--> pinned Fabric descriptor
   +--> pinned Harness descriptor
   +--> pinned Forge descriptor
   +--> pinned MNEL descriptor
   +--> ...
```

Each component repository can publish its own versioned descriptor. The main catalog pins/accepts compatible descriptors and exposes a single resolved view to callers.

This preserves component ownership while giving agents one door into the family.

## Local-first and provider-neutral behavior

Bootstrap should not require GitHub specifically. Possible acquisition sources include:

- Git repository;
- signed release archive;
- local filesystem checkout;
- package registry;
- OS package manager;
- local LAN mirror;
- removable media;
- Fabric-mediated transfer;
- future MNCS artifact store.

The plan should state which provider was selected and why.

## Human installer UX

A future human installer can remain simple because the bootstrap engine does the difficult work.

A useful flow is:

```text
1. Detect this machine
2. Choose role/components
3. Show dependencies and important changes
4. Authorize
5. Apply
6. Verify
7. Show what MNCS capabilities are now available
```

Advanced users can inspect the full plan. Ordinary users should not need to understand internal repository topology.

## Agent bootstrap UX

For an AI, the equivalent flow is:

```json
{"operation":"discover"}
```

then:

```json
{"operation":"plan","role":"fabric-worker"}
```

then, if authorized:

```json
{"operation":"apply","plan_id":"sha256:..."}
```

then:

```json
{"operation":"verify"}
```

The final response should tell the agent what changed in the capability graph and which tools/endpoints are now valid to use.

## Suggested implementation phases

### Phase A — specification and inventory

- define experimental protocol objects;
- inventory current MNCS components;
- record existing install/verify methods without changing them;
- create explicit platform support matrix.

### Phase B — read-only bootstrap

- `discover`;
- `catalog`;
- `plan`;
- JSON output and stable blocker/error codes;
- no mutation.

This phase is valuable immediately because agents can stop guessing.

### Phase C — bounded local apply

- Linux and Windows adapters for a small set of components;
- explicit privilege boundary;
- acquisition integrity checks;
- receipts;
- required verification.

### Phase D — reconciliation

- stored desired state;
- drift detection;
- idempotent reconcile;
- repair;
- upgrade/removal.

### Phase E — semantic cloning

- role export;
- field classification;
- secret/hardware remapping;
- clone planning;
- cross-host validation through Fabric.

### Phase F — human UI and deeper autonomous integration

- optional graphical installer;
- Harness policy integration;
- Fabric fleet deployment;
- capability-driven tool exposure;
- richer artifact provenance and signing.

### Phase G — additional platforms

- implement Darwin/macOS only when actual test hardware is available;
- preserve the already-reserved platform identity and manifest semantics.

## What this design intentionally avoids

It does not define deployment as:

- one giant shell script;
- one giant MCP server with every MNCS tool exposed during bootstrap;
- a model prompt that explains repository setup;
- copying an existing machine byte-for-byte;
- trusting success exit codes without verification;
- assuming all Unix-like systems are equivalent;
- putting secrets into reusable role files; or
- treating a bootstrap receipt as conformance evidence by itself.

## Relationship to MNCS principles

This design follows the broader machine-native direction of relocating human readability rather than requiring implementation internals to remain human-oriented. The bootstrap engine may become sophisticated, but its external contract should become easier for machines to reason about:

```text
observe -> declare -> plan -> authorize -> apply -> verify -> register
```

That contract is also suitable for evidence capture. Every transition can produce structured artifacts whose identities and results survive later automation, review, repair, or evolution.

The most important property is not that MNCS has an installer. It is that MNCS becomes self-describing enough that an authorized machine can reliably join, repair, or reproduce the ecosystem through one bounded protocol.
