"""
Maduk Business Intelligence - AI Prediction Pipeline Route
===========================================================
File: backend/routes/ai_prediction_pipeline_route.py

Connects frontend applications (Streamlit / React) to the core orchestrator:
`backend/services/ai_prediction_pipeline/prediction_pipeline.py`.
Includes dynamic ReportLab PDF export with top-centered logo and embedded charts.
"""

import json
import logging
import io
import os
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, UploadFile, File, Form, status, Body
from fastapi.responses import StreamingResponse, Response
import pandas as pd

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server-side PDF generation
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from backend.services.ai_prediction_pipeline.prediction_pipeline import AIPredictionPipeline

logger = logging.getLogger("MadukBI.PredictionRoute")

router = APIRouter(
    prefix="/ai-business-prediction",
    tags=["AI Prediction Pipeline"]
)

# Initialize pipeline orchestrator instance
pipeline = AIPredictionPipeline()


def _horizon_str_to_int(horizon_str: str) -> int:
    """Converts frontend dropdown selection strings to integer horizon periods."""
    horizon_map = {
        "30 Days": 30,
        "90 Days": 90,
        "6 Months": 6,
        "12 Months": 12
    }
    try:
        return int(horizon_str)
    except (ValueError, TypeError):
        return horizon_map.get(str(horizon_str).strip(), 30)


def _extract_dataframe_from_upload(file: UploadFile, contents: bytes) -> pd.DataFrame:
    """Parses uploaded multipart CSV/Excel files into a Pandas DataFrame."""
    filename = file.filename.lower()
    if filename.endswith(".csv"):
        return pd.read_csv(io.BytesIO(contents))
    elif filename.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(contents))
    elif filename.endswith(".parquet"):
        return pd.read_parquet(io.BytesIO(contents))
    else:
        raise ValueError("Unsupported file format. Please upload a .csv, .xlsx, or .parquet file.")


