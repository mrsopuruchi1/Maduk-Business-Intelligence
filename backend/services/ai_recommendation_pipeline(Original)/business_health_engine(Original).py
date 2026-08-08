"""
Maduk Business Intelligence - Business Health Engine
Calculates weighted composite health score (0-100), system confidence score,
overall risk level, and maps them to executive diagnostic tiers.
"""

import logging
from typing import Dict, Any, List
from backend.services.ai_recommendation_pipeline.models.schemas import BusinessHealthAssessment

logger = logging.getLogger("MadukBI.BusinessHealthEngine")


class BusinessHealthEngine:
    """Computes weighted percentage health score, confidence score, risk severity, and driver rationale."""

    WEIGHTS = {
        'profit_margin': 0.25,
        'revenue_growth': 0.20,
        'ebitda_margin': 0.15,
        'current_ratio': 0.15,
        'churn_rate': 0.15,
        'data_quality': 0.10
    }

    def evaluate(self, kpis: Dict[str, Any], quality_score: float) -> Dict[str, Any]:
        """
        Calculates composite business health, system confidence, and risk severity.

        Args:
            kpis: Dictionary of computed key performance indicators.
            quality_score: Overall data quality score (0-100).

        Returns:
            Dict containing Pydantic schema object and detailed internal diagnostics.
        """
        # 1. Normalize Components into 0 - 100 Sub-Scores
        net_margin = kpis.get('net_profit_margin', 0.0)
        s_margin = min(max(net_margin * 3.33, 0.0), 100.0)  # 30% Net Margin = 100 pts

        rev_growth = kpis.get('revenue_growth', 0.0)
        s_growth = min(max((rev_growth + 10.0) * 3.33, 0.0), 100.0)  # 20% Growth = 100 pts

        ebitda_margin = kpis.get('ebitda_margin', 0.0)
        s_ebitda = min(max(ebitda_margin * 4.0, 0.0), 100.0)  # 25% EBITDA = 100 pts

        curr_ratio = kpis.get('current_ratio', 1.0)
        s_ratio = min(max((curr_ratio / 2.0) * 100.0, 0.0), 100.0)  # Current Ratio 2.0 = 100 pts

        churn = kpis.get('churn_rate', 5.0)
        s_churn = max(0.0, 100.0 - (churn * 10.0))  # 0% Churn = 100 pts

        s_quality = min(max(quality_score, 0.0), 100.0)

        # 2. Weighted Score Summation
        composite_score = (
            (s_margin * self.WEIGHTS['profit_margin']) +
            (s_growth * self.WEIGHTS['revenue_growth']) +
            (s_ebitda * self.WEIGHTS['ebitda_margin']) +
            (s_ratio * self.WEIGHTS['current_ratio']) +
            (s_churn * self.WEIGHTS['churn_rate']) +
            (s_quality * self.WEIGHTS['data_quality'])
        )

        final_score = round(max(0.0, min(100.0, composite_score)), 1)

        # 3. Status Classification (5 Tiers)
        if final_score >= 85.0:
            status = "Excellent"
        elif final_score >= 70.0:
            status = "Healthy"
        elif final_score >= 55.0:
            status = "Stable"
        elif final_score >= 40.0:
            status = "At Risk"
        else:
            status = "Critical"

        # 4. Calculate Business Health Confidence Score
        # Derived from input data quality and statistical agreement between metric sub-scores
        sub_scores_list = [s_margin, s_growth, s_ebitda, s_ratio, s_churn]
        variance = sum((s - final_score) ** 2 for s in sub_scores_list) / len(sub_scores_list)
        stability_factor = max(0.0, 100.0 - (variance ** 0.5))
        
        raw_confidence = (s_quality * 0.6) + (stability_factor * 0.4)
        confidence_score = round(max(10.0, min(99.9, raw_confidence)), 1)

        # 5. Determine Overall Risk Level based on Health & Liquidity
        if final_score < 40.0 or curr_ratio < 0.8:
            risk_level = "Critical"
        elif final_score < 55.0 or curr_ratio < 1.0 or churn > 12.0:
            risk_level = "High"
        elif final_score < 75.0 or churn > 7.0:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        # Rationale Construction
        rationale: List[str] = [
            f"Evaluated Net Profit Margin: {net_margin}% (Sub-score: {s_margin:.1f}/100)",
            f"Evaluated Revenue Growth: {rev_growth}% (Sub-score: {s_growth:.1f}/100)",
            f"Current Liquidity Ratio: {curr_ratio} (Sub-score: {s_ratio:.1f}/100)",
            f"Business Health Confidence Score: {confidence_score}%"
        ]

        logger.info(
            f"Health Evaluation Complete: Score = {final_score}/100 | "
            f"Status = {status} | Confidence = {confidence_score}% | Risk = {risk_level}"
        )

        # Build schema object for upstream pipeline integration
        assessment_model = BusinessHealthAssessment(
            health_score=final_score,
            status=status,
            confidence_score=confidence_score,
            risk_level=risk_level,
            data_quality_score=round(s_quality, 1)
        )

        return {
            "model": assessment_model,
            "health_score": final_score,
            "status": status,
            "confidence_score": confidence_score,
            "risk_level": risk_level,
            "data_quality_score": round(s_quality, 1),
            "rationale": rationale,
            "sub_scores": {
                "profitability": round(s_margin, 1),
                "growth": round(s_growth, 1),
                "liquidity": round(s_ratio, 1),
                "retention": round(s_churn, 1)
            }
        }
