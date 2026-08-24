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
import asyncio
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, UploadFile, File, Form, status, Body
from fastapi.responses import StreamingResponse, Response
from starlette.concurrency import run_in_threadpool
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from backend.services.ai_prediction_pipeline.prediction_pipeline import AIPredictionPipeline

logger = logging.getLogger("MadukBI.PredictionRoute")

router = APIRouter(
    prefix="/ai-business-prediction",
    tags=["AI Prediction Pipeline"]
)

# =========================================================
# LAZY PIPELINE INITIALIZATION
# =========================================================
# Do not initialize the complete AI pipeline during FastAPI startup.
# This reduces startup cost and helps prevent Render health-check timeouts.
_pipeline = None
_forecast_lock = asyncio.Lock()


def get_pipeline() -> AIPredictionPipeline:
    """Return a lazily initialized AI prediction pipeline instance."""
    global _pipeline

    if _pipeline is None:
        logger.info("Initializing Maduk BI AI Prediction Pipeline...")
        _pipeline = AIPredictionPipeline()
        logger.info("Maduk BI AI Prediction Pipeline initialized successfully.")

    return _pipeline


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
    """Parses uploaded multipart CSV/Excel/Parquet files into a Pandas DataFrame."""
    filename = (file.filename or "").lower()
    if filename.endswith(".csv"):
        return pd.read_csv(io.BytesIO(contents))
    elif filename.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(contents))
    elif filename.endswith(".parquet"):
        return pd.read_parquet(io.BytesIO(contents))
    else:
        raise ValueError("Unsupported file format. Please upload a .csv, .xlsx, .xls, or .parquet file.")


