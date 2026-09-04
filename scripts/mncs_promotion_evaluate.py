#!/usr/bin/env python3
"""MNCS promotion-boundary evaluator (owner-native, MNCS semantics).

Consumes a declared promotion boundary
(``schemas/mncs-promotion-boundary-0.1.schema.json``) plus authoritative
``mncs.check-result/1`` evidence and optional MNCDS obligation records,
and produces one ``mncs.check-result/1`` promotion claim for transport.

Verdict rules (owned by MNCS, applied verbatim):

- required evidence FAIL -> FAIL (a valid negative finding blocks);
- required evidence UNKNOWN, missing, unstamped, or contract-mismatched ->
  UNKNOWN (incomplete evidence never fabricates PASS);
- open required MNCDS obligations (untolerated) -> UNKNOWN with the exact
  obligation keys named as blockers;
- rejected obligations with authoritative evidence -> FAIL;
- optional UNKNOWN/FAIL stays visible in ``unresolved`` and never decides;
- missing optional evidence has no effect.

No-claim conditions (exit 2, nothing written; transport records
``NOT_ESTABLISHED``/``INVALID``, never ``UNKNOWN``):

- malformed boundary, check, or obligation document;
- duplicate check ids or duplicate obligation keys;
- evidence stamped for a different subject repository/commit;
- obligation records bound to a different subject;
- subject commit that is not an exact 40-hex revision (moving refs are
  observations, never promotable).

Only the Python standard library is used.

Usage:
  mncs_promotion_evaluate.py --boundary boundary.json
      --checks mncs-check.json rights-check.json [...]
      --subject-repository epi13/example --subject-commit <40-hex>
      [--authority-map authority-map.json]
      [--obligations obligation-*.json]
      [--check-id promotion-boundary] [--provider mncs-promotion-boundary]
      [--contract-revision 0.1] [--producer-revision REV]
      --output promotion-check.json

Graph subjects (family-level boundaries): pass --subject-graph graph.json
instead of --subject-repository/--subject-commit. The boundary must then
declare the same graph (``graph.digest`` plus the exact member set); every
check and obligation must be stamped for one of the graph's member
repository/commit pairs, never for anything else. The resulting claim is
bound to subject ``mncs-family/graph`` at commit ``graph:<digest>``.
Graph identity (digest recomputation) is proven by mncs-actions graph
tooling; this evaluator enforces digest consistency plus exact member
binding. Only the Python standard library is used.

Authority: every boundary requirement names a semantic authority. The
pinned authority map (mncs-authority-map/0.1, derived from pinned family
producer descriptors) binds each check id to its exact provider string
and authority. A structurally valid check with the right id from the
wrong producer is untrusted substitution (no claim); a check whose
authority is not established through the map is incomplete (UNKNOWN),
never PASS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

BOUNDARY_SCHEMA_VERSION = "mncs-promotion-boundary/0.1"
AUTHORITY_MAP_SCHEMA_VERSION = "mncs-authority-map/0.1"
CHECK_RESULT_SCHEMA_VERSION = "mncs.check-result/1"
OBLIGATION_SCHEMA_VERSION = "mncds-obligation-record/0.2"

VERDICTS = ("PASS", "FAIL", "UNKNOWN")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
GRAPH_SUBJECT_REPOSITORY = "mncs-family/graph"
DEFAULT_OBLIGATION_CHECK_ID = "mncds-obligations"


class BoundaryError(RuntimeError):
    """No promotion claim is established."""


def _load_json(path: str, label: str) -> tuple[Any, bytes]:
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise BoundaryError(f"{label} {path}: cannot read: {exc}") from exc
    try:
        return json.loads(raw.decode("utf-8")), raw
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BoundaryError(f"{label} {path}: malformed JSON: {exc}") from exc


def _check_boundary(doc: Any) -> dict[str, Any]:
    if not isinstance(doc, dict):
        raise BoundaryError("boundary must be a JSON object")
    if doc.get("schema_version") != BOUNDARY_SCHEMA_VERSION:
        raise BoundaryError(f"boundary schema_version must be {BOUNDARY_SCHEMA_VERSION}")
    for field in ("boundary_id", "subject_repository"):
        value = doc.get(field)
        if not isinstance(value, str) or not value:
            raise BoundaryError(f"boundary.{field} must be a non-empty string")
    required = doc.get("required_evidence")
    if not isinstance(required, list) or not required:
        raise BoundaryError("boundary.required_evidence must be a non-empty array")
    optional = doc.get("optional_evidence") or []
    if not isinstance(optional, list):
        raise BoundaryError("boundary.optional_evidence must be an array when present")
    seen: set[str] = set()
    for entry in required + optional:
        if not isinstance(entry, dict):
            raise BoundaryError("boundary evidence entries must be objects")
        check_id = entry.get("check_id")
        authority = entry.get("authority")
        if not isinstance(check_id, str) or not check_id:
            raise BoundaryError("boundary evidence check_id must be a non-empty string")
        if not isinstance(authority, str) or not authority:
            raise BoundaryError("boundary evidence authority must be a non-empty string")
        if check_id in seen:
            raise BoundaryError(f"boundary declares duplicate check id: {check_id}")
        seen.add(check_id)
    if not isinstance(doc.get("require_subject_binding"), bool):
        raise BoundaryError("boundary.require_subject_binding must be a boolean")
    return doc


def _check_authority_map(doc: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(doc, dict):
        raise BoundaryError("authority map must be a JSON object")
    if doc.get("schema_version") != AUTHORITY_MAP_SCHEMA_VERSION:
        raise BoundaryError(f"authority map schema_version must be {AUTHORITY_MAP_SCHEMA_VERSION}")
    authorities = doc.get("authorities")
    if not isinstance(authorities, dict) or not authorities:
        raise BoundaryError("authority map authorities must be a non-empty object")
    for check_id, binding in authorities.items():
        if not isinstance(binding, dict):
            raise BoundaryError(f"authority map {check_id} must be an object")
        for field in ("provider", "authority"):
            value = binding.get(field)
            if not isinstance(value, str) or not value:
                raise BoundaryError(f"authority map {check_id} needs a non-empty {field}")
    return authorities


def _graph_members(doc: Any, label: str) -> list[tuple[str, str]]:
    """Validate a graph member list; return (repository, commit) pairs."""
    if not isinstance(doc, list) or not doc:
        raise BoundaryError(f"{label} must be a non-empty member array")
    members: list[tuple[str, str]] = []
    for index, member in enumerate(doc):
        if not isinstance(member, dict):
            raise BoundaryError(f"{label}[{index}] must be an object")
        repository = member.get("repository")
        commit = member.get("commit")
        if not isinstance(repository, str) or not repository:
            raise BoundaryError(f"{label}[{index}].repository must be non-empty")
        if not isinstance(commit, str) or not HEX40.match(commit):
            raise BoundaryError(f"{label}[{index}].commit must be an exact 40-hex revision")
        if (repository, commit) in members:
            raise BoundaryError(f"{label} contains a duplicate member: {repository}")
        members.append((repository, commit))
    return members


def _check_subject_graph(doc: Any, path: str) -> tuple[str, list[tuple[str, str]]]:
    """Validate a --subject-graph document; return (digest, members)."""
    if not isinstance(doc, dict):
        raise BoundaryError(f"graph {path}: must be a JSON object")
    digest = doc.get("digest")
    if not isinstance(digest, str) or not HEX64.match(digest):
        raise BoundaryError(f"graph {path}: digest must be a 64-hex graph identity")
    members = _graph_members(doc.get("members"), f"graph {path} members")
    return digest, members


def _check_boundary_graph(doc: Any) -> tuple[str, list[tuple[str, str]]] | None:
    """Validate the boundary's declared graph, if any."""
    if doc.get("graph") is None:
        return None
    graph = doc["graph"]
    if not isinstance(graph, dict):
        raise BoundaryError("boundary.graph must be an object when present")
    digest = graph.get("digest")
    if not isinstance(digest, str) or not HEX64.match(digest):
        raise BoundaryError("boundary.graph.digest must be a 64-hex graph identity")
    members = _graph_members(graph.get("members"), "boundary.graph.members")
    return digest, members


