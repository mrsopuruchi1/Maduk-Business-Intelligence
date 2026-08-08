"""
Maduk Business Intelligence - Scenario Analysis
===============================================
File: backend/services/ai_prediction_pipeline/scenario_analysis.py
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger("MadukBI.ScenarioAnalysis")


class ScenarioAnalyzer:
    """Generates optimistic, conservative, and stress-tested strategic scenario projections."""

    def generate_scenarios(
        self,
        forecast_df: pd.DataFrame,
        target_col: str,
        historical_df: pd.DataFrame,
        conservative_factor: float = 0.08,
        optimistic_factor: float = 0.08
    ) -> pd.DataFrame:
        """
        Applies volatility-adjusted drift factors to generate multi-scenario forecasts.

        Args:
            forecast_df: DataFrame with 'date', 'forecast', 'lower_bound', 'upper_bound'.
            target_col: Name of the primary target column.
            historical_df: Historical dataset for volatility calibration.
            conservative_factor: Downside risk shift factor (default 8%).
            optimistic_factor: Upside potential shift factor (default 8%).

        Returns:
            pd.DataFrame: Enriched with 'conservative' and 'optimistic' scenario columns.
        """
        logger.info("Generating strategic forecast scenarios (Expected, Conservative, Optimistic)...")
        scenarios_df = forecast_df.copy()

        # Compute historical percentage volatility (std / mean)
        hist_values = historical_df[target_col].dropna().values
        if len(hist_values) > 1 and np.mean(hist_values) != 0:
            volatility = float(np.std(hist_values) / np.mean(hist_values))
        else:
            volatility = 0.05

        # Compound scenario adjustment over the forecast horizon
        horizon_len = len(scenarios_df)
        time_steps = np.arange(1, horizon_len + 1)

        # Conservative scenario: Accounts for compounding downside risk and historical volatility
        downside_drift = 1.0 - (conservative_factor + (0.01 * volatility * time_steps))
        # Optimistic scenario: Accounts for compounding upside opportunities
        upside_drift = 1.0 + (optimistic_factor + (0.01 * volatility * time_steps))

        # Apply lower/upper confidence bounds as safety clamps
        if "lower_bound" in scenarios_df.columns and "upper_bound" in scenarios_df.columns:
            scenarios_df["conservative"] = np.minimum(
                scenarios_df["forecast"] * downside_drift,
                scenarios_df["lower_bound"]
            )
            scenarios_df["optimistic"] = np.maximum(
                scenarios_df["forecast"] * upside_drift,
                scenarios_df["upper_bound"]
            )
        else:
            scenarios_df["conservative"] = scenarios_df["forecast"] * downside_drift
            scenarios_df["optimistic"] = scenarios_df["forecast"] * upside_drift

        # Round outputs for clean JSON presentation
        scenarios_df["forecast"] = scenarios_df["forecast"].round(2)
        scenarios_df["conservative"] = scenarios_df["conservative"].round(2)
        scenarios_df["optimistic"] = scenarios_df["optimistic"].round(2)

        return scenarios_df
