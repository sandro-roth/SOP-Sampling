#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DATA_DIR="$PROJECT_ROOT/data"
CONFIG_DIR="$PROJECT_ROOT/config"

echo "Reset started..."
echo "Project root: $PROJECT_ROOT"

# 1. Delete all files in data
if [ -d "$DATA_DIR" ]; then
  rm -rf "$DATA_DIR"/*
  echo "data directory cleared"
else
  echo "data directory not found"
fi

# 2. Remove existing sop_questions_0_5.json
if [ -f "$CONFIG_DIR/sop_questions_0_5.json" ]; then
  rm "$CONFIG_DIR/sop_questions_0_5.json"
  echo "sop_questions_0_5.json removed"
else
  echo "sop_questions_0_5.json not found"
fi

# 3. Restore backup
if [ -f "$CONFIG_DIR/sop_questions_0_5_backup.json" ]; then
  cp "$CONFIG_DIR/sop_questions_0_5_backup.json" \
     "$CONFIG_DIR/sop_questions_0_5.json"
  echo "Backup restored"
else
  echo "Backup file not found"
  exit 1
fi

echo "Reset finished successfully"