def _check_result(doc: Any, path: str) -> dict[str, Any]:
    if not isinstance(doc, dict):
        raise BoundaryError(f"check {path}: must be a JSON object")
    if doc.get("schema_version") != CHECK_RESULT_SCHEMA_VERSION:
        raise BoundaryError(f"check {path}: schema_version must be {CHECK_RESULT_SCHEMA_VERSION}")
    if not isinstance(doc.get("id"), str) or not doc["id"]:
        raise BoundaryError(f"check {path}: id must be a non-empty string")
    if not isinstance(doc.get("provider"), str) or not doc["provider"]:
        raise BoundaryError(f"check {path}: provider must be a non-empty string")
    if doc.get("verdict") not in VERDICTS:
        raise BoundaryError(f"check {path}: verdict must be PASS, FAIL, or UNKNOWN")
    return doc


def _obligation(doc: Any, path: str) -> dict[str, Any]:
    if not isinstance(doc, dict):
        raise BoundaryError(f"obligation {path}: must be a JSON object")
    if doc.get("schema_version") != OBLIGATION_SCHEMA_VERSION:
        raise BoundaryError(
            f"obligation {path}: schema_version must be {OBLIGATION_SCHEMA_VERSION}"
        )
    for field in ("obligation_key",):
        if not isinstance(doc.get(field), str) or not doc[field]:
            raise BoundaryError(f"obligation {path}: {field} must be a non-empty string")
    if doc.get("status") not in ("open", "resolved", "rejected"):
        raise BoundaryError(f"obligation {path}: status must be open, resolved, or rejected")
    if not isinstance(doc.get("required"), bool):
        raise BoundaryError(f"obligation {path}: required must be a boolean")
    origin = doc.get("origin")
    if not isinstance(origin, dict):
        raise BoundaryError(f"obligation {path}: origin must be an object")
    if not isinstance(origin.get("authority"), str) or not origin["authority"]:
        raise BoundaryError(f"obligation {path}: origin.authority must be non-empty")
    subject = doc.get("subject")
    if (
        not isinstance(subject, dict)
        or not isinstance(subject.get("repository"), str)
        or not subject.get("repository")
        or not isinstance(subject.get("commit"), str)
        or not HEX40.match(subject["commit"])
    ):
        raise BoundaryError(
            f"obligation {path}: subject must bind an exact repository and 40-hex commit"
        )
    if doc["status"] in ("resolved", "rejected"):
        resolution = doc.get("resolution")
        if not isinstance(resolution, dict):
            raise BoundaryError(f"obligation {path}: resolved/rejected requires a resolution block")
        if not isinstance(resolution.get("resolved_by"), str) or not resolution["resolved_by"]:
            raise BoundaryError(f"obligation {path}: resolution must name its resolver")
        expected_kind = "fixed" if doc["status"] == "resolved" else "rejected"
        if resolution.get("resolution") != expected_kind:
            raise BoundaryError(
                f"obligation {path}: {doc['status']} requires resolution {expected_kind}"
            )
    if doc["status"] == "open" and "resolution" in doc:
        raise BoundaryError(f"obligation {path}: open obligations carry no resolution")
    return doc


