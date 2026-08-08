import logging
from typing import Dict, Any

import pandas as pd
import plotly.express as px

logger = logging.getLogger(__name__)


# ============================================
# 🔥 SAFE IMAGE EXPORT (Kaleido-safe)
# ============================================
def safe_to_image(fig):
    """
    Safely convert Plotly figure to PNG bytes.
    Prevents crash if kaleido is unavailable.
    """
    try:
        return fig.to_image(format="png", scale=2)

    except Exception as e:
        logger.warning(f"Kaleido image export failed: {str(e)}")
        return None


# ============================================
# 🔥 SAFE HTML EXPORT
# ============================================
def safe_to_html(fig):
    """
    Generate lightweight Plotly HTML safely.
    """
    try:
        return fig.to_html(
            full_html=False,
            include_plotlyjs="cdn"
        )

    except Exception as e:
        logger.warning(f"HTML export failed: {str(e)}")
        return ""


# ============================================
# 🔥 SMART CORRELATION SELECTION
# ============================================
def select_best_correlation(
    correlations,
    kpi=None
):
    """
    KPI-aware correlation selection.

    Prioritizes:
    - relationships involving KPI
    - business-important metrics
    - meaningful business correlations
    """

    if not correlations:
        return None

    priority_keywords = [
        "revenue",
        "sales",
        "profit",
        "income",
        "purchase",
        "conversion",
        "score",
        "spend"
    ]

    # ============================================
    # PRIORITY 1 → KPI INVOLVEMENT
    # ============================================
    if kpi:

        for corr in correlations:

            f1 = str(
                corr.get("feature_1", "")
            ).lower()

            f2 = str(
                corr.get("feature_2", "")
            ).lower()

            if (
                kpi.lower() == f1
                or kpi.lower() == f2
            ):
                return corr

    # ============================================
    # PRIORITY 2 → BUSINESS KPI RELATIONSHIPS
    # ============================================
    for corr in correlations:

        f1 = str(
            corr.get("feature_1", "")
        ).lower()

        f2 = str(
            corr.get("feature_2", "")
        ).lower()

        if (
            any(k in f1 for k in priority_keywords)
            and any(k in f2 for k in priority_keywords)
        ):
            return corr

    # ============================================
    # PRIORITY 3 → FALLBACK
    # ============================================
    return correlations[0]


# ============================================
# 🔥 SMART DATETIME PARSER
# ============================================
def parse_datetime_series(series):
    """
    Attempts multiple datetime parsing strategies.
    """

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%Y-%m",
        "%b-%Y",
        "%B-%Y"
    ]

    # ----------------------------------------
    # TRY COMMON FORMATS
    # ----------------------------------------
    for fmt in formats:

        try:
            parsed = pd.to_datetime(
                series,
                format=fmt,
                errors="coerce"
            )

            if parsed.notna().sum() >= max(3, len(series) * 0.5):
                return parsed

        except Exception:
            continue

    # ----------------------------------------
    # FALLBACK → AUTO INFERENCE
    # ----------------------------------------
    try:
        parsed = pd.to_datetime(
            series,
            errors="coerce",
            infer_datetime_format=True
        )

        return parsed

    except Exception:
        return pd.to_datetime(
            series,
            errors="coerce"
        )


# ============================================
# 🔥 SMART CATEGORY SELECTION
# ============================================
def select_best_category(
    df,
    categorical_cols
):
    """
    Select best category for bar chart.
    """

    if not categorical_cols:
        return None

    preferred_keywords = [
        "segment",
        "category",
        "region",
        "department",
        "gender",
        "group",
        "channel",
        "type"
    ]

    # ============================================
    # PRIORITY 1 → BUSINESS-FRIENDLY CATEGORY
    # ============================================
    for col in categorical_cols:

        if col not in df.columns:
            continue

        try:
            unique_vals = df[col].nunique(dropna=True)

            if not (2 <= unique_vals <= 12):
                continue

            lower_col = col.lower()

            if any(
                keyword in lower_col
                for keyword in preferred_keywords
            ):
                return col

        except Exception:
            continue

    # ============================================
    # PRIORITY 2 → FALLBACK CATEGORY
    # ============================================
    for col in categorical_cols:

        if col not in df.columns:
            continue

        try:
            unique_vals = df[col].nunique(dropna=True)

            if 2 <= unique_vals <= 12:
                return col

        except Exception:
            continue

    return None


