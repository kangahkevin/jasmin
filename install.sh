#!/usr/bin/env bash
# Clean, rebuild and install jasmin into the project virtualenv.
# Usage: ./install.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$SCRIPT_DIR"
VENV="$PROJECT/venv"
PYTHON="$VENV/bin/python"
PIP="$VENV/bin/pip"

cd "$PROJECT"

# ── 1) Clean ────────────────────────────────────────────────────────
"$PROJECT/clean.sh"

# ── 2) Create virtualenv if missing ─────────────────────────────────
if [ ! -f "$PYTHON" ]; then
    echo "== Creating virtualenv =="
    python3 -m venv "$VENV"
fi

# ── 3) Install/upgrade build tools ──────────────────────────────────
echo "== Upgrading pip + build tools =="
"$PIP" install --upgrade pip setuptools wheel build

# ── 4) Install dependencies ─────────────────────────────────────────
echo "== Installing dependencies =="
"$PIP" install -r "$PROJECT/requirements.txt"

# ── 5) Build wheel ──────────────────────────────────────────────────
echo "== Building wheel =="
"$PYTHON" -m build --wheel

WHEEL=$(ls -t "$PROJECT/dist"/jasmin-*.whl | head -n1)
echo "Built: $WHEEL"

# ── 6) Install into virtualenv ──────────────────────────────────────
echo "== Installing jasmin =="
"$PIP" install --upgrade --force-reinstall "$WHEEL"

# ── 7) Smoke test ───────────────────────────────────────────────────
echo "== Smoke test =="
"$VENV/bin/jasmind.py" --help 2>&1 | head -5 || true

echo "== Done =="
