import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ============================================
# 🔥 SAFE NUMERIC CONVERSION
# ============================================
def safe_numeric_conversion(
    series: pd.Series,
    threshold: float = 0.7
) -> Optional[pd.Series]:
    """
    Convert series to numeric only if conversion quality is good.
    """

    try:
        converted = pd.to_numeric(
            series,
            errors="coerce"
        )

        valid_ratio = (
            converted.notna().sum()
            / max(len(series), 1)
        )

        if valid_ratio >= threshold:
            return converted

        return None

    except Exception:
        return None


# ============================================
# 🔥 SAFE DATETIME CONVERSION
# ============================================
def safe_datetime_conversion(
    series: pd.Series,
    threshold: float = 0.7
) -> Optional[pd.Series]:
    """
    Convert series to datetime only if conversion quality is good.
    """

    try:
        # ----------------------------------------
        # FIRST PASS → STANDARD FORMAT
        # ----------------------------------------
        converted = pd.to_datetime(
            series,
            errors="coerce",
            format="%Y-%m-%d"
        )

        valid_ratio = (
            converted.notna().sum()
            / max(len(series), 1)
        )

        # ----------------------------------------
        # SECOND PASS → SAFE DATETIME DETECTION
        # ----------------------------------------
        if valid_ratio < threshold:

            sample_values = (
                series
                .dropna()
                .astype(str)
                .head(20)
                .tolist()
            )

            date_patterns = [
                r"^\d{4}-\d{2}-\d{2}$",   # 2025-01-31
                r"^\d{2}/\d{2}/\d{4}$",   # 31/01/2025
                r"^\d{4}/\d{2}/\d{2}$",   # 2025/01/31
                r"^\d{2}-\d{2}-\d{4}$",   # 31-01-2025
            ]

            matches = 0

            for value in sample_values:

                for pattern in date_patterns:

                    if pd.notna(value):

                        import re

                        if re.match(pattern, value):
                            matches += 1
                            break

            # ----------------------------------------
            # ONLY PARSE IF CONFIDENCE IS HIGH
            # ----------------------------------------
            if (
                sample_values
                and (matches / len(sample_values)) >= 0.6
            ):

                possible_formats = [
                    "%Y-%m-%d",
                    "%d/%m/%Y",
                    "%Y/%m/%d",
                    "%d-%m-%Y"
                ]

                for fmt in possible_formats:

                    try:
                        converted = pd.to_datetime(
                            series,
                            errors="coerce",
                            format=fmt
                        )

                        valid_ratio = (
                            converted.notna().sum()
                            / max(len(series), 1)
                        )

                        if valid_ratio >= threshold:
                            return converted

                    except Exception:
                        continue

        # ----------------------------------------
        # RETURN BEST RESULT
        # ----------------------------------------
        if valid_ratio >= threshold:
            return converted

        return None

    except Exception:
        return None


# ============================================
# 🔥 TEXT NORMALIZATION
# ============================================
def normalize_text_column(
    series: pd.Series
) -> pd.Series:
    """
    Normalize text safely.
    """

    try:
        return (
            series
            .astype(str)
            .str.strip()
            .str.lower()
        )

    except Exception:
        return series


