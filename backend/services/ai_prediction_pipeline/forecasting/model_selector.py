"""
Maduk Business Intelligence - Resource-Safe Dynamic Model Selector
====================================================================
File: backend/services/ai_prediction_pipeline/forecasting/model_selector.py

Selects the best available forecasting model using a chronological holdout.
The production default intentionally excludes Prophet, LSTM and SARIMA because
Maduk BI's Render free backend has a very small CPU/memory budget.

Optional models can be enabled with environment variables without changing code:
    MADUK_MODEL_SET=random_forest,lightgbm
    MADUK_MODEL_SET=random_forest,lightgbm,sarima
"""

from __future__ import annotations

import gc
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .base_model import BaseForecaster
from .random_forest_model import RandomForestForecaster
from .lightgbm_model import LightGBMForecaster
from .xgboost_model import XGBoostForecaster

logger = logging.getLogger("MadukBI.ModelSelector")


class ModelSelector:
    """Resource-safe automated model selection engine."""

    def __init__(
        self,
        cv_evaluator: Optional[Any] = None,
        metrics_evaluator: Optional[Any] = None,
        candidate_models: Optional[List[BaseForecaster]] = None,
    ):
        self.cv_evaluator = cv_evaluator
        self.metrics_evaluator = metrics_evaluator
        self.candidate_models = (
            candidate_models
            if candidate_models is not None
            else self._get_default_candidate_models()
        )

    def _get_default_candidate_models(self) -> List[BaseForecaster]:
        """
        Build the production candidate set.

        Prophet is deliberately NOT imported or instantiated. LSTM is also
        excluded because it is unnecessary for the low-resource deployment.
        SARIMA is opt-in because its fitting can be considerably slower on a
        small Render instance.
        """
        factories = {
            "random_forest": (RandomForestForecaster, "Random Forest"),
            "lightgbm": (LightGBMForecaster, "LightGBM"),
            "xgboost": (XGBoostForecaster, "XGBoost"),
        }

        # SARIMA is deliberately opt-in on the 512 MB / low-CPU deployment.
        if os.getenv("MADUK_ENABLE_SARIMA", "false").strip().lower() in {
            "1", "true", "yes", "on"
        }:
            from .sarima_model import SARIMAForecaster
            factories["sarima"] = (SARIMAForecaster, "SARIMA")

        configured = os.getenv(
            "MADUK_MODEL_SET",
            "random_forest,lightgbm",
        )
        requested = [x.strip().lower() for x in configured.split(",") if x.strip()]

        models: List[BaseForecaster] = []
        for key in requested:
            factory_info = factories.get(key)
            if factory_info is None:
                logger.warning("Ignoring unsupported/disabled model '%s'.", key)
                continue

            model_cls, display_name = factory_info
            try:
                models.append(model_cls())
                logger.info("Registered candidate model: %s", display_name)
            except Exception as exc:
                logger.warning(
                    "Candidate model '%s' disabled during initialization: %s",
                    display_name,
                    exc,
                )

        if not models:
            raise RuntimeError(
                "No forecasting models are available. Check the installed "
                "model dependencies and MADUK_MODEL_SET."
            )

        return models

    def select_best_model(
        self,
        df: pd.DataFrame,
        date_col: str,
        target_col: str,
        freq: str = "MS",
        forecast_horizon: int = 12,
        candidate_models: Optional[List[BaseForecaster]] = None,
    ) -> Dict[str, Any]:
        """Evaluate candidates on a chronological holdout and return the winner."""
        if df is None or df.empty or len(df) < 5:
            raise ValueError(
                "Dataset contains insufficient observations for model cross-validation."
            )

        models = candidate_models if candidate_models is not None else self.candidate_models
        if not models:
            raise RuntimeError("No forecasting candidate models are available.")

        test_size = min(max(1, int(forecast_horizon)), max(1, int(len(df) * 0.25)))
        train_df = df.iloc[:-test_size].copy()
        test_df = df.iloc[-test_size:].copy()

        if train_df.empty or test_df.empty:
            raise ValueError("Unable to create a valid chronological training/validation split.")

        all_metrics: Dict[str, Dict[str, Any]] = {}
        best_model_name: Optional[str] = None
        best_mape = float("inf")
        winning_instance: Optional[BaseForecaster] = None
        winning_residuals = np.array([], dtype=float)

        logger.info(
            "Evaluating %d resource-safe candidate model(s); train=%d, validation=%d",
            len(models),
            len(train_df),
            len(test_df),
        )

        for index, model in enumerate(models, start=1):
            model_name = getattr(model, "name", model.__class__.__name__)
            logger.info(
                "[%d/%d] Cross-validating candidate model: '%s'...",
                index,
                len(models),
                model_name,
            )

            try:
                model.fit(train_df, date_col, target_col, freq=freq)
                logger.info("[%d/%d] '%s' fit completed.", index, len(models), model_name)

                preds_df = model.predict_horizon(horizon=len(test_df), freq=freq)
                if preds_df is None or preds_df.empty or "forecast" not in preds_df.columns:
                    raise ValueError("Model returned no usable forecast values.")

                y_true = pd.to_numeric(test_df[target_col], errors="coerce").to_numpy(dtype=float)
                y_pred = pd.to_numeric(preds_df["forecast"], errors="coerce").to_numpy(dtype=float)

                n = min(len(y_true), len(y_pred))
                if n == 0:
                    raise ValueError("Model returned an empty validation forecast.")

                y_true = y_true[:n]
                y_pred = y_pred[:n]
                valid = np.isfinite(y_true) & np.isfinite(y_pred)
                if not np.any(valid):
                    raise ValueError("Validation forecast contains no finite numeric values.")

                metrics, residuals = self._compute_validation_metrics(
                    y_true[valid], y_pred[valid]
                )
                all_metrics[model_name] = metrics

                mape = metrics.get("MAPE", float("inf"))
                logger.info(
                    "[%d/%d] '%s' validation complete: MAPE=%.2f%% RMSE=%.2f MAE=%.2f",
                    index,
                    len(models),
                    model_name,
                    mape * 100.0,
                    metrics.get("RMSE", float("inf")),
                    metrics.get("MAE", float("inf")),
                )

                if mape < best_mape:
                    best_mape = mape
                    best_model_name = model_name
                    winning_instance = model
                    winning_residuals = residuals

            except Exception as exc:
                logger.exception(
                    "Error evaluating candidate model '%s': %s",
                    model_name,
                    exc,
                )
                all_metrics[model_name] = {
                    "error": str(exc),
                    "MAPE": float("inf"),
                    "RMSE": float("inf"),
                    "MAE": float("inf"),
                    "R2": float("-inf"),
                }
            finally:
                # Encourage native ML/statistical libraries to release temporary
                # arrays between candidates on the small Render instance.
                gc.collect()

        if winning_instance is None or best_model_name is None:
            raise RuntimeError(
                "All available forecasting models failed during cross-validation."
            )

        logger.info(
            "Selected Winning Model: '%s' with MAPE: %.2f%%",
            best_model_name,
            best_mape * 100.0,
        )

        # Do not retain fitted losing models between API requests. Rebuild a
        # fresh candidate registry for the next request while returning the
        # current winning instance to the pipeline. This avoids both memory
        # retention and accidentally evaluating only the previous winner.
        self.candidate_models = self._get_default_candidate_models()
        gc.collect()

        best_metrics = all_metrics[best_model_name]
        rationale = (
            f"The '{best_model_name}' was selected as the optimal forecasting "
            f"architecture after achieving the lowest Mean Absolute Percentage "
            f"Error (MAPE: {best_mape:.2%}) and RMSE of "
            f"{best_metrics.get('RMSE', 0.0):,.2f} on out-of-sample holdout validation."
        )

        return {
            "winning_model_instance": winning_instance,
            "winning_model_name": best_model_name,
            "selection_rationale": rationale,
            "best_metrics": best_metrics,
            "all_model_metrics": all_metrics,
            "residuals": winning_residuals,
        }

    @staticmethod
    def _compute_validation_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Tuple[Dict[str, float], np.ndarray]:
        """Compute MAPE, RMSE, MAE and R2 safely."""
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)
        residuals = y_true - y_pred

        non_zero = y_true != 0
        if np.any(non_zero):
            mape = float(
                np.mean(np.abs(residuals[non_zero] / y_true[non_zero]))
            )
        else:
            mape = 0.0

        mae = float(np.mean(np.abs(residuals)))
        rmse = float(np.sqrt(np.mean(residuals ** 2)))

        ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
        ss_res = float(np.sum(residuals ** 2))
        r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

        return {
            "MAPE": round(mape, 4),
            "RMSE": round(rmse, 2),
            "MAE": round(mae, 2),
            "R2": round(r2, 4),
        }, residuals
