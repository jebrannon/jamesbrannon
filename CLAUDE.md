# CLAUDE.md — James Brannon Portfolio

This file gives an LLM everything needed to pick up work on this codebase without prior context.

---

## What This Is

Personal portfolio/blog site for jamesbrannon.co.uk. Two halves:

1. **Site** — Vanilla JS SPA (pathname routing), LESS styles, built by Vite. Deployed to S3 + CloudFront. Source in `src/`.
2. **CMS** — FastAPI app with a Starlette Admin UI. Runs on AWS Lambda (via Mangum adapter). DynamoDB for storage. Source in `cms/`.

> **Naming convention:** always refer to these as **Site** and **CMS**. "Frontend/backend" or "frontend/API" are ambiguous — the CMS has both a backend API and an admin UI frontend.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Site | Vite 7.3, Vitest 4.0, Vanilla JS, LESS |
| CMS | FastAPI 0.128, starlette-admin 0.16, Mangum 0.21 |
| Database | DynamoDB (local: moto mock server; production: AWS) |
| Image processing | Pillow 11.3 (hero thumbnails + block images) |
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
npx vitest run                        # Frontend only (~150 tests)
cd cms && pytest tests/ -v            # Backend only (~311 tests, 4 skipped)
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
│   ├── main.js          # Entry point: loads styles, nav, router, footer, brand
│   ├── router.js        # Pathname-based SPA routing, dynamic meta tags, SEO
│   ├── nav.js           # Navigation menu
│   ├── brand.js         # Favicon/social links from API
│   ├── footer.js        # Footer contact links + scrollToFooter for /contact route
│   ├── utils.js         # HTML escape, date formatting
│   └── components/
│       └── blog-feed.js # Blog feed rendering
├── src/less/
│   ├── main.less        # Master import (loads all others)
│   ├── _base/           # normalize, defaults, helpers, colours, typography, themes
│   ├── _mixins/         # retina, cross-browser, typography mixins
│   ├── _theme/          # colour-scheme, typography-scheme
│   └── _layout/         # menu, body, header, footer
├── cms/app/
│   ├── main.py          # FastAPI app, CORS, middleware, security headers, lifespan
│   ├── handler.py       # AWS Lambda entry point (Mangum wrapper)
│   ├── models.py        # All Pydantic models (Post, Page, Category, Settings, SEO)
│   ├── db.py            # DynamoDB CRUD helpers, table auto-create
│   ├── constants.py     # DynamoDB key constants (CONTENT_POST, SETTINGS_BRAND, etc.)
│   ├── admin/
│   │   ├── views.py     # Starlette Admin ModelView subclasses + custom field types
│   │   ├── auth.py      # SimpleAuthProvider + rate limiting
│   │   └── templates/   # Custom Jinja2 admin templates
│   │       ├── layout.html          # Base layout; injects jbDialog singleton
│   │       ├── modals/actions.html  # Overrides Starlette Admin delete confirmation
│   │       └── forms/               # Custom field templates (toggle, asset_upload, etc.)
│   ├── routers/         # FastAPI routers: posts.py, pages.py, categories.py, settings.py
│   └── services/
│       ├── image.py     # Hero image + block image processing (local FS or S3)
│       └── llm.py       # Ollama excerpt generation (fire-and-forget)
├── cms/tests/           # pytest — conftest.py, test_*.py (moto + httpx)
│                        #   test_admin_views.py, test_auth.py, test_categories.py,
│                        #   test_favicon.py, test_image.py, test_llm.py,
│                        #   test_models.py, test_oauth.py, test_pages.py,
│                        #   test_posts.py, test_settings.py, test_startup.py,
│                        #   test_upload.py, test_views_helpers.py
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
| Settings | `SETTINGS` | `BRAND` / `SEO` / `PROFILE` / `BLOG` / `LAST_UPDATED` |

All PK/SK constants are in `cms/app/constants.py`.

**Pydantic models** (all in `cms/app/models.py`):

