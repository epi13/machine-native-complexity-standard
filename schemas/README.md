# Schemas

MNCS-owned schemas in this directory are authoritative for MNCS.

Operational bootstrap schemas (`mncs-family-registry-0.1`,
`mncs-host-observation-0.1`, `mncs-bootstrap-plan-0.1`,
`mncs-bootstrap-receipt-0.1`) describe installation discovery only. They are
not MNCS 0.2 claim schemas and do not confer conformance.

The files `mncds-development-record.schema.json` and
`mncds-development-record-0.1.schema.json` are **consumed copies** used by the
local MNCS validator consumer. The canonical MNCDS schemas live in
https://github.com/epi13/machine-native-complexity-development-specification.

Do not edit the consumed MNCDS copies to change MNCDS meaning. Change them only
to stay compatible with a published MNCDS version.
