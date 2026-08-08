"""
Maduk Business Intelligence - Executive Business Health & Recommendation Page
File: frontend/views/Get_Business_Recommendation.py

Production-ready React-style UI/UX built with Streamlit for AI business health 
predictions, financial key metrics, time-series forecasting, recommendations, 
and inline PDF report previews/downloads.
"""

import os
import base64
import json
from typing import Dict, Any, Optional

import pandas as pd
import requests
import streamlit as st

# Configurable backend endpoint URL
BACKEND_ENDPOINT = os.getenv(
    "BACKEND_API_URL", 
    "http://127.0.0.1:8000/api/v1/recommendations/analyze"
)


def render_pdf_iframe(pdf_base64: str, height: int = 700):
    """Renders a responsive in-browser PDF document previewer."""
    # Ensure correct base64 string formatting
    cleaned_b64 = pdf_base64.strip().replace("\n", "").replace("\r", "")
    pdf_display_code = f"""
        <iframe 
            src="data:application/pdf;base64,{cleaned_b64}" 
            width="100%" 
            height="{height}px" 
            style="border: 1px solid #334155; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);"
            type="application/pdf">
        </iframe>
    """
    st.markdown(pdf_display_code, unsafe_allow_html=True)


def safe_float(val: Any, default: float = 0.0) -> float:
    """Safely coerces input to float for formatting."""
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def render_get_business_recommendation_page():
    """Main rendering entry point for the AI Recommendation & Diagnostic View."""
    
    # =========================================================
    # REACT-STYLE CSS DESIGN SYSTEM & UI COMPONENTS
    # =========================================================
    st.markdown(
        """
        <style>
        /* Base Dark Modern Reset */
        .stApp {
            background-color: #020617;
            color: #f8fafc;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }

        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        /* Hero Banner Container */
        .hero-card {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            padding: 2.2rem;
            border-radius: 20px;
            border: 1px solid #334155;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 35px rgba(0, 0, 0, 0.4);
        }

        .hero-title {
            color: #ffffff;
            font-size: 2.1rem;
            font-weight: 800;
            margin-bottom: 0.6rem;
            line-height: 1.25;
            letter-spacing: -0.02em;
        }

        .highlight-text {
            background: linear-gradient(90deg, #facc15 0%, #f59e0b 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }

        .subtitle {
            color: #94a3b8;
            font-size: 1.05rem;
            line-height: 1.5;
        }

        /* Custom Section Titles */
        .section-card {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            padding: 1.1rem 1.4rem;
            border-radius: 16px;
            border: 1px solid #334155;
            margin-top: 1.8rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
        }

        .section-title {
            color: #ffffff;
            font-size: 1.25rem;
            font-weight: 700;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }

        .section-title span {
            color: #facc15;
        }

        /* Metric Cards */
        .metric-card {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(12px);
            padding: 1.25rem;
            border-radius: 16px;
            border: 1px solid #334155;
            text-align: center;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }

        .metric-card:hover {
            transform: translateY(-2px);
            border-color: #64748b;
        }

        .metric-title {
            color: #94a3b8;
            font-size: 0.8rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
            text-transform: uppercase;
            letter-spacing: 0.6px;
        }

        .metric-value {
            color: #ffffff;
            font-size: 1.65rem;
            font-weight: 800;
            line-height: 1.2;
        }

        .metric-value-gold {
            color: #facc15;
            font-size: 1.65rem;
            font-weight: 800;
            line-height: 1.2;
        }

        /* Executive Summary */
        .exec-card {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(12px);
            border-radius: 16px;
            border: 1px solid #334155;
            padding: 1.75rem;
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
            font-size: 1.05rem;
            line-height: 1.75;
            font-weight: 400;
        }

        /* Health Badges */
        .health-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.4rem 1rem;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        .health-excellent { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid #22c55e; }
        .health-good { background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #0284c7; }
        .health-warning { background: rgba(250, 204, 21, 0.2); color: #facc15; border: 1px solid #eab308; }
        .health-critical { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }

        /* Time-Phased Action Plan Cards */
        .action-card {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 1.2rem;
            margin-bottom: 0.85rem;
        }

        .action-title-30 { color: #fca5a5; font-weight: bold; font-size: 1.05rem; margin-bottom: 0.5rem; }
        .action-title-90 { color: #fde047; font-weight: bold; font-size: 1.05rem; margin-bottom: 0.5rem; }
        .action-title-365 { color: #6ee7b7; font-weight: bold; font-size: 1.05rem; margin-bottom: 0.5rem; }

        /* Insight Box */
        .insight-box {
            background: rgba(15, 23, 42, 0.6);
            color: #f1f5f9;
            padding: 1.1rem 1.3rem;
            border-radius: 14px;
            border: 1px solid #334155;
            margin-bottom: 0.85rem;
            font-size: 0.98rem;
            line-height: 1.6;
            display: flex;
            align-items: flex-start;
            gap: 0.85rem;
        }

        /* Success & Download Block */
        .success-box {
            background: linear-gradient(135deg, #052e16 0%, #14532d 100%);
            color: #ffffff;
            padding: 1.1rem 1.3rem;
            border-radius: 14px;
            border: 1px solid #22c55e;
            margin-bottom: 1.2rem;
            font-size: 0.95rem;
            line-height: 1.6;
        }

        .download-section {
            background: linear-gradient(135deg, #0f172a, #1e293b);
            padding: 1.75rem;
            border-radius: 18px;
            border: 1px solid #334155;
            margin-top: 2rem;
            margin-bottom: 1.5rem;
        }

        .download-title {
            color: #ffffff;
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        /* Streamlit Overrides */
        div.stButton > button {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: #ffffff;
            border: none;
            border-radius: 12px;
            padding: 0.85rem 1.5rem;
            font-weight: 700;
            width: 100%;
            font-size: 1.05rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3);
        }

        div.stButton > button:hover {
            transform: translateY(-2px);
            background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
            color: #facc15;
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
        }

        /* --- ADDED FILE UPLOADER BUTTON STYLES HERE --- */
        div[data-testid="stFileUploader"] button {
            background-color: #f8fafc !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 10px !important;
            transition: all 0.2s ease !important;
        }
        
        div[data-testid="stFileUploader"] button * {
            color: #0f172a !important;
            fill: #0f172a !important;
            font-weight: 700 !important;
        }
        
        div[data-testid="stFileUploader"] button:hover {
            background-color: #e2e8f0 !important;
            border-color: #94a3b8 !important;
        }
        /* -------------------------------------------------- */

        div.stDownloadButton > button {
            background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
            color: #ffffff;
            border-radius: 12px;
            border: none;
            padding: 0.85rem 1.5rem;
            font-weight: 700;
            width: 100%;
            font-size: 1rem;
            box-shadow: 0 4px 14px rgba(22, 163, 74, 0.3);
        }

        div.stDownloadButton > button:hover {
            color: #facc15;
            box-shadow: 0 6px 20px rgba(22, 163, 74, 0.5);
        }

        section[data-testid="stSidebar"] {
            background-color: #0f172a;
            border-right: 1px solid #334155;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # =========================================================
    # HEADER HERO BANNER
    # =========================================================
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">
                <span class="highlight-text">AI Business Health Prediction</span> & Recommendation Software 🩺💡
            </div>
            <div class="subtitle">
                Upload your financial or operational business datasets to generate real-time AI-powered health scores, core executive dashboard KPIs, time-series revenue forecasts, actionable growth advice, and compiled PDF reports.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # =========================================================
    # SIDEBAR CONTROL PANEL
    # =========================================================
    st.sidebar.title("⚙️ Orchestration Parameters")
    
    company_name = st.sidebar.text_input(
        "Company / Client Name",
        value="Enterprise Client",
        help="Used for executive PDF header branding and personalized contextual narrative generation."
    )

    industry = st.sidebar.selectbox(
        "Industry Sector",
        ["General Business", "E-Commerce & Retail", "SaaS & Software", "Financial Services", "Healthcare", "Manufacturing"]
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Pipeline Execution Modules")
    st.sidebar.checkbox("Compute Data Quality Score", value=True, disabled=True)
    st.sidebar.checkbox("Compute 16 Executive KPIs", value=True, disabled=True)
    st.sidebar.checkbox("Time-Series Revenue Forecasts", value=True, disabled=True)
    st.sidebar.checkbox("Anomaly & Outlier Risk Detection", value=True, disabled=True)
    st.sidebar.checkbox("LLM Narrative & Advice Generation", value=True, disabled=True)

    # =========================================================
    # DATASET UPLOAD SECTION
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
        "Upload CSV or Excel File (.csv, .xlsx, .xls)",
        type=["csv", "xlsx", "xls"],
        help="Dataset should contain financial/operational fields such as date, revenue, expenses, profit, customers, or marketing spend."
    )

    if uploaded_file is not None:
        try:
            uploaded_file.seek(0)
            if uploaded_file.name.endswith(".csv"):
                preview_df = pd.read_csv(uploaded_file)
            else:
                preview_df = pd.read_excel(uploaded_file)

            st.markdown(
                """
                <div class="section-card">
                    <div class="section-title">
                        🔍 <span>Dataset</span> Preview & Inspection
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.dataframe(preview_df.head(6), use_container_width=True)

            st.markdown(
                f"""
                <div class="success-box">
                    <b style="color:#facc15;">✅ File Validated & Ready</b><br>
                    <b>Dimensions:</b> {preview_df.shape[0]:,} Rows × {preview_df.shape[1]:,} Columns &nbsp;|&nbsp; 
                    <b>Filename:</b> {uploaded_file.name}
                </div>
                """,
                unsafe_allow_html=True
            )

        except Exception as e:
            st.error(f"Dataset parsing preview failed: {str(e)}")

    run_pipeline_btn = st.button("🚀 Execute AI Business Health Prediction & Advice")

    # =========================================================
    # PIPELINE RUN & RESULTS DISPLAY
    # =========================================================
    if run_pipeline_btn:
        if uploaded_file is None:
            st.warning("⚠️ Please select and upload a business dataset (.csv or .xlsx) before initiating analysis.")
        else:
            with st.spinner("⚡ Firing Up AI Business Health Prediction & Advice Engine..."):
                try:
                    uploaded_file.seek(0)
                    files = {
                        "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                    }
                    form_data = {
                        "company_name": company_name,
                        "industry": industry
                    }

                    response = requests.post(BACKEND_ENDPOINT, files=files, data=form_data, timeout=300)

                    if response.status_code != 200:
                        st.error(f"Backend API Error ({response.status_code}): {response.text}")
                    else:
                        payload: Dict[str, Any] = response.json()

                        if payload.get("status") != "success":
                            st.error(f"Pipeline Execution Error: {payload.get('detail', 'Unknown error occurred.')}")
                        else:
                            st.success("🎉 AI Business Prediction & Recommendation Pipeline Executed Successfully!")

                            health = payload.get("business_health", {})
                            dash = payload.get("dashboard_metrics", {})
                            recs = payload.get("recommendations", [])
                            action_plan = payload.get("action_plan", {})
                            insights = payload.get("insights", [])
                            anomalies = payload.get("anomalies", [])
                            narrative = payload.get("narrative_summary", "")
                            quality_score = safe_float(payload.get("data_quality_score"), 100.0)
                            pdf_base64 = payload.get("pdf_report_base64", "")
                            pdf_filename = payload.get("pdf_filename", "Executive_Report.pdf")

                            # -------------------------------------------------------------
                            # 1. EXECUTIVE OVERVIEW & HEALTH SCORE
                            # -------------------------------------------------------------
                            st.markdown(
                                """
                                <div class="section-card">
                                    <div class="section-title">🏥 Strategic Business Health Diagnostic</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            health_score = safe_float(health.get("health_score"), 0.0)
                            health_status = health.get("status", "Healthy")
                            
                            status_badge_class = "health-good"
                            if health_score >= 80:
                                status_badge_class = "health-excellent"
                            elif 40 <= health_score < 60:
                                status_badge_class = "health-warning"
                            elif health_score < 40:
                                status_badge_class = "health-critical"

                            col_h1, col_h2 = st.columns([1, 2])

                            with col_h1:
                                st.markdown(
                                    f"""
                                    <div class="metric-card" style="border-color: #facc15;">
                                        <div class="metric-title">Overall Health Score</div>
                                        <div class="metric-value-gold">{health_score:.1f} / 100</div>
                                        <div>
                                            <span class="health-badge {status_badge_class}">{health_status.upper()}</span>
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                            with col_h2:
                                st.markdown(
                                    f"""
                                    <div class="exec-card" style="margin-bottom:0px; height: 100%;">
                                        <div class="exec-header">📌 Executive Strategic Narrative</div>
                                        <div class="exec-narrative">{narrative or 'Comprehensive analytical assessment performed across operational, financial, and growth indicators.'}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                            # -------------------------------------------------------------
                            # 2. 16 CORE EXECUTIVE DASHBOARD METRICS GRID
                            # -------------------------------------------------------------
                            st.markdown(
                                """
                                <div class="section-card">
                                    <div class="section-title">📊 16 Core Executive Dashboard Metrics</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            # Row 1
                            r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
                            r1_c1.markdown(f"""<div class="metric-card"><div class="metric-title">Revenue Growth</div><div class="metric-value">{safe_float(dash.get('revenue_growth')):.1f}%</div></div>""", unsafe_allow_html=True)
                            r1_c2.markdown(f"""<div class="metric-card"><div class="metric-title">Net Profit Margin</div><div class="metric-value">{safe_float(dash.get('net_profit_margin')):.1f}%</div></div>""", unsafe_allow_html=True)
                            r1_c3.markdown(f"""<div class="metric-card"><div class="metric-title">Gross Margin</div><div class="metric-value">{safe_float(dash.get('gross_margin')):.1f}%</div></div>""", unsafe_allow_html=True)
                            r1_c4.markdown(f"""<div class="metric-card"><div class="metric-title">EBITDA Margin</div><div class="metric-value">{safe_float(dash.get('ebitda_margin')):.1f}%</div></div>""", unsafe_allow_html=True)

                            st.write("")

                            # Row 2
                            r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
                            r2_c1.markdown(f"""<div class="metric-card"><div class="metric-title">Operating Margin</div><div class="metric-value">{safe_float(dash.get('operating_margin')):.1f}%</div></div>""", unsafe_allow_html=True)
                            r2_c2.markdown(f"""<div class="metric-card"><div class="metric-title">Customer Growth</div><div class="metric-value">{safe_float(dash.get('customer_growth')):.1f}%</div></div>""", unsafe_allow_html=True)
                            r2_c3.markdown(f"""<div class="metric-card"><div class="metric-title">Churn Rate</div><div class="metric-value">{safe_float(dash.get('churn_rate')):.1f}%</div></div>""", unsafe_allow_html=True)
                            r2_c4.markdown(f"""<div class="metric-card"><div class="metric-title">CLV</div><div class="metric-value">${safe_float(dash.get('clv')):,.2f}</div></div>""", unsafe_allow_html=True)

                            st.write("")

                            # Row 3
                            r3_c1, r3_c2, r3_c3, r3_c4 = st.columns(4)
                            r3_c1.markdown(f"""<div class="metric-card"><div class="metric-title">CAC</div><div class="metric-value">${safe_float(dash.get('cac')):,.2f}</div></div>""", unsafe_allow_html=True)
                            r3_c2.markdown(f"""<div class="metric-card"><div class="metric-title">Marketing ROI</div><div class="metric-value">{safe_float(dash.get('marketing_roi')):.1f}x</div></div>""", unsafe_allow_html=True)
                            r3_c3.markdown(f"""<div class="metric-card"><div class="metric-title">Cash Balance</div><div class="metric-value">${safe_float(dash.get('cash_balance')):,.2f}</div></div>""", unsafe_allow_html=True)
                            r3_c4.markdown(f"""<div class="metric-card"><div class="metric-title">Current Ratio</div><div class="metric-value">{safe_float(dash.get('current_ratio')):.2f}</div></div>""", unsafe_allow_html=True)

                            st.write("")

                            # Row 4
                            r4_c1, r4_c2, r4_c3, r4_c4 = st.columns(4)
                            r4_c1.markdown(f"""<div class="metric-card"><div class="metric-title">Debt Ratio</div><div class="metric-value">{safe_float(dash.get('debt_ratio')):.2f}</div></div>""", unsafe_allow_html=True)
                            r4_c2.markdown(f"""<div class="metric-card"><div class="metric-title">Inventory Turnover</div><div class="metric-value">{safe_float(dash.get('inventory_turnover')):.2f}</div></div>""", unsafe_allow_html=True)
                            r4_c3.markdown(f"""<div class="metric-card"><div class="metric-title">ROI</div><div class="metric-value">{safe_float(dash.get('roi')):.1f}%</div></div>""", unsafe_allow_html=True)
                            r4_c4.markdown(f"""<div class="metric-card"><div class="metric-title">Data Quality Index</div><div class="metric-value">{quality_score:.1f}/100</div></div>""", unsafe_allow_html=True)

                            # -------------------------------------------------------------
                            # 3. TIME-PHASED ACTION PLAN (IF AVAILABLE)
                            # -------------------------------------------------------------
                            if action_plan:
                                st.markdown(
                                    """
                                    <div class="section-card">
                                        <div class="section-title">🚀 Time-Phased Priority Action Plan</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                
                                act_c1, act_c2, act_c3 = st.columns(3)

                                with act_c1:
                                    st.markdown('<div class="action-card"><div class="action-title-30">⚡ Immediate (30 Days)</div>', unsafe_allow_html=True)
                                    for item in action_plan.get("immediate_30_days", ["Maintain core operational liquidity."]):
                                        st.markdown(f"• {item}")
                                    st.markdown('</div>', unsafe_allow_html=True)

                                with act_c2:
                                    st.markdown('<div class="action-card"><div class="action-title-90">🎯 Medium-Term (90 Days)</div>', unsafe_allow_html=True)
                                    for item in action_plan.get("medium_term_90_days", ["Review vendor contracts and cost structures."]):
                                        st.markdown(f"• {item}")
                                    st.markdown('</div>', unsafe_allow_html=True)

                                with act_c3:
                                    st.markdown('<div class="action-card"><div class="action-title-365">🏔️ Strategic (12 Months)</div>', unsafe_allow_html=True)
                                    for item in action_plan.get("long_term_12_months", ["Explore new market expansion opportunities."]):
                                        st.markdown(f"• {item}")
                                    st.markdown('</div>', unsafe_allow_html=True)

                            # -------------------------------------------------------------
                            # 4. GROUNDED STRATEGIC RECOMMENDATIONS & INSIGHTS
                            # -------------------------------------------------------------
                            st.markdown(
                                """
                                <div class="section-card">
                                    <div class="section-title">💡 Grounded AI Strategic Recommendations</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            if recs:
                                for idx, rec in enumerate(recs, 1):
                                    if isinstance(rec, dict):
                                        cat = rec.get("category", "Strategy")
                                        finding = rec.get("finding", "Diagnostic finding recorded.")
                                        action = rec.get("action", "Recommended action steps.")
                                        impact = rec.get("impact", "Expected business impact.")

                                        with st.expander(f"Recommendation #{idx}: [{cat}] - {finding}", expanded=(idx == 1)):
                                            st.markdown(f"**Action Plan:** {action}")
                                            st.markdown(f"**Expected Business Impact:** `{impact}`")
                                    else:
                                        st.markdown(f"• {rec}")
                            else:
                                st.info("No critical risk recommendations identified for this dataset.")

                            # Analytical Insights & Anomalies
                            if insights or anomalies:
                                ins_col1, ins_col2 = st.columns(2)

                                with ins_col1:
                                    if insights:
                                        st.markdown("#### 🧠 Automated Business Insights")
                                        for ins in insights:
                                            st.markdown(f'<div class="insight-box"><span>💡</span><div>{ins}</div></div>', unsafe_allow_html=True)

                                with ins_col2:
                                    if anomalies:
                                        st.markdown("#### ⚠️ Anomalies & Operational Alerts")
                                        for anomaly in anomalies:
                                            if isinstance(anomaly, dict):
                                                st.warning(f"**[{anomaly.get('severity', 'Alert')}] {anomaly.get('metric', 'Anomaly')}:** {anomaly.get('details', '')}")
                                            else:
                                                st.warning(f"**Anomaly:** {anomaly}")

                            # -------------------------------------------------------------
                            # 5. EXECUTIVE PDF REPORT DOWNLOAD & PREVIEW
                            # -------------------------------------------------------------
                            if pdf_base64:
                                st.markdown(
                                    """
                                    <div class="download-section">
                                        <div class="download-title">📥 Executive PDF Business Intelligence Report</div>
                                        <p style="color:#cbd5e1; margin-top:6px; line-height:1.6; font-size:0.95rem;">
                                            Download the comprehensive PDF executive package complete with embedded trend charts, 
                                            health breakdowns, 16 key dashboard indicators, and AI recommendations.
                                        </p>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                                pdf_bytes = base64.b64decode(pdf_base64)
                                
                                d_col1, d_col2 = st.columns([1, 1])

                                with d_col1:
                                    st.download_button(
                                        label="📄 Download Full PDF Report",
                                        data=pdf_bytes,
                                        file_name=pdf_filename,
                                        mime="application/pdf",
                                        use_container_width=True
                                    )

                                with d_col2:
                                    show_preview = st.checkbox("👁️ Toggle Interactive PDF Preview", value=False)

                                if show_preview:
                                    st.markdown("---")
                                    st.subheader("📄 Embedded PDF Executive Report Preview")
                                    render_pdf_iframe(pdf_base64)

                except Exception as e:
                    st.error(f"Failed to communicate with pipeline backend services: {str(e)}")


if __name__ == "__main__":
    st.set_page_config(
        page_title="AI Business Health Prediction & Recommendation Software",
        page_icon="🩺💡",
        layout="wide"
    )
    render_get_business_recommendation_page()
