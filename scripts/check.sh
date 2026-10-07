#!/usr/bin/env bash
# Lint + tests (same as CI)
set -euo pipefail

echo "== ruff =="
ruff check src tests

echo "== pytest =="
pytest -q

echo "== build =="
pip install --quiet build
python -m build --wheel
echo "All checks passed."
