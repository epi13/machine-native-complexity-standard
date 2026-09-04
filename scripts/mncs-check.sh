#!/usr/bin/env bash
# Owner-native MNCS validation evidence for the mncs-promotion boundary.
#
# Runs the owner operation the family producer contract names
# (`mncs-standard-validate`: the owner mncs_validator package over
# examples/minimal/manifest.json), then projects the native report through
# the pinned mncs-actions transport adapter. The adapter owns the
# check-result envelope only; all validation semantics are MNCS's.
#
# Environment overrides (local runs only; CI uses the pins):
#   MNC_ACTIONS_DIR  use a local mncs-actions checkout instead of cloning
#   MNC_ACTIONS_PIN  immutable transport revision (default below; never @main)
set -uo pipefail

MNC_ACTIONS_PIN="${MNC_ACTIONS_PIN:-4b132651d50b31ae12f5f00c749ee1f32adb6322}"
MNC_ACTIONS_DIR="${MNC_ACTIONS_DIR:-/tmp/mncs-promotion-mncs-actions}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CANDIDATE_REPO="$(python3 -c "import json; print(json.load(open('promotion/candidate.json'))['repository'])")"
CANDIDATE_COMMIT="$(python3 -c "import json; print(json.load(open('promotion/candidate.json'))['commit'])")"

if [ ! -d "$MNC_ACTIONS_DIR" ]; then
  rm -rf "$MNC_ACTIONS_DIR"
  git clone -q --filter=blob:none --no-checkout https://github.com/epi13/mncs-actions "$MNC_ACTIONS_DIR"
  git -C "$MNC_ACTIONS_DIR" fetch -q --depth 1 origin "$MNC_ACTIONS_PIN"
  git -C "$MNC_ACTIONS_DIR" checkout -q "$MNC_ACTIONS_PIN"
fi
ADAPTER="$MNC_ACTIONS_DIR/adapters/validator_adapter.py"

python3 -m pip install -q -e '.[dev]' >/tmp/mncs-install.log 2>&1

python3 -c "from mncs_validator.cli import main; raise SystemExit(main(['validate', 'examples/minimal/manifest.json', '--json']))" >/tmp/mncs-report.json
VALIDATE_RC=$?
if [ "$VALIDATE_RC" -ne 0 ] && [ "$VALIDATE_RC" -ne 3 ]; then
  echo "owner validation failed operationally (rc=$VALIDATE_RC); no claim established" >&2
  exit "$VALIDATE_RC"
fi

mkdir -p .mncs
python3 "$ADAPTER" \
  --input /tmp/mncs-report.json \
  --output .mncs/mncs-check.json \
  --check-id mncs-validation \
  --provider mncs-validator-rs \
  --scope "mncs promotion candidate validation" \
  --claim "candidate manifest validates under the MNCS core contract" \
  --contract-revision 0.2 \
  --subject-repository "$CANDIDATE_REPO" \
  --subject-commit "$CANDIDATE_COMMIT"

# Propagate the evidence outcome: PASS continues green, anything else is red.
# Aggregation still decides the boundary; this only mirrors dogfood behavior.
VERDICT="$(python3 -c "import json; print(json.load(open('.mncs/mncs-check.json'))['verdict'])")"
echo "mncs-validation -> $VERDICT"
[ "$VERDICT" = "PASS" ]
