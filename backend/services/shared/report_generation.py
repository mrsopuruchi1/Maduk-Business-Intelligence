import io
import os
import base64
import logging
from typing import Dict, Any

from PIL import Image as PILImage
from io import BytesIO

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

logger = logging.getLogger(__name__)


# ============================================
# 🔥 OPTIMIZE LOGO
# ============================================
def optimize_logo(image_path):
    img = PILImage.open(image_path).convert("RGB")
    img.thumbnail((200, 200))

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=60, optimize=True)
    buffer.seek(0)

    return buffer


# ============================================
# 🔥 PDF GENERATOR
# ============================================
def generate_pdf_report(
    df,
    analysis: Dict[str, Any],
    charts: Dict[str, Any],
    conclusions: Dict[str, Any]
) -> str:

    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer)
        styles = getSampleStyleSheet()

        # ---------------------------------
        # CUSTOM CENTERED TITLE STYLE
        # ---------------------------------
        centered_title = ParagraphStyle(
            name="CenteredTitle",
            parent=styles["Title"],
            alignment=TA_CENTER
        )

        content = []

        analysis = analysis or {}
        conclusions = conclusions or {}
        charts = charts or {}

        summary = conclusions.get("summary", "")
        reasoning = conclusions.get("reasoning", "")
        recommendations = conclusions.get("recommendations", [])
        strategy = conclusions.get("strategy_report", "")

        if isinstance(summary, dict):
            summary = str(summary)

        if isinstance(reasoning, dict):
            reasoning = str(reasoning)

        if isinstance(strategy, dict):
            strategy = str(strategy) 

        # ============================================
        # 🔹 LOGO (CENTERED)
        # ============================================
        try:
            BASE_DIR = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(__file__)
                    )
                )
            )

            logo_path = os.path.join(
                BASE_DIR,
                "frontend",
                "assets",
                "madukai_logo.png"
            )

            if os.path.exists(logo_path):
                logo_buffer = optimize_logo(logo_path)

                logo = Image(logo_buffer, width=1.2 * inch, height=1.2 * inch)
                logo.hAlign = "CENTER"

                content.append(logo)
                content.append(Spacer(1, 10))

        except Exception as e:
            logger.warning(f"Logo failed: {str(e)}")

        # ============================================
        # 🔹 TITLE
        # ============================================
        content.append(
            Paragraph("Maduk Business Intelligence Report", centered_title)
        )
        content.append(Spacer(1, 20))

        # ============================================
        # 🔹 DATASET OVERVIEW
        # ============================================
        content.append(Paragraph("Dataset Overview", styles["Heading2"]))

        if hasattr(df, "shape"):
            rows, cols = df.shape
            content.append(
                Paragraph(f"Rows: {rows}, Columns: {cols}", styles["Normal"])
            )

        content.append(Spacer(1, 10))

        # ============================================
        # 🔹 EXECUTIVE SUMMARY
        # ============================================
        content.append(Paragraph("Executive Summary", styles["Heading2"]))

        content.append(
            Paragraph(summary if summary else "No summary available.", styles["Normal"])
        )

        content.append(Spacer(1, 12))

        # ============================================
        # 🔹 AI REASONING
        # ============================================
        content.append(Paragraph("AI Reasoning", styles["Heading2"]))

        content.append(
            Paragraph(reasoning if reasoning else "No reasoning available.", styles["Normal"])
        )

        content.append(Spacer(1, 12))

        # ============================================
        # 🔹 CHARTS (🔥 FIXED — REAL IMAGES)
        # ============================================
        content.append(Paragraph("Key Visual Insights", styles["Heading2"]))
        content.append(Spacer(1, 10))

        if charts:
            for chart in charts.values():

                # 🔹 Chart Title
                chart_title = f"{chart.get('type', 'Chart').title()} → {chart.get('column', '')}"
                content.append(Paragraph(chart_title, styles["Heading3"]))
                content.append(Spacer(1, 6))

                # 🔹 Chart Image (IMPORTANT FIX)
                if chart.get("image"):
                    try:
                        img = BytesIO(chart["image"])
                        content.append(Image(img, width=5.5 * inch, height=3 * inch))
                        content.append(Spacer(1, 12))
                    except Exception as e:
                        logger.warning(f"Chart image failed: {str(e)}")
                        content.append(Paragraph("Chart could not be rendered.", styles["Normal"]))
                        content.append(Spacer(1, 10))
                else:
                    content.append(Paragraph("Chart image not available.", styles["Normal"]))
                    content.append(Spacer(1, 10))
        else:
            content.append(Paragraph("No charts available.", styles["Normal"]))

        content.append(Spacer(1, 12))

        # ============================================
        # 🔹 RECOMMENDATIONS
        # ============================================
        content.append(Paragraph("Recommendations", styles["Heading2"]))

        if recommendations:
            for rec in recommendations:
                if isinstance(rec, dict):
                    content.append(
                        Paragraph(
                            f"<b>[{rec.get('priority', '').upper()}]</b> {rec.get('action')}<br/>"
                            f"<i>Reason:</i> {rec.get('reason')}<br/>"
                            f"<i>Impact:</i> {rec.get('impact')}",
                            styles["Normal"]
                        )
                    )
                    content.append(Spacer(1, 8))
                else:
                    content.append(Paragraph(f"• {str(rec)}", styles["Normal"]))
        else:
            content.append(Paragraph("No recommendations available.", styles["Normal"]))

        content.append(Spacer(1, 12))

        # ============================================
        # 🔹 STRATEGY REPORT
        # ============================================
        content.append(Paragraph("AI Strategy Report", styles["Heading2"]))

        content.append(
            Paragraph(strategy if strategy else "No strategy generated.", styles["Normal"])
        )

        # ============================================
        # 🔹 BUILD PDF
        # ============================================
        doc.build(content)

        buffer.seek(0)
        pdf_bytes = buffer.getvalue()

        if not pdf_bytes:
            return ""

        # 🔒 SIZE CONTROL (important for Streamlit)
        MAX_SIZE = 400000  # 400KB

        if len(pdf_bytes) > MAX_SIZE:
            logger.warning("PDF too large — skipped")
            return ""

        encoded = base64.b64encode(pdf_bytes).decode("utf-8")
        return encoded

    except Exception as e:
        logger.exception(f"[PDF ERROR] {str(e)}")
        return ""