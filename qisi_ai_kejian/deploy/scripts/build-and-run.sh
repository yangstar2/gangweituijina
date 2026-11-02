#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
if [[ ! -f backend/.env ]]; then
  cp backend/.env.example backend/.env
  echo "Created backend/.env from example — edit secrets before production."
fi
docker compose up -d --build
echo "Health:"
curl -fsS http://127.0.0.1:8000/api/health || true
echo
echo "Admin: http://127.0.0.1:8000/admin/members"