# =========================================================
# PDF CHART & REPORT GENERATION UTILITIES
# =========================================================
def _generate_line_chart_bytes(forecast_data: List[Dict[str, Any]]) -> io.BytesIO:
    """Generates a Line Chart image buffer for Revenue Forecast Trajectory."""
    # Matplotlib is intentionally imported lazily. Normal forecast requests
    # do not need chart generation and therefore avoid its startup/font-cache cost.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

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
    # Matplotlib is only loaded when a PDF report is requested.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

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
        ax.annotate(
            f"{height:,.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color="#ffffff",
            fontsize=7,
            fontweight="bold"
        )

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
        "DocTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=18, leading=22, textColor=colors.HexColor("#0f172a"),
        alignment=1, spaceAfter=10
    )
    section_heading = ParagraphStyle(
        "SectionHeading", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=12, leading=16, textColor=colors.HexColor("#1e293b"),
        spaceBefore=10, spaceAfter=6
    )
    body_style = ParagraphStyle(
        "BodyTextCustom", parent=styles["Normal"], fontName="Helvetica",
        fontSize=9, leading=13, textColor=colors.HexColor("#334155"), spaceAfter=6
    )

    story = []

    logo_path = os.path.join(os.getcwd(), "frontend", "assets", "madukai_logo.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(os.getcwd(), "Maduk-Business-Intelligence", "frontend", "assets", "madukai_logo.png")

    if os.path.exists(logo_path):
        logo_img = RLImage(logo_path, width=2.2 * inch, height=0.75 * inch)
        logo_img.hAlign = "CENTER"
        story.append(logo_img)
        story.append(Spacer(1, 10))

    story.append(Paragraph("AI Business Prediction & Executive Report", title_style))
    story.append(Spacer(1, 10))

    forecast_results = payload.get("forecast_results", {})
    metrics = payload.get("model_metrics", {})
    executive_summary = payload.get("executive_summary", {})
    insights = payload.get("business_insights", [])
    predictions = payload.get("prediction_results", {}).get("predictions", [])

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

    story.append(Paragraph("2. Strategic Executive Narrative", section_heading))
    summary_text = executive_summary.get("summary_narrative", "N/A")
    rationale_text = executive_summary.get("selection_rationale", "N/A")
    story.append(Paragraph(f"<b>Overview:</b> {summary_text}", body_style))
    story.append(Paragraph(f"<b>Model Rationale:</b> {rationale_text}", body_style))
    story.append(Spacer(1, 10))

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

    if insights:
        story.append(Paragraph("4. Recommended AI Business Insights", section_heading))
        for insight in insights:
            story.append(Paragraph(f"• {insight}", body_style))

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


# =========================================================
# STANDARD PRODUCTION ENDPOINT (For Streamlit UI)
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
    date_column: Optional[str] = Form("date"),
    target_column: Optional[str] = Form("revenue")
) -> Dict[str, Any]:
    try:
        logger.info(f"Received pipeline execution request for file '{file.filename}'.")

        contents = await file.read()
        if not contents:
            return {"success": False, "error": "Uploaded file is empty.", "error_type": "EmptyUpload"}

        df = _extract_dataframe_from_upload(file, contents)
        logger.info(
            f"Dataset loaded: rows={len(df)}, columns={len(df.columns)}, "
            f"columns={list(df.columns)}"
        )

        if df.empty or len(df) < 5:
            return {
                "success": False,
                "error": "Dataset contains insufficient rows for cross-validation forecasting (minimum 5 required).",
                "error_type": "InsufficientData"
            }

        # Explicitly resolve the time-series date column.
        if not date_column:
            if "date" in df.columns:
                date_column = "date"
            else:
                return {
                    "success": False,
                    "error": "No date column was provided and no 'date' column was found in the dataset.",
                    "error_type": "MissingDateColumn"
                }

        if date_column not in df.columns:
            return {
                "success": False,
                "error": f"Date column '{date_column}' not found. Available columns: {list(df.columns)}",
                "error_type": "MissingDateColumn"
            }

        # Revenue is the default target for the Business Revenue Forecast feature.
        if not target_column:
            target_column = "revenue"

        if target_column not in df.columns:
            return {
                "success": False,
                "error": f"Target column '{target_column}' not found. Available columns: {list(df.columns)}",
                "error_type": "MissingTargetColumn"
            }

        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
        if df[date_column].isna().all():
            return {
                "success": False,
                "error": f"Unable to parse any valid dates from column '{date_column}'.",
                "error_type": "InvalidDateColumn"
            }

        invalid_dates = int(df[date_column].isna().sum())
        if invalid_dates:
            logger.warning(
                f"Date column '{date_column}' contains {invalid_dates} invalid date value(s)."
            )

        horizon_steps = _horizon_str_to_int(forecast_horizon)

        secondary_targets = []
        if predict_profit and "profit" in df.columns:
            secondary_targets.append("profit")
        if predict_sales and "sales" in df.columns:
            secondary_targets.append("sales")

        logger.info(
            f"Forecast configuration: horizon={horizon_steps}, target={target_column}, "
            f"date_column={date_column}, secondary_targets={secondary_targets}, "
            f"predict_revenue={predict_revenue}, predict_sales={predict_sales}, "
            f"predict_leads={predict_leads}, predict_customers={predict_customers}, "
            f"predict_profit={predict_profit}"
        )

        # Forecasting is CPU-bound and synchronous. Never execute it directly
        # inside the FastAPI event loop: doing so can block /health and cause
        # Render health-check failures while the model selector is running.
        async with _forecast_lock:
            logger.info("Initializing pipeline on worker thread...")
            prediction_pipeline = await run_in_threadpool(get_pipeline)
            logger.info("Starting AIPredictionPipeline.run() in worker thread...")

            pipeline_output = await run_in_threadpool(
                prediction_pipeline.run,
                data_source=df,
                target_column=target_column,
                date_column=date_column,
                forecast_horizon=horizon_steps,
                confidence_level=0.95,
                secondary_targets=secondary_targets if secondary_targets else None,
            )

            logger.info("AIPredictionPipeline.run() completed successfully.")

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
            "prediction_results": {"predictions": forecast_values},
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
        return {
            "success": False,
            "error": str(ve),
            "error_type": type(ve).__name__
        }
    except Exception as e:
        logger.exception("Unexpected error during pipeline execution.")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


# =========================================================
# DEDICATED PDF REPORT GENERATION ENDPOINT
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
            headers={"Content-Disposition": "attachment; filename=maduk_ai_prediction_report.pdf"}
        )
    except Exception as e:
        logger.exception(f"[PDF GENERATION ERROR] {str(e)}")
        return Response(
            content=json.dumps({
                "error": f"Failed to generate PDF: {str(e)}",
                "error_type": type(e).__name__
            }),
            status_code=500,
            media_type="application/json"
        )


# =========================================================
# STREAMING PIPELINE ENDPOINT
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

        if not contents:
            return StreamingResponse(
                iter([json.dumps({
                    "log": "❌ Uploaded file is empty.",
                    "progress": 100,
                    "done": True,
                    "data": {"error_type": "EmptyUpload"}
                }) + "\n"]),
                media_type="text/plain"
            )

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

                logger.info("Starting streaming AIPredictionPipeline.run()...")
                prediction_pipeline = get_pipeline()
                pipeline_output = prediction_pipeline.run(data_source=df)
                logger.info("Streaming AIPredictionPipeline.run() completed successfully.")

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
                    "data": {
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                }) + "\n"

        return StreamingResponse(event_stream(), media_type="text/plain")

    except Exception as e:
        logger.exception(f"[ROUTE STREAM ERROR] {str(e)}")
        return StreamingResponse(
            iter([json.dumps({
                "log": f"❌ Request failed: {str(e)}",
                "progress": 100,
                "done": True,
                "data": {
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            }) + "\n"]),
            media_type="text/plain"
        )