- `Post` — slug, title, blocks (List[Dict]), date, published, category, excerpt, hero_image_url, hero_thumbnail_url + SEOMixin + ContentBase
- `Page` — slug, title, blocks, published + SEOMixin + ContentBase
- `Category` — slug, name, page_headline, max_items + ContentBase
- `BrandSettings` — display_name, role_title, logo_url, logo_dark_mode, favicon_url (single SVG with embedded dark-mode media query), favicon_dark_mode, linkedin, linkedin_text, instagram, instagram_text, email, email_text
- `SeoSettings` — inherits SEOMixin (seo_title, seo_description, og_image, og_type, canonical_url, no_index)
- `ProfileSettings` — headline, tagline, summary, blog feed config (BlogSettings), strengths (StrengthsSection), experience (ExperienceSection)
- `BlogSettings` — headline, category, limit (homepage blog feed)
- `StrengthsSection` / `StrengthItem` — headline, items list (name, description)
- `ExperienceSection` / `ExperienceItem` — headline, items list (job_title, company, dates, summary, page_link)
- `BlogPageSettings` — page_headline (stored under SETTINGS_BLOG key)
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
POST /api/preview-svg             # Auth-required; dark-mode inject preview (nothing saved)
GET /health                       # Health check
```

---

## Site Routing (SPA)

Pathname-based, handled in `src/js/router.js`. CloudFront must be configured with a catch-all 404 → `index.html` rule so all paths serve the SPA.

| Path | Page |
|---|---|
| `/` | Homepage — profile summary, blog feed, strengths, experience (from `/api/settings/profile`) |
| `/blog` | Blog listing — paginated (10/page), supports `?page=N` |
| `/blog/{slug}` | Blog post detail |
| `/contact` | Scrolls to `#Footer` (contact links from Brand settings) |
| `/{slug}` | Dynamic CMS page — any unmatched path looks up `/api/pages/{slug}` |

Router dynamically updates `<title>`, `<meta description>`, Open Graph tags, and `<link rel="canonical">`. Exported functions: `route(path, search)`, `navigate(href)`, `initRouter()`, `renderHomepage()`, `renderBlogListing(page)`, `renderPost(slug)`, `renderCMSPage(slug)`, `render404()`, `applyTheme(data)`, `applyHead(data)`, `fetchJSON(url)`.

`blog-feed.js` exports: `renderBlogFeed(container, options)`, `initBlogFeeds()` (auto-init all `[data-jb-blog-feed]` elements).

---

## Environment Variables

**Local** (`cms/.env`):
```
ENV=local                              # informational only — not read by app code
DYNAMODB_ENDPOINT=http://localhost:8001  # presence of this var signals local dev mode
DYNAMODB_TABLE=jamesbrannon-content
AWS_REGION=eu-west-2
AWS_ACCESS_KEY_ID=local
AWS_SECRET_ACCESS_KEY=local
ADMIN_USER=admin
ADMIN_PASS=changeme
SECRET_KEY=dev-secret-key-change-in-production
S3_BUCKET=jamesbrannon-media          # blank = use local filesystem
S3_BUCKET_REGION=eu-west-2
S3_ENDPOINT_URL=http://localhost:9000  # MinIO — omit for local FS fallback
S3_PUBLIC_BASE_URL=http://localhost:9000/jamesbrannon-media
```

> **Local dev detection:** `main.py` detects local dev by the presence of `DYNAMODB_ENDPOINT` (`_IS_LOCAL_DEV = bool(os.getenv("DYNAMODB_ENDPOINT"))`). The `ENV` var is present in `.env.example` for human readability only — the app does not read it.

**Optional:**
```
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
# Google OAuth (leave blank to use ADMIN_USER/ADMIN_PASS instead)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_ALLOWED_DOMAINS=jamesbrannon.co.uk
OAUTH_REDIRECT_URI=http://localhost:8000/auth/callback
```

**Production** (injected at runtime — never in `.env`):
```
ENV=production
DYNAMODB_TABLE=jamesbrannon-content
AWS_REGION=eu-west-2
SECRET_KEY=<python3 -c "import secrets; print(secrets.token_hex(32))">
CORS_ORIGINS=https://jamesbrannon.co.uk
S3_BUCKET=jamesbrannon-media
S3_BUCKET_REGION=eu-west-2
# Google OAuth — recommended for production
GOOGLE_CLIENT_ID=<from Google Cloud Console>
GOOGLE_CLIENT_SECRET=<from SSM>
GOOGLE_ALLOWED_DOMAINS=jamesbrannon.co.uk
OAUTH_REDIRECT_URI=https://<api-gateway-domain>/auth/callback
# Only required if NOT using Google OAuth
# ADMIN_USER=<strong>
# ADMIN_PASS=<strong>
```

---

## Admin UI

URL: `/admin` (Starlette Admin)

