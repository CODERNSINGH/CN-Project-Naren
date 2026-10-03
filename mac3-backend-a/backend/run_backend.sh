#!/usr/bin/env bash
# Start this Mac's backend (ID/port come from backend.env; override: ./run_backend.sh B 3002)
cd "$(dirname "$0")"
. ./backend.env
[ -d venv ] || python3 -m venv venv
. venv/bin/activate
pip install -q -r requirements.txt
echo "Starting Backend ${1:-$BACKEND_ID} on 0.0.0.0:${2:-$BACKEND_PORT}  (Ctrl+C to stop)"
BACKEND_ID="${1:-$BACKEND_ID}" BACKEND_PORT="${2:-$BACKEND_PORT}" exec python backend.py
