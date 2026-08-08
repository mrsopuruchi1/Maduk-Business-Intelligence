"""
Maduk Business Intelligence - Business Recommendations Engine
===========================================================
File: backend/services/ai_prediction_pipeline/business_recommendations.py
"""

import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger("MadukBI.BusinessRecommendations")


class BusinessRecommendationEngine:
    """Translates model forecasts and scenario projections into executive risk flags and recommendations."""

    def assess_risks(
        self,
        historical_df: pd.DataFrame,
        forecast_df: pd.DataFrame,
        metrics: Dict[str, float],
        target_col: str
    ) -> List[str]:
        """Evaluates time series anomalies and volatility to extract business risk statements."""
        logger.info("Assessing operational and business risks...")
        risks = []

        # 1. Backtest Model Fit Error Risk
        mape = metrics.get("MAPE", 0.0)
        if mape > 0.15:
            risks.append(
                f"High Forecast Variance: Backtested error (MAPE: {mape:.1%}) indicates historical instability in target dynamics."
            )

        # 2. Downside Scenario Exposure
        if "conservative" in forecast_df.columns and "forecast" in forecast_df.columns:
            expected_total = forecast_df["forecast"].sum()
            conservative_total = forecast_df["conservative"].sum()
            gap_pct = ((expected_total - conservative_total) / expected_total) * 100.0 if expected_total > 0 else 0.0
            
            if gap_pct > 10.0:
                risks.append(
                    f"Downside Exposure: Conservative scenario reflects a potential {gap_pct:.1f}% downside gap under market stress."
                )

        # 3. Projected Negative Trend
        forecast_vals = forecast_df["forecast"].values
        if len(forecast_vals) > 1 and forecast_vals[-1] < forecast_vals[0]:
            risks.append(
                "Negative Horizon Drift: Projected target trajectory demonstrates downward momentum over the second half of the horizon."
            )

        if not risks:
            risks.append("Low Operational Risk: Historical trends indicate steady predictability across the target variable.")

        return risks

    def generate_actions(
        self,
        risks: List[str],
        summary_data: Dict[str, Any],
        scenarios: pd.DataFrame
    ) -> List[str]:
        """Formulates actionable executive recommendations based on identified risks and scenario divergence."""
        logger.info("Generating strategic executive advisories...")
        actions = []

        kpis = summary_data.get("kpis", {})
        growth_rate = kpis.get("growth_rate_pct", 0.0)

        # Growth-oriented recommendations
        if growth_rate > 5.0:
            actions.append(
                "Capital Commitment: Align supply chain capacities and working capital to support the projected +{:.1f}% growth trajectory.".format(growth_rate)
            )
        elif growth_rate < -2.0:
            actions.append(
                "Cost Realignment: Implement operational buffer controls and review baseline expenditure to offset negative momentum."
            )

        # Scenario-oriented recommendations
        if "conservative" in scenarios.columns:
            min_conservative = scenarios["conservative"].min()
            actions.append(
                f"Risk Mitigation: Maintain working capital liquidity reserves above the minimum conservative threshold (${min_conservative:,.2f})."
            )

        actions.append(
            "Continuous Pipeline Monitoring: Re-run the automated forecasting pipeline monthly to update dynamic lag features and track scenario convergence."
        )

        return actions