def _reference_authorities(check: dict[str, Any]) -> list[str]:
    authorities: list[str] = []
    for ref in check.get("references") or []:
        if isinstance(ref, dict) and isinstance(ref.get("authority"), str):
            authorities.append(ref["authority"])
    return authorities


def _bind_authority(
    check_id: str,
    entry: dict[str, Any],
    check: dict[str, Any],
    authority_map: dict[str, dict[str, Any]],
    *,
    required: bool,
) -> tuple[bool, str | None]:
    """Verify the check satisfies the entry's required semantic authority.

    Returns (eligible, blocker_or_note). A structurally valid check with
    the right id from the wrong producer is untrusted substitution: that
    raises BoundaryError (no claim), exactly like a wrong-subject stamp.
    A check whose authority cannot be established through the pinned map
    is incomplete (blocker/note), never PASS.
    """
    expected = entry["authority"]
    scope = "required" if required else "optional"
    binding = authority_map.get(check_id)
    if binding is None:
        return False, (
            f"{scope} check {check_id} has no authority binding for authority {expected}"
        )
    if binding["authority"] != expected:
        raise BoundaryError(
            f"authority map binds {check_id} to {binding['authority']}, not the required {expected}"
        )
    if check["provider"] != binding["provider"]:
        raise BoundaryError(
            f"{scope} check {check_id} comes from provider "
            f"{check['provider']!r}, not the bound {binding['provider']!r}"
        )
    declared = check.get("authority")
    if declared is not None and declared != expected:
        raise BoundaryError(
            f"{scope} check {check_id} declares authority {declared!r}, not the required {expected}"
        )
    for authority in _reference_authorities(check):
        if authority != expected:
            raise BoundaryError(
                f"{scope} check {check_id} carries conflicting reference authority {authority!r}"
            )
    return True, None


