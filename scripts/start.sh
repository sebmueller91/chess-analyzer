#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

if [ ! -f .env ]; then
    echo "Error: .env file not found. Copy .env.example to .env and set your OPENAI_API_KEY."
    exit 1
fi

if ! grep -q "OPENAI_API_KEY=." .env 2>/dev/null; then
    echo "Warning: OPENAI_API_KEY appears to be empty in .env"
    echo "AI coaching features will not work without it."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🔨 Building and starting Chess Analyzer..."
docker compose up -d --build

echo ""
echo "✅ Chess Analyzer is running!"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📋 View logs: ./scripts/logs.sh"
echo "🛑 Stop:      ./scripts/stop.sh"
