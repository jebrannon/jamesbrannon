# CLAUDE.md — James Brannon Portfolio

This file gives an LLM everything needed to pick up work on this codebase without prior context.

---

## What This Is

Personal portfolio/blog site for jamesbrannon.co.uk. Two halves:

1. **Site** — Vanilla JS SPA (hash routing), LESS styles, built by Vite. Deployed to S3 + CloudFront. Source in `src/`.
2. **CMS** — FastAPI app with a Starlette Admin UI. Runs on AWS Lambda (via Mangum adapter). DynamoDB for storage. Source in `cms/`.

> **Naming convention:** always refer to these as **Site** and **CMS**. "Frontend/backend" or "frontend/API" are ambiguous — the CMS has both a backend API and an admin UI frontend.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Site | Vite 7, Vanilla JS, LESS |
| CMS | FastAPI, starlette-admin 0.16, Mangum |
| Database | DynamoDB (local: moto mock server; production: AWS) |
| Image processing | Pillow (hero thumbnails + block images) |
| AI (optional) | Ollama llama3.2 — auto-generates post excerpts |
| Node | 20 (pinned in `.nvmrc`) |
| Python | 3.12+ |

---

## Running Locally

```bash
# First-time setup
nvm use && npm install
cd cms && bash setup.sh    # creates .venv, installs deps, copies .env.example → .env

# Start all services (DynamoDB mock on :8001, API on :8000, Vite on :3000)
bash start.sh
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| CMS admin | http://localhost:8000/admin (admin / changeme for local) |
| API | http://localhost:8000/api |
| Health | http://localhost:8000/health |

Background logs: `/tmp/moto.log`, `/tmp/uvicorn.log`. `Ctrl+C` stops everything.

**Docker alternative:**
```bash
cd cms && docker compose up
```

**Seed data:**
```bash
cd cms && source .venv/bin/activate && python seed.py
```

---

## Running Tests

```bash
npm test                              # Both (mirrors CI)
npx vitest run                        # Frontend only (~85 tests)
cd cms && pytest tests/ -v            # Backend only (~115 tests)
npm run test:coverage                 # Frontend with coverage report
```

CI: GitHub Actions (`.github/workflows/ci.yml`) — Node 20 + Python 3.12, runs on push/PR.

Pre-commit hook: vitest + pytest.
Pre-push hook: secret scanning + build check + pytest.

---

## Building

```bash
npm run build      # → dist/
npm run preview    # serve dist/ locally
```

---

## Key Files to Know

```
jamesbrannon/
├── src/js/
│   ├── main.js          # Entry point: loads styles, nav, router, feeds
│   ├── router.js        # Hash-based SPA routing, dynamic meta tags, SEO
│   ├── nav.js           # Navigation menu
│   ├── brand.js         # Favicon/social links from API
│   ├── utils.js         # HTML escape, date formatting
│   └── components/
│       └── blog-feed.js # Blog feed rendering
├── src/less/
│   ├── main.less        # Master import (loads all others)
│   ├── _base/           # normalize, defaults, helpers, colours, typography, themes
│   ├── _mixins/         # retina, cross-browser, typography mixins
│   ├── _theme/          # colour-scheme, typography-scheme
│   └── _layout/         # menu, body, header
├── cms/app/
│   ├── main.py          # FastAPI app, CORS, middleware, security headers, lifespan
│   ├── handler.py       # AWS Lambda entry point (Mangum wrapper)
│   ├── models.py        # All Pydantic models (Post, Page, Category, Settings, SEO)
│   ├── db.py            # DynamoDB CRUD helpers, table auto-create
│   ├── constants.py     # DynamoDB key constants (CONTENT_POST, SETTINGS_BRAND, etc.)
│   ├── admin/
│   │   ├── views.py     # Starlette Admin ModelView subclasses
│   │   ├── auth.py      # SimpleAuthProvider + rate limiting
│   │   └── templates/   # Custom Jinja2 admin templates
│   ├── routers/         # FastAPI routers: posts.py, pages.py, categories.py, settings.py
│   └── services/
│       ├── image.py     # Hero image + block image processing (local FS or S3)
│       └── llm.py       # Ollama excerpt generation (fire-and-forget)
├── cms/tests/           # pytest — conftest.py, test_*.py (moto + httpx)
├── src/tests/           # Vitest — *.test.js (happy-dom)
├── cms/.env.example     # Local dev env template (committed)
├── cms/.env.production.example  # Production env template (committed)
├── vite.config.js       # Dev server :3000, proxies /api + /admin + /static → :8000
└── start.sh             # Starts moto + uvicorn + vite in one command
```

---

## Data Model

**Database:** AWS DynamoDB, single table (`jamesbrannon-content`).

**Key schema:**

| Record type | PK | SK |
|---|---|---|
| Post | `CONTENT#POST` | `SLUG#<slug>` |
| Page | `CONTENT#PAGE` | `SLUG#<slug>` |
| Category | `CONTENT#CATEGORY` | `SLUG#<slug>` |
| Settings | `SETTINGS` | `BRAND` / `SEO` / `PROFILE` |

