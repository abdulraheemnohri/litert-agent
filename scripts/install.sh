#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.12+ is required. Install it with your OS package manager, then rerun." >&2
  exit 1
fi

PYTHON="$(command -v python3)"
"$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' || {
  echo "Python 3.12+ is required." >&2
  exit 1
}

if [ ! -d .venv ]; then
  "$PYTHON" -m venv .venv
fi
if [ -x .venv/bin/python ]; then
  VENV_PYTHON=.venv/bin/python
else
  VENV_PYTHON=.venv/Scripts/python.exe
fi
"$VENV_PYTHON" scripts/bootstrap.py "$@"
echo "Environment ready. Activate it with: . .venv/bin/activate"
