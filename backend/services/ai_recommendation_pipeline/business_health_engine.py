# business_health_engine.py

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

    DEFAULT_WEIGHTS = {
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
        sub_scores: Dict[str, float] = {}
        active_weights: Dict[str, float] = {}

        # 1. Continuous Nonlinear Normalization into 0 - 100 Sub-Scores

        # Net Profit Margin Sub-Score
        net_margin = kpis.get('net_profit_margin')
        if net_margin is not None:
            net_margin = float(net_margin)
            if net_margin >= 30.0:
                s_margin = 100.0
            elif net_margin >= 0.0:
                s_margin = 40.0 + (net_margin / 30.0) * 60.0
            else:
                s_margin = max(0.0, 40.0 + (net_margin / 20.0) * 40.0)
            sub_scores['profit_margin'] = s_margin
            active_weights['profit_margin'] = self.DEFAULT_WEIGHTS['profit_margin']

        # Revenue Growth Sub-Score
        rev_growth = kpis.get('revenue_growth')
        if rev_growth is not None:
            rev_growth = float(rev_growth)
            if rev_growth >= 25.0:
                s_growth = 100.0
            elif rev_growth >= 0.0:
                s_growth = 50.0 + (rev_growth / 25.0) * 50.0
            else:
                s_growth = max(0.0, 50.0 + (rev_growth / 15.0) * 50.0)
            sub_scores['revenue_growth'] = s_growth
            active_weights['revenue_growth'] = self.DEFAULT_WEIGHTS['revenue_growth']

        # EBITDA Margin Sub-Score
        ebitda_margin = kpis.get('ebitda_margin')
        if ebitda_margin is not None:
            ebitda_margin = float(ebitda_margin)
            if ebitda_margin >= 25.0:
                s_ebitda = 100.0
            elif ebitda_margin >= 0.0:
                s_ebitda = 30.0 + (ebitda_margin / 25.0) * 70.0
            else:
                s_ebitda = max(0.0, 30.0 + (ebitda_margin / 10.0) * 30.0)
            sub_scores['ebitda_margin'] = s_ebitda
            active_weights['ebitda_margin'] = self.DEFAULT_WEIGHTS['ebitda_margin']

        # Current Liquidity Ratio Sub-Score
        curr_ratio = kpis.get('current_ratio')
        if curr_ratio is not None:
            curr_ratio = float(curr_ratio)
            if curr_ratio >= 2.0:
                s_ratio = 100.0
            elif curr_ratio >= 1.0:
                s_ratio = 50.0 + (curr_ratio - 1.0) * 50.0
            else:
                s_ratio = max(0.0, curr_ratio * 50.0)
            sub_scores['current_ratio'] = s_ratio
            active_weights['current_ratio'] = self.DEFAULT_WEIGHTS['current_ratio']

        # Churn Rate Sub-Score
        churn = kpis.get('churn_rate')
        if churn is not None:
            churn = float(churn)
            if churn <= 0.0:
                s_churn = 100.0
            elif churn <= 5.0:
                s_churn = 100.0 - (churn / 5.0) * 40.0
            elif churn <= 15.0:
                s_churn = max(0.0, 60.0 - ((churn - 5.0) / 10.0) * 60.0)
            else:
                s_churn = 0.0
            sub_scores['churn_rate'] = s_churn
            active_weights['churn_rate'] = self.DEFAULT_WEIGHTS['churn_rate']

        # Data Quality Score
        s_quality = min(max(float(quality_score), 0.0), 100.0)
        sub_scores['data_quality'] = s_quality
        active_weights['data_quality'] = self.DEFAULT_WEIGHTS['data_quality']

        # 2. Dynamic Weight Re-normalization
        total_weight = sum(active_weights.values())
        if total_weight > 0:
            composite_score = sum(sub_scores[k] * (active_weights[k] / total_weight) for k in sub_scores)
        else:
            composite_score = 50.0

        final_score = round(max(0.0, min(100.0, composite_score)), 1)

        # 3. Status Classification
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
        valid_sub_scores = [v for k, v in sub_scores.items() if k != 'data_quality']
        if valid_sub_scores:
            variance = sum((s - final_score) ** 2 for s in valid_sub_scores) / len(valid_sub_scores)
            stability_factor = max(0.0, 100.0 - (variance ** 0.5))
        else:
            stability_factor = 50.0

        raw_confidence = (s_quality * 0.6) + (stability_factor * 0.4)
        confidence_score = round(max(10.0, min(99.9, raw_confidence)), 1)

        # 5. Determine Overall Risk Level safely
        is_critical = (
            final_score < 40.0 or
            (curr_ratio is not None and curr_ratio < 0.8) or
            (net_margin is not None and net_margin < -15.0)
        )
        is_high = (
            final_score < 55.0 or
            (curr_ratio is not None and curr_ratio < 1.0) or
            (churn is not None and churn > 12.0) or
            (net_margin is not None and net_margin < 0.0)
        )
        is_medium = (
            final_score < 75.0 or
            (churn is not None and churn > 7.0) or
            (rev_growth is not None and rev_growth < 0.0)
        )

        if is_critical:
            risk_level = "Critical"
        elif is_high:
            risk_level = "High"
        elif is_medium:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        # Executive Rationale Construction
        rationale: List[str] = []
        if net_margin is not None:
            rationale.append(f"Net Profit Margin: {net_margin:.2f}% (Sub-score: {sub_scores['profit_margin']:.1f}/100)")
        if rev_growth is not None:
            rationale.append(f"Revenue Growth: {rev_growth:.2f}% (Sub-score: {sub_scores['revenue_growth']:.1f}/100)")
        if churn is not None:
            rationale.append(f"Customer Churn Rate: {churn:.2f}% (Sub-score: {sub_scores['churn_rate']:.1f}/100)")
        if curr_ratio is not None:
            rationale.append(f"Liquidity (Current Ratio): {curr_ratio:.2f} (Sub-score: {sub_scores['current_ratio']:.1f}/100)")
        rationale.append(f"System Confidence Index: {confidence_score}%")

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
            "sub_scores": {k: round(v, 1) for k, v in sub_scores.items()}
        }