def _bind_contract_revision(
    check_id: str,
    entry: dict[str, Any],
    check: dict[str, Any],
    *,
    required: bool,
) -> str | None:
    """Verify the check explicitly establishes the required contract revision.

    Returns a blocker/note, or None when eligible. An omitted revision can
    never satisfy an explicit requirement; a malformed carrier is no claim.
    """
    expected = entry.get("contract_revision")
    if not expected:
        return None
    scope = "required" if required else "optional"
    carried = check.get("contract_revision")
    if carried is None:
        return f"{scope} check {check_id} does not establish contract revision {expected}"
    if not isinstance(carried, str) or not carried:
        raise BoundaryError(f"{scope} check {check_id} carries a malformed contract revision")
    if carried != expected:
        return f"{scope} check {check_id} contract mismatch (expected {expected}, got {carried})"
    return None


def evaluate(
    boundary: dict[str, Any],
    checks: dict[str, tuple[dict[str, Any], bytes]],
    obligations: list[tuple[dict[str, Any], bytes]],
    subject_repository: str,
    subject_commit: str,
    authority_map: dict[str, dict[str, Any]] | None = None,
    own_check_id: str = "",
    member_subjects: list[tuple[str, str]] | None = None,
) -> tuple[str, list[str], list[str], list[dict[str, Any]]]:
    """Return (verdict, blockers, unresolved_notes, evidence_refs).

    In graph mode (``member_subjects`` given), every check stamp and every
    obligation subject must equal one of the graph's member pairs exactly;
    anything else is contradictory (no claim), exactly like a wrong-subject
    stamp in repository mode.
    """
    blockers: list[str] = []
    fail_blockers: list[str] = []
    notes: list[str] = []
    refs: list[dict[str, Any]] = []
    bindings = authority_map or {}
    require_binding = boundary["require_subject_binding"]
    tolerated = set(boundary.get("tolerated_obligations") or [])
    required = {entry["check_id"]: entry for entry in boundary["required_evidence"]}
    optional = {entry["check_id"]: entry for entry in (boundary.get("optional_evidence") or [])}

    for check_id, (check, raw) in checks.items():
        ref: dict[str, Any] = {
            "kind": "check-result",
            "check_id": check_id,
            "producer": check["provider"],
            "verdict": check["verdict"],
            "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
        }
        binding = bindings.get(check_id)
        if binding is not None:
            ref["authority"] = binding["authority"]
        if isinstance(check.get("contract_revision"), str):
            ref["contract_revision"] = check["contract_revision"]
        if isinstance(check.get("producer_revision"), str) and check["producer_revision"]:
            ref["producer_revision"] = check["producer_revision"]
        refs.append(ref)

    for check_id, entry in required.items():
        if own_check_id and check_id == own_check_id:
            # The promotion result cannot be its own input. A boundary may
            # name its own output so aggregation enforces its presence; the
            # evaluator skips the self-reference (noted, never blocking).
            notes.append(
                f"required check {check_id} is this evaluation's own output: "
                "aggregation enforces its presence"
            )
            continue
        check_pair = checks.get(check_id)
        if check_pair is None:
            blockers.append(f"required check {check_id} is missing")
            continue
        check = check_pair[0]
        eligible, authority_blocker = _bind_authority(
            check_id, entry, check, bindings, required=True
        )
        if not eligible:
            assert authority_blocker is not None
            blockers.append(authority_blocker)
            continue
        stamp = check.get("subject")
        if isinstance(stamp, dict):
            pair = (stamp.get("repository"), stamp.get("commit"))
            if member_subjects is not None:
                if pair not in member_subjects:
                    raise BoundaryError(
                        f"required check {check_id} is stamped for "
                        f"{stamp.get('repository')}@{stamp.get('commit')}, "
                        "which is not a member of the candidate graph"
                    )
            elif (
                stamp.get("repository") != subject_repository
                or stamp.get("commit") != subject_commit
            ):
                raise BoundaryError(
                    f"required check {check_id} is stamped for "
                    f"{stamp.get('repository')}@{stamp.get('commit')}, "
                    f"not {subject_repository}@{subject_commit}"
                )
        elif require_binding:
            blockers.append(f"required check {check_id} carries no subject binding")
            continue
        revision_blocker = _bind_contract_revision(check_id, entry, check, required=True)
        if revision_blocker is not None:
            blockers.append(revision_blocker)
            continue
        verdict = check["verdict"]
        if verdict == "FAIL":
            summary = check.get("summary") or check.get("claim") or "negative finding"
            fail_blockers.append(f"required check {check_id} FAIL: {summary}")
        elif verdict == "UNKNOWN":
            blockers.append(f"required check {check_id} UNKNOWN: evidence incomplete")
            for item in check.get("unresolved") or []:
                if isinstance(item, str) and item:
                    blockers.append(f"required check {check_id} unresolved: {item}")

    for check_id, entry in optional.items():
        check_pair = checks.get(check_id)
        if check_pair is None:
            continue
        check = check_pair[0]
        eligible, authority_note = _bind_authority(check_id, entry, check, bindings, required=False)
        if not eligible:
            assert authority_note is not None
            notes.append(f"{authority_note}: visible, not deciding")
            continue
        stamp = check.get("subject")
        if isinstance(stamp, dict):
            pair = (stamp.get("repository"), stamp.get("commit"))
            bound = (
                pair in member_subjects
                if member_subjects is not None
                else pair
                == (
                    subject_repository,
                    subject_commit,
                )
            )
            if not bound:
                raise BoundaryError(f"optional check {check_id} is stamped for another subject")
        revision_note = _bind_contract_revision(check_id, entry, check, required=False)
        if revision_note is not None:
            notes.append(f"{revision_note}: visible, not deciding")
            continue
        if check["verdict"] in ("FAIL", "UNKNOWN"):
            notes.append(f"optional check {check_id} {check['verdict']}: visible, not deciding")

    seen_obligations: set[str] = set()
    for record, raw in obligations:
        key = record["obligation_key"]
        if key in seen_obligations:
            raise BoundaryError(f"duplicate obligation key: {key}")
        seen_obligations.add(key)
        subject = record["subject"]
        pair = (subject["repository"], subject["commit"])
        if member_subjects is not None:
            if pair not in member_subjects:
                raise BoundaryError(
                    f"obligation {key} is bound to "
                    f"{subject['repository']}@{subject['commit']}, "
                    "which is not a member of the candidate graph"
                )
        elif subject["repository"] != subject_repository or subject["commit"] != subject_commit:
            raise BoundaryError(
                f"obligation {key} is bound to "
                f"{subject['repository']}@{subject['commit']}, "
                f"not {subject_repository}@{subject_commit}"
            )
        refs.append(
            {
                "kind": "mncds-obligation-record",
                "obligation_key": key,
                "authority": record["origin"]["authority"],
                "contract_revision": OBLIGATION_SCHEMA_VERSION,
                "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
                "subject": {
                    "repository": subject["repository"],
                    "commit": subject["commit"],
                },
                "status": record["status"],
            }
        )
        if record["status"] == "rejected":
            fail_blockers.append(f"obligation {key} rejected with authoritative evidence")
        elif record["status"] == "open" and record["required"] and key not in tolerated:
            blockers.append(f"obligation {key} open (required)")
        elif record["status"] == "open":
            notes.append(f"obligation {key} open (optional): visible, not deciding")

    blockers = fail_blockers + blockers
    verdict = "FAIL" if fail_blockers else ("UNKNOWN" if blockers else "PASS")
    return verdict, blockers, notes, refs


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate an MNCS promotion boundary.")
    parser.add_argument("--boundary", required=True)
    parser.add_argument("--checks", nargs="*", default=[])
    parser.add_argument("--subject-repository", default="")
    parser.add_argument("--subject-commit", default="")
    parser.add_argument("--subject-graph", default="")
    parser.add_argument("--obligations", nargs="*", default=[])
    parser.add_argument("--authority-map", default="")
    parser.add_argument("--check-id", default="promotion-boundary")
    parser.add_argument("--provider", default="mncs-promotion-boundary")
    parser.add_argument("--contract-revision", default="0.1")
    parser.add_argument("--producer-revision", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        graph_mode = bool(args.subject_graph)
        if graph_mode and (args.subject_repository or args.subject_commit):
            raise BoundaryError("--subject-graph excludes --subject-repository/--subject-commit")
        if not graph_mode and (not args.subject_repository or not HEX40.match(args.subject_commit)):
            raise BoundaryError("subject must be a repository plus an exact 40-hex commit")
        boundary_doc, boundary_raw = _load_json(args.boundary, "boundary")
        boundary = _check_boundary(boundary_doc)
        graph_digest = ""
        member_subjects: list[tuple[str, str]] | None = None
        if graph_mode:
            graph_doc, _ = _load_json(args.subject_graph, "subject graph")
            graph_digest, member_subjects = _check_subject_graph(graph_doc, args.subject_graph)
            declared = _check_boundary_graph(boundary)
            if declared is None:
                raise BoundaryError("graph subjects require a boundary that declares graph")
            if declared[0] != graph_digest or set(declared[1]) != set(member_subjects):
                raise BoundaryError("boundary declares a different graph than the subject graph")
            if boundary["subject_repository"] != GRAPH_SUBJECT_REPOSITORY:
                raise BoundaryError(f"graph boundary must belong to {GRAPH_SUBJECT_REPOSITORY}")
        elif boundary["subject_repository"] != args.subject_repository:
            raise BoundaryError(
                f"boundary belongs to {boundary['subject_repository']}, "
                f"not {args.subject_repository}"
            )
        checks: dict[str, tuple[dict[str, Any], bytes]] = {}
        for path in args.checks:
            doc, raw = _load_json(path, "check")
            check = _check_result(doc, path)
            if check["id"] in checks:
                raise BoundaryError(f"duplicate check id: {check['id']}")
            checks[check["id"]] = (check, raw)
        records = []
        for path in args.obligations:
            doc, raw = _load_json(path, "obligation")
            records.append((_obligation(doc, path), raw))
        authority_map: dict[str, dict[str, Any]] = {}
        authority_map_raw: bytes | None = None
        if args.authority_map:
            map_doc, authority_map_raw = _load_json(args.authority_map, "authority map")
            authority_map = _check_authority_map(map_doc)
        if graph_mode:
            assert member_subjects is not None
            subject_repository = GRAPH_SUBJECT_REPOSITORY
            subject_commit = f"graph:{graph_digest}"
        else:
            subject_repository = args.subject_repository
            subject_commit = args.subject_commit
        verdict, blockers, notes, refs = evaluate(
            boundary,
            checks,
            records,
            subject_repository,
            subject_commit,
            authority_map,
            args.check_id,
            member_subjects,
        )
        refs.append(
            {
                "kind": "promotion-boundary",
                "boundary_id": boundary["boundary_id"],
                "contract_revision": BOUNDARY_SCHEMA_VERSION,
                "digest": "sha256:" + hashlib.sha256(boundary_raw).hexdigest(),
            }
        )
        if authority_map_raw is not None:
            refs.append(
                {
                    "kind": "authority-map",
                    "contract_revision": AUTHORITY_MAP_SCHEMA_VERSION,
                    "digest": "sha256:" + hashlib.sha256(authority_map_raw).hexdigest(),
                }
            )
        required_ids = [
            entry["check_id"]
            for entry in boundary["required_evidence"]
            if entry["check_id"] != args.check_id
        ]
        passed = sum(
            1
            for check_id in required_ids
            if check_id in checks and checks[check_id][0]["verdict"] == "PASS"
        )
        result = {
            "schema_version": CHECK_RESULT_SCHEMA_VERSION,
            "id": args.check_id,
            "provider": args.provider,
            "verdict": verdict,
            "scope": f"promotion boundary {boundary['boundary_id']}",
            "claim": (
                "candidate revision carries sufficient authoritative evidence "
                "to cross the declared boundary"
            ),
            "summary": (
                f"boundary {boundary['boundary_id']} over {len(required_ids)} required "
                f"({passed} PASS) -> {verdict}"
                + (f"; blockers: {'; '.join(blockers)}" if blockers else "; no blockers")
            ),
            "contract_revision": BOUNDARY_SCHEMA_VERSION,
            "subject": {
                "repository": subject_repository,
                "commit": subject_commit,
            },
            "promotion": {
                "boundary_id": boundary["boundary_id"],
                "boundary_revision": BOUNDARY_SCHEMA_VERSION,
                "subject": {
                    "repository": subject_repository,
                    "commit": subject_commit,
                },
                "required_total": len(required_ids),
                "required_passed": passed,
                "blockers": blockers,
            },
            "references": refs,
        }
        if blockers or notes:
            result["unresolved"] = blockers + notes
        if graph_mode:
            assert member_subjects is not None
            result["promotion"]["graph_digest"] = graph_digest
            result["promotion"]["graph_members"] = [
                {"repository": repository, "commit": commit}
                for repository, commit in member_subjects
            ]
        if args.producer_revision:
            result["producer_revision"] = args.producer_revision
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"boundary {boundary['boundary_id']} -> {verdict} ({args.output})")
        return 0
    except BoundaryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
