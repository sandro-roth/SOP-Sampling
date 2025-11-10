#!/usr/bin/env bash
set -euo pipefail

# Check if db is up and running
#/script/wait-for-db.sh

# Start UI application
echo 'Starting UI service ...'
# src importable
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR/../src"
exec python -m sop_ui.app