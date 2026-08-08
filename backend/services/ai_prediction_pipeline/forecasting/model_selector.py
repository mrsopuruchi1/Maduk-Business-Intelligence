"""
Maduk Business Intelligence - Dynamic Model Selector
===================================================
File: backend/services/ai_prediction_pipeline/forecasting/model_selector.py

Evaluates candidate models via rolling-origin backtesting or temporal split,
selects the top-performing forecaster based on objective error metrics (MAPE/RMSE),
and provides detailed rationale along with model rankings.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

from .base_model import BaseForecaster
from .prophet_model import ProphetForecaster
from .sarima_model import SARIMAForecaster
from .xgboost_model import XGBoostForecaster
from .lightgbm_model import LightGBMForecaster
from .random_forest_model import RandomForestForecaster
from .lstm_model import LSTMForecaster

logger = logging.getLogger("MadukBI.ModelSelector")


class ModelSelector:
    """
    Automated Model Selection Engine.
    
    Manages model registration, parallel/sequential cross-validation, fallback wraps
    for failed library instantiations, error metric comparison, and retrains the winning 
    model on the full dataset.
    """

    def __init__(
        self, 
        cv_evaluator: Optional[Any] = None, 
        metrics_evaluator: Optional[Any] = None,
        candidate_models: Optional[List[BaseForecaster]] = None
    ):
        """
        Initialize the selector with optional custom evaluators and model candidates.
        """
        self.cv_evaluator = cv_evaluator
        self.metrics_evaluator = metrics_evaluator
        self.candidate_models = candidate_models or self._get_default_candidate_models()

    def _get_default_candidate_models(self) -> List[BaseForecaster]:
        """
        Instantiates available default model adapters with fallback handling
        if optional C-dependencies or packages (e.g. PyTorch/Prophet) are absent.
        """
        models: List[BaseForecaster] = []

        # Classical Statistical & Tree-based Models (Core Defaults)
        for model_cls, name in [
            (RandomForestForecaster, "Random Forest"),
            (LightGBMForecaster, "LightGBM"),
            (XGBoostForecaster, "XGBoost"),
            (SARIMAForecaster, "SARIMA"),
        ]:
            try:
                models.append(model_cls())
            except Exception as e:
                logger.warning(f"Could not initialize candidate model {name}: {e}")

        # Additive & Deep Learning Models
        for model_cls, name in [
            (ProphetForecaster, "Prophet"),
            (LSTMForecaster, "PyTorch LSTM"),
        ]:
            try:
                models.append(model_cls())
            except Exception as e:
                logger.info(f"Optional candidate model {name} disabled (Dependency missing or failed to initialize).")

        return models

    def select_best_model(
        self,
        df: pd.DataFrame,
        date_col: str,
        target_col: str,
        freq: str = "MS",
        forecast_horizon: int = 12
    ) -> Dict[str, Any]:
        """
        Runs backtesting across all candidate models and selects the top performer.

        Args:
            df: Cleaned and feature-engineered DataFrame.
            date_col: Name of datetime column.
            target_col: Name of target variable column.
            freq: Time series frequency string (e.g., 'MS', 'D', 'W').
            forecast_horizon: Number of future periods to predict.

        Returns:
            Dict containing:
                - winning_model_instance: Refitted instance of winning forecaster
                - winning_model_name: Name of selected model
                - selection_rationale: Detailed explanation for selection
                - best_metrics: Performance metrics dictionary for winning model
                - all_model_metrics: Comparison breakdown for all candidates
                - residuals: Residual error array on holdout split
        """
        logger.info(f"Evaluating {len(self.candidate_models)} candidate forecasting models...")

        if df.empty or len(df) < 5:
            raise ValueError("Dataset contains insufficient observations for model cross-validation.")

        # Determine train/test split boundary for backtesting validation
        test_size = min(forecast_horizon, int(len(df) * 0.25))
        test_size = max(1, test_size)  # Ensure at least 1 observation in test split
        
        train_df = df.iloc[:-test_size].copy()
        test_df = df.iloc[-test_size:].copy()

        all_metrics: Dict[str, Dict[str, Any]] = {}
        model_forecasts: Dict[str, pd.DataFrame] = {}
        model_instances: Dict[str, BaseForecaster] = {}

        best_model_name = None
        best_mape = float("inf")
        winning_instance = None
        winning_residuals = np.array([])

        for model in self.candidate_models:
            model_name = model.name
            try:
                logger.info(f"Cross-validating candidate model: '{model_name}'...")
                
                # Fit model on training slice
                model.fit(train_df, date_col, target_col, freq=freq)
                
                # Generate out-of-sample forecast for validation length
                preds_df = model.predict_horizon(horizon=len(test_df), freq=freq)
                
                # Compute error metrics
                y_true = test_df[target_col].values
                y_pred = preds_df["forecast"].values

                metrics, residuals = self._compute_validation_metrics(y_true, y_pred)
                
                all_metrics[model_name] = metrics
                model_forecasts[model_name] = preds_df
                model_instances[model_name] = model

                mape = metrics.get("MAPE", float("inf"))

                # Select winning model based on MAPE primary ranking metric
                if mape < best_mape:
                    best_mape = mape
                    best_model_name = model_name
                    winning_instance = model
                    winning_residuals = residuals

            except Exception as e:
                logger.error(f"Error evaluating candidate model '{model_name}': {str(e)}")
                all_metrics[model_name] = {"error": str(e), "MAPE": float("inf"), "RMSE": float("inf")}

        if winning_instance is None or best_model_name is None:
            raise RuntimeError("All candidate models failed during cross-validation evaluation.")

        logger.info(f"Selected Winning Model: '{best_model_name}' with MAPE: {best_mape:.2%}")

        # Retrain winning model on the COMPLETE dataset prior to future horizon projection
        logger.info(f"Retraining winning model '{best_model_name}' on complete dataset...")
        winning_instance.fit(df, date_col, target_col, freq=freq)

        rationale = (
            f"The '{best_model_name}' was selected as the optimal forecasting architecture "
            f"after achieving the lowest Mean Absolute Percentage Error (MAPE: {best_mape:.2%}) "
            f"and RMSE of {all_metrics[best_model_name].get('RMSE', 0.0):,.2f} on out-of-sample holdout validation."
        )

        return {
            "winning_model_instance": winning_instance,
            "winning_model_name": best_model_name,
            "selection_rationale": rationale,
            "best_metrics": all_metrics[best_model_name],
            "all_model_metrics": all_metrics,
            "residuals": winning_residuals
        }

    def _compute_validation_metrics(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray
    ) -> Tuple[Dict[str, float], np.ndarray]:
        """
        Computes standard statistical metrics for backtest evaluation.
        """
        residuals = y_true - y_pred
        
        # Prevent division by zero in MAPE calculation
        non_zero_mask = y_true != 0
        if np.any(non_zero_mask):
            mape = float(np.mean(np.abs(residuals[non_zero_mask] / y_true[non_zero_mask])))
        else:
            mape = 0.0

        mae = float(np.mean(np.abs(residuals)))
        rmse = float(np.sqrt(np.mean(residuals ** 2)))

        # R-squared calculation
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        ss_res = np.sum(residuals ** 2)
        r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

        metrics = {
            "MAPE": round(mape, 4),
            "RMSE": round(rmse, 2),
            "MAE": round(mae, 2),
            "R2": round(r2, 4)
        }

        return metrics, residuals
