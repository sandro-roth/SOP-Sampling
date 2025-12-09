#!/usr/bin/env bash
set -euo pipefail
echo 'Starting identify service ...'

exec python -m user_mask.app
