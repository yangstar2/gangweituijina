#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PATH="${HOME}/.local/bin:${PATH}"
if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
elif python3 -m venv .venv 2>/dev/null; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install -q -r requirements.txt
else
  echo "venv unavailable; using user site-packages (pip install --user -r requirements.txt)"
  python3 -m pip install --user -q -r requirements.txt
fi
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
