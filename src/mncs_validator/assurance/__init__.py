"""Public compatibility façade for offline MNCS 0.3 RC validation.

The package implements the non-normative reference validator. It never executes
providers, candidates, analyzers, compilers, benchmarks, or evidence binaries.
"""

# SPDX-License-Identifier: Apache-2.0

from .assurance_case import validate_assurance_value
from .contract import validate_contract_value
from .dispatch import validate_rc_file, validate_rc_value
from .freshness import freshness_status, parse_time
from .graph import (
    claim_cycles,
    derive_claim_statuses,
    graph_impact_closure,
    material_change_impact,
)
from .model import AssuranceIssue, AssuranceValidationReport, RecordKind
from .records import validate_measurement_value, validate_threat_value
from .revalidation import derive_revalidation
from .status import STATUS_ORDER, Status, aggregate_status

__all__ = [
    "STATUS_ORDER",
    "AssuranceIssue",
    "AssuranceValidationReport",
    "RecordKind",
    "Status",
    "aggregate_status",
    "claim_cycles",
    "derive_claim_statuses",
    "derive_revalidation",
    "freshness_status",
    "graph_impact_closure",
    "material_change_impact",
    "parse_time",
    "validate_assurance_value",
    "validate_contract_value",
    "validate_measurement_value",
    "validate_rc_file",
    "validate_rc_value",
    "validate_threat_value",
]
