import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


# ============================================
# 🔥 AI REASONING ENGINE (PRODUCTION READY)
# ============================================
def generate_ai_reasoning(
    analysis: Dict[str, Any],
    insights: List[Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    AI reasoning layer:
    - Converts analytics into business interpretation
    - Extracts opportunities and risks
    - Produces structured reasoning output
    """

    try:
        analysis = analysis or {}
        insights = insights or []
        context = context or {}

        domain = context.get("domain", "business")
        kpi = context.get("kpi") or "key business metrics"
        target = context.get("target_variable") or kpi

        reasoning_blocks: List[str] = []
        opportunities: List[str] = []
        risks: List[str] = []

        # ============================================
        # 🔹 1. INSIGHT INTERPRETATION (SAFE PARSING)
        # ============================================
        for ins in insights[:5]:

            # FIX: handle dict OR string safely (your bug source)
            if isinstance(ins, dict):
                text = ins.get("insight") or ins.get("text") or ""
                score = ins.get("score", 0)
            else:
                text = str(ins)
                score = 0

            if not text:
                continue

            phrases = [
    f"This indicates that {text.lower()}",
    f"The data shows that {text.lower()}",
    f"This reveals that {text.lower()}",]

            reasoning_blocks.append(
    f"{phrases[len(reasoning_blocks) % len(phrases)]}, "
    f"which impacts {kpi or 'key outcomes'}.")

            if "increase" in text.lower() or "positive" in text.lower():
                opportunities.append(
                    f"Leverage this positive driver to improve {kpi}."
                )

            if "decrease" in text.lower() or "negative" in text.lower():
                risks.append(
                    f"Decline in this area could negatively affect {kpi}."
                )

        # ============================================
        # 🔹 2. CORRELATION INTERPRETATION
        # ============================================
        correlations = analysis.get("top_correlations") or []

        if correlations and isinstance(correlations, list):

            top = correlations[0]
            if isinstance(top, dict):

                f1 = top.get("feature_1", "Feature A")
                f2 = top.get("feature_2", "Feature B")
                corr = top.get("correlation", 0)

                reasoning_blocks.append(
                    f"There is a measurable relationship between {f1} and {f2} "
                    f"(correlation: {corr:.2f}), meaning changes in {f1} "
                    f"directly influence {f2}."
                )

                opportunities.append(
                    f"Improving {f1} can significantly enhance {f2} performance."
                )

        # ============================================
        # 🔹 3. FEATURE IMPORTANCE
        # ============================================
        importance = analysis.get("feature_importance") or {}

        if isinstance(importance, dict) and importance:

            try:
                top_feature = max(importance, key=importance.get)

                reasoning_blocks.append(
                    f"{top_feature} is a major driver of {target}, "
                    f"making it a high-impact optimization variable."
                )

                opportunities.append(
                    f"Prioritize optimization of {top_feature} to improve {target}."
                )

            except Exception:
                pass

        # ============================================
        # 🔹 4. TREND INTERPRETATION
        # ============================================
        trends = analysis.get("trends") or []

        if isinstance(trends, list):

            for t in trends[:3]:

                if not isinstance(t, dict):
                    continue

                col = t.get("column")
                trend = t.get("trend")

                if not col or not trend:
                    continue

                if trend == "increasing":
                    reasoning_blocks.append(
                        f"{col} shows an upward trend indicating growth momentum."
                    )
                    opportunities.append(
                        f"Capitalize on increasing {col} to scale performance."
                    )

                elif trend == "decreasing":
                    reasoning_blocks.append(
                        f"{col} is declining, indicating potential performance risk."
                    )
                    risks.append(
                        f"Declining {col} may negatively affect business outcomes."
                    )

        # ============================================
        # 🔹 5. DATA QUALITY CHECKS
        # ============================================
        missing = analysis.get("missing_values") or {}
        total_missing = sum(missing.values()) if isinstance(missing, dict) else 0

        if total_missing > 0:
            risks.append(
                "Data quality issues detected (missing values present), which may reduce accuracy."
            )

        duplicates = analysis.get("duplicate_rows") or 0

        if duplicates and duplicates > 0:
            risks.append(
                "Duplicate records detected, which may distort analytical insights."
            )

        # ============================================
        # 🔹 6. FINAL SYNTHESIS (CLEAN OUTPUT)
        # ============================================
        overall_reasoning = " ".join(reasoning_blocks).strip()

        opportunities = list(dict.fromkeys(opportunities))[:5]
        risks = list(dict.fromkeys(risks))[:5]

        logger.info("AI reasoning generated successfully")

        return {
            "reasoning": overall_reasoning,
            "opportunities": opportunities,
            "risks": risks
        }

    except Exception as e:
        logger.exception(f"AI reasoning failed: {str(e)}")

        return {
            "reasoning": "Unable to generate reasoning due to processing error.",
            "opportunities": [],
            "risks": []
        }