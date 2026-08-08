"""
Maduk Business Intelligence - Time Series Detector
==================================================
File: backend/services/ai_prediction_pipeline/time_series_detector.py
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger("MadukBI.TimeSeriesDetector")


class TimeSeriesDetector:
    """Detects target variables, datetime axes, and sampling frequencies."""

    def detect_structure(
        self, 
        df: pd.DataFrame, 
        date_col: Optional[str] = None, 
        target_col: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Identifies date and target columns and validates time-series feasibility.

        Args:
            df: Input DataFrame.
            date_col: Explicit date column name (optional).
            target_col: Explicit target column name (optional).

        Returns:
            Dict with validity status, resolved column names, and detected frequency.
        """
        logger.info("Detecting time series metadata...")
        
        # Resolve Date Column
        resolved_date_col = date_col
        if not resolved_date_col:
            for col in df.columns:
                if "date" in col or "time" in col or "year" in col or "month" in col:
                    resolved_date_col = col
                    break
            if not resolved_date_col:
                for col in df.columns:
                    if self._try_parse_dates(df[col]):
                        resolved_date_col = col
                        break

        if not resolved_date_col:
            return {
                "is_valid_time_series": False,
                "reason": "No parseable datetime column identified."
            }

        # Resolve Target Column
        resolved_target_col = target_col
        numeric_cols = [c for c in df.select_dtypes(include=['number']).columns if c != resolved_date_col]
        
        if not resolved_target_col:
            priority_keywords = ["revenue", "sales", "target", "value", "demand", "volume", "amount"]
            for kw in priority_keywords:
                match = [c for c in numeric_cols if kw in c]
                if match:
                    resolved_target_col = match[0]
                    break
            if not resolved_target_col and numeric_cols:
                resolved_target_col = numeric_cols[0]

        if not resolved_target_col or resolved_target_col not in df.columns:
            return {
                "is_valid_time_series": False,
                "reason": "No numeric target column identified."
            }

        # Validate Date Parsing and Sort Sequence
        try:
            parsed_dates = pd.to_datetime(df[resolved_date_col], errors='coerce')
            if parsed_dates.isnull().sum() / len(parsed_dates) > 0.3:
                return {
                    "is_valid_time_series": False,
                    "reason": f"Column '{resolved_date_col}' has >30% unparseable date values."
                }
        except Exception as e:
            return {
                "is_valid_time_series": False,
                "reason": f"Failed to parse datetime column: {str(e)}"
            }

        # Estimate Frequency
        sorted_dates = parsed_dates.dropna().sort_values()
        detected_freq = pd.infer_freq(sorted_dates)
        
        if not detected_freq:
            # Manual fallback estimation based on median days difference
            diff_days = sorted_dates.diff().dt.days.median()
            if diff_days <= 1:
                detected_freq = "D"
            elif 6 <= diff_days <= 8:
                detected_freq = "W"
            elif 27 <= diff_days <= 32:
                detected_freq = "MS"
            elif 88 <= diff_days <= 93:
                detected_freq = "QS"
            elif 360 <= diff_days <= 366:
                detected_freq = "YS"
            else:
                detected_freq = "D"

        return {
            "is_valid_time_series": True,
            "date_column": resolved_date_col,
            "target_column": resolved_target_col,
            "frequency": detected_freq,
            "total_observations": len(df)
        }

    def _try_parse_dates(self, series: pd.Series) -> bool:
        if pd.api.types.is_numeric_dtype(series):
            return False
        try:
            sample = series.dropna().head(10)
            if sample.empty:
                return False
            pd.to_datetime(sample, errors='raise')
            return True
        except Exception:
            return False
