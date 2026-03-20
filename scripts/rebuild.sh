#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "🔄 Rebuilding Chess Analyzer (no cache)..."
docker compose down
docker compose build --no-cache
docker compose up -d
echo ""
echo "✅ Chess Analyzer rebuilt and running!"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
