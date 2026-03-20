# ♟ Chess Analyzer

**AI-powered chess game analysis and coaching for Chess.com players**

Chess Analyzer fetches your games from Chess.com, analyzes them with Stockfish, detects recurring weaknesses and patterns, and provides personalized AI coaching — all running privately on your home network.

<!-- Screenshot placeholder: The dashboard shows a dark-themed UI with analysis summary cards, opening performance charts, phase accuracy breakdowns, and an interactive AI coach chat panel -->

## ✨ Features

- **Game Analysis** — Fetches and analyzes your recent Chess.com games using Stockfish
- **Weakness Detection** — Identifies recurring patterns and weaknesses across your games
- **Opening Performance** — Tracks win rates and accuracy for each opening you play
- **Phase Analysis** — Breaks down your performance in opening, middlegame, and endgame
- **Color Comparison** — Compares your play as White vs Black
- **Mistake Examples** — Highlights your most instructive mistakes with context
- **AI Coaching Summary** — GPT-generated personalized coaching narrative
- **Interactive AI Coach Chat** — Ask questions about your games, weaknesses, and improvement paths
- **Multi-Player Support** — Analyze multiple Chess.com usernames as local profiles
- **Modern Dashboard** — Professional, responsive dark-themed UI
- **Dockerized** — One command to build and run on any machine
- **Raspberry Pi Ready** — Optimized for ARM64, runs on a Pi 5 with Ubuntu Server

## 🏗 Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Next.js   │────▶│   FastAPI    │────▶│  Chess.com  │
│  Frontend   │     │   Backend    │     │  Public API │
│  (Port 3000)│     │  (Port 8000) │     └─────────────┘
└─────────────┘     │              │
                    │  ┌─────────┐ │     ┌─────────────┐
                    │  │ SQLite  │ │────▶│  Stockfish  │
                    │  │   DB    │ │     │   Engine    │
                    │  └─────────┘ │     └─────────────┘
                    │              │
                    │              │────▶┌─────────────┐
                    │              │     │  OpenAI API │
                    └──────────────┘     └─────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 14, React, Tailwind CSS, Recharts |
| Backend | Python 3.11, FastAPI, Uvicorn |
| Database | SQLite (async via aiosqlite) |
| Chess Engine | Stockfish (via python-chess) |
| AI | OpenAI API (gpt-4o-mini) |
| Deployment | Docker, Docker Compose |

## 📋 Prerequisites

