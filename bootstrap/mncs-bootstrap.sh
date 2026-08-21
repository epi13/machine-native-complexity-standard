#!/usr/bin/env sh
# Minimal POSIX bootstrap shim. Discovers Python before the richer mncs CLI.
# SPDX-License-Identifier: Apache-2.0

set -eu

json=0
for arg in "$@"; do
  if [ "$arg" = "--json" ]; then
    json=1
  fi
done

emit() {
  message=$1
  python_state=$2
  if [ "$json" -eq 1 ]; then
    printf '{"ok":%s,"python":"%s","message":"%s","disclaimer":"This shim is operational only. It is not MNCS conformance, certification, or promotion."}\n' \
      "$3" "$python_state" "$message"
  else
    printf '%s\n' "$message"
  fi
}

resolve_python() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi
  return 1
}

if ! python_bin=$(resolve_python); then
  emit "Python 3.11+ is not installed. Install Python, then re-run this shim or pip install the MNCS validator." "missing" "false"
  exit 14
fi

if command -v mncs >/dev/null 2>&1; then
  exec mncs bootstrap "$@"
fi

here=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
if [ -f "$here/src/mncs_validator/cli.py" ]; then
  PYTHONPATH="$here/src${PYTHONPATH:+:$PYTHONPATH}"
  export PYTHONPATH
  exec "$python_bin" -m mncs_validator bootstrap "$@"
fi

emit "Python is available at $python_bin, but the mncs CLI is not installed. pip install the MNCS validator, then re-run." "available" "false"
exit 10
