"""
Maduk Business Intelligence - Metrics Evaluator
==============================================
File: backend/services/ai_prediction_pipeline/evaluation/metrics.py

Provides standardized mathematical metrics for evaluating time series forecasts.
"""

import logging
from typing import Dict, Any, Union
import numpy as np
import pandas as pd

logger = logging.getLogger("MadukBI.MetricsEvaluator")


class MetricsEvaluator:
    """Computes backtesting and validation metrics for forecasting models."""

    @staticmethod
    def evaluate(
        y_true: Union[np.ndarray, pd.Series, list],
        y_pred: Union[np.ndarray, pd.Series, list]
    ) -> Dict[str, float]:
        """
        Computes accurate time series regression and error metrics.

        Args:
            y_true: Array-like actual target values.
            y_pred: Array-like forecasted values.

        Returns:
            Dict containing MAPE, RMSE, MAE, sMAPE, R2, and Max Error.
        """
        y_true_arr = np.array(y_true, dtype=float).flatten()
        y_pred_arr = np.array(y_pred, dtype=float).flatten()

        if len(y_true_arr) != len(y_pred_arr):
            raise ValueError(f"Shape mismatch: y_true length ({len(y_true_arr)}) != y_pred length ({len(y_pred_arr)})")

        if len(y_true_arr) == 0:
            return {"MAPE": 0.0, "RMSE": 0.0, "MAE": 0.0, "sMAPE": 0.0, "R2": 0.0, "MAX_ERROR": 0.0}

        residuals = y_true_arr - y_pred_arr

        # 1. Mean Absolute Error (MAE)
        mae = float(np.mean(np.abs(residuals)))

        # 2. Root Mean Squared Error (RMSE)
        rmse = float(np.sqrt(np.mean(residuals ** 2)))

        # 3. Mean Absolute Percentage Error (MAPE) with zero-division guard
        non_zero_mask = y_true_arr != 0
        if np.any(non_zero_mask):
            mape = float(np.mean(np.abs(residuals[non_zero_mask] / y_true_arr[non_zero_mask])))
        else:
            mape = 0.0

        # 4. Symmetric Mean Absolute Percentage Error (sMAPE)
        denominator = (np.abs(y_true_arr) + np.abs(y_pred_arr)) / 2.0
        nz_denom_mask = denominator != 0
        if np.any(nz_denom_mask):
            smape = float(np.mean(np.abs(residuals[nz_denom_mask]) / denominator[nz_denom_mask]))
        else:
            smape = 0.0

        # 5. Coefficient of Determination (R²)
        ss_tot = np.sum((y_true_arr - np.mean(y_true_arr)) ** 2)
        ss_res = np.sum(residuals ** 2)
        r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

        # 6. Maximum Absolute Error
        max_error = float(np.max(np.abs(residuals)))

        return {
            "MAPE": round(mape, 4),
            "RMSE": round(rmse, 2),
            "MAE": round(mae, 2),
            "sMAPE": round(smape, 4),
            "R2": round(r2, 4),
            "MAX_ERROR": round(max_error, 2)
        }

    @staticmethod
    def calculate_residuals(
        y_true: Union[np.ndarray, pd.Series, list],
        y_pred: Union[np.ndarray, pd.Series, list]
    ) -> np.ndarray:
        """Returns residual array (actuals - predictions)."""
        return np.array(y_true, dtype=float).flatten() - np.array(y_pred, dtype=float).flatten()
