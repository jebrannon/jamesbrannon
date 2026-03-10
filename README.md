# James Brannon

Personal portfolio site — [jamesbrannon.co.uk](https://jamesbrannon.co.uk)

## Stack

### Frontend
- **Vite 5** — dev server and build tool
- **LESS** — CSS preprocessing
- **Vanilla JS** — no framework dependencies

### CMS
- **FastAPI** — REST API (`/api/*`) + admin UI (`/admin`)
- **starlette-admin** — admin UI with Tabler design system
- **DynamoDB** (local: moto server, production: AWS)
- **Ollama** — local LLM for auto-generating post excerpts (llama3.2)

## Requirements

- Node 20+ (use [nvm](https://github.com/nvm-sh/nvm))
- Python 3.9+

## Installation

### Frontend

```bash
nvm use
npm install
```

### CMS

```bash
cd cms
bash setup.sh
```

This creates `cms/.venv`, installs Python dependencies, and copies `.env.example` → `.env`.
Edit `cms/.env` to set credentials before running.

## Development

Three processes are needed for full local development:

```bash
# 1. Local DynamoDB (moto server)
cd cms && source .venv/bin/activate
moto_server -p 8001 &

# 2. CMS API + admin
uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
npm run dev
```

| Service      | URL                              |
|-------------|----------------------------------|
| Frontend     | http://localhost:3000            |
| CMS admin    | http://127.0.0.1:8000/admin      |
| API          | http://127.0.0.1:8000/api        |

Admin credentials are set in `cms/.env` (default: `admin / changeme`).

Vite proxies `/api` and `/admin` to port 8000 in development, so the frontend
at port 3000 can reach the CMS without CORS configuration.

## Ollama (auto-excerpt)

Posts save an AI-generated excerpt if none is provided manually.

```bash
brew install ollama
ollama pull llama3.2
ollama serve
```

Runs at `http://localhost:11434` by default. Configure via `OLLAMA_URL` and
`OLLAMA_MODEL` in `cms/.env`. Silent failure — saves succeed even if Ollama is down.

## Testing

```bash
# All tests (Vitest + pytest) — also runs on every commit via git hook
npm test

# Frontend only
npx vitest run

# CMS only
cd cms && source .venv/bin/activate && pytest tests/ -v
```

~271 tests total: 85 Vitest (frontend) + 186 pytest (CMS, 5 skipped).

## Build

```bash
npm run build
```

Outputs a production-ready bundle to `dist/`.

```bash
npm run preview
```

Serves the `dist/` build locally for final checks before deploying.

## Project structure

```
├── index.html
├── public/
│   └── images/
├── src/
│   ├── js/
│   │   ├── main.js
│   │   ├── router.js
│   │   └── components/
│   ├── less/
│   │   ├── _base/
│   │   ├── _layout/
│   │   ├── _mixins/
│   │   ├── _theme/
│   │   └── main.less
│   └── tests/
├── cms/
│   ├── app/
│   │   ├── admin/          # starlette-admin views + templates
│   │   ├── routers/        # FastAPI route handlers (posts, pages, categories)
│   │   ├── services/       # image processing (Pillow), LLM (Ollama)
│   │   ├── db.py           # DynamoDB CRUD helpers
│   │   ├── models.py       # Pydantic models
│   │   └── main.py         # FastAPI app entry point
│   ├── tests/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── setup.sh
└── vite.config.js
```

## Git hooks

- **pre-commit** — runs Vitest + pytest on every commit
- **pre-push** — secret scanning (AWS keys, tokens, .env files) + build integrity tests + pytest
