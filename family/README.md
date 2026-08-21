# MNCS family registry

`mncs-family.v0.1.json` is the machine-readable map of the MNCS family.

It is an **operational discovery contract**. Component repositories remain
authoritative for their own specifications, services, and evidence.

The registry does not create conformance, certification, independent evidence,
protected custody, governance approval, PASS, or promotion authority.

Schema: [`../schemas/mncs-family-registry-0.1.schema.json`](../schemas/mncs-family-registry-0.1.schema.json)

```bash
mncs family --json
mncs components --profile developer --json
python scripts/validate-family-registry.py
```
