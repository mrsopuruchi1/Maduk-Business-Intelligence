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
        logger.info("Generating dataset health profile...")
        total_rows, total_cols = df.shape
        total_cells = total_rows * total_cols
        missing_cells = int(df.isnull().sum().sum())
        missing_percentage = (missing_cells / total_cells) * 100 if total_cells else 0.0
        column_profiles = {}

        for col in df.columns:
            series = df[col]
            null_count = int(series.isnull().sum())
            is_num = pd.api.types.is_numeric_dtype(series)
            is_dt = pd.api.types.is_datetime64_any_dtype(series) or self._can_parse_datetime(series)

            profile = {
                "dtype": str(series.dtype),
                "null_count": null_count,
                "null_percentage": (null_count / total_rows) * 100 if total_rows else 0.0,
                "unique_values": int(series.nunique(dropna=True)),
                "is_numeric": is_num,
                "is_datetime": is_dt,
            }

            if is_num:
                numeric = pd.to_numeric(series, errors="coerce").replace(
                    [np.inf, -np.inf], np.nan
                ).dropna()
                if not numeric.empty:
                    profile.update({
                        "mean": float(numeric.mean()),
                        "std": float(numeric.std()) if len(numeric) > 1 else 0.0,
                        "min": float(numeric.min()),
                        "p25": float(numeric.quantile(0.25)),
                        "median": float(numeric.median()),
                        "p75": float(numeric.quantile(0.75)),
                        "max": float(numeric.max()),
                        "skewness": float(numeric.skew()) if len(numeric) > 2 else 0.0,
                    })
            elif is_dt:
                dt_series = pd.to_datetime(series, errors="coerce").dropna()
                if not dt_series.empty:
                    profile.update({
                        "min_date": str(dt_series.min()),
                        "max_date": str(dt_series.max()),
                    })

            column_profiles[str(col)] = profile

        return {
            "rows": total_rows,
            "columns": total_cols,
            "total_cells": total_cells,
            "total_missing_values": missing_cells,
            "overall_missing_percentage": round(float(missing_percentage), 2),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 3),
            "column_profiles": column_profiles,
        }

    def _can_parse_datetime(self, series: pd.Series) -> bool:
        if pd.api.types.is_numeric_dtype(series):
            return False
        sample = series.dropna().head(20)
        if sample.empty:
            return False
        try:
            pd.to_datetime(sample, errors="raise")
            return True
        except (ValueError, TypeError, OverflowError):
            return False
