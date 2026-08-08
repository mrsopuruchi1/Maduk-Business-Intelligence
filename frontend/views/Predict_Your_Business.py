"""
Maduk Business Intelligence - Predict Your Business View
=========================================================
File: frontend/views/Predict_Your_Business.py

React-Style UI/UX for AI Business Predictions, Revenue Forecasting,
Executive Narrative Callouts, and Interactive Dashboard Metrics.
Includes backend integration for PDF Report downloads with charts.
"""

import json
from io import BytesIO
from typing import Any, Dict

import pandas as pd
import requests
import streamlit as st


def render_predict_your_business_page():

    # =========================================================
    # CUSTOM CSS (REACT-STYLE UI/UX DESIGN SYSTEM)
    # =========================================================
    st.markdown(
        """
        <style>
        .stApp {
            background: #020617;
            color: #ffffff;
        }

        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }

        html, body, [class*="css"] {
            color: #ffffff;
        }

        /* Hero Banner Container */
        .hero-card {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            padding: 2.2rem;
            border-radius: 20px;
            border: 1px solid #334155;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        }

        .hero-title {
            color: #ffffff;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            line-height: 1.2;
        }

        .highlight-text {
            color: #facc15;
            font-weight: 700;
        }

        .subtitle {
            color: #94a3b8;
            font-size: 1.05rem;
        }

        /* Section Header Component */
        .section-card {
            background: linear-gradient(135deg, #111827 0%, #1e293b 100%);
            padding: 1.1rem 1.4rem;
            border-radius: 16px;
            border: 1px solid #334155;
            margin-top: 1.5rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 6px 20px rgba(0,0,0,0.25);
        }

        .section-title {
            color: #ffffff;
            font-size: 1.25rem;
            font-weight: 700;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .section-title span {
            color: #facc15;
        }

        /* Metric Cards */
        .metric-card {
            background: linear-gradient(135deg, #111827 0%, #1e293b 100%);
            padding: 1.4rem;
            border-radius: 16px;
            border: 1px solid #334155;
            text-align: center;
            box-shadow: 0 8px 24px rgba(0,0,0,0.35);
            min-height: 130px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .metric-title {
            color: #facc15;
            font-size: 0.85rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.6px;
        }

        .metric-value {
            color: #ffffff;
            font-size: 1.75rem;
            font-weight: 800;
            line-height: 1.2;
            word-wrap: break-word;
        }

        /* Executive Summary Callout Box */
        .exec-card {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(12px);
            border-radius: 16px;
            border: 1px solid #334155;
            padding: 1.5rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        }

        .exec-header {
            color: #38bdf8;
            font-size: 1rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .exec-narrative {
            color: #f8fafc;
            font-size: 1rem;
            line-height: 1.7;
            font-weight: 400;
        }

        .exec-rationale {
            background: rgba(30, 41, 59, 0.6);
            border-left: 3px solid #facc15;
            padding: 1rem;
            border-radius: 0 12px 12px 0;
            margin-top: 1rem;
            color: #cbd5e1;
            font-size: 0.93rem;
            line-height: 1.6;
        }

        /* Metadata Badges Grid */
        .meta-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 0.5rem;
        }

        .meta-badge {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .meta-label {
            color: #94a3b8;
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .meta-value {
            color: #f8fafc;
            font-size: 1.05rem;
            font-weight: 700;
        }

        /* Generic Insight Box */
        .insight-box {
            background: rgba(15, 23, 42, 0.6);
            color: #f1f5f9;
            padding: 1rem 1.25rem;
            border-radius: 12px;
            border: 1px solid #334155;
            margin-bottom: 0.75rem;
            font-size: 0.95rem;
            line-height: 1.6;
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
        }

        /* Success Container */
        .success-box {
            background: linear-gradient(135deg, #052e16 0%, #14532d 100%);
            color: #ffffff;
            padding: 1rem 1.2rem;
            border-radius: 14px;
            border: 1px solid #22c55e;
            margin-bottom: 1rem;
            font-size: 0.95rem;
            line-height: 1.6;
        }

        /* Action Buttons */
        .download-section {
            background: linear-gradient(135deg, #111827, #0f172a);
            padding: 1.5rem;
            border-radius: 18px;
            border: 1px solid #334155;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }

        .download-title {
            color: #ffffff;
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        div.stButton > button {
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: #ffffff;
            border: none;
            border-radius: 12px;
            padding: 0.85rem 1.5rem;
            font-weight: 700;
            width: 100%;
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        div.stButton > button:hover {
            transform: translateY(-2px);
            background: linear-gradient(135deg, #1d4ed8, #1e40af);
            color: #facc15;
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
        }

        div.stDownloadButton > button {
            background: linear-gradient(135deg, #16a34a, #15803d);
            color: #ffffff;
            border-radius: 12px;
            border: none;
            padding: 0.85rem 1.5rem;
            font-weight: 700;
            width: 100%;
        }

        div.stDownloadButton > button:hover {
            color: #facc15;
            box-shadow: 0 4px 15px rgba(22, 163, 74, 0.4);
        }

        div[data-testid="stFileUploader"] button {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #334155 !important;
            font-weight: 700;
        }

        section[data-testid="stSidebar"] {
            background: #0f172a;
            border-right: 1px solid #334155;
        }

        section[data-testid="stSidebar"] * {
            color: #ffffff !important;
        }

        .stDataFrame {
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #334155;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # =========================================================
    # HEADER HERO CARD
    # =========================================================
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">
                <span class="highlight-text">📈 AI Business Revenue</span>
                Forecasting Platform
            </div>
            <div class="subtitle">Upload your business data and get accurate/precise AI-powered revenue forecast.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # =========================================================
    # SIDEBAR CONFIGURATION
    # =========================================================
    st.sidebar.title("⚙️ Prediction Settings")

    forecast_horizon = st.sidebar.selectbox(
        "Forecast Horizon",
        ["30 Days", "90 Days", "6 Months", "12 Months"]
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Prediction Options")

    predict_revenue = st.sidebar.checkbox("Revenue Prediction", value=True)
    predict_sales = st.sidebar.checkbox("Sales Forecast", value=True)
    predict_leads = st.sidebar.checkbox("Lead Forecast", value=True)
    predict_customers = st.sidebar.checkbox("Customer Growth", value=True)
    predict_profit = st.sidebar.checkbox("Profit Prediction", value=True)

    # =========================================================
    # DATASET UPLOAD
    # =========================================================
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">
                📂 <span>Upload</span> Business Dataset
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel File",
        type=["csv", "xlsx", "xls"]
    )

    # Preview Dataset
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                preview_df = pd.read_csv(uploaded_file)
            else:
                preview_df = pd.read_excel(uploaded_file)

            st.markdown(
                """
                <div class="section-card">
                    <div class="section-title">
                        📊 <span>Dataset</span> Preview
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.dataframe(preview_df.head(10), use_container_width=True)

            st.markdown(
                f"""
                <div class="success-box">
                    <b style="color:#facc15;">✅ Dataset Loaded Successfully</b><br><br>
                    <b>Rows:</b> {preview_df.shape[0]:,}<br>
                    <b>Columns:</b> {preview_df.shape[1]:,}
                </div>
                """,
                unsafe_allow_html=True
            )

        except Exception as e:
            st.error(f"Dataset preview failed: {str(e)}")

    # Trigger Pipeline Run
    run_prediction = st.button("🚀 Run AI Revenue Forecast")

    # =========================================================
    # PIPELINE EXECUTION & RESULTS DISPLAY
    # =========================================================
    if run_prediction:
        if uploaded_file is None:
            st.warning("Please upload a dataset first.")
        else:
            with st.spinner("Executing AI Revenue Forecasting Engine..."):
                try:
                    API_URL = "http://127.0.0.1:8000/ai-business-prediction/run-pipeline"
                    uploaded_file.seek(0)

                    files = {
                        "file": (uploaded_file.name, uploaded_file, uploaded_file.type)
                    }

                    payload = {
                        "forecast_horizon": forecast_horizon,
                        "predict_revenue": predict_revenue,
                        "predict_sales": predict_sales,
                        "predict_leads": predict_leads,
                        "predict_customers": predict_customers,
                        "predict_profit": predict_profit
                    }

                    response = requests.post(API_URL, files=files, data=payload, timeout=300)

                    if response.status_code != 200:
                        st.error(f"Backend Error: {response.text}")
                    else:
                        results: Dict[str, Any] = response.json()

                        if not results.get("success", False):
                            st.error(results.get("error", "Pipeline execution failed."))
                        else:
                            st.success("AI Prediction Completed Successfully")

                            prediction_results = results.get("prediction_results", {})
                            forecast_results = results.get("forecast_results", {})
                            metrics = results.get("model_metrics", {})
                            executive_summary = results.get("executive_summary", {})
                            pipeline_metadata = results.get("pipeline_metadata", {})

                            # 1. METRICS DASHBOARD
                            st.markdown(
                                """
                                <div class="section-card">
                                    <div class="section-title">📊 AI Results Dashboard</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            predicted_revenue = forecast_results.get("predicted_revenue", 0)
                            forecast_growth = forecast_results.get("forecast_growth_percent", 0)
                            best_month = forecast_results.get("best_month", "N/A")
                            confidence_score = metrics.get("forecast_accuracy", "N/A")

                            col1, col2, col3, col4 = st.columns(4)

                            with col1:
                                st.markdown(
                                    f"""
                                    <div class="metric-card">
                                        <div class="metric-title">Predicted Revenue</div>
                                        <div class="metric-value">${predicted_revenue:,.0f}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                            with col2:
                                st.markdown(
                                    f"""
                                    <div class="metric-card">
                                        <div class="metric-title">Forecast Growth</div>
                                        <div class="metric-value">{forecast_growth}%</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                            with col3:
                                st.markdown(
                                    f"""
                                    <div class="metric-card">
                                        <div class="metric-title">Best Period</div>
                                        <div class="metric-value">{best_month}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                            with col4:
                                st.markdown(
                                    f"""
                                    <div class="metric-card">
                                        <div class="metric-title">Confidence Score</div>
                                        <div class="metric-value">{confidence_score}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                            # 2. AI BUSINESS INSIGHTS
                            st.markdown(
                                """
                                <div class="section-card">
                                    <div class="section-title">🧠 AI Business Insights</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            insights = results.get("business_insights", [])
                            if insights:
                                for insight in insights:
                                    st.markdown(
                                        f"""
                                        <div class="insight-box">
                                            <span>💡</span>
                                            <div>{insight}</div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                            else:
                                st.info("No business insights generated.")

                            # 3. EXECUTIVE SUMMARY
                            st.markdown(
                                """
                                <div class="section-card">
                                    <div class="section-title">📄 Executive Summary</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            summary_narrative = executive_summary.get("summary_narrative", "Executive summary not available.")
                            selection_rationale = executive_summary.get("selection_rationale", "Selection rationale not available.")

                            st.markdown(
                                f"""
                                <div class="exec-card">
                                    <div class="exec-header">📌 Strategic Executive Narrative</div>
                                    <div class="exec-narrative">{summary_narrative}</div>
                                    <div class="exec-rationale">
                                        <b>Model Architecture Rationale:</b> {selection_rationale}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            # 4. MODEL PERFORMANCE METRICS
                            st.markdown(
                                """
                                <div class="section-card">
                                    <div class="section-title">🎯 Model Performance</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            if metrics:
                                st.dataframe(pd.DataFrame([metrics]), use_container_width=True)
                            else:
                                st.info("No model evaluation metrics available.")

                            # 5. PREDICTION RESULTS TABLE
                            predictions = prediction_results.get("predictions", [])
                            if predictions:
                                st.markdown(
                                    """
                                    <div class="section-card">
                                        <div class="section-title">📈 Prediction Results</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                st.dataframe(pd.DataFrame(predictions), use_container_width=True)

                            # 6. REVENUE FORECAST TABLE
                            forecast_table = forecast_results.get("forecast_table", [])
                            if forecast_table:
                                st.markdown(
                                    """
                                    <div class="section-card">
                                        <div class="section-title">📅 Revenue Forecast</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                st.dataframe(pd.DataFrame(forecast_table), use_container_width=True)

                            # 7. EXPORT / DOWNLOAD PDF REPORT
                            st.markdown(
                                """
                                <div class="download-section">
                                    <div class="download-title">📥 Download AI Report</div>
                                    <p style="color:#cbd5e1; margin-top:6px; line-height:1.6; font-size:0.95rem;">
                                        Export your full prediction results, embedded forecast line charts, metric bar charts, business insights, and executive summary as a formatted PDF.
                                    </p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            # Request PDF from Backend Endpoint
                            PDF_API_URL = "http://127.0.0.1:8000/ai-business-prediction/generate-pdf-report"
                            pdf_res = requests.post(PDF_API_URL, json=results, timeout=120)

                            if pdf_res.status_code == 200:
                                st.download_button(
                                    label="📄 Download Comprehensive AI Report (PDF)",
                                    data=pdf_res.content,
                                    file_name="maduk_ai_prediction_report.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                            else:
                                st.error("Failed to generate PDF report from backend.")

                            # 8. PIPELINE METADATA
                            st.markdown(
                                """
                                <div class="section-card">
                                    <div class="section-title">⚡ Pipeline Metadata</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            date_col = pipeline_metadata.get("date_column", "N/A")
                            target_col = pipeline_metadata.get("target_column", "N/A")
                            freq = pipeline_metadata.get("frequency", "N/A")
                            horizon = pipeline_metadata.get("forecast_horizon", "N/A")
                            confidence = pipeline_metadata.get("confidence_level", 0.95)

                            st.markdown(
                                f"""
                                <div class="meta-grid">
                                    <div class="meta-badge">
                                        <div class="meta-label">Date Field</div>
                                        <div class="meta-value">{date_col}</div>
                                    </div>
                                    <div class="meta-badge">
                                        <div class="meta-label">Target Column</div>
                                        <div class="meta-value">{target_col}</div>
                                    </div>
                                    <div class="meta-badge">
                                        <div class="meta-label">Inferred Frequency</div>
                                        <div class="meta-value">{freq}</div>
                                    </div>
                                    <div class="meta-badge">
                                        <div class="meta-label">Horizon Steps</div>
                                        <div class="meta-value">{horizon} Periods</div>
                                    </div>
                                    <div class="meta-badge">
                                        <div class="meta-label">Confidence Level</div>
                                        <div class="meta-value">{float(confidence)*100:.0f}%</div>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                except Exception as e:
                    st.error(f"Pipeline execution error: {str(e)}")
