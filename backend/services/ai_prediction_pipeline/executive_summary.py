"""
Maduk Business Intelligence - Executive Summary Generator
=========================================================
File: backend/services/ai_prediction_pipeline/executive_summary.py
"""

import logging
from typing import Dict, Any
import pandas as pd
import numpy as np

logger = logging.getLogger("MadukBI.ExecutiveSummary")


class ExecutiveSummaryGenerator:
    """Produces narrative summaries and executive KPI card payloads."""

    def generate_summary(
        self,
        historical_df: pd.DataFrame,
        forecast_df: pd.DataFrame,
        date_col: str,
        target_col: str,
        winning_model_name: str,
        metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Generates executive summary narrative and high-level KPIs.

        Returns:
            Dict containing 'summary_text' and 'kpis' sub-dictionaries.
        """
        logger.info("Synthesizing executive summary and KPI values...")

        # Historical vs Projected Totals
        hist_values = historical_df[target_col].dropna().values
        last_hist_val = float(hist_values[-1]) if len(hist_values) > 0 else 0.0
        hist_total = float(np.sum(hist_values))

        forecast_vals = forecast_df["forecast"].values
        forecast_total = float(np.sum(forecast_vals))
        forecast_mean = float(np.mean(forecast_vals))

        # Calculate Growth Rate
        growth_pct = 0.0
        if last_hist_val > 0:
            first_forecast = forecast_vals[0]
            growth_pct = ((forecast_mean - last_hist_val) / last_hist_val) * 100.0

        # Assess Trend Direction
        if growth_pct > 2.0:
            trend_str = "UPWARD GROWTH"
        elif growth_pct < -2.0:
            trend_str = "DOWNWARD SLU"
        else:
            trend_str = "STABLE / FLAT"

        mape_val = metrics.get("MAPE", 0.0)
        confidence_str = "High (MAPE < 5%)" if mape_val < 0.05 else ("Moderate (MAPE < 15%)" if mape_val < 0.15 else "Low Risk")

        summary_text = (
            f"The AI Prediction Engine has completed automated dynamic evaluation and selected '{winning_model_name}' "
            f"as the optimal model based on an out-of-sample MAPE error rate of {mape_val:.2%}. "
            f"Over the projected {len(forecast_df)}-period horizon, the overall trend reflects an {trend_str} trajectory "
            f"with expected aggregate target outcome of {forecast_total:,.2f} "
            f"(representing an estimated average period growth shift of {growth_pct:+.1f}%)."
        )

        kpis = {
            "current_period_baseline": round(last_hist_val, 2),
            "projected_horizon_total": round(forecast_total, 2),
            "projected_period_average": round(forecast_mean, 2),
            "growth_rate_pct": round(growth_pct, 2),
            "trend_direction": trend_str,
            "forecast_confidence": confidence_str,
            "selected_model": winning_model_name
        }

        return {
            "summary_text": summary_text,
            "kpis": kpis
        }
