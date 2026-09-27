#!/usr/bin/env bash
# Template preflight for the client-starter scaffold. Run before committing a
# dependency change and before every public template release:
#   ./preflight.sh
# 1. requirements.txt must be fully pinned with hashes (pip-compile output).
# 2. pip-audit must report no known vulnerabilities.
# 3. Every python file must compile.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PREFLIGHT_PYTHON:-python3}"

echo "[1/3] requirements.txt pinned with hashes"
if grep -E '^[A-Za-z0-9_.-]+' "$HERE/requirements.txt" | grep -vqE '==[^ ]+ \\$'; then
    echo "FAIL: unpinned or hash-less requirement in requirements.txt" >&2; exit 1
fi
grep -q -- '--hash=sha256:' "$HERE/requirements.txt" || { echo "FAIL: no hashes" >&2; exit 1; }

echo "[2/3] pip-audit"
if ! "$PY" -m pip_audit --version >/dev/null 2>&1; then
    echo "FAIL: pip-audit not installed (pip install pip-audit)" >&2; exit 1
fi
"$PY" -m pip_audit --require-hashes -r "$HERE/requirements.txt"

echo "[3/3] byte-compile"
"$PY" -m py_compile "$HERE"/app/*.py "$HERE"/app/modules/*.py "$HERE"/tools/*.py
echo "preflight OK"
