import streamlit as st
from utils.api_config import get_backend_url
import requests
import json
import base64
import streamlit.components.v1 as components


# ============================================
# 🧠 INSIGHT PROCESSOR (ROBUST)
# ============================================
def simplify_insights(insights):
    clean = []

    if not insights:
        return []

    for ins in insights:
        # handle dict or string safely
        if isinstance(ins, dict):
            ins = ins.get("text") or ins.get("insight") or str(ins)

        ins_text = str(ins)

        lower = ins_text.lower()

        if "strong positive relationship" in lower:
            clean.append("Customers who spend more tend to make more purchases.")
        elif "influential factor" in lower:
            clean.append("Spending behavior is the strongest driver of performance.")
        else:
            clean.append(ins_text)

    return list(dict.fromkeys(clean))


# ============================================
# 🔧 SAFE JSON PARSER
# ============================================
def safe_json_parse(line):
    try:
        return json.loads(line.decode("utf-8"))
    except Exception:
        return None


# ============================================
# MAIN PAGE
# ============================================
def render_analyze_your_data_page():

    # ============================================
    # 🎨 UI STYLING (React-style cards)
    # ============================================
    st.markdown("""
    <style>
    .container {max-width: 1100px; margin: auto; padding-top: 20px;}

    .card {
        background: linear-gradient(135deg, #0B1E3A, #132E57);
        color: #E5E7EB;
        padding: 18px;
        border-radius: 16px;
        box-shadow: 0px 6px 18px rgba(0,0,0,0.2);
        margin-bottom: 12px;
        font-size: 15px;
    }

    .title {font-size: 32px; font-weight: 700; color: #111827;}
    .subtitle {color: #6B7280; margin-bottom: 20px;}

    .stButton button {
        background: #2563EB;
        color: white;
        border-radius: 10px;
        height: 45px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="container">', unsafe_allow_html=True)

    # ============================================
    # HEADER
    # ============================================
    st.markdown('<div class="title">📊 AI Data Analysis & Analytics Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Upload your dataset and get accurate/precise AI-powered business insights and analytics.</div>', unsafe_allow_html=True)

    # ============================================
    # UPLOAD
    # ============================================
    uploaded_file = st.file_uploader("Upload dataset", type=["csv", "xlsx", "json"])
    run_clicked = st.button("🚀 Run Data Analysis", use_container_width=True)

    # ============================================
    # PIPELINE CALL
    # ============================================
    if run_clicked:

        if not uploaded_file:
            st.warning("Please upload a dataset first")
            return

        terminal = st.empty()
        progress_bar = st.progress(0)

        logs = []
        final_result = None

        url = f"{get_backend_url()}/run-pipeline-stream"
        files = {"file": uploaded_file}

        try:
            response = requests.post(url, files=files, stream=True)

            for line in response.iter_lines():
                if not line:
                    continue

                data = safe_json_parse(line)
                if not data:
                    continue

                # ---------- LOGS ----------
                if "log" in data:
                    logs.append(data["log"])
                    terminal.markdown(
                        '<div class="card">' + "<br>".join(logs[-15:]) + '</div>',
                        unsafe_allow_html=True
                    )

                # ---------- PROGRESS ----------
                if "progress" in data:
                    progress_bar.progress(int(data["progress"]))

                # ---------- FINAL ----------
                if data.get("done"):
                    final_result = data.get("data")
                    break

        except Exception as e:
            st.error(f"Connection error: {str(e)}")
            return

        if not final_result:
            st.error("Analysis failed - empty result")
            return

        st.session_state["result"] = final_result
        st.success("✅ Analysis Complete")

    # ============================================
    # RESULTS RENDERING
    # ============================================
    if "result" in st.session_state:

        result = st.session_state["result"]

        # 🔥 SUPPORT BOTH OLD + NEW BACKEND STRUCTURE
        summary = result.get("summary") or result.get("conclusions", {}).get("summary", "")
        insights = simplify_insights(
            result.get("insights") or result.get("conclusions", {}).get("insights", [])
        )
        recommendations = result.get("recommendations") or result.get("conclusions", {}).get("recommendations", [])
        charts = result.get("charts", {})
        pdf_base64 = result.get("pdf_report", "")

        # 🔥 METRICS SAFE EXTRACTION
        metrics = result.get("metrics", {})
        if not metrics:
            analysis = result.get("analysis", {})
            shape = analysis.get("shape", [0, 0])
            metrics = {
                "rows": shape[0],
                "columns": shape[1]
            }

        # ============================================
        # 📊 METRICS
        # ============================================
        st.markdown("## 📊 Dashboard")

        col1, col2 = st.columns(2)
        col1.metric("📄 Rows", metrics.get("rows", 0))
        col2.metric("📊 Columns", metrics.get("columns", 0))

        # ============================================
        # 🧾 SUMMARY
        # ============================================
        st.markdown("## 🧾 Executive Summary")

        if summary:
            st.markdown(f'<div class="card">{summary}</div>', unsafe_allow_html=True)
        else:
            st.info("No summary available")

        # ============================================
        # 🧠 INSIGHTS
        # ============================================
        st.markdown("## 🧠 Key Insights")

        if insights:
            for ins in insights:
                st.markdown(f'<div class="card">✅ {ins}</div>', unsafe_allow_html=True)
        else:
            st.info("No insights available")

        # ============================================
        # 📊 CHARTS
        # ============================================
        st.markdown("## 📊 Visual Insights")

        if charts:
            for chart in charts.values():
                html = chart.get("html")
                if html:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    components.html(html, height=420)
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("No charts generated")

        # ============================================
        # 💡 RECOMMENDATIONS
        # ============================================
        st.markdown("## 💡 Recommendations")

        if recommendations:
            for r in recommendations:
                if isinstance(r, dict):
                    st.markdown(f"""
                    <div class="card">
                    <b>🔥 Priority:</b> {r.get("priority", "").upper()}<br>
                    <b>📌 Action:</b> {r.get("action", "")}<br>
                    <b>📊 Impact:</b> {r.get("impact", "")}<br>
                    <b>🧠 Reason:</b> {r.get("reason", "")}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="card">👉 {str(r)}</div>', unsafe_allow_html=True)
        else:
            st.info("No recommendations available")

        # ============================================
        # 📄 PDF DOWNLOAD
        # ============================================
        st.markdown("## 📄 Download Report")

        if pdf_base64:
            try:
                pdf_bytes = base64.b64decode(pdf_base64)

                st.download_button(
                    "⬇️ Download Full Report (PDF)",
                    data=pdf_bytes,
                    file_name="maduk_BI_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception:
                st.error("PDF decoding failed")
        else:
            st.info("PDF not available")

    st.markdown('</div>', unsafe_allow_html=True)