# ============================================
# 🔥 CHART GENERATION ENGINE
# ============================================
def generate_focused_charts(
    df,
    analysis: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:

    try:
        charts: Dict[str, Any] = {}

        # ============================================
        # SAFETY CHECK
        # ============================================
        if df is None or getattr(df, "empty", True):
            logger.warning(
                "Empty DataFrame — no charts generated"
            )
            return charts

        analysis = analysis or {}
        context = context or {}

        # ============================================
        # COLUMN EXTRACTION
        # ============================================
        column_types = (
            analysis.get("column_types", {}) or {}
        )

        numeric_cols = (
            column_types.get("numeric", []) or []
        )

        categorical_cols = (
            column_types.get("categorical", []) or []
        )

        datetime_cols = (
            column_types.get("datetime", []) or []
        )

        correlations = (
            analysis.get("top_correlations", []) or []
        )

        # ============================================
        # KPI DETECTION
        # ============================================
        kpi = context.get("kpi")

        if (
            not kpi
            or kpi not in df.columns
        ):

            if numeric_cols:
                kpi = numeric_cols[0]

        if not kpi:
            logger.warning(
                "No KPI found for chart generation"
            )
            return charts

        # ============================================
        # 🔹 1. SCATTER PLOT
        # ============================================
        try:
            selected_corr = select_best_correlation(
                correlations,
                kpi=kpi
            )

            if selected_corr:

                x = selected_corr.get("feature_1")
                y = selected_corr.get("feature_2")

                if (
                    x in numeric_cols
                    and y in numeric_cols
                    and x in df.columns
                    and y in df.columns
                ):

                    scatter_df = df[[x, y]].copy()

                    scatter_df[x] = pd.to_numeric(
                        scatter_df[x],
                        errors="coerce"
                    )

                    scatter_df[y] = pd.to_numeric(
                        scatter_df[y],
                        errors="coerce"
                    )

                    scatter_df = scatter_df.dropna()

                    if not scatter_df.empty:

                        fig = px.scatter(
                            scatter_df,
                            x=x,
                            y=y,
                            title=f"{x} vs {y} (Key Relationship)",
                            trendline=None
                        )

                        fig.update_layout(
                            template="plotly_white",
                            height=500
                        )

                        charts["scatter"] = {
                            "type": "scatter",
                            "column": f"{x} vs {y}",
                            "html": safe_to_html(fig),
                            "json": fig.to_dict(),
                            "image": safe_to_image(fig)
                        }

        except Exception as e:
            logger.warning(
                f"Scatter chart failed: {str(e)}"
            )

        # ============================================
        # 🔹 2. BAR CHART
        # ============================================
        try:
            if (
                categorical_cols
                and kpi in df.columns
            ):

                segment = select_best_category(
                    df,
                    categorical_cols
                )

                if segment:

                    bar_df = df[[segment, kpi]].copy()

                    bar_df[kpi] = pd.to_numeric(
                        bar_df[kpi],
                        errors="coerce"
                    )

                    bar_df = bar_df.dropna()

                    if not bar_df.empty:

                        grouped = (
                            bar_df
                            .groupby(
                                segment,
                                as_index=False
                            )[kpi]
                            .mean()
                        )

                        grouped = grouped.sort_values(
                            by=kpi,
                            ascending=False
                        )

                        grouped = grouped.head(10)

                        if not grouped.empty:

                            fig = px.bar(
                                grouped,
                                x=segment,
                                y=kpi,
                                title=f"{kpi} by {segment}",
                                text_auto=".2f"
                            )

                            fig.update_layout(
                                template="plotly_white",
                                height=500
                            )

                            charts["bar"] = {
                                "type": "bar",
                                "column": f"{segment} vs {kpi}",
                                "html": safe_to_html(fig),
                                "json": fig.to_dict(),
                                "image": safe_to_image(fig)
                            }

        except Exception as e:
            logger.warning(
                f"Bar chart failed: {str(e)}"
            )

        # ============================================
        # 🔹 3. LINE CHART (TIME SERIES)
        # ============================================
        try:
            time_col = None

            # ----------------------------------------
            # PRIORITY 1 → DETECTED DATETIME
            # ----------------------------------------
            for col in datetime_cols:

                if col in df.columns:
                    time_col = col
                    break

            # ----------------------------------------
            # PRIORITY 2 → STRING DATETIME INFERENCE
            # ----------------------------------------
            if not time_col:

                datetime_keywords = [
                    "date",
                    "time",
                    "month",
                    "year",
                    "day"
                ]

                for col in df.columns:

                    lower_col = col.lower()

                    if any(
                        keyword in lower_col
                        for keyword in datetime_keywords
                    ):
                        time_col = col
                        break

            # ----------------------------------------
            # BUILD LINE CHART
            # ----------------------------------------
            if (
                time_col
                and kpi in df.columns
            ):

                trend_df = df[[time_col, kpi]].copy()

                # 🔥 SMART DATETIME PARSING
                trend_df[time_col] = parse_datetime_series(
                    trend_df[time_col]
                )

                trend_df[kpi] = pd.to_numeric(
                    trend_df[kpi],
                    errors="coerce"
                )

                trend_df = trend_df.dropna()

                if not trend_df.empty:

                    trend_df = (
                        trend_df
                        .groupby(
                            time_col,
                            as_index=False
                        )[kpi]
                        .mean()
                    )

                    trend_df = trend_df.sort_values(
                        by=time_col
                    )

                    fig = px.line(
                        trend_df,
                        x=time_col,
                        y=kpi,
                        title=f"{kpi} Trend Over Time",
                        markers=True
                    )

                    fig.update_layout(
                        template="plotly_white",
                        height=500
                    )

                    charts["trend"] = {
                        "type": "line",
                        "column": f"{time_col} vs {kpi}",
                        "html": safe_to_html(fig),
                        "json": fig.to_dict(),
                        "image": safe_to_image(fig)
                    }

        except Exception as e:
            logger.warning(
                f"Trend chart failed: {str(e)}"
            )

        # ============================================
        # FINAL LOGGING
        # ============================================
        logger.info(
            f"Generated {len(charts)} focused charts"
        )

        return charts

    except Exception as e:
        logger.exception(
            f"Chart generation failed completely: {str(e)}"
        )

        return {}