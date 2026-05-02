# Kinetic — Deployment Checklist

Target platform: **Render** (Blueprint deploy via `render.yaml`).
The checklist is ordered; complete each section before moving to the next.

---

## Prerequisites

- [ ] Render account at render.com (free tier sufficient to start)
- [ ] GitHub repo connected to Render (Settings → Connect account)
- [ ] Google Gemini API key — obtain from [aistudio.google.com](https://aistudio.google.com)
- [ ] `uv` installed locally for hash generation: `pip install uv`

---

## 1 — Prepare credentials.toml

This file holds tenant usernames, bcrypt password hashes, and (for SQLite local mode) DB paths.
It is **gitignored and must never be committed**. You will upload it to Render as a Secret File.

**1a. Copy the example:**
```bash
cp credentials.toml.example credentials.toml
```

**1b. Generate a bcrypt hash for each tenant password:**
```bash
uv run python -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_PASSWORD', bcrypt.gensalt()).decode())"
```

**1c. Fill in `credentials.toml`:**
```toml
[tenants.demo]
password_hash = "$2b$12$<hash-from-step-1b>"
db_path = "./kinetic_demo.db"      # ignored in production (Postgres used instead)
display_name = "Demo"

[tenants.personal]
password_hash = "$2b$12$<hash-from-step-1b>"
db_path = "./kinetic_personal.db"  # ignored in production
display_name = "Personal"
```

> **Tenant notes:**
> - The `demo` tenant unlocks the "Simulate Week" button in the dashboard.
> - Add additional `[tenants.<name>]` blocks for any other users.
> - `db_path` values are only used in local SQLite mode; they are ignored when `DATABASE_URL` is set.

---

## 2 — Deploy via Render Blueprint

**2a.** In the Render dashboard, click **New → Blueprint**.
**2b.** Select the Kinetic GitHub repo. Render reads `render.yaml` automatically.
**2c.** Render will provision:
- `kinetic-db` — PostgreSQL 16, basic-256mb (~$7/mo)
- `kinetic-api` — Python web service, starter plan (~$7/mo, always-on)
- `kinetic-frontend` — Static site, free plan

**2d.** Let the initial build run. It will **fail** on first deploy — that is expected until the secret file and env vars are set in steps 3–4.

---

## 3 — Upload credentials.toml as a Secret File

**3a.** In the Render dashboard, open the **kinetic-api** service.
**3b.** Go to **Environment → Secret Files → Add Secret File**.
**3c.** Set the filename to exactly:
```
/etc/secrets/credentials.toml
```
**3d.** Paste the full contents of your local `credentials.toml` into the file body field.
**3e.** Save. (Render will re-deploy automatically.)

---

## 4 — Configure Environment Variables

### kinetic-api

Navigate to **kinetic-api → Environment → Environment Variables**.

| Variable | Value | Notes |
|---|---|---|
| `GEMINI_API_KEY` | `AIza…` | From aistudio.google.com |
| `FRONTEND_URL` | `https://kinetic-frontend-c2bd.onrender.com` | Set after the frontend service URL is known; enables CORS |
| `SECRET_KEY` | *(auto-generated)* | Already set by Blueprint — do not override unless rotating |
| `CREDENTIALS_PATH` | `/etc/secrets/credentials.toml` | Already set by Blueprint — do not change |
| `DATABASE_URL` | *(auto-injected)* | Already set by Blueprint binding — do not change |
| `PYTHON_VERSION` | `3.12.0` | Already set by Blueprint — do not change |

After saving, Render triggers a new deploy. The pre-deploy migration script runs automatically before the app starts.

### kinetic-frontend

Navigate to **kinetic-frontend → Environment → Environment Variables**.

| Variable | Value | Notes |
|---|---|---|
| `VITE_API_BASE_URL` | `https://kinetic-api-drk6.onrender.com` | Vite bakes this into the JS bundle at build time |

After saving, **manually trigger a redeploy** of `kinetic-frontend` (Deploy → Deploy latest commit) so Vite rebuilds with the correct API URL baked in.

---

## 5 — Verify the Deploy

**5a. Health check:**
```
GET https://kinetic-api-drk6.onrender.com/health
→ {"status": "ok"}
```

**5b. Auth endpoint:**
```
POST https://kinetic-api-drk6.onrender.com/api/auth/login
Content-Type: application/json
{"username": "demo", "password": "<your-demo-password>"}
→ {"access_token": "...", "token_type": "bearer"}
```

**5c. Frontend loads:** open `https://kinetic-frontend-c2bd.onrender.com` — you should see the landing page, and be able to log in with a tenant from credentials.toml.

**5d. Simulate Week (demo tenant only):** after logging in as `demo`, click **Simulate Week** to seed historical data and verify the full dashboard renders.

---

## 6 — Adding or Rotating Tenants

To add a tenant or change a password after initial deploy:

1. Generate a new bcrypt hash locally (step 1b above).
2. Edit `credentials.toml` locally — add or update the `[tenants.<name>]` block.
3. In Render: **kinetic-api → Environment → Secret Files** — edit the file and paste the updated contents.
4. Render redeploys automatically.

To **remove** a tenant, delete their block from the secret file and redeploy.

---

## 7 — Rotating SECRET_KEY

Rotating the key invalidates all active JWTs (all users will be logged out).

1. Generate a new key: `python -c "import secrets; print(secrets.token_hex(32))"`
2. In Render: **kinetic-api → Environment → Environment Variables** — update `SECRET_KEY`.
3. Render redeploys automatically.

---

## Local Development Reference

```bash
cp .env.example .env
# Fill in GEMINI_API_KEY and SECRET_KEY

cp credentials.toml.example credentials.toml
# Fill in password hashes for local tenants

uv sync
uv run uvicorn kinetic.main:app --reload --port 8000

cd frontend && npm install && npm run dev
# Frontend on :5173, proxies /api → :8000
```

SQLite is used locally (no `DATABASE_URL` needed). Each named tenant gets its own `kinetic_<tenant>.db` file.