**Views** (`cms/app/admin/views.py`):
- `PostView` — create/edit blog posts (slug, title, rich text blocks, hero image, category, SEO, theme); auto-dates on publish; auto-generates excerpt via Ollama
- `PageView` — create/edit static pages
- `CategoryView` — manage categories
- `BlogSettingsView` — singleton: blog landing page headline
- `ProfileView` — singleton: homepage content (headline, tagline, summary, blog feed config, experience, strengths)
- `BrandView` — singleton: favicons (SVG upload → PNG generation), social links + display text
- `SeoView` — singleton: site-level SEO and Open Graph settings
- `DashboardView` — admin homepage (latest post, last-updated timestamp)

**Auth** (`cms/app/admin/auth.py`):
- `SimpleAuthProvider` — username/password, constant-time HMAC comparison, rate-limited (5 attempts / 15 min). Used when `GOOGLE_CLIENT_ID` is unset.
- `GoogleOAuthProvider` — delegates to Google OAuth 2.0 (`/auth/google` → `/auth/callback`), domain-restricted via `GOOGLE_ALLOWED_DOMAINS`.

**Custom field types** (`cms/app/admin/views.py`):
- `BlocksField` — block editor (text + media, repeatable); uses `forms/blocks.html`
- `RichTextField` — contenteditable rich-text with formatting toolbar; sanitised via bleach; uses `forms/rich_text.html`
- `ToggleField` — styled toggle switch (BooleanField subclass); uses `forms/toggle.html`
- `EnumSelectField` — plain Bootstrap select for enums; uses `forms/enum_select.html`
- `SlugAutoFillField` — auto-generates slug from title (posts) or name (categories); uses `forms/slug_autofill.html`
- `FieldsetCollectionField` — repeated fieldsets (experience, strengths); uses `forms/collection_fieldset.html`
- `PageSelectField` — dynamic select from `/api/pages`; uses `forms/page_select.html`
- `CategorySelectField` — dynamic select from `/api/categories`; uses `forms/category_select.html`
- `SvgFileField` — SVG upload via CustomUploader modal (preview + optional dark mode injection); uses `forms/asset_upload.html`
- `ImageFileField` — image upload with preview; uses `forms/image_upload.html`

**Custom form templates** (`cms/app/admin/templates/forms/`): `blocks.html`, `rich_text.html`, `toggle.html`, `enum_select.html`, `slug_autofill.html`, `collection_fieldset.html`, `page_select.html`, `category_select.html`, `asset_upload.html`, `image_upload.html`

---

## Image Handling

`cms/app/services/image.py`:

- `save_hero_image(image_bytes, slug, ext)` — saves original + generates 1200×630 JPEG thumbnail via Pillow; returns `(hero_url, thumbnail_url)`
- `save_block_image(image_bytes, name, ext)` — saves block editor image; returns URL
- `save_favicon(svg_bytes, save_name, inject_dark_mode=True)` — saves SVG + generates PNG variants at 16, 32, 192, 512 px via cairosvg (optional); returns SVG URL
- `save_logo(svg_bytes, inject_dark_mode=True)` — saves site logo SVG; returns URL
- `_inject_dark_mode(svg_bytes)` — injects `@media (prefers-color-scheme: dark)` into SVG if not present; samples dominant fill colour to determine flip direction
- `ensure_s3_bucket_exists()` — called on lifespan startup; creates bucket if missing (no-op when S3 not configured)

**Local:** saved to `cms/static/post-images/` (images), `cms/static/favicons/` (favicons), `cms/static/logos/` (logo)
**Production:** uploaded to `s3://{S3_BUCKET}/post-images/`, `s3://{S3_BUCKET}/favicons/`, `s3://{S3_BUCKET}/logos/` — switched automatically by presence of `S3_BUCKET` env var.

Static files served by FastAPI at `/static/`.

---

## Shared Dialog Component (jbDialog)

A singleton Alpine component that provides a reusable confirmation dialog throughout the admin UI.

