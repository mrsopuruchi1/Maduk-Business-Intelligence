"""
Maduk Business Intelligence - Data Profiler
============================================
File: backend/services/ai_prediction_pipeline/data_profiler.py

Purpose:
    Generates structural metadata, data types, missingness, and
    statistical health checks without allowing problematic columns
    (boolean, infinite, malformed, or mixed-type data) to crash
    the prediction pipeline.
"""

import logging
from typing import Dict, Any

import numpy as np
import pandas as pd

logger = logging.getLogger("MadukBI.DataProfiler")


class DataProfiler:
    """
    Generates structural metadata, data types, missingness,
    and statistical health checks.

    The profiler is intentionally defensive because raw business
    datasets may contain:
        - Boolean columns
        - NaN values
        - Infinite values
        - Mixed data types
        - Date strings
        - Numeric columns stored as strings
        - Malformed values
    """

    def generate_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Profiles the input DataFrame.

        Args:
            df: Raw input DataFrame.

        Returns:
            Dict containing:
                - rows
                - columns
                - total_cells
                - total_missing_values
                - overall_missing_percentage
                - memory_usage_mb
                - column_profiles
        """

        logger.info("Generating dataset health profile...")

        if df is None:
            raise ValueError("DataProfiler received a None DataFrame.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                f"DataProfiler expected a pandas DataFrame, "
                f"received {type(df).__name__}."
            )

        total_rows, total_cols = df.shape
        total_cells = total_rows * total_cols

        # ---------------------------------------------------------
        # Overall missing-value statistics
        # ---------------------------------------------------------
        try:
            missing_cells = int(df.isnull().sum().sum())
        except Exception as exc:
            logger.warning(
                "Could not calculate total missing values: %s",
                exc
            )
            missing_cells = 0

        missing_percentage = (
            float((missing_cells / total_cells) * 100)
            if total_cells > 0
            else 0.0
        )

        column_profiles: Dict[str, Dict[str, Any]] = {}

        # ---------------------------------------------------------
        # Profile every column independently
        # ---------------------------------------------------------
        for col in df.columns:
            try:
                series = df[col]

                null_count = int(series.isnull().sum())

                # IMPORTANT:
                # bool is technically treated as numeric by some
                # pandas/numpy operations, but it should NOT be
                # passed through numeric statistical calculations.
                is_bool = pd.api.types.is_bool_dtype(series)

                is_num = (
                    pd.api.types.is_numeric_dtype(series)
                    and not is_bool
                )

                is_dt = (
                    pd.api.types.is_datetime64_any_dtype(series)
                    or self._can_parse_datetime(series)
                )

                profile: Dict[str, Any] = {
                    "dtype": str(series.dtype),
                    "null_count": null_count,
                    "null_percentage": (
                        float((null_count / total_rows) * 100)
                        if total_rows > 0
                        else 0.0
                    ),
                    "unique_values": int(series.nunique(dropna=True)),
                    "is_numeric": bool(is_num),
                    "is_boolean": bool(is_bool),
                    "is_datetime": bool(is_dt),
                }

                # -------------------------------------------------
                # Numeric statistics
                # -------------------------------------------------
                if is_num:
                    self._add_numeric_statistics(
                        profile=profile,
                        series=series,
                        column_name=str(col),
                    )

                # -------------------------------------------------
                # Datetime statistics
                # -------------------------------------------------
                elif is_dt:
                    self._add_datetime_statistics(
                        profile=profile,
                        series=series,
                        column_name=str(col),
                    )

                column_profiles[str(col)] = profile

            except Exception as exc:
                # A single malformed column must never terminate
                # the complete profiling operation.
                logger.warning(
                    "Could not completely profile column '%s': %s",
                    col,
                    exc,
                )

                column_profiles[str(col)] = {
                    "dtype": str(df[col].dtype),
                    "null_count": int(df[col].isnull().sum()),
                    "null_percentage": (
                        float(
                            (df[col].isnull().sum() / total_rows) * 100
                        )
                        if total_rows > 0
                        else 0.0
                    ),
                    "unique_values": int(
                        df[col].nunique(dropna=True)
                    ),
                    "is_numeric": False,
                    "is_boolean": bool(
                        pd.api.types.is_bool_dtype(df[col])
                    ),
                    "is_datetime": False,
                    "profile_error": str(exc),
                }

        # ---------------------------------------------------------
        # Memory usage
        # ---------------------------------------------------------
        try:
            memory_usage_mb = round(
                df.memory_usage(deep=True).sum()
                / (1024 * 1024),
                3,
            )
        except Exception as exc:
            logger.warning(
                "Could not calculate memory usage: %s",
                exc,
            )
            memory_usage_mb = 0.0

        logger.info(
            "Dataset profile generated successfully: "
            "rows=%s, columns=%s, missing_values=%s",
            total_rows,
            total_cols,
            missing_cells,
        )

        return {
            "rows": total_rows,
            "columns": total_cols,
            "total_cells": total_cells,
            "total_missing_values": missing_cells,
            "overall_missing_percentage": round(
                missing_percentage,
                2,
            ),
            "memory_usage_mb": memory_usage_mb,
            "column_profiles": column_profiles,
        }

    # =============================================================
    # NUMERIC STATISTICS
    # =============================================================

    def _add_numeric_statistics(
        self,
        profile: Dict[str, Any],
        series: pd.Series,
        column_name: str,
    ) -> None:
        """
        Safely calculates numeric statistics.

        Boolean columns are excluded before this method is called.

        Infinite values are converted to NaN so that quantile,
        mean, median, and percentile calculations remain stable.
        """

        try:
            # Convert safely to numeric.
            numeric_series = pd.to_numeric(
                series,
                errors="coerce",
            )

            # Remove +/- infinity.
            numeric_series = numeric_series.replace(
                [np.inf, -np.inf],
                np.nan,
            )

            numeric_series = numeric_series.dropna()

            if numeric_series.empty:
                logger.debug(
                    "No valid numeric values available for column '%s'.",
                    column_name,
                )
                return

            # Convert to float64 explicitly.
            #
            # This is important because it prevents boolean/object
            # values from reaching NumPy percentile operations.
            numeric_values = numeric_series.astype(
                np.float64,
                copy=False,
            )

            profile["mean"] = float(
                numeric_values.mean()
            )

            profile["std"] = (
                float(numeric_values.std())
                if len(numeric_values) > 1
                else 0.0
            )

            profile["min"] = float(
                numeric_values.min()
            )

            # -----------------------------------------------------
            # Safe quantile calculations
            # -----------------------------------------------------
            profile["p25"] = float(
                numeric_values.quantile(0.25)
            )

            profile["median"] = float(
                numeric_values.quantile(0.50)
            )

            profile["p75"] = float(
                numeric_values.quantile(0.75)
            )

            profile["max"] = float(
                numeric_values.max()
            )

            profile["skewness"] = (
                float(numeric_values.skew())
                if len(numeric_values) > 2
                else 0.0
            )

        except Exception as exc:
            # Do NOT allow one bad numeric column to crash
            # DataProfiler or the entire forecasting pipeline.
            logger.warning(
                "Numeric statistics failed for column '%s': %s",
                column_name,
                exc,
            )

            profile["statistics_error"] = str(exc)

    # =============================================================
    # DATETIME STATISTICS
    # =============================================================

    def _add_datetime_statistics(
        self,
        profile: Dict[str, Any],
        series: pd.Series,
        column_name: str,
    ) -> None:
        """Safely calculates minimum and maximum dates."""

        try:
            dt_series = pd.to_datetime(
                series,
                errors="coerce",
            ).dropna()

            if dt_series.empty:
                return

            profile.update(
                {
                    "min_date": str(dt_series.min()),
                    "max_date": str(dt_series.max()),
                }
            )

        except Exception as exc:
            logger.warning(
                "Datetime statistics failed for column '%s': %s",
                column_name,
                exc,
            )

            profile["datetime_error"] = str(exc)

    # =============================================================
    # DATETIME DETECTION
    # =============================================================

    def _can_parse_datetime(
        self,
        series: pd.Series,
    ) -> bool:
        """
        Determines whether a non-datetime column contains
        sufficiently parseable date values.

        A small sample is used for performance, but parsing must
        succeed for a high proportion of the sample.

        Numeric columns are deliberately excluded because numbers
        such as transaction IDs can otherwise be interpreted as
        timestamps.
        """

        # Already a datetime column.
        if pd.api.types.is_datetime64_any_dtype(series):
            return True

        # Never interpret numeric or boolean columns as dates.
        if (
            pd.api.types.is_numeric_dtype(series)
            or pd.api.types.is_bool_dtype(series)
        ):
            return False

        sample = series.dropna().head(20)

        if sample.empty:
            return False

        try:
            parsed = pd.to_datetime(
                sample,
                errors="coerce",
            )

            valid_count = int(parsed.notna().sum())

            if valid_count == 0:
                return False

            # Require at least 80% of sampled values to be valid
            # dates. This reduces false positives from ordinary
            # text columns.
            parse_ratio = valid_count / len(sample)

            if parse_ratio < 0.80:
                return False

            return True

        except (
            ValueError,
            TypeError,
            OverflowError,
        ):
            return False