# =========================================================
# 🎨 PDF CHART & REPORT GENERATION UTILITIES
# =========================================================
def _generate_line_chart_bytes(forecast_data: List[Dict[str, Any]]) -> io.BytesIO:
    """Generates a Line Chart image buffer for Revenue Forecast Trajectory."""
    df_fc = pd.DataFrame(forecast_data)
    buf = io.BytesIO()

    fig, ax = plt.subplots(figsize=(6.5, 2.8), dpi=150)
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#1e293b")

    if not df_fc.empty and "forecast" in df_fc.columns:
        x_axis = df_fc["date"] if "date" in df_fc.columns else range(len(df_fc))
        y_axis = df_fc["forecast"]
        
        ax.plot(x_axis, y_axis, color="#38bdf8", linewidth=2.5, marker="o", markersize=3, label="Forecasted Revenue")
        ax.fill_between(range(len(df_fc)), y_axis, color="#38bdf8", alpha=0.15)

    ax.set_title("Projected Revenue Trajectory", color="#ffffff", fontsize=11, fontweight="bold", pad=10)
    ax.tick_params(colors="#94a3b8", labelsize=7)
    ax.grid(True, linestyle="--", alpha=0.2, color="#94a3b8")
    
    # Format axes
    for spine in ax.spines.values():
        spine.set_color("#334155")

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(buf, format="png", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _generate_bar_chart_bytes(metrics: Dict[str, Any]) -> io.BytesIO:
    """Generates a Bar Chart image buffer for Model Evaluation Metrics."""
    buf = io.BytesIO()

    fig, ax = plt.subplots(figsize=(6.5, 2.5), dpi=150)
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#1e293b")

    metric_names = ["MAPE (%)", "RMSE", "MAE"]
    values = [
        float(metrics.get("MAPE", 0.0)),
        float(metrics.get("RMSE", 0.0)),
        float(metrics.get("MAE", 0.0))
    ]

    bars = ax.bar(metric_names, values, color=["#facc15", "#38bdf8", "#22c55e"], width=0.45)

    ax.set_title("Model Error Metrics Breakdown", color="#ffffff", fontsize=11, fontweight="bold", pad=10)
    ax.tick_params(colors="#94a3b8", labelsize=8)
    ax.grid(True, linestyle="--", alpha=0.2, color="#94a3b8", axis="y")

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{height:,.2f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center", va="bottom",
                    color="#ffffff", fontsize=7, fontweight="bold")

    for spine in ax.spines.values():
        spine.set_color("#334155")

    plt.tight_layout()
    plt.savefig(buf, format="png", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _generate_pdf_report_bytes(payload: Dict[str, Any]) -> bytes:
    """Compiles complete PDF report with logo, charts, metrics, and insights."""
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,  # Centered
        spaceAfter=10
    )
    
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )

    story = []

    # 1. TOP CENTERED LOGO
    logo_path = os.path.join(os.getcwd(), "frontend", "assets", "madukai_logo.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(os.getcwd(), "Maduk-Business-Intelligence", "frontend", "assets", "madukai_logo.png")

    if os.path.exists(logo_path):
        logo_img = RLImage(logo_path, width=2.2 * inch, height=0.75 * inch)
        logo_img.hAlign = "CENTER"
        story.append(logo_img)
        story.append(Spacer(1, 10))

    # Document Header Title
    story.append(Paragraph("AI Business Prediction & Executive Report", title_style))
    story.append(Spacer(1, 10))

    # Extract Data Sections
    forecast_results = payload.get("forecast_results", {})
    metrics = payload.get("model_metrics", {})
    executive_summary = payload.get("executive_summary", {})
    insights = payload.get("business_insights", [])
    predictions = payload.get("prediction_results", {}).get("predictions", [])

    # 2. EXECUTIVE DASHBOARD SUMMARY TABLE
    story.append(Paragraph("1. Executive Results Dashboard", section_heading))
    
    kpi_data = [
        [
            Paragraph("<b>Predicted Revenue:</b>", body_style),
            Paragraph(f"${forecast_results.get('predicted_revenue', 0):,.2f}", body_style),
            Paragraph("<b>Winning Model:</b>", body_style),
            Paragraph(str(metrics.get("winning_model", "N/A")), body_style)
        ],
        [
            Paragraph("<b>Forecast Growth:</b>", body_style),
            Paragraph(f"{forecast_results.get('forecast_growth_percent', 0)}%", body_style),
            Paragraph("<b>Confidence Score:</b>", body_style),
            Paragraph(str(metrics.get("forecast_accuracy", "N/A")), body_style)
        ],
        [
            Paragraph("<b>Best Period:</b>", body_style),
            Paragraph(str(forecast_results.get("best_month", "N/A")), body_style),
            Paragraph("<b>MAPE Error:</b>", body_style),
            Paragraph(f"{metrics.get('MAPE', 0.0):.2f}%", body_style)
        ]
    ]

    kpi_table = Table(kpi_data, colWidths=[1.5 * inch, 2.0 * inch, 1.5 * inch, 2.0 * inch])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # 3. EXECUTIVE NARRATIVE
    story.append(Paragraph("2. Strategic Executive Narrative", section_heading))
    summary_text = executive_summary.get("summary_narrative", "N/A")
    rationale_text = executive_summary.get("selection_rationale", "N/A")
    
    story.append(Paragraph(f"<b>Overview:</b> {summary_text}", body_style))
    story.append(Paragraph(f"<b>Model Rationale:</b> {rationale_text}", body_style))
    story.append(Spacer(1, 10))

    # 4. CHARTS SECTION (LINE CHART & BAR CHART)
    story.append(Paragraph("3. Predictive Analytics Visualizations", section_heading))
    
    line_buf = _generate_line_chart_bytes(predictions)
    bar_buf = _generate_bar_chart_bytes(metrics)

    line_img = RLImage(line_buf, width=6.8 * inch, height=2.6 * inch)
    line_img.hAlign = "CENTER"
    story.append(line_img)
    story.append(Spacer(1, 10))

    bar_img = RLImage(bar_buf, width=6.8 * inch, height=2.4 * inch)
    bar_img.hAlign = "CENTER"
    story.append(bar_img)
    story.append(Spacer(1, 12))

    # 5. BUSINESS INSIGHTS
    if insights:
        story.append(Paragraph("4. Recommended AI Business Insights", section_heading))
        for insight in insights:
            story.append(Paragraph(f"• {insight}", body_style))

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


# =========================================================
# 🚀 STANDARD PRODUCTION ENDPOINT (For Streamlit UI)
# =========================================================
@router.post(
    "/run-pipeline",
    status_code=status.HTTP_200_OK,
    summary="Run AI Business Prediction Pipeline",
    description="Main REST endpoint consumed by Predict_Your_Business.py. Ingests uploaded dataset, executes prediction pipeline, and returns formatted UI results."
)
async def run_pipeline_endpoint(
    file: UploadFile = File(...),
    forecast_horizon: str = Form("12 Months"),
    predict_revenue: bool = Form(True),
    predict_sales: bool = Form(True),
    predict_leads: bool = Form(False),
    predict_customers: bool = Form(False),
    predict_profit: bool = Form(True),
    date_column: Optional[str] = Form(None),
    target_column: Optional[str] = Form(None)
) -> Dict[str, Any]:

    try:
        logger.info(f"Received pipeline execution request for file '{file.filename}'.")

        # 1. Read uploaded data file
        contents = await file.read()
        if not contents:
            return {"success": False, "error": "Uploaded file is empty."}

        df = _extract_dataframe_from_upload(file, contents)

        if df.empty or len(df) < 5:
            return {
                "success": False,
                "error": "Dataset contains insufficient rows for cross-validation forecasting (minimum 5 required)."
            }

        # 2. Determine horizon and dynamic secondary targets
        horizon_steps = _horizon_str_to_int(forecast_horizon)

        secondary_targets = []
        if predict_profit and "profit" in df.columns:
            secondary_targets.append("profit")
        if predict_sales and "sales" in df.columns:
            secondary_targets.append("sales")

        # 3. Call AIPredictionPipeline matching prediction_pipeline.py parameter signature
        pipeline_output = pipeline.run(
            data_source=df,
            target_column=target_column,
            date_column=date_column,
            forecast_horizon=horizon_steps,
            confidence_level=0.95,
            secondary_targets=secondary_targets if secondary_targets else None
        )

        # 4. Map output to Streamlit UI contract
        kpis = pipeline_output.get("kpi_cards", {})
        forecast_values = pipeline_output.get("forecast_values", [])
        metrics = pipeline_output.get("validation_metrics", {})
        best_model_info = pipeline_output.get("best_model_and_selection", {})

        predicted_revenue = float(kpis.get("projected_horizon_total", 0.0))
        forecast_growth = float(kpis.get("growth_rate_pct", 0.0))

        best_month = "N/A"
        if forecast_values:
            df_fc = pd.DataFrame(forecast_values)
            if "forecast" in df_fc.columns and "date" in df_fc.columns:
                max_idx = df_fc["forecast"].idxmax()
                best_month = pd.to_datetime(df_fc.loc[max_idx, "date"]).strftime("%B %Y")

        confidence_score = kpis.get("forecast_confidence", "N/A")

        return {
            "success": True,
            "prediction_results": {
                "predictions": forecast_values
            },
            "forecast_results": {
                "predicted_revenue": round(predicted_revenue, 2),
                "forecast_growth_percent": round(forecast_growth, 2),
                "best_month": best_month,
                "forecast_table": forecast_values
            },
            "model_metrics": {
                "winning_model": best_model_info.get("winning_model", "Automated"),
                "forecast_accuracy": confidence_score,
                "MAPE": metrics.get("MAPE", 0.0),
                "RMSE": metrics.get("RMSE", 0.0),
                "MAE": metrics.get("MAE", 0.0),
                "R2": metrics.get("R2", 0.0)
            },
            "business_insights": pipeline_output.get("recommended_actions", []) + pipeline_output.get("business_risks", []),
            "executive_summary": {
                "summary_narrative": pipeline_output.get("executive_summary", ""),
                "selection_rationale": best_model_info.get("selection_rationale", "")
            },
            "pipeline_metadata": pipeline_output.get("pipeline_metadata", {})
        }

    except ValueError as ve:
        logger.error(f"Validation error during pipeline run: {str(ve)}")
        return {"success": False, "error": str(ve)}
    except Exception as e:
        logger.exception("Unexpected error during pipeline execution.")
        return {"success": False, "error": f"Internal Server Error: {str(e)}"}


# =========================================================
# 📄 DEDICATED PDF REPORT GENERATION ENDPOINT
# =========================================================
@router.post(
    "/generate-pdf-report",
    summary="Generate Formatted PDF Report",
    description="Generates an executive-ready PDF report containing company logo, embedded line & bar charts, and metric breakdown."
)
async def generate_pdf_report_endpoint(payload: Dict[str, Any] = Body(...)):
    """Accepts pipeline result JSON payload and returns compiled PDF bytes."""
    try:
        pdf_bytes = _generate_pdf_report_bytes(payload)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=maduk_ai_prediction_report.pdf"
            }
        )
    except Exception as e:
        logger.exception(f"[PDF GENERATION ERROR] {str(e)}")
        return Response(
            content=json.dumps({"error": f"Failed to generate PDF: {str(e)}"}),
            status_code=500,
            media_type="application/json"
        )


