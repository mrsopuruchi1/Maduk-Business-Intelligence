# Maduk Business Intelligence (Maduk BI)

Maduk-Business-Intelligence is an AI SaaS platform that contains softwares that perform data analysis, business revenue forecast, and business health prediction & recommendation that help digital agencies and service business executives to make informed data-driven decisions.

Maduk BI also contains AI chatbot that answers questions about a business based on the dataset uploaded to it. The platform serves as an autonomous AI business consultant that helps digital agencies and service businesses to make informed decisions and succeed.

Built with:
- Streamlit frontend
- FastAPI backend
- PostgreSQL database
- Flutterwave payments
- PDF report generation
- AI forecasting

## Features

✔ Multi-format data loading (CSV, Excel, JSON)  
✔ Data analysis and charts  
✔ Revenue forecasting (ML)  
✔ AI recommendations  
✔ PDF report export  
✔ Email automation  
✔ Subscription tiers  
✔ Currency auto-detection (NGN/USD)  
✔ Secure authentication  
✔ Payment integration

## Architecture

Frontend:
- Streamlit (UI)

Backend:
- FastAPI (auth, payments)
- PostgreSQL (database)

Payments:
- Flutterwave subscription billing

Hosting:
- Render

## Setup

### Frontend

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py

## Render deployment

This repository is structured as two Render web services:

- **`maduk-bi-frontend`** — Streamlit application (`frontend/App.py`)
- **`maduk-bi-backend`** — FastAPI API (`backend/main.py`)
- **`maduk-bi-postgres`** — Render PostgreSQL database

The root `render.yaml` defines the services and database. Secrets such as `SECRET_KEY`, `OPENAI_API_KEY`, Flutterwave credentials, and SMTP credentials must be supplied in the Render Dashboard and are never committed to Git.

For local development, copy `.env.example` to `.env` and provide local values.

### Production data

Do not use the local SQLite database in production. Render PostgreSQL is the production database. Uploaded datasets and generated model artifacts are runtime data and are intentionally excluded from Git.

### Service communication

The Streamlit frontend reads `BACKEND_API_HOSTPORT` and sends server-side requests to the FastAPI service over Render's private network. The FastAPI service uses `DATABASE_URL` supplied by the Render PostgreSQL resource.
