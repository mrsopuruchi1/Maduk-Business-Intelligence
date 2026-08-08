"""
Maduk Business Intelligence - Rolling Origin Cross Validation
============================================================
File: backend/services/ai_prediction_pipeline/evaluation/cross_validation.py

Executes expanding window time-series backtesting for objective evaluation.
"""

import logging
from typing import Dict, Any, List, Generator, Tuple
import pandas as pd
import numpy as np

from .metrics import MetricsEvaluator

logger = logging.getLogger("MadukBI.CrossValidation")


class RollingOriginCV:
    """
    Time-Series Cross-Validation Engine using Expanding Window Splitter.
    Ensures backtests respect chronology without lookahead leakage.
    """

    def __init__(self, n_splits: int = 3, min_train_size: int = 12):
        """
        Args:
            n_splits: Number of rolling backtest folds to evaluate.
            min_train_size: Minimum initial historical observations needed for training.
        """
        self.n_splits = n_splits
        self.min_train_size = min_train_size
        self.metrics_evaluator = MetricsEvaluator()

    def split(
        self, 
        df: pd.DataFrame, 
        forecast_horizon: int = 12
    ) -> Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]:
        """
        Yields (train_slice, test_slice) DataFrames across rolling-origin iterations.

        Args:
            df: Chronologically sorted input DataFrame.
            forecast_horizon: Number of periods in each holdout test fold.

        Yields:
            Tuples of (train_df, test_df)
        """
        n_samples = len(df)
        total_test_span = self.n_splits * forecast_horizon

        if n_samples < (self.min_train_size + forecast_horizon):
            logger.warning("Dataset length is too small for multi-split CV. Falling back to single split.")
            train_idx = max(1, n_samples - forecast_horizon)
            yield df.iloc[:train_idx].copy(), df.iloc[train_idx:].copy()
            return

        # Calculate dynamic fold offsets
        start_test_idx = n_samples - total_test_span
        if start_test_idx < self.min_train_size:
            start_test_idx = self.min_train_size

        step_size = max(1, int((n_samples - start_test_idx - forecast_horizon) / max(1, self.n_splits - 1))) if self.n_splits > 1 else forecast_horizon

        for i in range(self.n_splits):
            split_idx = start_test_idx + (i * step_size)
            test_end_idx = min(split_idx + forecast_horizon, n_samples)

            if split_idx >= n_samples or split_idx < self.min_train_size:
                break

            train_df = df.iloc[:split_idx].copy()
            test_df = df.iloc[split_idx:test_end_idx].copy()

            if not test_df.empty:
                yield train_df, test_df

    def evaluate_model(
        self,
        model: Any,
        df: pd.DataFrame,
        date_col: str,
        target_col: str,
        freq: str = "MS",
        forecast_horizon: int = 12
    ) -> Dict[str, Any]:
        """
        Performs rolling backtests on a specific forecaster model and aggregates mean performance.

        Args:
            model: BaseForecaster instance.
            df: Feature engineered DataFrame sorted by date.
            date_col: Datetime column name.
            target_col: Target variable column name.
            freq: Time series frequency string.
            forecast_horizon: Test horizon length per fold.

        Returns:
            Dict containing aggregate cross-validation metrics and fold summaries.
        """
        fold_metrics: List[Dict[str, float]] = []
        all_residuals: List[np.ndarray] = []

        for fold_idx, (train_df, test_df) in enumerate(self.split(df, forecast_horizon=forecast_horizon)):
            try:
                # Fit candidate model on expanding training set
                model.fit(train_df, date_col, target_col, freq=freq)

                # Forecast for test horizon length
                horizon_len = len(test_df)
                preds_df = model.predict_horizon(horizon=horizon_len, freq=freq)

                y_true = test_df[target_col].values
                y_pred = preds_df["forecast"].values

                # Compute metrics for fold
                metrics = self.metrics_evaluator.evaluate(y_true, y_pred)
                residuals = self.metrics_evaluator.calculate_residuals(y_true, y_pred)

                fold_metrics.append(metrics)
                all_residuals.append(residuals)

            except Exception as e:
                logger.error(f"Error during CV fold {fold_idx + 1} for model '{model.name}': {e}")

        if not fold_metrics:
            return {
                "mean_metrics": {"MAPE": float("inf"), "RMSE": float("inf"), "MAE": float("inf"), "R2": 0.0},
                "residuals": np.array([])
            }

        # Compute mean metrics across all folds
        avg_mape = float(np.mean([m["MAPE"] for m in fold_metrics]))
        avg_rmse = float(np.mean([m["RMSE"] for m in fold_metrics]))
        avg_mae = float(np.mean([m["MAE"] for m in fold_metrics]))
        avg_r2 = float(np.mean([m["R2"] for m in fold_metrics]))

        combined_residuals = np.concatenate(all_residuals) if all_residuals else np.array([])

        return {
            "mean_metrics": {
                "MAPE": round(avg_mape, 4),
                "RMSE": round(avg_rmse, 2),
                "MAE": round(avg_mae, 2),
                "R2": round(avg_r2, 4)
            },
            "fold_count": len(fold_metrics),
            "residuals": combined_residuals
        }
