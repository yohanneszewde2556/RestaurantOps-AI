# RestaurantOps AI 🍽️

**AI-powered inventory and procurement management for restaurants.**

RestaurantOps AI monitors ingredient stock, analyzes consumption patterns, detects low-stock and near-expiry items, generates intelligent procurement recommendations, and delivers insights through an AI assistant powered by Google Gemini.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, Recharts |
| Backend | Python 3.11+, FastAPI, SQLAlchemy, SQLite |
| AI | Google Gemini API |
| Notifications | Telegram Bot API |
| Weather | Open-Meteo API (no key required) |
| Scheduling | APScheduler |

---

## Project Structure

```
RestaurantOps AI/
├── frontend/               # React + Vite SPA
│   └── src/
│       ├── components/     # Reusable UI components
│       ├── pages/          # Route-level page components
│       ├── layouts/        # Shell layouts (sidebar, topbar)
│       ├── services/       # API call wrappers
│       ├── hooks/          # Custom React hooks
│       ├── types/          # TypeScript type definitions
│       └── utils/          # Utility functions
│
├── backend/                # FastAPI application
│   ├── main.py             # Application entry point
│   └── app/
│       ├── api/            # Route handlers (controllers)
│       ├── core/           # Config, responses, shared utilities
│       ├── models/         # SQLAlchemy ORM models
│       ├── schemas/        # Pydantic request/response schemas
│       ├── services/       # Business logic layer
│       ├── agents/         # AI agent definitions and tool calling
│       ├── integrations/   # External API clients (Gemini, Telegram, Weather)
│       ├── automation/     # APScheduler job definitions
│       └── database/       # Engine, session factory, migrations
│
├── docs/                   # Architecture docs and API specs
├── .env.example            # Environment variable template
├── .gitignore
└── README.md
```

---

## Prerequisites

- **Python** 3.11 or higher
- **Node.js** 18 or higher
- **npm** 9+ or **pnpm** 8+

---

## Quick Start

### 1. Clone and configure environment

```bash
git clone <repo-url>
cd "RestaurantOps AI"

# Copy environment template
cp .env.example backend/.env
# Edit backend/.env and fill in your API keys
```

### 2. Start the Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (macOS / Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:
- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`

### 3. Start the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

---

## Running Tests

```bash
cd backend
pytest -v
```

---

## API Keys

| Service | Where to get it | Required |
|---------|----------------|----------|
| Google Gemini | [aistudio.google.com](https://aistudio.google.com/app/apikey) | For AI assistant |
| Telegram Bot Token | [@BotFather](https://t.me/BotFather) on Telegram | For notifications |
| Telegram Chat ID | [@userinfobot](https://t.me/userinfobot) on Telegram | For notifications |
| Open-Meteo | No key needed | Built-in |

---

## Roadmap

- **Stage 1** ✅ Project initialization and architecture
- **Stage 2** — Database models (Ingredient, Sale, ProcurementOrder, AutomationLog)
- **Stage 3** — Inventory CRUD API + frontend Inventory page
- **Stage 4** — Sales tracking + consumption analytics
- **Stage 5** — AI agent with Gemini tool calling
- **Stage 6** — Procurement recommendations
- **Stage 7** — Telegram notifications
- **Stage 8** — APScheduler automation jobs
- **Stage 9** — Reports and charts
- **Stage 10** — Production hardening

---

## Architecture Decisions

### Why async SQLAlchemy + aiosqlite?
FastAPI is fully async. Using aiosqlite keeps the database I/O non-blocking, ensuring the event loop is never stalled during database queries.

### Why SQLite?
Perfect for the MVP: zero-ops, file-based, no server to manage. The SQLAlchemy abstraction makes it trivial to swap to PostgreSQL in production.

### Why is AI configuration kept on the backend?
The Gemini API key is never sent to the browser. All AI tool calling goes through validated backend service functions, so the AI cannot perform arbitrary database operations.

### Why the service layer?
AI tools call service functions, not database queries directly. This enforces validation, authorization, and business rules at a single point.
