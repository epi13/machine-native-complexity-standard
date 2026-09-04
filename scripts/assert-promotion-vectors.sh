#!/usr/bin/env bash
# Adversarial promotion vectors for the repository-owned mncs-promotion boundary.
#
# Exercises the real MNCS boundary, authority map, and evidence through the
# working-tree MNCS evaluator (the dogfooded subject itself) and the pinned
# mncs-actions claim validator. Every vector asserts an exact outcome; a
# green run means the boundary holds.
#
# Environment overrides (local runs only; CI clones the pin):
#   MNC_ACTIONS_DIR  local mncs-actions checkout (default: clone MNC_ACTIONS_PIN)
#   MNC_ACTIONS_PIN  immutable transport revision (never @main)
#   MNDS_PACKAGE     pip target for the mncds validator
set -uo pipefail

MNC_ACTIONS_PIN="${MNC_ACTIONS_PIN:-4b132651d50b31ae12f5f00c749ee1f32adb6322}"
MNC_ACTIONS_DIR="${MNC_ACTIONS_DIR:-/tmp/mncs-vectors-mncs-actions}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -x "$MNC_ACTIONS_DIR/adapters/validator_adapter.py" ]; then
  rm -rf "$MNC_ACTIONS_DIR"
  git clone -q --filter=blob:none --no-checkout https://github.com/epi13/mncs-actions "$MNC_ACTIONS_DIR"
  git -C "$MNC_ACTIONS_DIR" fetch -q --depth 1 origin "$MNC_ACTIONS_PIN"
  git -C "$MNC_ACTIONS_DIR" checkout -q "$MNC_ACTIONS_PIN"
fi
EVAL="python3 scripts/mncs_promotion_evaluate.py"

CANDIDATE_REPO="$(python3 -c "import json; print(json.load(open('promotion/candidate.json'))['repository'])")"
CANDIDATE_COMMIT="$(python3 -c "import json; print(json.load(open('promotion/candidate.json'))['commit'])")"
VECTORS="$(mktemp -d)"

export MNC_ACTIONS_DIR
bash scripts/mncs-check.sh >/dev/null
bash scripts/mncds-obligations-check.sh >/dev/null

