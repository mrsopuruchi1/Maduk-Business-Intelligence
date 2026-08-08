"""
Maduk Business Intelligence - Data Profiler Engine
Analyzes statistical properties, data health, missingness, and data reliability metrics.
"""

import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

logger = logging.getLogger("MadukBI.DataProfiler")


class DataProfiler:
    """Profiles raw datasets and calculates a comprehensive quality score."""

    def profile(self, df: pd.DataFrame, mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Profiles dataset completeness, record integrity, and statistics.

        Args:
            df: Validated DataFrame.
            mapping: Canonical column mappings dictionary.

        Returns:
            Dict containing quality scores, statistics, and structural profiles.
        """
        total_rows, total_cols = df.shape
        total_cells = total_rows * total_cols
        
        if total_cells == 0:
            return {"data_quality_score": 0.0, "descriptive_stats": {}}

        # 1. Missingness & Completeness Evaluation
        null_count = int(df.isnull().sum().sum())
        completeness_pct = ((total_cells - null_count) / total_cells) * 100.0

        # 2. Duplicate Record Evaluation
        duplicate_rows = int(df.duplicated().sum())
        uniqueness_pct = max(0.0, 100.0 - ((duplicate_rows / total_rows) * 100.0))

        # 3. Canonical Completeness (How many critical business metrics were mapped?)
        critical_fields = ['date', 'revenue', 'expenses', 'profit', 'customers']
        found_critical = sum(1 for field in critical_fields if field in mapping)
        canonical_coverage_pct = (found_critical / len(critical_fields)) * 100.0

        # Weighted Data Quality Score Calculation
        data_quality_score = round(
            (completeness_pct * 0.40) +
            (uniqueness_pct * 0.30) +
            (canonical_coverage_pct * 0.30),
            1
        )

        # 4. Generate Descriptive Statistics for Appendix
        numeric_df = df.select_dtypes(include=[np.number])
        stats_summary: Dict[str, Dict[str, float]] = {}
        
        if not numeric_df.empty:
            described = numeric_df.describe().T
            for col, row in described.iterrows():
                stats_summary[str(col)] = {
                    "mean": round(float(row['mean']), 2),
                    "std": round(float(row['std']), 2) if not np.isnan(row['std']) else 0.0,
                    "min": round(float(row['min']), 2),
                    "max": round(float(row['max']), 2),
                    "median": round(float(numeric_df[col].median()), 2)
                }

        logger.info(f"Data Profiling Complete. Evaluated Data Quality Score: {data_quality_score}/100")

        return {
            "data_quality_score": data_quality_score,
            "total_records": total_rows,
            "total_columns": total_cols,
            "null_cells": null_count,
            "duplicate_rows": duplicate_rows,
            "completeness_pct": round(completeness_pct, 1),
            "canonical_coverage_pct": round(canonical_coverage_pct, 1),
            "descriptive_stats": stats_summary
        }
