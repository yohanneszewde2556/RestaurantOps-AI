# RestaurantOps AI — Architecture Documentation

## Overview

RestaurantOps AI follows a **clean, layered architecture** with strict frontend/backend separation. Every architectural decision is made with production maintainability and future scaling in mind.

---

## Backend Architecture

```
Request → FastAPI Router → Service Layer → Database (SQLAlchemy)
                        ↘ AI Agent → Tool calling → Service Layer
                        ↘ Integration (Telegram / Weather / Gemini)
                        ↘ Scheduler (APScheduler) → Service Layer
```

### Layers

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Routers** | `app/api/` | HTTP request handling, input validation via Pydantic |
| **Services** | `app/services/` | Business logic, the single source of truth for all operations |
| **Models** | `app/models/` | SQLAlchemy ORM table definitions |
| **Schemas** | `app/schemas/` | Pydantic request/response contracts |
| **Agents** | `app/agents/` | Gemini AI tool definitions + orchestration |
| **Integrations** | `app/integrations/` | External API clients (Gemini, Telegram, Open-Meteo) |
| **Automation** | `app/automation/` | APScheduler job definitions |
| **Database** | `app/database/` | Engine, session factory, migrations |
| **Core** | `app/core/` | Configuration, response envelopes, shared utilities |

### Key Decisions

**1. Service layer as the single gated entry point**
AI tools, scheduler jobs, and API routes all call the *same* service functions. This means:
- Validation runs once, in one place.
- Authorization checks are centralized.
- No route can be bypassed by the AI.

**2. Async all the way through**
FastAPI + aiosqlite + async SQLAlchemy keeps the event loop non-blocking. Every database query, external API call, and scheduler job is async-native.

**3. Pydantic for all I/O**
Every API request and response is typed with Pydantic models. The AI agent receives only structured data from service functions — never raw SQL results.

**4. Secrets on the backend only**
`GEMINI_API_KEY` and `TELEGRAM_BOT_TOKEN` are read from environment variables server-side only. The frontend never sees them.

---

## Frontend Architecture

```
Browser → React Router → DashboardLayout (Shell)
                       → Page Component
                       → useApi Hook → services/api.ts → FastAPI
```

### Layers

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Pages** | `src/pages/` | Route-level smart components |
| **Layouts** | `src/layouts/` | Shell wrappers (sidebar + topbar) |
| **Components** | `src/components/` | Reusable, stateless UI pieces |
| **Hooks** | `src/hooks/` | Encapsulated data-fetching logic |
| **Services** | `src/services/` | API call wrappers (no business logic) |
| **Types** | `src/types/` | TypeScript types mirroring backend Pydantic schemas |
| **Utils** | `src/utils/` | Pure formatting / helper functions |

### Key Decisions

**1. Proxy-based API calls**
Vite proxies `/api` → `http://localhost:8000` in development. The frontend never hardcodes a base URL.

**2. Typed API envelope**
Every backend response is `ApiSuccess<T> | ApiError`. The frontend discriminates on `response.success` before using data, making error handling explicit.

**3. `useApi` generic hook**
One hook pattern for all data fetching: loading state, error state, data, and a `refetch` trigger. No third-party data-fetching library needed at this stage.

---

## Data Flow: Inventory Check (Stage 7+)

```
APScheduler trigger
  → InventoryCheckJob (automation/inventory_check.py)
    → InventoryService.get_low_stock_ingredients()
      → SQLAlchemy query
    → GeminiAgent.analyze(low_stock_items)
      → Gemini API (tool calling)
        → ProcurementService.suggest_order()  ← validated service call
    → TelegramIntegration.send_message(report)
    → AutomationLogService.log(result)
```

---

## Database Schema (Stage 2)

Planned tables:
- `ingredients` — stock levels, expiry, thresholds
- `sales` — menu item sales records
- `sale_items` — ingredients consumed per sale (junction)
- `procurement_orders` — suggested/approved supplier orders
- `procurement_items` — line items per order
- `automation_logs` — scheduler job execution history

---

## Security Model

| Concern | Mitigation |
|---------|-----------|
| API key exposure | Keys only in `.env` on backend; never sent to browser |
| CORS | Explicitly configured to local origins only (in dev) |
| SQL injection | SQLAlchemy ORM with parameterized queries |
| Input validation | Pydantic validates all request bodies |
| AI tool access | AI calls service functions, not raw DB access |