PASS=0
check_verdict() {  # name expected actual
  if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "vector $1: PASS ($2)";
  else echo "vector $1: FAIL (expected $2, got $3)"; exit 1; fi
}
check_no_claim() {  # name rc
  if [ "$2" -ne 0 ]; then PASS=$((PASS+1)); echo "vector $1: PASS (no claim, exit $2)";
  else echo "vector $1: FAIL (expected no claim, got exit 0)"; exit 1; fi
}
OBLIGATIONS=(promotion/obligations/*.json)
BASE_ARGS="--boundary promotion/mncs-promotion.boundary.json --authority-map promotion/authority-map.json --checks .mncs/mncs-check.json .mncs/mncds-obligations-check.json --obligations ${OBLIGATIONS[*]} --subject-repository $CANDIDATE_REPO --subject-commit $CANDIDATE_COMMIT --check-id promotion-boundary --provider mncs-promotion-boundary --contract-revision 0.1 --producer-revision test-revision"

# 1. pass universe: real evidence over the real boundary.
$EVAL $BASE_ARGS --output "$VECTORS/pass.json" >/dev/null
check_verdict "pass-universe" "PASS" "$(python3 -c "import json; print(json.load(open('$VECTORS/pass.json'))['verdict'])")"

# 2. no self-approval: the required self entry is skipped (noted, never
# blocking) and decided only by the other required checks.
python3 - "$VECTORS/pass.json" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1]))
assert doc["promotion"]["required_total"] == 2, doc["promotion"]
assert any("own output" in note for note in doc.get("unresolved", [])), doc.get("unresolved")
print("self-skip noted; required_total excludes self")
PY
if [ "$?" -ne 0 ]; then echo "vector no-self-approval: FAIL"; exit 1; fi
PASS=$((PASS+1)); echo "vector no-self-approval: PASS"

MUT() {  # name jq-ish python edit of all obligation files into VECTORS dir
  python3 - "$VECTORS" "$1" <<'PY'
import glob, json, sys
outdir, which = sys.argv[1], sys.argv[2]
for path in glob.glob("promotion/obligations/*.json"):
    doc = json.load(open(path))
    if which == "open":
        doc["status"] = "open"
        doc.pop("resolution", None)
        doc["required"] = True
    elif which == "rejected":
        doc["status"] = "rejected"
        doc["resolution"] = {
            "resolution": "rejected",
            "evidence_refs": ["sha256:" + "c" * 64],
            "resolved_by": "epi13/machine-native-complexity-standard",
            "resolved_at": "2026-09-04T00:00:00Z",
        }
        doc["required"] = True
    elif which == "malformed":
        doc.pop("obligation_key", None)
    json.dump(doc, open(f"{outdir}/{which}-{path.split('/')[-1]}", "w"), indent=2)
PY
}
ARGS_FOR() {  # vector dir -> evaluator args with mutated obligations
  echo "--boundary promotion/mncs-promotion.boundary.json --authority-map promotion/authority-map.json --checks .mncs/mncs-check.json .mncs/mncds-obligations-check.json --obligations $1/$2-*.json --subject-repository $CANDIDATE_REPO --subject-commit $CANDIDATE_COMMIT --check-id promotion-boundary --provider mncs-promotion-boundary --contract-revision 0.1 --producer-revision test-revision"
}

# 3. open required obligation holds the boundary at UNKNOWN.
MUT open
# shellcheck disable=SC2086
$EVAL $(ARGS_FOR "$VECTORS" open) --output "$VECTORS/open-out.json" >/dev/null
check_verdict "open-obligation" "UNKNOWN" "$(python3 -c "import json; print(json.load(open('$VECTORS/open-out.json'))['verdict'])")"

# 4. rejected required obligation stays a negative result.
MUT rejected
# shellcheck disable=SC2086
$EVAL $(ARGS_FOR "$VECTORS" rejected) --output "$VECTORS/rejected-out.json" >/dev/null
check_verdict "rejected-obligation" "FAIL" "$(python3 -c "import json; print(json.load(open('$VECTORS/rejected-out.json'))['verdict'])")"

# 5. malformed obligation establishes no claim (never UNKNOWN).
MUT malformed
# shellcheck disable=SC2086
$EVAL $(ARGS_FOR "$VECTORS" malformed) --output "$VECTORS/malformed-out.json" >/dev/null 2>&1
check_no_claim "malformed-obligation" "$?"

# 6. contradictory duplicate obligation keys establish no claim.
DUPES=(promotion/obligations/*.json)
$EVAL --boundary promotion/mncs-promotion.boundary.json --authority-map promotion/authority-map.json \
  --checks .mncs/mncs-check.json .mncs/mncds-obligations-check.json \
  --obligations "${DUPES[0]}" "${DUPES[0]}" \
  --subject-repository "$CANDIDATE_REPO" --subject-commit "$CANDIDATE_COMMIT" \
  --check-id promotion-boundary --output "$VECTORS/dup-out.json" >/dev/null 2>&1
check_no_claim "duplicate-obligation" "$?"

# 7. wrong commit: evidence for another revision promotes nothing here.
$EVAL --boundary promotion/mncs-promotion.boundary.json --authority-map promotion/authority-map.json \
  --checks .mncs/mncs-check.json .mncs/mncds-obligations-check.json --obligations "${OBLIGATIONS[@]}" \
  --subject-repository "$CANDIDATE_REPO" --subject-commit dddddddddddddddddddddddddddddddddddddddd \
  --check-id promotion-boundary --output "$VECTORS/wrong-commit.json" >/dev/null 2>&1
check_no_claim "wrong-commit" "$?"

# 8. moving ref instead of an immutable revision is rejected.
$EVAL --boundary promotion/mncs-promotion.boundary.json --authority-map promotion/authority-map.json \
  --checks .mncs/mncs-check.json .mncs/mncds-obligations-check.json --obligations "${OBLIGATIONS[@]}" \
  --subject-repository "$CANDIDATE_REPO" --subject-commit main \
  --check-id promotion-boundary --output "$VECTORS/moving-ref.json" >/dev/null 2>&1
check_no_claim "moving-ref" "$?"

# 9. missing required evidence stays UNKNOWN (never PASS).
$EVAL --boundary promotion/mncs-promotion.boundary.json --authority-map promotion/authority-map.json \
  --checks .mncs/mncs-check.json --obligations "${OBLIGATIONS[@]}" \
  --subject-repository "$CANDIDATE_REPO" --subject-commit "$CANDIDATE_COMMIT" \
  --check-id promotion-boundary --output "$VECTORS/missing.json" >/dev/null
check_verdict "missing-required" "UNKNOWN" "$(python3 -c "import json; print(json.load(open('$VECTORS/missing.json'))['verdict'])")"

# 10. tampered authority binding establishes no claim.
python3 - "$VECTORS/authmap.json" <<'PY'
import json, sys
doc = json.load(open("promotion/authority-map.json"))
doc["authorities"]["mncds-obligations"]["authority"] = "adversarial-authority"
json.dump(doc, open(sys.argv[1], "w"), indent=2)
PY
$EVAL --boundary promotion/mncs-promotion.boundary.json --authority-map "$VECTORS/authmap.json" \
  --checks .mncs/mncs-check.json .mncs/mncds-obligations-check.json --obligations "${OBLIGATIONS[@]}" \
  --subject-repository "$CANDIDATE_REPO" --subject-commit "$CANDIDATE_COMMIT" \
  --check-id promotion-boundary --output "$VECTORS/tampered.json" >/dev/null 2>&1
check_no_claim "wrong-authority" "$?"

# 11. duplicate check ids for one requirement establish no claim.
cp .mncs/mncs-check.json "$VECTORS/mncs-check-dup.json"
$EVAL --boundary promotion/mncs-promotion.boundary.json --authority-map promotion/authority-map.json \
  --checks .mncs/mncs-check.json "$VECTORS/mncs-check-dup.json" .mncs/mncds-obligations-check.json \
  --obligations "${OBLIGATIONS[@]}" \
  --subject-repository "$CANDIDATE_REPO" --subject-commit "$CANDIDATE_COMMIT" \
  --check-id promotion-boundary --output "$VECTORS/dup-check.json" >/dev/null 2>&1
check_no_claim "duplicate-checks" "$?"

# 12. stale revision: obligations bound to a superseded candidate promote nothing.
python3 - "promotion/obligations/promotion-self-reference.obligation.json" "$VECTORS/stale.json" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1])); doc["subject"]["commit"] = "0" * 40
json.dump(doc, open(sys.argv[2], "w"), indent=2)
PY
$EVAL --boundary promotion/mncs-promotion.boundary.json --authority-map promotion/authority-map.json \
  --checks .mncs/mncs-check.json .mncs/mncds-obligations-check.json --obligations "$VECTORS/stale.json" \
  --subject-repository "$CANDIDATE_REPO" --subject-commit "$CANDIDATE_COMMIT" \
  --check-id promotion-boundary --output "$VECTORS/stale-out.json" >/dev/null 2>&1
check_no_claim "stale-revision" "$?"

# 13. forged digest: every bound digest must recompute from the exact
# consumed bytes. The control rebinds the genuine claim cleanly; the
# forged claim (one digest flipped) must mismatch.
python3 - "$VECTORS/pass.json" <<'PY'
import hashlib, json, sys

def digest(path):
    return "sha256:" + hashlib.sha256(open(path, "rb").read()).hexdigest()

consumed = {
    ("check-result", "mncs-validation"): ".mncs/mncs-check.json",
    ("check-result", "mncds-obligations"): ".mncs/mncds-obligations-check.json",
    ("mncds-obligation-record", "pressure.mncs.promotion-self-reference.required"):
        "promotion/obligations/promotion-self-reference.obligation.json",
    ("mncds-obligation-record", "pressure.mncs.promotion-adoption.optional"):
        "promotion/obligations/promotion-adoption.obligation.json",
    ("promotion-boundary", "mncs-promotion"): "promotion/mncs-promotion.boundary.json",
    ("authority-map", ""): "promotion/authority-map.json",
}

def key(ref):
    kind = ref.get("kind")
    if kind == "check-result":
        return (kind, ref.get("check_id"))
    if kind == "mncds-obligation-record":
        return (kind, ref.get("obligation_key"))
    if kind == "promotion-boundary":
        return (kind, ref.get("boundary_id"))
    if kind == "authority-map":
        return (kind, "")
    return (kind, None)

def rebind(doc):
    problems = []
    for ref in doc.get("references", []):
        path = consumed.get(key(ref))
        if path is None:
            problems.append(f"unconsumed reference: {key(ref)}")
        elif ref.get("digest") != digest(path):
            problems.append(f"digest mismatch: {key(ref)}")
    return problems

genuine = json.load(open(sys.argv[1]))
control = rebind(genuine)
assert not control, f"control claim must rebind cleanly: {control}"

forged = json.loads(json.dumps(genuine))
forged["references"][0]["digest"] = "sha256:" + "f" * 64
problems = rebind(forged)
assert problems, "forged digest must mismatch the consumed bytes"
print("forged-digest detected:", problems[0])
PY
if [ "$?" -ne 0 ]; then echo "vector forged-digest: FAIL"; exit 1; fi
PASS=$((PASS+1)); echo "vector forged-digest: PASS"

rm -rf "$VECTORS"
echo "promotion vectors: $PASS/13 PASS"