All PK/SK constants are in `cms/app/constants.py`.

**Pydantic models** (all in `cms/app/models.py`):

- `Post` — slug, title, blocks (List[Dict]), date, published, category, excerpt, hero_image_url, hero_thumbnail_url + SEOMixin + ContentBase
- `Page` — slug, title, blocks, published + SEOMixin + ContentBase
- `Category` — slug, name, page_headline, max_items + ContentBase
- `BrandSettings` — favicons (light/dark), linkedin, instagram, email
- `SeoSettings` — inherits SEOMixin (seo_title, seo_description, og_image, og_type, canonical_url, no_index)
- `ProfileSettings` — headline, tagline, summary, blog feed config, strengths, experience sections
- `ContentBase` — theme_mode (dark/light), theme_style (professional/thoughts) + SEOMixin
- `SEOMixin` — seo_title, seo_description, og_image, og_type, canonical_url, no_index

**Enums:** `ThemeMode` (dark/light), `ThemeStyle` (professional/thoughts), `OGType` (website/article/profile)

No migrations. Table is created automatically by `db.create_table_if_not_exists()` on app startup (lifespan event). In Lambda, lifespan is off — table must be pre-created by IaC.

---

## API Endpoints

All read-only; no auth required. Admin writes go through the `/admin` UI.

```
GET /api/posts                    # Published posts (sorted by date desc)
GET /api/posts/{slug}             # Single published post
GET /api/pages                    # Published pages
GET /api/pages/{slug}             # Single published page
GET /api/categories               # All categories
GET /api/categories/{slug}        # Single category
GET /api/settings/brand           # Brand settings (favicons, socials)
GET /api/settings/seo             # Site SEO settings
GET /api/settings/profile         # Profile / homepage content
POST /api/upload-image            # Auth-required; upload block editor image
GET /health                       # Health check
```

---

## Frontend Routing (SPA)

Hash-based, handled in `src/js/router.js`:

| Hash | Page |
|---|---|
| `#about` | Homepage (profile, blog feed, experience) |
| `#blog` | Blog listing |
| `#blog/{slug}` | Blog post detail |
| `#contact` | Contact page |
| `#page/{slug}` | Static page |
| *(fallback)* | Homepage |

Router dynamically updates `<title>`, `<meta description>`, Open Graph tags, and `<link rel="canonical">`.

---

## Environment Variables

**Local** (`cms/.env`):
```
ENV=local
DYNAMODB_ENDPOINT=http://localhost:8001
DYNAMODB_TABLE=jamesbrannon-content
AWS_REGION=eu-west-2
AWS_ACCESS_KEY_ID=local
AWS_SECRET_ACCESS_KEY=local
ADMIN_USER=admin
ADMIN_PASS=changeme
SECRET_KEY=dev-secret-key-change-in-production
S3_BUCKET=                   # blank = use local filesystem
S3_BUCKET_REGION=eu-west-2
```