### Development Machine (Mac/Linux)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) with Docker Compose v2
- [Git](https://git-scm.com/)

### Raspberry Pi (Deployment)
- **Raspberry Pi 5** (recommended) or Pi 4 (2GB+ RAM)
- **Ubuntu Server 24.04 LTS** (64-bit ARM) or Raspberry Pi OS (64-bit)
- Docker and Git:
  ```bash
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker $USER
  # Log out and back in
  sudo apt install -y git
  ```

### Required
- **OpenAI API Key** — Get one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
  - Used for coaching summaries and AI chat
  - The app will show a clear error if this is missing

### Not Required
- No Chess.com API key (uses public API)
- No Python or Node.js on the host (everything runs in Docker)

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/chess-analyzer.git
cd chess-analyzer

# Configure environment
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY

# Build and start
./scripts/start.sh

# Open in browser
# http://localhost:3000 (local) or http://<pi-ip>:3000 (network)
```

## 🐳 Docker Usage

```bash
# Start (build if needed)
./scripts/start.sh
# or: docker compose up -d --build

# Stop
./scripts/stop.sh
# or: docker compose down

# View logs
./scripts/logs.sh
# or: docker compose logs -f

# Full rebuild (clear cache)
./scripts/rebuild.sh

# Check status
docker compose ps
```

### Data Persistence
Game data and analysis results are stored in `./data/` (mounted as a Docker volume). This directory persists across container restarts and rebuilds.

## 🍓 Raspberry Pi Deployment

### Initial Setup
```bash
# On your Pi (SSH in)
git clone https://github.com/yourusername/chess-analyzer.git
cd chess-analyzer
cp .env.example .env
nano .env  # Set OPENAI_API_KEY

./scripts/start.sh
```

### Updating
```bash
cd chess-analyzer
git pull
./scripts/start.sh  # Rebuilds automatically
```

### Performance Tuning
The default settings are optimized for Raspberry Pi:
- `ANALYSIS_DEPTH=12` — Lower = faster analysis (default is fine for Pi)
- `DEFAULT_GAME_COUNT=50` — Analyzing fewer games is faster
- Analysis runs in the background — the UI stays responsive

## ⚙️ Configuration

All configuration is via environment variables in `.env`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | — | OpenAI API key for AI features |
| `STOCKFISH_PATH` | No | `/usr/games/stockfish` | Path to Stockfish in Docker |
| `ANALYSIS_DEPTH` | No | `12` | Stockfish search depth |
| `DATABASE_PATH` | No | `/app/data/app.db` | SQLite database path |
| `DEFAULT_GAME_COUNT` | No | `50` | Default games to analyze |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model for coaching |
| `CHAT_HISTORY_LIMIT` | No | `10` | Chat messages in context |

## 🤖 AI Chess Coach

The integrated AI coach uses your analysis data to provide personalized advice:

**What it does:**
- Answers questions about your chess weaknesses
- Explains specific mistakes from your games
- Suggests study topics and training plans
- Provides opening recommendations based on your results

**What it doesn't do:**
- Analyze raw PGN or positions directly
- Make claims not supported by your data
- Replace actual Stockfish analysis

**Example questions:**
- "What is my biggest weakness?"
- "Why do I lose more with Black?"
- "Is the Sicilian working for me?"
- "What should I study to improve?"
- "Explain my mistake on move 15 against opponent123"

## 📁 Project Structure

```
chess-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Environment configuration
│   │   ├── database.py          # SQLite setup
│   │   ├── models.py            # Database models
│   │   ├── schemas.py           # API schemas
│   │   ├── routers/             # API endpoints
│   │   │   ├── analysis.py      # Analysis triggers
│   │   │   ├── players.py       # Player management
│   │   │   ├── reports.py       # Report retrieval
│   │   │   └── chat.py          # AI coach chat
│   │   └── services/            # Business logic
│   │       ├── chess_com.py     # Chess.com API client
│   │       ├── pgn_parser.py    # PGN parsing
│   │       ├── stockfish.py     # Stockfish integration
│   │       ├── weakness.py      # Weakness detection
│   │       ├── openai_summary.py # Coaching summaries
│   │       └── openai_chat.py   # AI chat
│   ├── tests/                   # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages
│   │   ├── components/          # React components
│   │   └── lib/                 # API client
│   ├── Dockerfile
│   └── package.json
├── scripts/
│   ├── start.sh                 # Build & start
│   ├── stop.sh                  # Stop
│   ├── rebuild.sh               # Full rebuild
│   └── logs.sh                  # View logs
├── docker-compose.yml
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Start game analysis |
| `GET` | `/api/status/{username}` | Get analysis progress |
| `GET` | `/api/players` | List analyzed players |
| `GET` | `/api/reports/{username}` | Get analysis report |
| `POST` | `/api/players/{username}/reanalyze` | Re-analyze a player |
| `DELETE` | `/api/players/{username}` | Delete player data |
| `POST` | `/api/chat` | Send chat message |
| `DELETE` | `/api/chat/{username}` | Clear chat history |

Full API documentation available at `http://localhost:8000/docs` (Swagger UI).

## 🔮 Future Improvements

- Interactive chess board for viewing mistake positions
- Game-by-game drill-down view
- Historical trend tracking (improvement over time)
- Lichess.org support
- Custom evaluation thresholds
- Export reports as PDF
- Dark/light theme toggle
- Webhook notifications when analysis completes
- Multi-language support

## 📄 License

This project is licensed under the GNU General Public License v3.0 — see the [LICENSE](LICENSE) file for details.

---

Built with ♟ by chess enthusiasts, for chess enthusiasts.
