import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


# ============================================
# 🔥 EXECUTIVE SUMMARY ENGINE
# ============================================
def generate_executive_summary(
    analysis: Dict[str, Any],
    context: Dict[str, Any],
    reasoning: Dict[str, Any]
) -> str:
    """
    Generates a human-readable executive summary.

    Focus:
    - What is happening
    - Why it matters
    - What action to take

    Returns:
        String summary
    """

    try:
        analysis = analysis or {}
        context = context or {}
        reasoning = reasoning or {}

        shape = analysis.get("shape", (0, 0))
        correlations = analysis.get("top_correlations", [])
        trends = analysis.get("trends", [])

        domain = context.get("domain", "business")
        kpi = context.get("kpi", "performance")
        target = context.get("target_variable", kpi)

        opportunities = reasoning.get("opportunities", [])
        risks = reasoning.get("risks", [])

        rows, cols = shape if len(shape) == 2 else (0, 0)

        # ============================================
        # 🔹 1. OPENING (WHAT IS HAPPENING)
        # ============================================
        intro = (
            f"This analysis examines a {domain} dataset consisting of "
            f"{rows} records and {cols} variables, with a focus on improving {kpi}."
        )

        # ============================================
        # 🔹 2. KEY DRIVER (WHY IT IS HAPPENING)
        # ============================================
        driver_text = ""

        if correlations:
            top = correlations[0]
            f1 = top.get("feature_1")
            f2 = top.get("feature_2")
            corr = top.get("correlation", 0)

            driver_text = (
                f"The results show a strong relationship between {f1} and {f2} "
                f"(correlation: {corr:.2f}), indicating that changes in {f1} "
                f"are closely linked to performance in {f2}."
            )

        # ============================================
        # 🔹 3. TREND (WHAT DIRECTION)
        # ============================================
        trend_text = ""

        if trends:
            t = trends[0]
            col = t.get("column")
            trend = t.get("trend")

            if trend == "increasing":
                trend_text = f"{col} is trending upward, suggesting positive momentum."
            elif trend == "decreasing":
                trend_text = f"{col} is showing a decline, which may require attention."

        # ============================================
        # 🔹 4. OPPORTUNITIES (WHAT TO DO)
        # ============================================
        opportunity_text = ""

        if opportunities:
            opportunity_text = f"A key opportunity lies in {opportunities[0].lower()}"

        # ============================================
        # 🔹 5. RISKS (WHAT TO WATCH)
        # ============================================
        risk_text = ""

        if risks:
            risk_text = f"However, {risks[0].lower()}"

        # ============================================
        # 🔹 FINAL NARRATIVE
        # ============================================
        summary_parts = [
            intro,
            driver_text,
            trend_text,
            opportunity_text,
            risk_text
        ]

        # Clean empty parts
        summary = " ".join([part for part in summary_parts if part])

        logger.info("Executive summary generated successfully")

        return summary.strip()

    except Exception as e:
        logger.exception(f"Executive summary generation failed: {str(e)}")

        return "Unable to generate executive summary."