**Optional:**
```
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

**Production** (injected at runtime — never in `.env`):
```
ENV=production
DYNAMODB_TABLE=jamesbrannon-content
AWS_REGION=eu-west-2
ADMIN_USER=<strong>
ADMIN_PASS=<strong>
SECRET_KEY=<python3 -c "import secrets; print(secrets.token_hex(32))">
CORS_ORIGINS=https://jamesbrannon.co.uk
S3_BUCKET=jamesbrannon-media
S3_BUCKET_REGION=eu-west-2
```

---

## Admin UI

URL: `/admin` (Starlette Admin)

**Views** (`cms/app/admin/views.py`):
- `PostView` — create/edit blog posts (slug, title, rich text blocks, hero image, category, SEO, theme)
- `PageView` — create/edit static pages
- `CategoryView` — manage categories
- `ProfileView` — homepage content (headline, tagline, blog feed config, experience, strengths)
- `BrandView` — favicons, social links
- `SeoView` — site-level SEO
- `DashboardView` — admin homepage

**Auth** (`cms/app/admin/auth.py`): `SimpleAuthProvider` — username/password, constant-time comparison (HMAC), rate-limited (5 attempts / 15 min).

**Custom form templates** (`cms/app/admin/templates/forms/`):
- `blocks.html` — block editor (rich text + images)
- `rich_text.html` — TinyMCE WYSIWYG
- `enum_select.html` — dropdown for theme_style, og_type, etc.
- `slug_autofill.html` — auto-generates slug from title
- `collection_fieldset.html` — repeated fieldsets (experience entries, strengths)

---

## Image Handling

`cms/app/services/image.py`:

- `save_hero_image(slug, file)` — saves original + generates 1200×630 JPEG thumbnail via Pillow
- `save_block_image(slug, name, file)` — saves block editor image

**Local:** saved to `cms/static/post-images/`
**Production:** uploaded to `s3://{S3_BUCKET}/post-images/` — switched automatically by presence of `S3_BUCKET` env var.

Static files served by FastAPI at `/static/`.

---

## Design System

`cms/static/tokens.css` — CSS custom properties for colours and typography. The intended single source of truth for design tokens, shared by both the Site and the CMS admin.

**Known debt:** tokens are currently duplicated. The Site defines identical values in `src/less/_base/colours.less` and `src/less/_base/typography.less` (comments in those files acknowledge this). The goal is for `cms/static/tokens.css` to be the sole definition, with the Site consuming it directly. Until that's done, any token change must be made in both places.

LESS files in `src/less/` follow the structure: `_base/` → `_mixins/` → `_theme/` → `_layout/`, all imported by `src/less/main.less`.

Font: Barlow Semi Condensed (Google Fonts). Loaded via Google Fonts CDN in both the Site (`index.html`) and the CMS admin (`cms/app/admin/templates/base.html`).

---

## Security Hardening

Already in place:
- `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`
- `Strict-Transport-Security` (production only)
- CORS restricted to `CORS_ORIGINS` env var
- Rate-limited login (5 attempts / 15 min, tracked in-memory)
- Constant-time HMAC comparison for admin password
- Session middleware: `httponly=True`, `secure=True` (prod), `samesite=strict`
- App refuses to start with default credentials outside `ENV=local`

---

## AWS Deployment

See **`DEPLOYMENT.md`** for the full deployment plan — architecture, agreed decisions, AWS resource names, environment variable reference, deployment checklist, and post-launch runbook.

**Lambda entry point:** `cms/app/handler.py` (`handler.handler`)

Key facts for development context:
- IaC: AWS CDK (Python) in `infra/`
- Local S3 mock: MinIO (Docker) — same code path as production
- All file saves (images, favicons, tokens.css) go direct to S3/MinIO — no FastAPI `/static` mount in production
- Secrets via SSM Parameter Store
- Deploy on push to `master`

---

## Conventions

- **Slugs:** lowercase + hyphens, regex `^[a-z0-9][a-z0-9-]*$`, validated on write
- **Python constants:** UPPERCASE (e.g. `CONTENT_POST`, `SETTINGS_BRAND`) in `constants.py`
- **Private helpers:** `_leading_underscore`
- **Logging:** JSON format `{"time": "...", "level": "...", "name": "...", "msg": "..."}`, debug for optional failures, exceptions logged with stack traces
- **Async:** All FastAPI routers and services are async; Mangum handles the Lambda ↔ ASGI bridge
- **DynamoDB:** Single-table design — always use helpers in `db.py`, never raw boto3 calls in routers
- **Tests:** `@mock_aws` decorator from moto, fixture-based setup in `conftest.py`, test isolation per test function

---

## Current Branch

`CLAUDE-1` — branched from `master`. Check `git log` for recent commits.
