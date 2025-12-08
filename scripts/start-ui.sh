#!/usr/bin/env bash
set -euo pipefail
echo 'Starting UI service ...'

exec python -m sop_ui.app
