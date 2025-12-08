#!/usr/bin/env bash
set -euo pipefail
echo 'Starting UI service ...'

# call wait for db here!

exec python -m sop_ui.app
