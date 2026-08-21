"""
Maduk Business Intelligence - Data Validator
=============================================
File: backend/services/ai_prediction_pipeline/data_validator.py

Production-safe dataset validation and cleaning for the Maduk BI
AI Prediction Pipeline.
"""

import logging
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

logger = logging.getLogger("MadukBI.DataValidator")


class DataValidator:
    """
    Cleans datasets, handles missing/infinite values, performs lightweight
    data-quality checks, and optionally evaluates time-series stationarity.

    The validator is intentionally lightweight so that large uploaded
    datasets do not cause unnecessary CPU/memory consumption on the backend.
    """

    def __init__(
        self,
        run_stationarity_tests: bool = True,
        stationarity_maxlag: int = 12,
        stationarity_sample_size: int = 1000,
    ):
        self.run_stationarity_tests = run_stationarity_tests
        self.stationarity_maxlag = stationarity_maxlag
        self.stationarity_sample_size = stationarity_sample_size

    def validate_and_clean(
        self,
        df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate and clean a raw DataFrame.

        Returns:
            Tuple containing:
                cleaned DataFrame
                data-quality report
        """

        logger.info("Executing data validation and cleaning procedures...")

        # ---------------------------------------------------------
        # 0. Basic input validation
        # ---------------------------------------------------------
        if df is None:
            raise ValueError("Input dataset is None.")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input dataset must be a pandas DataFrame.")

        if df.empty:
            raise ValueError("Input dataset is empty.")

        logger.info(
            "Validator received dataset: rows=%s, columns=%s",
            len(df),
            len(df.columns),
        )

        clean_df = df.copy()

        # ---------------------------------------------------------
        # 1. Standardize column headers FIRST
        # ---------------------------------------------------------
        clean_df.columns = [
            str(c).strip().lower().replace(" ", "_").replace("-", "_")
            for c in clean_df.columns 
        ]

        logger.info(f"Column headers standardized: {list(clean_df.columns)}") 

        # Prevent duplicate column names after normalization.
        clean_df = self._make_unique_columns(clean_df)

        logger.info(
            "Normalized columns: %s",
            list(clean_df.columns)
        )

        # ---------------------------------------------------------
        # 2. Remove completely empty rows/columns
        # ---------------------------------------------------------
        before_empty_cleanup = clean_df.shape

        empty_columns = [
            col for col in clean_df.columns
            if clean_df[col].isna().all()
        ]

        if empty_columns:
            clean_df = clean_df.drop(columns=empty_columns)
            logger.warning(
                "Removed completely empty columns: %s",
                empty_columns
            )

        empty_rows = int(clean_df.isna().all(axis=1).sum())

        if empty_rows > 0:
            clean_df = clean_df.dropna(how="all")

        logger.info(
            "Empty-data cleanup complete. Shape: %s -> %s",
            before_empty_cleanup,
            clean_df.shape,
        )

        # ---------------------------------------------------------
        # 3. Deduplicate rows
        # ---------------------------------------------------------
        initial_rows = len(clean_df)

        clean_df = clean_df.drop_duplicates()

        duplicates_removed = initial_rows - len(clean_df)

        logger.info(
            "Duplicate cleanup complete. Removed %s duplicate rows.",
            duplicates_removed
        )

        # ---------------------------------------------------------
        # 4. Detect date columns and convert obvious date fields
        # ---------------------------------------------------------
        date_columns = []

        for col in clean_df.columns:
            col_lower = str(col).lower()

            if (
                col_lower == "date"
                or col_lower.endswith("_date")
                or col_lower in {
                    "datetime",
                    "timestamp",
                    "time",
                    "period"
                }
            ):
                try:
                    converted = pd.to_datetime(
                        clean_df[col],
                        errors="coerce"
                    )

                    valid_dates = converted.notna().sum()

                    if valid_dates >= max(
                        5,
                        int(len(clean_df) * 0.50)
                    ):
                        clean_df[col] = converted
                        date_columns.append(col)

                        logger.info(
                            "Detected date column: '%s' (%s valid values)",
                            col,
                            valid_dates
                        )

                except Exception as exc:
                    logger.warning(
                        "Could not convert column '%s' to datetime: %s",
                        col,
                        exc
                    )

        # ---------------------------------------------------------
        # 5. Identify numeric columns AFTER column normalization
        # ---------------------------------------------------------
        numeric_cols = list(
            clean_df.select_dtypes(
                include=[np.number]
            ).columns
        )

        logger.info(
            "Detected numeric columns: %s",
            numeric_cols
        )

        # ---------------------------------------------------------
        # 6. Replace infinite values
        # ---------------------------------------------------------
        infinite_values_replaced = 0

        if numeric_cols:
            numeric_block = clean_df[numeric_cols]

            infinite_mask = ~np.isfinite(
                numeric_block.to_numpy(dtype=float)
            )

            infinite_values_replaced = int(
                infinite_mask.sum()
            )

            if infinite_values_replaced > 0:
                clean_df[numeric_cols] = (
                    numeric_block.replace(
                        [np.inf, -np.inf],
                        np.nan
                    )
                )

                logger.warning(
                    "Replaced %s infinite numeric values with NaN.",
                    infinite_values_replaced
                )

        # ---------------------------------------------------------
        # 7. Missing-value analysis
        # ---------------------------------------------------------
        missing_before = int(clean_df.isna().sum().sum())

        missing_imputed = 0

        # Recalculate numeric columns after all transformations.
        numeric_cols = list(
            clean_df.select_dtypes(
                include=[np.number]
            ).columns
        )

        for col in numeric_cols:

            n_nulls = int(clean_df[col].isna().sum())

            if n_nulls == 0:
                continue

            # Time-series friendly interpolation/fill.
            try:
                clean_df[col] = (
                    clean_df[col]
                    .interpolate(
                        method="linear",
                        limit_direction="both"
                    )
                    .ffill()
                    .bfill()
                )
            except Exception as exc:
                logger.warning(
                    "Interpolation failed for '%s': %s. "
                    "Using median imputation.",
                    col,
                    exc
                )

                median_value = clean_df[col].median()

                if pd.notna(median_value):
                    clean_df[col] = clean_df[col].fillna(
                        median_value
                    )

            remaining_nulls = int(
                clean_df[col].isna().sum()
            )

            missing_imputed += max(
                0,
                n_nulls - remaining_nulls
            )

        # ---------------------------------------------------------
        # 8. Handle remaining non-numeric missing values
        # ---------------------------------------------------------
        categorical_cols = [
            col
            for col in clean_df.columns
            if col not in numeric_cols
            and col not in date_columns
        ]

        for col in categorical_cols:

            n_nulls = int(clean_df[col].isna().sum())

            if n_nulls == 0:
                continue

            mode = clean_df[col].mode(dropna=True)

            if not mode.empty:
                clean_df[col] = clean_df[col].fillna(
                    mode.iloc[0]
                )

            remaining_nulls = int(
                clean_df[col].isna().sum()
            )

            missing_imputed += max(
                0,
                n_nulls - remaining_nulls
            )

        missing_after = int(clean_df.isna().sum().sum())

        logger.info(
            "Missing-value handling complete: before=%s, "
            "imputed=%s, remaining=%s",
            missing_before,
            missing_imputed,
            missing_after,
        )

        # ---------------------------------------------------------
        # 9. Stationarity tests
        # ---------------------------------------------------------
        stationarity_results = {}

        if self.run_stationarity_tests and numeric_cols:

            logger.info(
                "Starting lightweight stationarity analysis..."
            )

            # Identifier columns should not be tested as time series.
            excluded_columns = {
                "id",
                "business_id",
                "customer_id",
                "user_id",
                "account_id",
                "transaction_id",
                "record_id",
            }

            stationarity_columns = [
                col
                for col in numeric_cols
                if str(col).lower() not in excluded_columns
            ]

            for col in stationarity_columns:

                try:
                    series = (
                        pd.to_numeric(
                            clean_df[col],
                            errors="coerce"
                        )
                        .replace(
                            [np.inf, -np.inf],
                            np.nan
                        )
                        .dropna()
                    )

                    if len(series) < 20:
                        continue

                    if series.nunique() <= 1:
                        continue

                    # Limit the workload on production servers.
                    if len(series) > self.stationarity_sample_size:
                        series = series.tail(
                            self.stationarity_sample_size
                        )

                    # ADF cannot use a lag >= approximately half
                    # of the available observations.
                    safe_maxlag = min(
                        self.stationarity_maxlag,
                        max(1, len(series) // 4)
                    )

                    adf_stat, p_val, used_lag, observations, _, _ = (
                        adfuller(
                            series,
                            maxlag=safe_maxlag,
                            autolag="AIC"
                        )
                    )

                    stationarity_results[col] = {
                        "adf_statistic": float(adf_stat),
                        "p_value": float(p_val),
                        "used_lag": int(used_lag),
                        "observations": int(observations),
                        "is_stationary": bool(
                            p_val < 0.05
                        ),
                    }

                except Exception as exc:

                    logger.warning(
                        "ADF test skipped for column '%s': %s",
                        col,
                        exc
                    )

            logger.info(
                "Stationarity analysis complete for %s columns.",
                len(stationarity_results)
            )

        else:
            logger.info(
                "Stationarity analysis disabled."
            )

        # ---------------------------------------------------------
        # 10. Final data-quality score
        # ---------------------------------------------------------
        total_cells = (
            clean_df.shape[0] *
            clean_df.shape[1]
        )

        missing_penalty = (
            missing_after / total_cells
            if total_cells > 0
            else 0.0
        )

        duplicate_penalty = (
            min(
                0.05,
                duplicates_removed / max(initial_rows, 1)
            )
        )

        quality_score = (
            1.0
            - missing_penalty
            - duplicate_penalty
        )

        quality_score = max(
            0.0,
            min(
                1.0,
                round(float(quality_score), 2)
            )
        )

        # ---------------------------------------------------------
        # 11. Final validation report
        # ---------------------------------------------------------
        quality_report = {
            "duplicates_removed": int(
                duplicates_removed
            ),
            "empty_rows_removed": int(
                empty_rows
            ),
            "empty_columns_removed": int(
                len(empty_columns)
            ),
            "missing_values_before": int(
                missing_before
            ),
            "missing_values_imputed": int(
                missing_imputed
            ),
            "missing_values_remaining": int(
                missing_after
            ),
            "infinite_values_replaced": int(
                infinite_values_replaced
            ),
            "date_columns_detected": date_columns,
            "numeric_columns_detected": numeric_cols,
            "quality_score": quality_score,
            "stationarity_tests": stationarity_results,
            "is_clean": bool(
                quality_score >= 0.70
            ),
        }

        logger.info(
            "Data validation completed successfully. "
            "Final shape=%s, quality_score=%s",
            clean_df.shape,
            quality_score,
        )

        return clean_df, quality_report

    @staticmethod
    def _make_unique_columns(
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Ensures normalized column names remain unique.

        Example:
            revenue, revenue -> revenue, revenue_2
        """

        columns = []
        counts = {}

        for column in df.columns:

            base = str(column)

            if base not in counts:
                counts[base] = 0
                columns.append(base)
            else:
                counts[base] += 1
                columns.append(
                    f"{base}_{counts[base] + 1}"
                )

        result = df.copy()
        result.columns = columns

        return result