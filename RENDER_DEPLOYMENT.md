# Render deployment checklist for Maduk Business Intelligence

## Architecture

- `frontend/App.py`: Streamlit UI
- `backend/main.py`: FastAPI API
- Render Postgres: production database
- Streamlit calls FastAPI through Render's private network using `BACKEND_API_HOSTPORT`

## Blueprint

`render.yaml` provisions:
- `maduk-bi-frontend` (Streamlit)
- `maduk-bi-backend` (FastAPI)
- `maduk-bi-postgres` (Postgres 17)

The current plans are Starter for the frontend, Standard for the backend, and Basic-256MB for Postgres. Adjust the plans in Render if needed.

## Secrets

Set these in Render, not Git:
- `OPENAI_API_KEY`
- `FLUTTERWAVE_SECRET_KEY`
- `FLUTTERWAVE_PUBLIC_KEY`
- `FLUTTERWAVE_SECRET_HASH`
- `SMTP_SERVER`
- `SMTP_EMAIL`
- `SMTP_PASSWORD`
- `REDIS_URL` only if Redis/Key Value is provisioned

`SECRET_KEY` is generated automatically by the Blueprint.

## Important production behavior

- The local SQLite database is excluded. Production uses Render Postgres.
- Local datasets and generated model artifacts are excluded from Git.
- The FastAPI backend converts Render's `postgresql://` URL to the async SQLAlchemy `postgresql+asyncpg://` form.
- The frontend no longer hard-codes `localhost:8000`.
- Flutterwave's payment redirect uses Render's `RENDER_EXTERNAL_URL` when available.
- OpenAI calls use the current Python client interface.

## Deploy

1. Replace/update the corresponding files in your local Git repository with this Render-ready version.
2. Run `git status`.
3. Confirm `.env`, `venv/`, `*.db`, `*.csv`, `*.pkl`, and generated logs are not tracked.
4. If generated files were previously tracked, remove them from Git's index with `git rm --cached` before committing.
5. Commit and push.
6. In Render, create a new Blueprint from the repository and select `render.yaml`.
7. Enter the requested secret values.
8. Wait for the Postgres, backend, and frontend services to deploy.
9. Test the backend `/health` endpoint and then the Streamlit service.
