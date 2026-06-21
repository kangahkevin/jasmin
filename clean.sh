#!/usr/bin/env bash
# Remove all build artifacts, caches and temporary files.
# Usage: ./clean.sh [--venv]
#   --venv  also remove the virtualenv
set -euo pipefail

PROJECT="$(cd "$(dirname "$0")" && pwd)"

echo "== Cleaning build artifacts =="
rm -rf "$PROJECT/build" \
       "$PROJECT/dist" \
       "$PROJECT/jasmin.egg-info" \
       "$PROJECT/UNKNOWN.egg-info"

echo "== Cleaning Python caches =="
find "$PROJECT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$PROJECT" -type f -name "*.pyo" -delete 2>/dev/null || true

echo "== Cleaning test artifacts =="
rm -rf "$PROJECT/.pytest_cache" \
       "$PROJECT/_trial_temp" \
       "$PROJECT/.coverage" \
       "$PROJECT/.tox"
find "$PROJECT" -type d -name "_trial_temp" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

echo "== Cleaning C extensions =="
find "$PROJECT" -type f -name "*.so" -delete 2>/dev/null || true

echo "== Cleaning OS junk =="
find "$PROJECT" -type f -name ".DS_Store" -delete 2>/dev/null || true

if [[ "${1:-}" == "--venv" ]]; then
    echo "== Removing virtualenv =="
    rm -rf "$PROJECT/venv"
fi

echo "== Done =="
