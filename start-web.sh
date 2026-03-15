#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
  echo "python not found; please install Python 3.10+ and add it to PATH."
  exit 1
fi

python3 dev_start.py --open 2>/dev/null || python dev_start.py --open