# =========================================================
# 🌊 STREAMING PIPELINE ENDPOINT
# =========================================================
@router.post(
    "/run-pipeline-stream",
    summary="Stream AI Business Prediction Execution",
    description="Streams step-by-step progress, logs, and final prediction results as Line-delimited JSON (NDJSON)."
)
async def run_pipeline_stream_endpoint(file: UploadFile = File(...)):
    """Streams progressive execution metrics and logs as JSON-Lines."""
    try:
        file.file.seek(0)
        contents = await file.read()
        df = _extract_dataframe_from_upload(file, contents)

        def event_stream():
            try:
                yield json.dumps({
                    "log": "🔍 Initializing Ingestion & Data Profiling...",
                    "progress": 15,
                    "done": False,
                    "data": {}
                }) + "\n"

                yield json.dumps({
                    "log": "🧹 Validating dataset and running quality checks...",
                    "progress": 35,
                    "done": False,
                    "data": {}
                }) + "\n"

                yield json.dumps({
                    "log": "⚙️ Executing Backtesting, Rolling CV & Model Selection...",
                    "progress": 65,
                    "done": False,
                    "data": {}
                }) + "\n"

                pipeline_output = pipeline.run(data_source=df)

                yield json.dumps({
                    "log": "✅ Prediction Pipeline Completed Successfully!",
                    "progress": 100,
                    "done": True,
                    "data": pipeline_output
                }, default=str) + "\n"

            except Exception as e:
                logger.exception(f"[STREAM PIPELINE ERROR] {str(e)}")
                yield json.dumps({
                    "log": f"❌ Pipeline crashed: {str(e)}",
                    "progress": 100,
                    "done": True,
                    "data": {}
                }) + "\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/plain"
        )

    except Exception as e:
        logger.exception(f"[ROUTE STREAM ERROR] {str(e)}")
        return StreamingResponse(
            iter([json.dumps({
                "log": f"❌ Request failed: {str(e)}",
                "progress": 100,
                "done": True,
                "data": {}
            }) + "\n"]),
            media_type="text/plain"
        )
