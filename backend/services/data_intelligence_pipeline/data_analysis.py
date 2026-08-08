import logging
import re
from typing import Dict, Any, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# =====================================================
# 🔥 SMART BUSINESS COLUMN SCORING
# =====================================================
def get_business_priority_score(column_name: str) -> int:
    """
    Assign business importance scores to columns.
    Higher score = more likely to become KPI/target.
    """

    col = str(column_name).lower()

    score = 0

    high_priority_keywords = [
        "revenue",
        "sales",
        "profit",
        "income",
        "earnings",
        "gmv",
        "arr",
        "mrr",
        "purchase",
        "orders",
        "customers",
        "conversion",
        "retention"
    ]

    medium_priority_keywords = [
        "spend",
        "marketing",
        "traffic",
        "visits",
        "leads",
        "clicks",
        "growth",
        "margin",
        "cost"
    ]

    low_priority_keywords = [
        "id",
        "index",
        "code",
        "phone",
        "zip"
    ]

    for keyword in high_priority_keywords:
        if keyword in col:
            score += 100

    for keyword in medium_priority_keywords:
        if keyword in col:
            score += 50

    for keyword in low_priority_keywords:
        if keyword in col:
            score -= 100

    return score


# =====================================================
# 🔥 SAFE DATETIME PARSING
# =====================================================
def try_parse_datetime(
    series: pd.Series,
    threshold: float = 0.6
) -> bool:
    """
    Safely determine whether a column is datetime-like.
    Prevents pandas fallback warnings.
    """

    try:
        sample_values = (
            series
            .dropna()
            .astype(str)
            .head(20)
            .tolist()
        )

        if not sample_values:
            return False

        date_patterns = [
            r"^\d{4}-\d{2}-\d{2}$",   # 2025-01-31
            r"^\d{2}/\d{2}/\d{4}$",   # 31/01/2025
            r"^\d{4}/\d{2}/\d{2}$",   # 2025/01/31
            r"^\d{2}-\d{2}-\d{4}$",   # 31-01-2025
        ]

        matches = 0

        for value in sample_values:

            for pattern in date_patterns:

                if re.match(pattern, value):
                    matches += 1
                    break

        confidence = matches / len(sample_values)

        if confidence < threshold:
            return False

        parsed = pd.to_datetime(
            series,
            errors="coerce",
            format="%Y-%m-%d"
        )

        valid_ratio = (
            parsed.notna().sum()
            / max(len(series), 1)
        )

        return valid_ratio >= threshold

    except Exception:
        return False


# =====================================================
# 🔥 SMART DATETIME INFERENCE
# =====================================================
def infer_datetime_columns(
    df: pd.DataFrame
) -> List[str]:
    """
    Detect datetime columns including string/object columns.
    """

    detected: List[str] = []

    for col in df.columns:

        try:
            # ----------------------------------------
            # ALREADY DATETIME
            # ----------------------------------------
            if pd.api.types.is_datetime64_any_dtype(
                df[col]
            ):
                detected.append(col)
                continue

            # ----------------------------------------
            # ONLY CHECK OBJECT / STRING
            # ----------------------------------------
            if not (
                pd.api.types.is_object_dtype(df[col])
                or pd.api.types.is_string_dtype(df[col])
            ):
                continue

            # ----------------------------------------
            # SAFE DATETIME DETECTION
            # ----------------------------------------
            if try_parse_datetime(df[col]):
                detected.append(col)

        except Exception as e:
            logger.warning(
                f"Datetime inference failed for "
                f"{col}: {str(e)}"
            )

    return detected


