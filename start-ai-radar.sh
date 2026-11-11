#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "==================================================="
echo "  AI Tech Radar - Starting Local Server"
echo "  URL: http://127.0.0.1:8096"
echo "==================================================="

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "[INFO] Created initial .env from .env.example"
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "[SETUP] Creating Python virtual environment (.venv)..."
  python3 -m venv .venv
  echo "[SETUP] Installing dependencies..."
  .venv/bin/pip install -r requirements.txt
fi

exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8096
