# Deployment Plan — jamesbrannon.co.uk

This is the living deployment reference for the project. Update it as decisions change, infrastructure is added, or steps are completed. The `/sync` command will keep this in sync.

---

## Architecture

```
Browser
  ├── Static assets (HTML/JS/CSS/images)
  │     └── S3 (jamesbrannon-frontend) → CloudFront (cdn.jamesbrannon.co.uk)
  │
  ├── API + Admin (/api/*, /admin/*, /health)
  │     └── API Gateway (HTTP API) → Lambda → FastAPI via Mangum
  │
  ├── Database
  │     └── DynamoDB (jamesbrannon-content, PAY_PER_REQUEST, eu-west-2)
  │
  └── Uploaded media + admin-generated assets (favicons, tokens.css)
        └── S3 (jamesbrannon-media) → CloudFront (media.jamesbrannon.co.uk)
```

---

## Agreed Decisions

| Concern | Decision | Reason |
|---|---|---|
| IaC | AWS CDK (Python) | AWS-native, written in same language as app, lives in `infra/` |
| Local S3 mock | MinIO (Docker) | Production-like, persistent, browser UI — better dev/prod parity than moto |
| Static asset serving | S3-direct (Option B) | Same code path locally and in production — no `/static` FastAPI mount in prod |
| Secrets | SSM Parameter Store (SecureString) | Free tier, simpler than Secrets Manager for a personal project |
| Deploy trigger | Push to `master` | Solo project, auto-deploy on merge |
| Lambda memory | 512MB | Required headroom for Pillow image processing |
| Lambda timeout | 15 seconds | Sufficient for image uploads; API Gateway hard cap is 29s |
| Region | eu-west-2 (London) | Closest to intended audience |
| CDN strategy | Two separate CloudFront distributions | Site caches aggressively; media caches aggressively; API/admin bypasses CloudFront entirely. Cleaner cache policy separation, no extra cost. |
| Admin deployment | Same Lambda as API | Personal site — traffic doesn't justify two deployments. Simplicity wins. |
| Admin auth | Google OAuth (domain-locked) | `GOOGLE_ALLOWED_DOMAINS` env var. Local dev falls back to `ADMIN_USER`/`ADMIN_PASS` when `GOOGLE_CLIENT_ID` is unset. Alternate domains (jamesbrannon.uk, justjam.es) can be added to the env var. |

---

## AWS Resources

All resources to be created by CDK stack in `infra/`. Names are fixed — do not change without updating env vars and CDK stack together.

| Resource | Type | Name / ID |
|---|---|---|
| DynamoDB table | Table | `jamesbrannon-content` |
| Media S3 bucket | S3 | `jamesbrannon-media` |
| Frontend S3 bucket | S3 | `jamesbrannon-frontend` |
| Lambda function | Lambda | `jamesbrannon-cms` |
| API Gateway | HTTP API | `jamesbrannon-api` |
| CloudFront (site) | Distribution | `jamesbrannon.co.uk` → origin: `jamesbrannon-frontend` S3 — aggressive caching |
| CloudFront (media) | Distribution | `media.jamesbrannon.co.uk` → origin: `jamesbrannon-media` S3 — aggressive caching |
| Lambda IAM role | IAM Role | `jamesbrannon-lambda-role` |
| SSM — Google client ID | SecureString | `/jamesbrannon/prod/GOOGLE_CLIENT_ID` |
| SSM — Google client secret | SecureString | `/jamesbrannon/prod/GOOGLE_CLIENT_SECRET` |
| SSM — secret key | SecureString | `/jamesbrannon/prod/SECRET_KEY` |
| ACM certificate | Certificate | `jamesbrannon.co.uk` + `*.jamesbrannon.co.uk` (us-east-1 for CloudFront) |
| Route 53 hosted zone | DNS | `jamesbrannon.co.uk` |

---

## Environment Variables

Full reference for production Lambda environment. All sensitive values come from SSM at deploy time — never hardcoded.