# =====================================================
# 🔥 MAIN ANALYSIS ENGINE
# =====================================================
def analyze_data(
    df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Decision Intelligence Data Analyzer

    Features:
    - Descriptive statistics
    - Correlation analysis
    - Business-weighted ranking
    - Smart KPI detection
    - Smart target detection
    - Datetime inference
    - Trend detection
    """

    try:

        results: Dict[str, Any] = {}

        # =====================================================
        # SAFETY
        # =====================================================
        if df is None or df.empty:

            logger.warning(
                "Empty DataFrame received for analysis"
            )

            return {
                "shape": (0, 0),
                "columns": [],
                "column_types": {
                    "numeric": [],
                    "categorical": [],
                    "datetime": []
                },
                "top_correlations": [],
                "feature_importance": {},
                "trends": [],
                "missing_values": {},
                "duplicate_rows": 0,
                "target_column": None,
                "recommended_kpi": None
            }

        # =====================================================
        # BASIC INFO
        # =====================================================
        results["shape"] = df.shape
        results["columns"] = list(df.columns)

        # =====================================================
        # TYPE DETECTION
        # =====================================================
        numeric_cols = (
            df.select_dtypes(include=[np.number])
            .columns
            .tolist()
        )

        datetime_cols = infer_datetime_columns(df)

        categorical_cols: List[str] = []

        for col in df.columns:

            if col in numeric_cols:
                continue

            if col in datetime_cols:
                continue

            try:
                unique_ratio = (
                    df[col].nunique(dropna=True)
                    / max(len(df), 1)
                )

                # exclude likely IDs
                if unique_ratio > 0.7:
                    continue

                categorical_cols.append(col)

            except Exception:
                continue

        results["column_types"] = {
            "numeric": numeric_cols,
            "categorical": categorical_cols,
            "datetime": datetime_cols
        }

        # =====================================================
        # NUMERIC SUMMARY
        # =====================================================
        if numeric_cols:

            try:

                desc = (
                    df[numeric_cols]
                    .describe(include="all")
                )

                results["numeric_summary"] = (
                    desc.replace(
                        [np.inf, -np.inf],
                        np.nan
                    )
                    .fillna(0)
                    .to_dict()
                )

            except Exception as e:

                logger.warning(
                    f"Numeric summary failed: {str(e)}"
                )

                results["numeric_summary"] = {}

        else:
            results["numeric_summary"] = {}

        # =====================================================
        # DISTRIBUTION ANALYSIS
        # =====================================================
        distributions = {}

        for col in numeric_cols:

            try:

                series = pd.to_numeric(
                    df[col],
                    errors="coerce"
                ).dropna()

                if len(series) > 3:

                    distributions[col] = {
                        "mean": round(
                            float(series.mean()),
                            4
                        ),
                        "median": round(
                            float(series.median()),
                            4
                        ),
                        "std": round(
                            float(series.std()),
                            4
                        ),
                        "skewness": round(
                            float(series.skew()),
                            4
                        ),
                        "min": round(
                            float(series.min()),
                            4
                        ),
                        "max": round(
                            float(series.max()),
                            4
                        )
                    }

            except Exception as e:

                logger.warning(
                    f"Distribution analysis failed "
                    f"for {col}: {str(e)}"
                )

        results["distributions"] = distributions

        # =====================================================
        # CATEGORICAL SUMMARY
        # =====================================================
        categorical_summary = {}

        for col in categorical_cols:

            try:

                categorical_summary[col] = (
                    df[col]
                    .astype(str)
                    .value_counts(dropna=True)
                    .head(10)
                    .to_dict()
                )

            except Exception as e:

                logger.warning(
                    f"Categorical summary failed "
                    f"for {col}: {str(e)}"
                )

        results["categorical_summary"] = (
            categorical_summary
        )

        # =====================================================
        # 🔥 SMART KPI / TARGET DETECTION
        # =====================================================
        recommended_kpi = None
        target_column = None

        if numeric_cols:

            ranked_numeric = sorted(
                numeric_cols,
                key=lambda col: (
                    get_business_priority_score(col),
                    abs(
                        pd.to_numeric(
                            df[col],
                            errors="coerce"
                        ).mean()
                    )
                ),
                reverse=True
            )

            if ranked_numeric:

                recommended_kpi = ranked_numeric[0]
                target_column = ranked_numeric[0]

        results["recommended_kpi"] = (
            recommended_kpi
        )

        results["target_column"] = (
            target_column
        )

        # =====================================================
        # 🔥 BUSINESS-WEIGHTED CORRELATION RANKING
        # =====================================================
        top_correlations = []

        if len(numeric_cols) > 1:

            corr_df = df[numeric_cols].copy()

            for col in numeric_cols:

                corr_df[col] = pd.to_numeric(
                    corr_df[col],
                    errors="coerce"
                )

            corr_matrix = corr_df.corr(
                numeric_only=True
            )

            results["correlation_matrix"] = (
                corr_matrix
                .fillna(0)
                .to_dict()
            )

            correlation_pairs = []

            seen = set()

            for col1 in numeric_cols:

                for col2 in numeric_cols:

                    if col1 == col2:
                        continue

                    pair = tuple(
                        sorted([col1, col2])
                    )

                    if pair in seen:
                        continue

                    seen.add(pair)

                    try:
                        corr_value = corr_matrix.loc[
                            col1,
                            col2
                        ]

                        if pd.isna(corr_value):
                            continue

                        abs_corr = abs(
                            float(corr_value)
                        )

                        business_weight = (
                            get_business_priority_score(
                                col1
                            )
                            + get_business_priority_score(
                                col2
                            )
                        )

                        final_score = (
                            abs_corr * 1000
                            + business_weight
                        )

                        strength = (
                            "strong"
                            if abs_corr >= 0.7
                            else "moderate"
                            if abs_corr >= 0.4
                            else "weak"
                        )

                        correlation_pairs.append({
                            "feature_1": col1,
                            "feature_2": col2,
                            "correlation": round(
                                abs_corr,
                                4
                            ),
                            "strength": strength,
                            "business_score": round(
                                final_score,
                                2
                            )
                        })

                    except Exception:
                        continue

            correlation_pairs = sorted(
                correlation_pairs,
                key=lambda x: x["business_score"],
                reverse=True
            )

            top_correlations = (
                correlation_pairs[:10]
            )

        results["top_correlations"] = (
            top_correlations
        )

        # =====================================================
        # FEATURE IMPORTANCE
        # =====================================================
        feature_importance = {}

        if (
            target_column
            and target_column in numeric_cols
            and len(numeric_cols) > 1
        ):

            try:

                corr_target = (
                    df[numeric_cols]
                    .corr(numeric_only=True)[
                        target_column
                    ]
                    .drop(
                        labels=[target_column],
                        errors="ignore"
                    )
                    .abs()
                    .sort_values(
                        ascending=False
                    )
                )

                feature_importance = {
                    key: round(
                        float(value),
                        4
                    )
                    for key, value in (
                        corr_target.items()
                    )
                    if not pd.isna(value)
                }

            except Exception as e:

                logger.warning(
                    f"Feature importance failed: "
                    f"{str(e)}"
                )

        results["feature_importance"] = (
            feature_importance
        )

        # =====================================================
        # TREND DETECTION
        # =====================================================
        trends = []

        if datetime_cols and numeric_cols:

            time_col = datetime_cols[0]

            try:

                trend_df = df.copy()

                trend_df[time_col] = pd.to_datetime(
                    trend_df[time_col],
                    errors="coerce",
                    format="%Y-%m-%d"
                )

                trend_df = trend_df.dropna(
                    subset=[time_col]
                )

                trend_df = trend_df.sort_values(
                    by=time_col
                )

                for col in numeric_cols:

                    try:

                        series = pd.to_numeric(
                            trend_df[col],
                            errors="coerce"
                        ).dropna()

                        if len(series) > 5:

                            x = np.arange(
                                len(series)
                            )

                            y = series.values

                            slope = float(
                                np.polyfit(
                                    x,
                                    y,
                                    1
                                )[0]
                            )

                            trend = (
                                "increasing"
                                if slope > 0
                                else "decreasing"
                                if slope < 0
                                else "stable"
                            )

                            trends.append({
                                "column": col,
                                "trend": trend,
                                "slope": round(
                                    slope,
                                    6
                                )
                            })

                    except Exception as e:

                        logger.warning(
                            f"Trend detection failed "
                            f"for {col}: {str(e)}"
                        )

            except Exception as e:

                logger.warning(
                    f"Trend analysis failed: "
                    f"{str(e)}"
                )

        results["trends"] = trends

        # =====================================================
        # DATA QUALITY
        # =====================================================
        results["missing_values"] = (
            df.isnull()
            .sum()
            .astype(int)
            .to_dict()
        )

        results["duplicate_rows"] = int(
            df.duplicated().sum()
        )

        # =====================================================
        # FINAL LOGGING
        # =====================================================
        logger.info(
            "Data analysis completed successfully"
        )

        return results

    except Exception as e:

        logger.exception(
            f"Data analysis failed: {str(e)}"
        )

        raise