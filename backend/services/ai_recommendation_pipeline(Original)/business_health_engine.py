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
        # 1. Continuous Nonlinear Normalization into 0 - 100 Sub-Scores

        # Net Profit Margin Sub-Score (-20% margin = 0 pts, 0% = 40 pts, 30%+ = 100 pts)
        net_margin = float(kpis.get('net_profit_margin', 0.0))
        if net_margin >= 30.0:
            s_margin = 100.0
        elif net_margin >= 0.0:
            s_margin = 40.0 + (net_margin / 30.0) * 60.0
        else:
            s_margin = max(0.0, 40.0 + (net_margin / 20.0) * 40.0)

        # Revenue Growth Sub-Score (-15% growth = 0 pts, 0% = 50 pts, 25%+ = 100 pts)
        rev_growth = float(kpis.get('revenue_growth', 0.0))
        if rev_growth >= 25.0:
            s_growth = 100.0
        elif rev_growth >= 0.0:
            s_growth = 50.0 + (rev_growth / 25.0) * 50.0
        else:
            s_growth = max(0.0, 50.0 + (rev_growth / 15.0) * 50.0)

        # EBITDA Margin Sub-Score (-10% = 0 pts, 0% = 30 pts, 25%+ = 100 pts)
        ebitda_margin = float(kpis.get('ebitda_margin', 0.0))
        if ebitda_margin >= 25.0:
            s_ebitda = 100.0
        elif ebitda_margin >= 0.0:
            s_ebitda = 30.0 + (ebitda_margin / 25.0) * 70.0
        else:
            s_ebitda = max(0.0, 30.0 + (ebitda_margin / 10.0) * 30.0)

        # Current Liquidity Ratio Sub-Score (0.0 ratio = 0 pts, 1.0 = 50 pts, 2.0+ = 100 pts)
        curr_ratio = float(kpis.get('current_ratio', 1.0))
        if curr_ratio >= 2.0:
            s_ratio = 100.0
        elif curr_ratio >= 1.0:
            s_ratio = 50.0 + (curr_ratio - 1.0) * 50.0
        else:
            s_ratio = max(0.0, curr_ratio * 50.0)

        # Churn Rate Sub-Score (0% churn = 100 pts, 5% churn = 60 pts, 15%+ churn = 0 pts)
        churn = float(kpis.get('churn_rate', 0.0))
        if churn <= 0.0:
            s_churn = 100.0
        elif churn <= 5.0:
            s_churn = 100.0 - (churn / 5.0) * 40.0
        elif churn <= 15.0:
            s_churn = max(0.0, 60.0 - ((churn - 5.0) / 10.0) * 60.0)
        else:
            s_churn = 0.0

        # Data Quality Score
        s_quality = min(max(float(quality_score), 0.0), 100.0)

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

        # 3. Status Classification (5 Executive Tiers)
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
        sub_scores_list = [s_margin, s_growth, s_ebitda, s_ratio, s_churn]
        variance = sum((s - final_score) ** 2 for s in sub_scores_list) / len(sub_scores_list)
        stability_factor = max(0.0, 100.0 - (variance ** 0.5))
        
        raw_confidence = (s_quality * 0.6) + (stability_factor * 0.4)
        confidence_score = round(max(10.0, min(99.9, raw_confidence)), 1)

        # 5. Determine Overall Risk Level based on Health & Multi-Metric Stress Factors
        if final_score < 40.0 or curr_ratio < 0.8 or net_margin < -15.0:
            risk_level = "Critical"
        elif final_score < 55.0 or curr_ratio < 1.0 or churn > 12.0 or net_margin < 0.0:
            risk_level = "High"
        elif final_score < 75.0 or churn > 7.0 or rev_growth < 0.0:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        # Executive Rationale Construction
        rationale: List[str] = [
            f"Net Profit Margin: {net_margin:.2f}% (Sub-score: {s_margin:.1f}/100)",
            f"Revenue Growth: {rev_growth:.2f}% (Sub-score: {s_growth:.1f}/100)",
            f"Customer Churn Rate: {churn:.2f}% (Sub-score: {s_churn:.1f}/100)",
            f"Liquidity (Current Ratio): {curr_ratio:.2f} (Sub-score: {s_ratio:.1f}/100)",
            f"System Confidence Index: {confidence_score}%"
        ]

        logger.info(
            f"Health Evaluation Complete: Score = {final_score}/100 | "
            f"Status = {status} | Confidence = {confidence_score}% | Risk = {risk_level}"
        )

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
                "retention": round(s_churn, 1),
                "ebitda": round(s_ebitda, 1)
            }
        }
