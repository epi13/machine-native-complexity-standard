# MNCS family

MNCS defines the **standard and evidence model**.

The wider MNCS family supplies language research, execution fabric, development
controls, experimental infrastructure, shared records, research systems, and
supporting tools. Those projects keep their own repositories and authority.

```text
                         MNCS
                  Standard / Evidence
                         │
          ┌──────────────┼──────────────┐
          │              │              │
        MNCDS        MNCS Language    Commons
     Development       Language /     Shared
       process          compiler       records
          │              │              │
          └──────────┬───┴──────┬───────┘
                     │          │
                   Forge      Fabric
                verification  execution
                     │          │
                     └────Harness
                            │
                  operator routing /
                    experimentation
```

Atlas is the human orientation guide. The machine-readable map used by bootstrap
is `family/mncs-family.v0.1.json`.

## Authority

| Component | Owns | Does not own |
| --- | --- | --- |
| MNCS | Implementation evidence, schemas, conformance corpus | Development process, execution, promotion |
| MNCDS | Development-process specification | Implementation acceptance |
| Forge | Bounded development/evaluation workflows | Package management, independent evaluation |
| Fabric | Persistent exact-target execution and workers | Conformance, Commons truth |
| Harness | Model/tool routing and deployment acceptance | Fabric fleet lifecycle |
| Control MCP | Protected workspace orchestration | Fabric, Harness policy, MNCS status |
| Commons | Structured coordination records | Execution authority |
| Atlas | Family orientation | Normative meaning |
| Language / studies / RAVEL / MNEL / lineage / rights | Research in their domains | Silent rewrite of MNCS |

Cross-component version compatibility is currently `UNKNOWN`. Explicit `--ref`
pins are supported; a published compatible-set matrix is not.

```bash
mncs family --json
mncs components --profile developer --json
```
