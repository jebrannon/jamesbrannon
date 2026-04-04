#!/bin/bash
# Run once to set up the CMS local dev environment (no Docker required for tests)
set -e
cd "$(dirname "$0")"

echo "Setting up CMS Python environment..."
python3 -m venv .venv
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements-dev.txt --quiet

cp -n .env.example .env 2>/dev/null && echo "Created .env from .env.example — edit it before running." || echo ".env already exists."

# ── Install git hooks ─────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -d "$REPO_ROOT/hooks" ]; then
  cp "$REPO_ROOT/hooks/pre-commit" "$REPO_ROOT/.git/hooks/pre-commit"
  cp "$REPO_ROOT/hooks/pre-push"   "$REPO_ROOT/.git/hooks/pre-push"
  chmod +x "$REPO_ROOT/.git/hooks/pre-commit" "$REPO_ROOT/.git/hooks/pre-push"
  echo "Git hooks installed."
fi

echo ""
echo "✅ Setup complete."
echo ""
echo "To start the CMS (requires Docker for DynamoDB Local):"
echo "  docker compose up"
echo ""
echo "To start the CMS API only (uses moto server for local DynamoDB):"
echo "  source .venv/bin/activate"
echo "  moto_server -p 8001 &"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""
echo "To run tests:"
echo "  .venv/bin/python -m pytest tests/ -v"
