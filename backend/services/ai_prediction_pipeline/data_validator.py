"""
Maduk Business Intelligence - Data Validator
===========================================
File: backend/services/ai_prediction_pipeline/data_validator.py
"""

import logging
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

logger = logging.getLogger("MadukBI.DataValidator")


class DataValidator:
    """Cleans datasets, handles missing values, and checks time series stability."""

    def validate_and_clean(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validates, cleans, and generates a data quality report.

        Args:
            df: Raw DataFrame.

        Returns:
            Tuple containing (cleaned_df, quality_report_dict).
        """
        logger.info("Executing data validation and cleaning procedures...")
        clean_df = df.copy()
        
        # Deduplicate
        initial_rows = len(clean_df)
        clean_df = clean_df.drop_duplicates()
        duplicates_removed = initial_rows - len(clean_df)

        # Standardize column headers
        clean_df.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in clean_df.columns]

        # Handle Missing Values
        missing_imputed = 0
        numeric_cols = clean_df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            n_nulls = clean_df[col].isnull().sum()
            if n_nulls > 0:
                missing_imputed += int(n_nulls)
                # Forward-fill first for time-series continuity, then backward-fill for remaining edge nulls
                clean_df[col] = clean_df[col].ffill().bfill()

        # Check for numeric series stationarity using Augmented Dickey-Fuller
        stationarity_results = {}
        for col in numeric_cols:
            series = clean_df[col].dropna()
            if len(series) > 15 and series.nunique() > 1:
                try:
                    adf_stat, p_val, _, _, _, _ = adfuller(series, maxlag=None)
                    stationarity_results[col] = {
                        "adf_statistic": float(adf_stat),
                        "p_value": float(p_val),
                        "is_stationary": bool(p_val < 0.05)
                    }
                except Exception as e:
                    logger.debug(f"ADF test failed for column {col}: {e}")

        # Compute data quality score (0.0 - 1.0 scale)
        total_cells = clean_df.shape[0] * clean_df.shape[1]
        quality_score = 1.0 - (missing_imputed / total_cells) if total_cells > 0 else 1.0
        if duplicates_removed > 0:
            quality_score -= 0.05
        quality_score = max(0.0, round(float(quality_score), 2))

        quality_report = {
            "duplicates_removed": duplicates_removed,
            "missing_values_imputed": missing_imputed,
            "quality_score": quality_score,
            "stationarity_tests": stationarity_results,
            "is_clean": bool(quality_score > 0.70)
        }

        return clean_df, quality_report
