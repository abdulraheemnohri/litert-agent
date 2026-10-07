#!/usr/bin/env bash
# Development setup for litert-agent
set -euo pipefail

python -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

echo
echo "Setup complete."
echo "Make sure the LiteRT-LM CLI is on your PATH (no other model backend is supported)."
echo "Activate with: source .venv/bin/activate"
