import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


# ============================================
# 🔥 RECOMMENDATION ENGINE (DECISION LAYER)
# ============================================
def generate_recommendations(
    analysis: Dict[str, Any],
    reasoning: Dict[str, Any],
    context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Converts insights into prioritized, actionable business decisions.
    """

    try:
        # ---------------- SAFE INPUTS ----------------
        analysis = analysis or {}
        reasoning = reasoning or {}
        context = context or {}

        feature_importance = analysis.get("feature_importance", {}) or {}
        correlations = analysis.get("top_correlations", []) or []
        trends = analysis.get("trends", []) or []

        opportunities = reasoning.get("opportunities", []) or []
        risks = reasoning.get("risks", []) or []

        kpi = context.get("kpi", "key metric")
        target = context.get("target_variable", kpi)

        recommendations: List[Dict[str, Any]] = []

        # ============================================
        # 🔹 1. HIGH IMPACT (CORRELATION DRIVER)
        # ============================================
        if correlations:
            top = correlations[0]

            f1 = top.get("feature_1")
            f2 = top.get("feature_2")
            corr = top.get("correlation", 0)

            if f1 and f2:
                recommendations.append({
                    "priority": "high",
                    "action": f"Increase focus on optimizing {f1}",
                    "reason": f"{f1} strongly influences {f2} (correlation: {corr:.2f})",
                    "impact": f"Direct improvement in {kpi}"
                })

        # ============================================
        # 🔹 2. FEATURE IMPORTANCE ACTIONS
        # ============================================
        if isinstance(feature_importance, dict) and feature_importance:

            # Remove target/kpi from candidates
            filtered_features = {
                f: v for f, v in feature_importance.items()
                if f not in [target, kpi]
            }

            if filtered_features:
                top_feature = max(filtered_features, key=filtered_features.get)

                recommendations.append({
                    "priority": "high",
                    "action": f"Prioritize improvement of {top_feature}",
                    "reason": f"{top_feature} is a strong driver of {target}",
                    "impact": f"Significant uplift in {target}"
                })

        # ============================================
        # 🔹 3. TREND ACTIONS
        # ============================================
        for t in trends[:3]:
            col = t.get("column")
            trend = t.get("trend")

            if not col:
                continue

            if trend == "increasing":
                recommendations.append({
                    "priority": "medium",
                    "action": f"Scale initiatives related to {col}",
                    "reason": f"{col} is trending upward",
                    "impact": "Opportunity for growth"
                })

            elif trend == "decreasing":
                recommendations.append({
                    "priority": "high",
                    "action": f"Investigate and reverse decline in {col}",
                    "reason": f"{col} is trending downward",
                    "impact": "Prevent performance loss"
                })

        # ============================================
        # 🔹 4. OPPORTUNITIES → ACTIONS
        # ============================================
        for op in opportunities[:3]:
            recommendations.append({
                "priority": "medium",
                "action": op,
                "reason": "Derived from AI reasoning",
                "impact": "Potential performance improvement"
            })

        # ============================================
        # 🔹 5. RISKS → MITIGATION
        # ============================================
        for rk in risks[:3]:
            recommendations.append({
                "priority": "high",
                "action": f"Mitigate risk: {rk}",
                "reason": "Identified risk from AI reasoning",
                "impact": "Prevent negative outcomes"
            })

        # ============================================
        # 🔹 6. REMOVE DUPLICATES (🔥 IMPORTANT)
        # ============================================
        seen = set()
        unique_recommendations = []

        for rec in recommendations:
            key = (rec["action"], rec["reason"])
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)

        # ============================================
        # 🔹 7. PRIORITY SORTING
        # ============================================
        priority_order = {"high": 3, "medium": 2, "low": 1}

        unique_recommendations.sort(
            key=lambda x: priority_order.get(x["priority"], 0),
            reverse=True
        )

        # Limit output
        final_output = unique_recommendations[:7]

        logger.info(f"Generated {len(final_output)} recommendations")

        return final_output

    except Exception as e:
        logger.exception(f"Recommendation generation failed: {str(e)}")

        return [
            {
                "priority": "low",
                "action": "Review dataset quality and rerun analysis",
                "reason": "Fallback recommendation due to system error",
                "impact": "Data validation improvement"
            }
        ]