**Files:**
- Singleton HTML + script: `cms/app/admin/templates/layout.html` (injected once into every page)
- Action modal override: `cms/app/admin/templates/modals/actions.html` (overrides Starlette Admin's delete confirmation — keeps same IDs so `actions.js` wiring is untouched)
- CSS class: `.jb-dialog` (`cms/static/admin.css`, layer 5/components)

**Usage from any page:**
```js
window.jbDialog.open({
  title: 'Are you sure?',       // optional, defaults to 'Are you sure?'
  body:  'This cannot be undone.',
  onConfirm: () => { /* ... */ },
});
```

**Alpine config (global singleton):**
```js
jbDialog() // exposed as window.jbDialog via init() lifecycle hook
// State: title, body (reactive — drives the template)
// Methods: open({ title, body, onConfirm }), confirm(), cancel()
```

**CSS class `.jb-dialog`:** dark background (`--jb-dark`), no header/footer dividers, 1rem padding all around, 480px min-width, H4 modal title (italic bold), custom close icon (`/static/icons/close.svg`).

**Modal backdrop:** controlled by `.modal-backdrop.show { opacity: 0.75 }`. Token: `--jb-backdrop: rgba(0, 0, 0, 0.75)` (defined in `admin-tokens.css`; the `.show` opacity rule is what actually applies it).

---

## CustomUploader Component

The **CustomUploader** is the reusable file upload component for the admin UI. Currently handles SVG uploads; designed to be extended for other media types.

**Files:**
- Template: `cms/app/admin/templates/forms/asset_upload.html`
- Alpine component: `window.assetUpload` (defined inline in the template, registered once via IIFE guard)
- CSS classes: `jb-upload-*` prefix (`cms/static/admin.css`, layer 8)
- Preview endpoint: `POST /api/preview-svg` (`cms/app/main.py`)

**Alpine config shape:**
```js
assetUpload({
  currentUrl:  '/static/logos/logo.svg',  // saved asset URL or ''
  previewType: 'logo',                    // 'logo' | 'favicon' | ''
  darkMode:    true,                      // true only for SVG uploads
})
```

**Modal flow:**
1. User clicks "Choose file" → file picker opens
2. File selected → Bootstrap modal opens with raw SVG preview
3. If `darkMode: true`: toggle shown — "Add dark mode support?"
4. Toggle on → `POST /api/preview-svg` → spinner shown (no cancel) → modal preview updates; dual light/dark swatches shown side by side when dark mode is on
5. Confirm → file staged, inline preview updated, modal closes
6. Cancel (or Escape/backdrop) → file selection cleared, saved asset preview restored

**Dark mode flag:**
A hidden input `<input type="hidden" name="{field_id}_dark_mode" value="true|false">` is submitted with the form. `BrandView._dark_mode_flag()` reads it and passes `inject_dark_mode` to `save_logo()`/`save_favicon()`.

**Using it in a new field:**
```jinja2
{% with action=('EDIT' | ra),
        data=obj[field.name],
        error=errors.get(field.name, None) if errors else None,
        current_url=raw_obj.some_url,
        preview_type='logo',
        dark_mode=true %}
    {% include field.form_template %}
{% endwith %}
```
Set `field.form_template = "forms/asset_upload.html"` in the field's `__post_init__`.

**CSS classes:**
- `.jb-upload` — root wrapper
- `.jb-upload-preview-row` — flex row of swatches
- `.jb-upload-preview-row--logo` / `--favicon` — size variants (80px / 24px)
- `.jb-upload-swatch--light` / `--dark` — background variants
- `.jb-upload-modal` — upload modal (extends `.jb-dialog`)
- `.jb-upload-modal-preview` — preview area inside modal (dark bg, `align-items: stretch`)
- `.jb-upload-modal-swatches` — dual side-by-side light/dark swatch layout (dark mode on)
- `.jb-upload-progress` / `.jb-upload-progress-bar` — file read progress

**`POST /api/preview-svg`:** Auth-gated (session required). Accepts `multipart/form-data` with `file` field. Returns `{"preview": "data:image/svg+xml;base64,..."}`. Validates SVG by checking content starts with `<`. Nothing is saved.

---

## Design System

Site and Admin token systems are intentionally separate:

- **Site** — `src/less/_base/colours.less` (LESS variables + CSS custom properties) and `src/less/_base/typography.less` (CSS custom properties). Compiled by Vite/LESS into the Site bundle.
- **Admin** — `cms/static/admin-tokens.css` (CSS custom properties for colours, typography, and buttons) and `cms/static/admin.css` (component styles). Loaded directly by `cms/app/admin/templates/base.html`.

They currently share the same colour and typography values but are not linked — changing one does not affect the other. This is intentional.

LESS files in `src/less/` follow the structure: `_base/` → `_mixins/` → `_theme/` → `_layout/`, all imported by `src/less/main.less`.

Font: Barlow Semi Condensed (Google Fonts). Loaded via Google Fonts CDN in both the Site (`index.html`) and the CMS admin (`cms/app/admin/templates/base.html`).

### Admin CSS architecture

Load order: `tabler.min.css` (CDN) → `admin-tokens.css` → `admin.css`. This order is critical — our files must load after Tabler to override it.

**Token ownership rule:** every `var(--jb-*)` is ours (defined in `admin-tokens.css`); every `var(--tblr-*)` is Tabler's API. These two prefixes are the complete distinction.

**`admin-tokens.css`** defines all custom design tokens:
- `--jb-dark/light/primary/secondary/grey-dark/grey-mild/grey-light` — brand palette
- `--font`, `--fs-*`, `--lh-*`, `--fw-*`, `--ls-*` — typography scale
- `--jb-btn-radius/font/fs/lh/fw/padding/transform` — button base
- `--jb-btn-primary/secondary/default/danger-*` — button variants (bg, text, hover-bg, hover-text)
- `--jb-btn-disabled-bg/border/text` — disabled state (dark bg, dark border, mild-grey text)
- `--jb-icon-close/home/logout/message` — icon path strings (NOT `url()` — CSS vars can't interpolate inside `url()`)
- `--jb-backdrop` — modal overlay: `rgba(0, 0, 0, 0.75)`
- `--jb-radius` — 0.25rem; applied to inputs, buttons, UI components

**`admin.css`** is structured in 8 explicit layers:
1. **Tabler remap** — override `--tblr-*` tokens to apply our palette (the intended Tabler theming API)
2. **Typography** — body, headings, text utilities (`b/strong` use `--fw-medium`)
3. **Layout** — navbar, sidebar, page header/body, list toolbar
4. **Forms** — inputs, labels, fieldset legends, card chrome; toggle component (`.jb-toggle-row`)
5. **Components** — buttons (incl. disabled state), badges, tables, sidebar icons; shared dialog (`.jb-dialog`)
6. **Singleton pages** — scoped via `.jb-singleton` class (added to `<body>` by `singleton_edit.html`)
7. **Block editor** — all `.jb-block*` and rich-text editor styles
8. **Upload** — SVG/image upload components (`.jb-upload-*`), swatch variants, modal extends `.jb-dialog`

**`!important` discipline:** only used where Tabler's high-specificity selectors cannot be beaten by token remapping alone. Always accompanied by a comment explaining why.

**No inline styles in templates.** BEM modifier classes handle variants (`.jb-upload-swatch--light`, `.jb-upload-swatch--dark`, `.jb-pixel-preview`). If you find yourself writing `style=` in a template, add a class to `admin.css` instead.

---

## Security Hardening

Already in place:
- `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`
- `Strict-Transport-Security` (production only)
- CORS restricted to `CORS_ORIGINS` env var
- Rate-limited login (5 attempts / 15 min, tracked in-memory)
- Constant-time HMAC comparison for admin password
- Session middleware: `httponly=True`, `secure=True` (prod), `samesite=strict`
- App refuses to start with default credentials outside `ENV=local` (also enforced for missing `S3_BUCKET`)
- Google OAuth 2.0 support — domain-locked; `GOOGLE_CLIENT_ID` presence enables it; falls back to `ADMIN_USER`/`ADMIN_PASS` when absent
- CSRF-safe OAuth state parameter (random token in session, validated on callback)

---

## AWS Deployment

See **`DEPLOYMENT.md`** for the full deployment plan — architecture, agreed decisions, AWS resource names, environment variable reference, deployment checklist, and post-launch runbook.

**Lambda entry point:** `cms/app/handler.py` (`handler.handler`)

Key facts for development context:
- IaC: AWS CDK (Python) in `infra/`
- Local S3 mock: MinIO (Docker) — same code path as production
- All file saves (images, favicons) go direct to S3/MinIO — no FastAPI `/static` mount in production
- Secrets via SSM Parameter Store
- Deploy on push to `master`

---

## Conventions

- **Slugs:** lowercase + hyphens, regex `^[a-z0-9][a-z0-9-]*$`, validated on write
- **Python constants:** UPPERCASE (e.g. `CONTENT_POST`, `SETTINGS_BRAND`) in `constants.py`
- **Private helpers:** `_leading_underscore`
- **Logging:** JSON format `{"time": "...", "level": "...", "name": "...", "msg": "..."}`, debug for optional failures, exceptions logged with stack traces
- **Async:** FastAPI services are async; routers use standard `def` handlers (FastAPI runs them in a thread pool). Mangum handles the Lambda ↔ ASGI bridge
- **DynamoDB:** Single-table design — always use helpers in `db.py`, never raw boto3 calls in routers
- **Tests:** `@mock_aws` decorator from moto, fixture-based setup in `conftest.py`, test isolation per test function

---

## Current Branch

`CLAUDE-1` — branched from `master`. Check `git log` for recent commits.
