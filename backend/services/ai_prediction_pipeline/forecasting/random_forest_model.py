"""
Maduk Business Intelligence - Random Forest Forecaster
======================================================
File: backend/services/ai_prediction_pipeline/forecasting/random_forest_model.py
"""

import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from .base_model import BaseForecaster

logger = logging.getLogger("MadukBI.RandomForestModel")


class RandomForestForecaster(BaseForecaster):
    """Ensemble Random Forest regressor for time series forecasting."""

    def __init__(self):
        super().__init__("Random Forest Regressor")
        self.model = None
        self.feature_cols: List[str] = []
        self.last_date = None
        self.target_col = None
        self.date_col = None
        self.importance_scores: Dict[str, float] = {}
        self.last_known_features: pd.DataFrame = pd.DataFrame()

    def fit(self, df: pd.DataFrame, date_col: str, target_col: str, freq: str = "MS") -> "RandomForestForecaster":
        logger.info("Fitting Random Forest model...")
        self.date_col = date_col
        self.target_col = target_col
        
        train_df = df.copy()
        train_df[date_col] = pd.to_datetime(train_df[date_col])
        train_df = train_df.sort_values(by=date_col).reset_index(drop=True)
        self.last_date = train_df[date_col].max()

        self.feature_cols = [c for c in train_df.columns if c not in [date_col, target_col]]
        
        X = train_df[self.feature_cols]
        y = train_df[target_col]

        # Store last known feature row for recursive rolling inference
        self.last_known_features = X.tail(1).copy()

        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=2,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X, y)
        self.is_fitted = True

        # Extract normalized Gini importance scores
        importances = self.model.feature_importances_
        total_imp = np.sum(importances) if np.sum(importances) > 0 else 1.0
        self.importance_scores = {
            col: float(imp / total_imp) for col, imp in zip(self.feature_cols, importances)
        }
        return self

    def predict_horizon(self, horizon: int, freq: str = "MS") -> pd.DataFrame:
        if not self.is_fitted:
            raise RuntimeError("Random Forest model must be fitted prior to predicting.")

        future_dates = pd.date_range(start=self.last_date, periods=horizon + 1, freq=freq)[1:]
        
        # Iterative prediction leveraging tree ensemble variance for prediction intervals
        preds = []
        estimator_preds = []
        
        # Prepare feature vector for horizon extrapolation
        current_input = self.last_known_features.values.copy()

        for _ in range(horizon):
            step_pred = float(self.model.predict(current_input)[0])
            preds.append(step_pred)
            
            # Predict across all trees in forest to estimate variance
            all_trees = np.array([tree.predict(current_input)[0] for tree in self.model.estimators_])
            estimator_preds.append(all_trees)

        preds_arr = np.array(preds)
        tree_stds = np.std(np.array(estimator_preds), axis=1)

        # 95% Confidence interval estimation from ensemble std deviation
        lower_bound = preds_arr - (1.96 * tree_stds)
        upper_bound = preds_arr + (1.96 * tree_stds)

        return pd.DataFrame({
            "date": future_dates,
            "forecast": preds_arr,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound
        })

    def get_feature_importance(self) -> Dict[str, float]:
        return dict(sorted(self.importance_scores.items(), key=lambda x: x[1], reverse=True))