| Variable | Value / Source | Notes |
|---|---|---|
| `ENV` | `production` | Enables production mode (HSTS, strict auth, S3 required) |
| `DYNAMODB_TABLE` | `jamesbrannon-content` | Absence of `DYNAMODB_ENDPOINT` signals production DynamoDB |
| `AWS_REGION` | `eu-west-2` | |
| `GOOGLE_CLIENT_ID` | SSM `/jamesbrannon/prod/GOOGLE_CLIENT_ID` | OAuth app client ID — set to enable Google Sign-in |
| `GOOGLE_CLIENT_SECRET` | SSM `/jamesbrannon/prod/GOOGLE_CLIENT_SECRET` | |
| `GOOGLE_ALLOWED_DOMAINS` | `jamesbrannon.co.uk` | Comma-separated. Add `jamesbrannon.uk`, `justjam.es` etc. as needed |
| `OAUTH_REDIRECT_URI` | `https://<api-gateway-domain>/auth/callback` | Must match the authorised redirect URI in Google Cloud Console |
| `SECRET_KEY` | SSM `/jamesbrannon/prod/SECRET_KEY` | Generate: `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `CORS_ORIGINS` | `https://jamesbrannon.co.uk` | Comma-separated if multiple origins needed |
| `S3_BUCKET` | `jamesbrannon-media` | Must be set — absence causes startup failure in production |
| `S3_BUCKET_REGION` | `eu-west-2` | |
| `S3_ENDPOINT_URL` | _(unset in production)_ | Only for local dev / MinIO — absence means real AWS S3 |
| `S3_PUBLIC_BASE_URL` | _(unset in production)_ | Override for public file URL base; defaults to AWS S3 path pattern |
| `OLLAMA_URL` | _(unset in production)_ | Optional — local LLM for excerpt generation (default: http://localhost:11434) |
| `OLLAMA_MODEL` | _(unset in production)_ | Optional — Ollama model name (default: llama3.2) |

See `cms/.env.production.example` for the full template.

---

## Local Development vs Production Parity

| Concern | Local | Production |
|---|---|---|
| Database | moto mock server (:8001) | AWS DynamoDB (eu-west-2) |
| S3 / file storage | MinIO (Docker, :9000) | AWS S3 (jamesbrannon-media) |
| API server | uvicorn --reload (:8000) | Lambda + API Gateway |
| Frontend | Vite dev server (:3000) | S3 + CloudFront |
| Secrets | `cms/.env` file | SSM Parameter Store |
| Admin static assets | MinIO bucket | S3 (jamesbrannon-media) + CloudFront |

The code path for file storage is identical in both environments — boto3 pointed at MinIO locally, at AWS S3 in production. Switching is controlled entirely by env vars.

---

## Deployment Checklist

Work through this in order. Tick items off as they are completed.

### Phase 1 — Local dev parity ✅
- [x] Add MinIO to `docker-compose.yml` and `start.sh`
- [x] Refactor `image.py` to use S3-direct for all file saves (hero images, block images, favicons)
- [x] Add `S3_BUCKET` startup validation to `main.py` (fail fast if missing in production)
- [x] Update `cms/.env.example` with MinIO config
- [x] Update tests to use moto S3 mock (329 passing, 4 skipped)

### Phase 2 — Infrastructure (CDK)
- [ ] Scaffold `infra/` CDK app (Python)
- [ ] DynamoDB table stack
- [ ] S3 buckets stack (media + frontend)
- [ ] Lambda function + IAM role stack
- [ ] API Gateway HTTP API stack
- [ ] CloudFront distributions stack (site + media)
- [ ] ACM certificate (us-east-1 for CloudFront)
- [ ] Route 53 hosted zone + DNS records
- [ ] SSM parameters (create manually — never in CDK or git)

### Phase 3 — CI/CD
- [ ] Add deploy workflow (`.github/workflows/deploy.yml`) — triggered on push to `master`
- [ ] Frontend build step: `npm run build` → upload `dist/` to S3 → CloudFront invalidation
- [ ] Backend build step: package Lambda zip (app + dependencies) → deploy via CDK
- [ ] Store AWS deploy credentials as GitHub Actions secrets

### Phase 4 — Pre-launch
- [ ] End-to-end test on staging AWS account
- [ ] Admin UI feature complete
- [ ] All content entered and published
- [ ] SEO settings configured
- [ ] Performance check (Lambda cold start, CloudFront cache headers)
- [ ] Security review (CORS origins, CSP headers, rate limiting)

### Phase 5 — Launch
- [ ] Point Route 53 to CloudFront distributions
- [ ] Verify SSL certificate
- [ ] Smoke test all routes
- [ ] Monitor Lambda logs (CloudWatch) for first 24 hours

---

## Post-Deployment Runbook

*(To be filled in once deployment is complete)*

### Deploying a change
Push to `master` — GitHub Actions handles the rest.

### Updating SSM secrets
```bash
aws ssm put-parameter \
  --name "/jamesbrannon/prod/ADMIN_PASS" \
  --value "new-value" \
  --type SecureString \
  --overwrite \
  --region eu-west-2
```
Then redeploy Lambda to pick up the new value.

### Rolling back
```bash
# Roll back to previous Lambda version via CDK or AWS Console
# Or revert the commit and push to master to trigger a redeploy
```

### Checking logs
```bash
aws logs tail /aws/lambda/jamesbrannon-cms --follow --region eu-west-2
```

---

## Open Questions

*(Add anything undecided here so it doesn't get lost)*

None currently.
