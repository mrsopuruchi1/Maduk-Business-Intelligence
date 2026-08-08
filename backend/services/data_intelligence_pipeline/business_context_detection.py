import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


# ============================================
# 🔥 BUSINESS CONTEXT DETECTION ENGINE
# ============================================
def detect_business_context(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detects:
    - Business domain
    - KPI column
    - Target variable
    - Preferred chart dimensions

    Features:
    - Business-priority KPI scoring
    - KPI preference hierarchy
    - Smart categorical selection
    - Safer fallback logic
    """

    try:
        analysis = analysis or {}

        columns: List[str] = analysis.get("columns", []) or []

        column_types = analysis.get("column_types", {}) or {}

        numeric_cols: List[str] = (
            column_types.get("numeric", []) or []
        )

        categorical_cols: List[str] = (
            column_types.get("categorical", []) or []
        )

        datetime_cols: List[str] = (
            column_types.get("datetime", []) or []
        )

        correlations = (
            analysis.get("top_correlations", []) or []
        )

        feature_importance = (
            analysis.get("feature_importance", {}) or {}
        )

        categorical_summary = (
            analysis.get("categorical_summary", {}) or {}
        )

        target_from_analysis = analysis.get("target_column")

        # ============================================
        # SAFE LOWERCASE MAPPING
        # ============================================
        columns_lower_map = {
            str(col).lower(): col
            for col in columns
        }

        columns_lower = list(columns_lower_map.keys())

        # ============================================
        # 🔹 1. DOMAIN DETECTION
        # ============================================
        domain = "general"

        sales_keywords = [
            "revenue",
            "sales",
            "profit",
            "income",
            "orders",
            "purchase",
            "marketing"
        ]

        customer_keywords = [
            "customer",
            "client",
            "segment",
            "gender",
            "user",
            "age"
        ]

        finance_keywords = [
            "expense",
            "cost",
            "budget",
            "cash",
            "finance",
            "margin"
        ]

        operations_keywords = [
            "delivery",
            "operations",
            "shipment",
            "efficiency",
            "process",
            "time"
        ]

        if any(
            any(keyword in col for keyword in sales_keywords)
            for col in columns_lower
        ):
            domain = "sales"

        elif any(
            any(keyword in col for keyword in customer_keywords)
            for col in columns_lower
        ):
            domain = "customer"

        elif any(
            any(keyword in col for keyword in finance_keywords)
            for col in columns_lower
        ):
            domain = "finance"

        elif any(
            any(keyword in col for keyword in operations_keywords)
            for col in columns_lower
        ):
            domain = "operations"

        # ============================================
        # 🔹 2. KPI PRIORITY SCORING
        # ============================================
        #
        # IMPORTANT:
        # Prefer:
        # revenue > sales > profit > income
        #
        # Over:
        # expense > visits > clicks
        #
        # ============================================
        kpi_priority_scores = {
            # HIGH BUSINESS VALUE
            "revenue": 100,
            "sales": 95,
            "profit": 92,
            "income": 90,
            "earnings": 88,
            "margin": 85,
            "conversion": 82,
            "purchase": 80,
            "orders": 78,

            # MEDIUM
            "growth": 70,
            "retention": 68,
            "score": 65,
            "amount": 62,
            "value": 60,

            # LOWER PRIORITY
            "spend": 45,
            "expense": 40,
            "cost": 38,
            "visits": 30,
            "traffic": 28,
            "clicks": 25,
            "impressions": 20
        }

        # ============================================
        # 🔹 3. SMART KPI DETECTION
        # ============================================
        kpi_column = None
        best_score = -1

        for col in numeric_cols:

            lower_col = col.lower()

            score = 0

            for keyword, keyword_score in kpi_priority_scores.items():

                if keyword in lower_col:
                    score = max(score, keyword_score)

            # Boost highly important business columns
            if lower_col.endswith("_revenue"):
                score += 15

            if lower_col.endswith("_profit"):
                score += 12

            if lower_col.endswith("_sales"):
                score += 10

            if score > best_score:
                best_score = score
                kpi_column = col

        # fallback
        if not kpi_column and numeric_cols:
            kpi_column = numeric_cols[0]

        # ============================================
        # 🔹 4. TARGET VARIABLE DETECTION
        # ============================================
        target_variable = None

        # --------------------------------------------
        # PRIORITY 1 → explicit target from analysis
        # --------------------------------------------
        if (
            target_from_analysis
            and target_from_analysis in numeric_cols
        ):
            target_variable = target_from_analysis

        # --------------------------------------------
        # PRIORITY 2 → detected KPI
        # --------------------------------------------
        if (
            not target_variable
            and kpi_column in numeric_cols
        ):
            target_variable = kpi_column

        # --------------------------------------------
        # PRIORITY 3 → strongest feature importance
        # --------------------------------------------
        if (
            not target_variable
            and isinstance(feature_importance, dict)
            and feature_importance
        ):

            try:
                target_variable = max(
                    feature_importance,
                    key=lambda x: abs(feature_importance[x])
                )

            except Exception:
                pass

        # --------------------------------------------
        # PRIORITY 4 → top correlation
        # --------------------------------------------
        if not target_variable and correlations:

            try:
                top_corr = correlations[0]

                f1 = top_corr.get("feature_1")
                f2 = top_corr.get("feature_2")

                if f2 in numeric_cols:
                    target_variable = f2

                elif f1 in numeric_cols:
                    target_variable = f1

            except Exception:
                pass

        # --------------------------------------------
        # PRIORITY 5 → fallback
        # --------------------------------------------
        if not target_variable and numeric_cols:
            target_variable = numeric_cols[-1]

        # ============================================
        # 🔹 5. SMART CATEGORICAL SELECTION
        # ============================================
        preferred_categorical = None

        category_priority_keywords = [
            "segment",
            "category",
            "region",
            "department",
            "group",
            "type",
            "channel",
            "gender"
        ]

        # PRIORITY 1 → business-friendly category
        for col in categorical_cols:

            lower_col = col.lower()

            try:
                unique_count = len(
                    categorical_summary.get(col, {})
                )

                if not (2 <= unique_count <= 12):
                    continue

                if any(
                    keyword in lower_col
                    for keyword in category_priority_keywords
                ):
                    preferred_categorical = col
                    break

            except Exception:
                continue

        # PRIORITY 2 → fallback category
        if not preferred_categorical:

            for col in categorical_cols:

                try:
                    unique_count = len(
                        categorical_summary.get(col, {})
                    )

                    if 2 <= unique_count <= 12:
                        preferred_categorical = col
                        break

                except Exception:
                    continue

        # ============================================
        # 🔹 6. DATETIME PREFERENCE
        # ============================================
        preferred_datetime = None

        if datetime_cols:
            preferred_datetime = datetime_cols[0]

        # ============================================
        # 🔹 7. CONFIDENCE SCORE
        # ============================================
        confidence = 1.0

        if domain == "general":
            confidence -= 0.2

        if not kpi_column:
            confidence -= 0.3

        if not target_variable:
            confidence -= 0.2

        if not correlations:
            confidence -= 0.1

        confidence = max(0.0, min(confidence, 1.0))

        # ============================================
        # 🔹 FINAL OUTPUT
        # ============================================
        context = {
            "domain": domain,
            "target_variable": target_variable,
            "kpi": kpi_column,
            "preferred_categorical": preferred_categorical,
            "preferred_datetime": preferred_datetime,
            "confidence": round(confidence, 2)
        }

        logger.info(
            f"Business context detected: {context}"
        )

        return context

    except Exception as e:
        logger.exception(
            f"Business context detection failed: {str(e)}"
        )

        return {
            "domain": "unknown",
            "target_variable": None,
            "kpi": None,
            "preferred_categorical": None,
            "preferred_datetime": None,
            "confidence": 0.0
        }