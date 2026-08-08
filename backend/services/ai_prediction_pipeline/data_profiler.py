"""
Maduk Business Intelligence - Data Profiler
==========================================
File: backend/services/ai_prediction_pipeline/data_profiler.py
"""

import logging
from typing import Dict, Any
import numpy as np
import pandas as pd

logger = logging.getLogger("MadukBI.DataProfiler")


class DataProfiler:
    """Generates structural metadata, data types, missingness, and statistical health checks."""

    def generate_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Profiles the input DataFrame.

        Args:
            df: Raw input DataFrame.

        Returns:
            Dict containing shape, missingness summary, memory footprint, and column metrics.
        """
        logger.info("Generating dataset health profile...")
        total_rows, total_cols = df.shape
        total_cells = total_rows * total_cols
        missing_cells = int(df.isnull().sum().sum())
        missing_percentage = float((missing_cells / total_cells) * 100) if total_cells > 0 else 0.0

        column_profiles = {}
        for col in df.columns:
            series = df[col]
            null_count = int(series.isnull().sum())
            is_num = pd.api.types.is_numeric_dtype(series)
            is_dt = pd.api.types.is_datetime64_any_dtype(series) or self._can_parse_datetime(series)

            profile = {
                "dtype": str(series.dtype),
                "null_count": null_count,
                "null_percentage": float((null_count / total_rows) * 100) if total_rows > 0 else 0.0,
                "unique_values": int(series.nunique()),
                "is_numeric": is_num,
                "is_datetime": is_dt,
            }

            if is_num and not series.dropna().empty:
                profile.update({
                    "mean": float(series.mean()),
                    "std": float(series.std()) if len(series.dropna()) > 1 else 0.0,
                    "min": float(series.min()),
                    "p25": float(series.quantile(0.25)),
                    "median": float(series.median()),
                    "p75": float(series.quantile(0.75)),
                    "max": float(series.max()),
                    "skewness": float(series.skew()) if len(series.dropna()) > 2 else 0.0
                })
            elif is_dt and not series.dropna().empty:
                dt_series = pd.to_datetime(series, errors='coerce').dropna()
                if not dt_series.empty:
                    profile.update({
                        "min_date": str(dt_series.min()),
                        "max_date": str(dt_series.max())
                    })

            column_profiles[str(col)] = profile

        return {
            "rows": total_rows,
            "columns": total_cols,
            "total_cells": total_cells,
            "total_missing_values": missing_cells,
            "overall_missing_percentage": round(missing_percentage, 2),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 3),
            "column_profiles": column_profiles
        }

    def _can_parse_datetime(self, series: pd.Series) -> bool:
        """Determines if a non-datetime column contains parseable dates."""
        if pd.api.types.is_numeric_dtype(series):
            return False
        sample = series.dropna().head(20)
        if sample.empty:
            return False
        try:
            pd.to_datetime(sample, errors='raise')
            return True
        except (ValueError, TypeError, OverflowError):
            return False
