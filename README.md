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