# ============================================
# 🧼 DATA CLEANING ENGINE (PRODUCTION READY)
# ============================================
def clean_data(
    df: pd.DataFrame,
    drop_duplicates: bool = True,
    handle_missing: str = "auto",
    fill_numeric: str = "median",
    fill_categorical: str = "mode",
    normalize_text: bool = True,
    convert_types: bool = True
) -> pd.DataFrame:
    """
    Decision Intelligence Data Cleaner

    Features:
    - Smart numeric conversion
    - Smart datetime inference
    - Robust missing value handling
    - Duplicate removal
    - Text normalization
    - Safer type inference
    - Prevents silent data corruption
    """

    try:
        # ============================================
        # SAFE COPY
        # ============================================
        df = df.copy()

        # ============================================
        # STANDARDIZE COLUMN NAMES
        # ============================================
        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(r"\s+", "_", regex=True)
        )

        # ============================================
        # REMOVE DUPLICATES
        # ============================================
        if drop_duplicates:

            before = len(df)

            df = df.drop_duplicates()

            removed = before - len(df)

            logger.info(
                f"Removed {removed} duplicate rows"
            )

        # ============================================
        # SMART TYPE CONVERSION
        # ============================================
        if convert_types:

            for col in df.columns:

                try:
                    original_series = df[col]

                    # ----------------------------------------
                    # SKIP ALREADY NUMERIC
                    # ----------------------------------------
                    if pd.api.types.is_numeric_dtype(
                        original_series
                    ):
                        continue

                    # ----------------------------------------
                    # SKIP ALREADY DATETIME
                    # ----------------------------------------
                    if pd.api.types.is_datetime64_any_dtype(
                        original_series
                    ):
                        continue

                    # ----------------------------------------
                    # TRY NUMERIC CONVERSION
                    # ----------------------------------------
                    numeric_series = (
                        safe_numeric_conversion(
                            original_series
                        )
                    )

                    if numeric_series is not None:

                        df[col] = numeric_series

                        logger.info(
                            f"Converted '{col}' to numeric"
                        )

                        continue

                    # ----------------------------------------
                    # TRY DATETIME CONVERSION
                    # ----------------------------------------
                    datetime_series = (
                        safe_datetime_conversion(
                            original_series
                        )
                    )

                    if datetime_series is not None:

                        df[col] = datetime_series

                        logger.info(
                            f"Converted '{col}' to datetime"
                        )

                        continue

                    # ----------------------------------------
                    # KEEP AS OBJECT
                    # ----------------------------------------
                    df[col] = (
                        original_series
                        .astype("object")
                    )

                except Exception as e:
                    logger.warning(
                        f"Type conversion failed for "
                        f"{col}: {str(e)}"
                    )

        # ============================================
        # HANDLE MISSING VALUES
        # ============================================
        if handle_missing == "drop":

            before = len(df)

            df = df.dropna()

            logger.info(
                f"Dropped {before - len(df)} rows "
                f"with missing values"
            )

        elif handle_missing in ["auto", "fill"]:

            numeric_cols = (
                df.select_dtypes(include=np.number)
                .columns
                .tolist()
            )

            categorical_cols = (
                df.select_dtypes(include=["object"])
                .columns
                .tolist()
            )

            datetime_cols = (
                df.select_dtypes(
                    include=[
                        "datetime64[ns]",
                        "datetime64"
                    ]
                )
                .columns
                .tolist()
            )

            # ----------------------------------------
            # NUMERIC COLUMNS
            # ----------------------------------------
            for col in numeric_cols:

                try:
                    if df[col].isnull().sum() == 0:
                        continue

                    if fill_numeric == "mean":

                        fill_value = df[col].mean()

                    elif fill_numeric == "median":

                        fill_value = df[col].median()

                    else:

                        fill_value = 0

                    df[col] = df[col].fillna(
                        fill_value
                    )

                except Exception as e:
                    logger.warning(
                        f"Numeric fill failed for "
                        f"{col}: {str(e)}"
                    )

            # ----------------------------------------
            # CATEGORICAL COLUMNS
            # ----------------------------------------
            for col in categorical_cols:

                try:
                    if df[col].isnull().sum() == 0:
                        continue

                    if fill_categorical == "mode":

                        mode = df[col].mode()

                        fill_value = (
                            mode.iloc[0]
                            if not mode.empty
                            else "unknown"
                        )

                    else:

                        fill_value = "unknown"

                    df[col] = df[col].fillna(
                        fill_value
                    )

                except Exception as e:
                    logger.warning(
                        f"Categorical fill failed for "
                        f"{col}: {str(e)}"
                    )

            # ----------------------------------------
            # DATETIME COLUMNS
            # ----------------------------------------
            for col in datetime_cols:

                try:
                    if df[col].isnull().sum() == 0:
                        continue

                    median_date = (
                        df[col].dropna()
                    )

                    if not median_date.empty:

                        fill_value = (
                            median_date.iloc[0]
                        )

                        df[col] = df[col].fillna(
                            fill_value
                        )

                except Exception as e:
                    logger.warning(
                        f"Datetime fill failed for "
                        f"{col}: {str(e)}"
                    )

        # ============================================
        # TEXT NORMALIZATION
        # ============================================
        if normalize_text:

            object_cols = (
                df.select_dtypes(
                    include=["object"]
                )
                .columns
                .tolist()
            )

            for col in object_cols:

                try:
                    df[col] = normalize_text_column(
                        df[col]
                    )

                except Exception as e:
                    logger.warning(
                        f"Text normalization failed for "
                        f"{col}: {str(e)}"
                    )

        # ============================================
        # REMOVE FULLY EMPTY COLUMNS
        # ============================================
        before_cols = len(df.columns)

        df = df.dropna(
            axis=1,
            how="all"
        )

        removed_cols = (
            before_cols - len(df.columns)
        )

        if removed_cols > 0:

            logger.info(
                f"Removed {removed_cols} empty columns"
            )

        # ============================================
        # RESET INDEX
        # ============================================
        df = df.reset_index(drop=True)

        # ============================================
        # FINAL LOGGING
        # ============================================
        logger.info(
            "Data cleaning completed successfully"
        )

        logger.info(
            f"Final dataset shape: {df.shape}"
        )

        return df

    except Exception as e:
        logger.exception(
            f"Data cleaning failed: {str(e)}"
        )

        raise