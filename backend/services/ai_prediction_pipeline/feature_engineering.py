"""
Maduk Business Intelligence - Feature Engineering
==============================================
File: backend/services/ai_prediction_pipeline/feature_engineering.py
"""

import logging
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger("MadukBI.FeatureEngineering")


class FeatureEngineering:
    """Generates lag, rolling, calendar, and seasonal features for time series forecasting."""

    def transform(
        self, 
        df: pd.DataFrame, 
        date_col: str, 
        target_col: str, 
        freq: str = "MS"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Transforms clean time-series data by constructing predictive features.

        Args:
            df: Cleaned input DataFrame.
            date_col: Resolved date column name.
            target_col: Resolved target column name.
            freq: Time series frequency string.

        Returns:
            Tuple containing (transformed_df, feature_metadata_dict).
        """
        logger.info("Generating predictive features (lags, rolling averages, seasonality)...")
        
        # Work on sorted data copy
        transformed_df = df.copy()
        transformed_df[date_col] = pd.to_datetime(transformed_df[date_col])
        transformed_df = transformed_df.sort_values(by=date_col).reset_index(drop=True)

        generated_features = []

        # 1. Calendar Features
        dates = transformed_df[date_col]
        transformed_df["year"] = dates.dt.year
        transformed_df["month"] = dates.dt.month
        transformed_df["day"] = dates.dt.day
        transformed_df["dayofweek"] = dates.dt.dayofweek
        transformed_df["quarter"] = dates.dt.quarter
        transformed_df["is_month_end"] = dates.dt.is_month_end.astype(int)
        generated_features.extend(["year", "month", "day", "dayofweek", "quarter", "is_month_end"])

        # 2. Cyclical Encodings for Month and Day of Week
        transformed_df["sin_month"] = np.sin(2 * np.pi * transformed_df["month"] / 12.0)
        transformed_df["cos_month"] = np.cos(2 * np.pi * transformed_df["month"] / 12.0)
        generated_features.extend(["sin_month", "cos_month"])

        # 3. Autoregressive Lag Features
        lag_steps = [1, 2, 3, 6, 12] if len(transformed_df) >= 24 else [1, 2, 3]
        for lag in lag_steps:
            col_name = f"{target_col}_lag_{lag}"
            transformed_df[col_name] = transformed_df[target_col].shift(lag)
            generated_features.append(col_name)

        # 4. Rolling Window Statistics
        window_sizes = [3, 6] if len(transformed_df) >= 12 else [2, 3]
        for w in window_sizes:
            mean_col = f"{target_col}_rolling_mean_{w}"
            std_col = f"{target_col}_rolling_std_{w}"
            # Shift by 1 to prevent data leakage from current observed target
            shifted_target = transformed_df[target_col].shift(1)
            transformed_df[mean_col] = shifted_target.rolling(window=w).mean()
            transformed_df[std_col] = shifted_target.rolling(window=w).std()
            generated_features.extend([mean_col, std_col])

        # Drop initial rows containing NaNs created by lag and rolling operations
        transformed_df = transformed_df.bfill().ffill()

        metadata = {
            "total_features_created": len(generated_features),
            "feature_names": generated_features,
            "lags_applied": lag_steps,
            "rolling_windows_applied": window_sizes
        }

        return transformed_df, metadata
