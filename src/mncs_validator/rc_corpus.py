"""Versioned release-candidate conformance corpus runner."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from .assurance import (
    AssuranceValidationReport,
    RecordKind,
    validate_rc_value,
)
from .mncds import MncdsValidationReport, validate_development_value


@dataclass(frozen=True)
class CorpusSummary:
    """Deterministic release-candidate corpus counts."""

    total: int
    matched: int
    mismatched: int
    categories: dict[str, int]

    def as_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "matched": self.matched,
            "mismatched": self.mismatched,
            "categories": self.categories,
        }


def default_corpus_path() -> Path:
    """Locate the repository or installed release-candidate corpus."""

    repository = Path("conformance/release-candidate/corpus.json")
    if repository.is_file():
        return repository
    installed = (
        Path(sys.prefix)
        / "share"
        / "mncs-validator"
        / "conformance"
        / "release-candidate"
        / "corpus.json"
    )
    return installed


def _tokens(pointer: str) -> list[str]:
    if not pointer.startswith("/"):
        raise ValueError(f"JSON pointer must start with '/': {pointer}")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def apply_mutation(value: dict[str, Any], mutation: dict[str, Any]) -> None:
    """Apply the corpus's deliberately small JSON mutation language."""

    tokens = _tokens(cast(str, mutation["path"]))
    parent: Any = value
    for token in tokens[:-1]:
        parent = parent[int(token)] if isinstance(parent, list) else parent[token]
    final = tokens[-1]
    operation = mutation["op"]
    if operation == "set":
        if isinstance(parent, list):
            parent[int(final)] = copy.deepcopy(mutation["value"])
        else:
            parent[final] = copy.deepcopy(mutation["value"])
    elif operation == "delete":
        if isinstance(parent, list):
            del parent[int(final)]
        else:
            del parent[final]
    elif operation == "append":
        target = parent[int(final)] if isinstance(parent, list) else parent[final]
        if not isinstance(target, list):
            raise ValueError(f"append target is not an array: {mutation['path']}")
        target.append(copy.deepcopy(mutation["value"]))
    else:
        raise ValueError(f"unsupported mutation operation: {operation}")


def load_cases(corpus_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Resolve bases and materialize all cases without network access."""

    corpus = cast(dict[str, Any], json.loads(corpus_path.read_text(encoding="utf-8")))
    base_paths = cast(dict[str, str], corpus["bases"])
    bases = {
        kind: cast(
            dict[str, Any],
            json.loads((corpus_path.parent / relative).resolve().read_text(encoding="utf-8")),
        )
        for kind, relative in base_paths.items()
    }
    materialized: list[dict[str, Any]] = []
    for raw_case in cast(list[dict[str, Any]], corpus["cases"]):
        case = copy.deepcopy(raw_case)
        value = copy.deepcopy(bases[cast(str, case["kind"])])
        for mutation in cast(list[dict[str, Any]], case.get("mutations", [])):
            apply_mutation(value, mutation)
        case["value"] = value
        materialized.append(case)
    return corpus, materialized


def run_corpus(corpus_path: Path) -> tuple[CorpusSummary, list[dict[str, Any]]]:
    """Run every case and preserve all mismatches and issue codes."""

    corpus, cases = load_cases(corpus_path)
    default_at = datetime.fromisoformat(cast(str, corpus["evaluation_time"]).replace("Z", "+00:00"))
    results: list[dict[str, Any]] = []
    categories: dict[str, int] = {}
    matched = 0
    for case in cases:
        kind = cast(str, case["kind"])
        value = cast(dict[str, Any], case["value"])
        at_text = cast(str, case.get("at", corpus["evaluation_time"]))
        at = datetime.fromisoformat(at_text.replace("Z", "+00:00"))
        report: AssuranceValidationReport | MncdsValidationReport
        if kind == "mncds":
            report = validate_development_value(value, target=cast(str, case["id"]))
        elif value.get("schema_version") != "0.3-rc.1":
            report = AssuranceValidationReport(
                target=cast(str, case["id"]), kind=kind, valid=False, supported=False
            )
            report.add("UNSUPPORTED-VERSION", "unsupported schema version", "$/schema_version")
        else:
            report = validate_rc_value(
                value, cast(RecordKind, kind), target=cast(str, case["id"]), at=at or default_at
            )
        actual = report.category
        categories[actual] = categories.get(actual, 0) + 1
        actual_codes = {item.code for item in report.issues + report.warnings}
        required_codes = set(cast(list[str], case.get("issue_codes", [])))
        agrees = actual == case["expected"] and required_codes <= actual_codes
        matched += int(agrees)
        results.append(
            {
                "id": case["id"],
                "kind": kind,
                "expected": case["expected"],
                "actual": actual,
                "matched": agrees,
                "issue_codes": sorted(actual_codes),
            }
        )
    summary = CorpusSummary(
        total=len(results),
        matched=matched,
        mismatched=len(results) - matched,
        categories=dict(sorted(categories.items())),
    )
    return summary, results
