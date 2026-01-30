#!/bin/bash
set -e

echo "Reset started..."

# Prefer Docker mount paths if they exist, else fall back to project-relative paths.
if [ -d "/data" ] && [ -d "/config" ]; then
  DATA_DIR="/data"
  CONFIG_DIR="/config"
  echo "Detected Docker mounts: /data and /config"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
  DATA_DIR="$PROJECT_ROOT/data"
  CONFIG_DIR="$PROJECT_ROOT/config"
  echo "Detected local project paths:"
  echo "Project root: $PROJECT_ROOT"
fi

echo "Using DATA_DIR=$DATA_DIR"
echo "Using CONFIG_DIR=$CONFIG_DIR"

# 1) Delete all files in data
if [ -d "$DATA_DIR" ]; then
  rm -rf "$DATA_DIR"/*
  echo "data directory cleared"
else
  echo "data directory not found: $DATA_DIR"
fi

# 2) Remove existing sop_questions_0_5.json
if [ -f "$CONFIG_DIR/sop_questions_0_5.json" ]; then
  rm -f "$CONFIG_DIR/sop_questions_0_5.json"
  echo "sop_questions_0_5.json removed"
else
  echo "sop_questions_0_5.json not found"
fi

# 3) Restore backup
if [ -f "$CONFIG_DIR/sop_questions_0_5_backup.json" ]; then
  cp "$CONFIG_DIR/sop_questions_0_5_backup.json" "$CONFIG_DIR/sop_questions_0_5.json"
  echo "Backup restored to sop_questions_0_5.json"
else
  echo "Backup file not found: $CONFIG_DIR/sop_questions_0_5_backup.json"
  exit 1
fi

echo "Reset finished successfully"