import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


# ============================================
# 🔥 INSIGHT RANKING ENGINE (PRODUCTION READY)
# ============================================
def rank_insights(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Scores and ranks insights based on:
    - Strength (correlation / trend magnitude)
    - Business Impact (relevance to outcomes)
    - Confidence (data quality & consistency)

    Returns:
        Ranked list of insights (highest first)
    """

    try:
        ranked_insights: List[Dict[str, Any]] = []

        analysis = analysis or {}

        correlations = analysis.get("top_correlations") or []
        feature_importance = analysis.get("feature_importance") or {}
        trends = analysis.get("trends") or []
        missing = analysis.get("missing_values") or {}
        duplicates = analysis.get("duplicate_rows") or 0

        # safe numeric conversion
        total_missing = sum(missing.values()) if isinstance(missing, dict) else 0
        duplicate_penalty = 0.1 if duplicates else 0.0
        missing_penalty = 0.2 if total_missing > 0 else 0.0

        # ============================================
        # 🔹 1. CORRELATION INSIGHTS
        # ============================================
        for item in correlations:
            if not isinstance(item, dict):
                continue

            f1 = item.get("feature_1")
            f2 = item.get("feature_2")

            try:
                corr = abs(float(item.get("correlation", 0)))
            except Exception:
                corr = 0.0

            if not f1 or not f2:
                continue

            strength_score = max(0.0, min(corr, 1.0))
            business_impact = 0.7 if corr > 0.6 else 0.4
            confidence = max(0.0, 1.0 - missing_penalty - duplicate_penalty)

            total_score = (
                0.5 * strength_score +
                0.3 * business_impact +
                0.2 * confidence
            )

            ranked_insights.append({
                "type": "correlation",
                "insight": f"{f1} strongly influences {f2} (corr={corr:.2f})",
                "features": [f1, f2],
                "strength": round(strength_score, 3),
                "business_impact": round(business_impact, 3),
                "confidence": round(confidence, 3),
                "score": round(total_score, 3)
            })

        # ============================================
        # 🔹 2. FEATURE IMPORTANCE INSIGHTS
        # ============================================
        if isinstance(feature_importance, dict):
            for feature, importance in feature_importance.items():

                try:
                    strength_score = abs(float(importance))
                except Exception:
                    strength_score = 0.0

                strength_score = max(0.0, min(strength_score, 1.0))

                business_impact = 0.8 if strength_score > 0.5 else 0.5
                confidence = max(0.0, 1.0 - missing_penalty)

                total_score = (
                    0.5 * strength_score +
                    0.3 * business_impact +
                    0.2 * confidence
                )

                ranked_insights.append({
                    "type": "feature_importance",
                    "insight": f"{feature} is a key driver of performance",
                    "features": [feature],
                    "strength": round(strength_score, 3),
                    "business_impact": round(business_impact, 3),
                    "confidence": round(confidence, 3),
                    "score": round(total_score, 3)
                })

        # ============================================
        # 🔹 3. TREND INSIGHTS
        # ============================================
        for t in trends:
            if not isinstance(t, dict):
                continue

            col = t.get("column")
            trend = t.get("trend", "stable")

            try:
                slope = abs(float(t.get("slope", 0)))
            except Exception:
                slope = 0.0

            if not col:
                continue

            strength_score = max(0.0, min(slope, 1.0))
            business_impact = 0.6
            confidence = 1.0

            total_score = (
                0.5 * strength_score +
                0.3 * business_impact +
                0.2 * confidence
            )

            ranked_insights.append({
                "type": "trend",
                "insight": f"{col} is {trend} over time",
                "features": [col],
                "strength": round(strength_score, 3),
                "business_impact": round(business_impact, 3),
                "confidence": round(confidence, 3),
                "score": round(total_score, 3)
            })

        # ============================================
        # 🔹 4. SORT & FILTER 🔥
        # ============================================
        ranked_insights = sorted(
            ranked_insights,
            key=lambda x: x.get("score", 0),
            reverse=True
        )

        filtered = [ins for ins in ranked_insights if ins.get("score", 0) > 0.5]

        logger.info(f"Ranked {len(filtered)} high-value insights")

        return filtered[:10]

    except Exception as e:
        logger.exception(f"Insight ranking failed: {str(e)}")
        return []