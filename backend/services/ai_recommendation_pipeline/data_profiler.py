# data_profiler.py

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
        Profiles dataset completeness, record integrity, and schema coverage.

        Args:
            df: Validated DataFrame.
            mapping: Canonical column mappings dictionary.

        Returns:
            Dict containing quality scores, statistics, and structural profiles.
        """
        total_rows, total_cols = df.shape
        total_cells = total_rows * total_cols
        
        if total_cells == 0:
            return {
                "data_quality_score": 0.0,
                "mapped_domains": [],
                "unmapped_domains": ['financials', 'customers', 'liquidity', 'marketing'],
                "descriptive_stats": {}
            }

        # 1. Missingness & Completeness Evaluation
        null_count = int(df.isnull().sum().sum())
        completeness_pct = ((total_cells - null_count) / total_cells) * 100.0

        # 2. Duplicate Record Evaluation
        duplicate_rows = int(df.duplicated().sum())
        uniqueness_pct = max(0.0, 100.0 - ((duplicate_rows / total_rows) * 100.0))

        # 3. Accuracy Score Aggregation (if provided in dataset)
        acc_col = mapping.get('accuracy_score') or next((c for c in df.columns if 'accuracy' in c.lower()), None)
        if acc_col and acc_col in df:
            accuracy_val = float(df[acc_col].mean())
            accuracy_pct = accuracy_val * 100.0 if accuracy_val <= 1.0 else accuracy_val
        else:
            accuracy_pct = completeness_pct

        # 4. Canonical Completeness & Domain Mapping Audit
        domain_checks = {
            'financials': ['revenue', 'expenses', 'profit'],
            'customers': ['active_customers', 'churn_rate', 'new_customers'],
            'liquidity': ['cash_balance', 'debt', 'inventory'],
            'marketing': ['marketing_spend', 'cac']
        }

        mapped_domains = []
        unmapped_domains = []

        for domain, fields in domain_checks.items():
            if any(f in mapping for f in fields):
                mapped_domains.append(domain)
            else:
                unmapped_domains.append(domain)

        canonical_coverage_pct = (len(mapped_domains) / len(domain_checks)) * 100.0

        # Weighted Data Quality Score Calculation
        data_quality_score = round(
            (completeness_pct * 0.35) +
            (accuracy_pct * 0.35) +
            (uniqueness_pct * 0.15) +
            (canonical_coverage_pct * 0.15),
            1
        )

        # 5. Generate Descriptive Statistics for Appendix
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
            "mapped_domains": mapped_domains,
            "unmapped_domains": unmapped_domains,
            "descriptive_stats": stats_summary
        }
