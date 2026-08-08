"""
Maduk Business Intelligence - Confidence Intervals Generator
============================================================
File: backend/services/ai_prediction_pipeline/confidence_intervals.py
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger("MadukBI.ConfidenceIntervals")


class ConfidenceIntervalGenerator:
    """Calculates dynamic prediction intervals based on model residual distributions."""

    def calculate_intervals(
        self,
        forecast_df: pd.DataFrame,
        historical_df: pd.DataFrame,
        target_col: str,
        confidence_level: float = 0.95,
        residuals: Optional[np.ndarray] = None
    ) -> pd.DataFrame:
        """
        Attaches lower_bound and upper_bound columns to forecast estimates.

        Args:
            forecast_df: Base model predictions.
            historical_df: Historical training data.
            target_col: Target variable name.
            confidence_level: Statistical confidence level (e.g. 0.95 for 95% CI).
            residuals: Out-of-sample residual errors from backtesting.

        Returns:
            pd.DataFrame with 'lower_bound' and 'upper_bound'.
        """
        logger.info(f"Computing {confidence_level:.0%} confidence intervals...")
        result_df = forecast_df.copy()

        # Check if bounds are already computed by specific forecaster adapters
        if "lower_bound" in result_df.columns and "upper_bound" in result_df.columns:
            if not result_df["lower_bound"].isnull().any():
                return result_df

        # Z-score lookup based on confidence level
        z_scores = {0.80: 1.282, 0.90: 1.645, 0.95: 1.960, 0.99: 2.576}
        z_stat = z_scores.get(confidence_level, 1.960)

        # Estimate residual standard deviation
        if residuals is not None and len(residuals) > 2:
            std_error = np.std(residuals)
        else:
            hist_vals = historical_df[target_col].dropna().values
            std_error = np.std(hist_vals) * 0.10 if len(hist_vals) > 0 else 1.0

        # Expand uncertainty over extended forecasting horizons (sqrt of time horizon expansion)
        horizon = len(result_df)
        horizon_expansion = np.sqrt(np.arange(1, horizon + 1))
        margin_of_error = z_stat * std_error * horizon_expansion

        result_df["lower_bound"] = (result_df["forecast"] - margin_of_error).round(2)
        result_df["upper_bound"] = (result_df["forecast"] + margin_of_error).round(2)

        # Prevent negative values for naturally non-negative metrics
        if (historical_df[target_col] >= 0).all():
            result_df["lower_bound"] = result_df["lower_bound"].clip(lower=0.0)

        return result_df
