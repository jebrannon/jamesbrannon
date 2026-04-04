#!/bin/bash
# Start all local development services.
# Usage: bash start.sh

set -e
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ── Node version ───────────────────────────────────────────────────────────────
NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"
nvm use --silent 2>/dev/null || true

# ── Preflight checks ───────────────────────────────────────────────────────────
if [ ! -f "$REPO_ROOT/cms/.env" ]; then
  echo -e "${RED}Error:${NC} cms/.env not found."
  echo -e "       Run ${YELLOW}cd cms && bash setup.sh${NC} first."
  exit 1
fi

if [ ! -d "$REPO_ROOT/cms/.venv" ]; then
  echo -e "${RED}Error:${NC} cms/.venv not found."
  echo -e "       Run ${YELLOW}cd cms && bash setup.sh${NC} first."
  exit 1
fi

# ── Cleanup on exit ────────────────────────────────────────────────────────────
PIDS=()
cleanup() {
  echo -e "\n${YELLOW}Stopping services...${NC}"
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  docker compose -f "$REPO_ROOT/cms/docker-compose.yml" stop minio 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# ── MinIO (local S3) ───────────────────────────────────────────────────────────
if command -v docker &> /dev/null && docker info &> /dev/null; then
  echo -e "${YELLOW}Starting MinIO...${NC}"
  docker compose -f "$REPO_ROOT/cms/docker-compose.yml" up minio -d --quiet-pull 2>/dev/null
  for i in {1..20}; do
    curl -sf http://localhost:9000/minio/health/live > /dev/null 2>&1 && break
    sleep 0.5
  done
  echo -e "  ${GREEN}✓${NC} http://localhost:9000  (console: http://localhost:9001)"
else
  echo -e "${YELLOW}⚠️  Docker not running — MinIO skipped. Image uploads will use local filesystem.${NC}"
fi

# ── DynamoDB (moto) ────────────────────────────────────────────────────────────
echo -e "${YELLOW}Starting DynamoDB (moto)...${NC}"
"$REPO_ROOT/cms/.venv/bin/moto_server" -p 8001 > /tmp/moto.log 2>&1 &
PIDS+=($!)

# Wait for moto to accept connections
for i in {1..10}; do
  curl -s http://localhost:8001 > /dev/null 2>&1 && break
  sleep 0.5
done
echo -e "  ${GREEN}✓${NC} http://localhost:8001"

# ── CMS API ────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}Starting CMS API...${NC}"
(cd "$REPO_ROOT/cms" && "$REPO_ROOT/cms/.venv/bin/uvicorn" app.main:app --reload --port 8000) > /tmp/uvicorn.log 2>&1 &
PIDS+=($!)

for i in {1..20}; do
  curl -s http://localhost:8000/health > /dev/null 2>&1 && break
  sleep 0.5
done
echo -e "  ${GREEN}✓${NC} http://localhost:8000  (admin: http://localhost:8000/admin)"

# ── Frontend ───────────────────────────────────────────────────────────────────
echo -e "${YELLOW}Starting frontend...${NC}"
echo ""
echo -e "  Logs: ${YELLOW}/tmp/moto.log${NC}  ${YELLOW}/tmp/uvicorn.log${NC}"
echo -e "  Press ${YELLOW}Ctrl+C${NC} to stop all services."
echo ""
cd "$REPO_ROOT" && npm run dev
