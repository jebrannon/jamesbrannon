# James Brannon

Personal portfolio site — [jamesbrannon.co.uk](https://jamesbrannon.co.uk)

---

## Stack

| Layer | Technology |
|---|---|
| Site | Vite 7.3, Vitest 4.0, Vanilla JS, LESS |
| CMS | FastAPI 0.128, starlette-admin 0.16, Mangum 0.21 |
| Database | DynamoDB (local: moto mock, production: AWS) |
| AI | Ollama (llama3.2) — auto-generates post excerpts |

---

## Quick start

**Requirements:** Node 20+ (via [nvm](https://github.com/nvm-sh/nvm)) and Python 3.12+

### 1. First-time setup

```bash
# Install frontend dependencies (nvm switches to Node 20 via .nvmrc)
nvm use && npm install

# Set up the CMS Python environment and create your .env
cd cms && bash setup.sh
```

`setup.sh` creates `cms/.venv`, installs Python dependencies, and copies `.env.example → .env`.
Edit `cms/.env` to set credentials before running (default is `admin / changeme` for local dev).

> The `.env` file is gitignored and never committed. If you need to recreate it: `cp cms/.env.example cms/.env`

### 2. Start everything

```bash
bash start.sh
```

That's it. `start.sh` loads the right Node version, starts DynamoDB and the CMS API in the
background, then runs the Vite dev server in the foreground. `Ctrl+C` stops everything.

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| CMS admin | http://localhost:8000/admin |
| API | http://localhost:8000/api |

Background service logs are written to `/tmp/moto.log` and `/tmp/uvicorn.log`.

---

## Development

### Docker (alternative to manual setup)

If you prefer Docker, a single command starts both DynamoDB and the API:

```bash
cd cms && docker compose up
```

DynamoDB data is persisted across restarts via a named Docker volume (`dynamodb-data`).

### Seed data

Populate a fresh local database with sample content:

```bash
cd cms && source .venv/bin/activate && python seed.py
```

The script is idempotent — safe to run multiple times.

### Ollama (optional — AI excerpt generation)

Posts auto-generate an excerpt via a local LLM when none is provided manually.
Saves succeed silently if Ollama is not running — it's optional.

```bash
brew install ollama
ollama pull llama3.2
ollama serve   # runs at http://localhost:11434
```

Configure the URL and model via `OLLAMA_URL` and `OLLAMA_MODEL` in `cms/.env`.

---

## Testing

```bash
# Frontend tests (Vitest)
npm test

# Frontend only
npx vitest run

# Backend only
cd cms && source .venv/bin/activate && pytest tests/ -v
```

~506 tests: ~156 Vitest (Site) + ~350 pytest (CMS, 4 skipped). CI runs on every push via GitHub Actions.

---

## Build

```bash
npm run build      # outputs production bundle to dist/
npm run preview    # serve dist/ locally for a final check
```

---

## Project structure

```
├── src/
│   ├── js/
│   │   ├── main.js
│   │   ├── router.js
│   │   ├── nav.js
│   │   ├── footer.js
│   │   ├── brand.js
│   │   ├── utils.js
│   │   └── components/
│   ├── less/
│   └── tests/
├── cms/
│   ├── app/
│   │   ├── admin/          # starlette-admin views + auth
│   │   ├── routers/        # API route handlers (posts, pages, categories)
│   │   ├── services/       # image processing (Pillow), LLM (Ollama)
│   │   ├── db.py           # DynamoDB CRUD helpers
│   │   ├── models.py       # Pydantic models
│   │   ├── handler.py      # AWS Lambda entry point (Mangum)
│   │   └── main.py         # FastAPI app, middleware, startup
│   ├── tests/
│   ├── .env.example              # local dev env template (committed)
│   ├── .env.production.example   # production env template (committed)
│   └── setup.sh
└── .github/workflows/ci.yml
```

---

## AWS Deployment (Planned)

The site will run entirely on AWS with no servers to manage.

### Architecture

```
Browser
  │
  ├── Static assets (HTML/JS/CSS)
  │     └── S3 (static hosting) → CloudFront CDN
  │
  ├── API requests (/api/*, /admin/*)
  │     └── API Gateway (HTTP API) → Lambda → FastAPI (via Mangum)
  │
  ├── Database
  │     └── DynamoDB (PAY_PER_REQUEST, serverless)
  │
  └── Uploaded images
        └── S3 bucket (jamesbrannon-media) → CloudFront CDN
```

### How it fits together

- **`cms/app/handler.py`** is the Lambda entry point (`handler.handler`). It wraps the FastAPI app using [Mangum](https://mangum.faas.guru/).
- **Images** — `S3_BUCKET` env var switches image uploads from local filesystem to S3 automatically. No code changes needed.
- **Database** — the DynamoDB table must be pre-created by IaC (Terraform / CDK) before the first Lambda invocation. The auto-create logic in `lifespan` is bypassed in Lambda (`lifespan="off"`).
- **Secrets** — credentials are injected at runtime from AWS Secrets Manager or SSM Parameter Store, not from a `.env` file.

### What still needs doing before deployment

- [ ] IaC (CDK) — DynamoDB table, Lambda function, API Gateway, S3 buckets, CloudFront distributions
- [ ] Domain and SSL — Route 53 + ACM certificate for `jamesbrannon.co.uk`
- [ ] SSM Parameter Store — store `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `SECRET_KEY`
- [ ] CI/CD — GitHub Actions deploy workflow (push to `master` → build + deploy)
- [ ] Google OAuth — register app in Google Cloud Console, set redirect URI

### Required production environment variables

See `cms/.env.production.example` for the full template. Key variables:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Strong random string — `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth app credentials (recommended) |
| `GOOGLE_ALLOWED_DOMAINS` | Comma-separated domains e.g. `jamesbrannon.co.uk` |
| `OAUTH_REDIRECT_URI` | Must match the redirect URI registered in Google Cloud Console |
| `CORS_ORIGINS` | CloudFront domain, e.g. `https://jamesbrannon.co.uk` |
| `S3_BUCKET` / `S3_BUCKET_REGION` | Media upload bucket |
| `DYNAMODB_TABLE` / `AWS_REGION` | DynamoDB config |

---

## Git hooks

- **pre-commit** — runs Vitest + pytest
- **pre-push** — secret scanning (AWS keys, tokens, `.env` files) + build check + pytest
