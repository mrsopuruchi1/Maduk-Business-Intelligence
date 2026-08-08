"""
Maduk Business Intelligence - Feature Engineering Engine
Generates synthetic business variables, growth rates, and missing core financial vectors.
"""

import logging
from typing import Dict, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger("MadukBI.FeatureEngineering")


class FeatureEngineering:
    """Transforms datasets by generating required synthetic financial and metric features."""

    def transform(self, df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Transforms dataset by injecting synthetic financial columns and derivatives.

        Args:
            df: Validated input DataFrame.
            mapping: Schema mapping dictionary.

        Returns:
            Enriched pandas DataFrame with synthesized variables.
        """
        df_out = df.copy()

        rev_col = mapping.get('revenue')
        exp_col = mapping.get('expenses')
        prof_col = mapping.get('profit')
        date_col = mapping.get('date')

        # 1. Synthesize Profit if missing but Revenue and Expenses exist
        if rev_col and exp_col and not prof_col:
            synth_prof_col = '_synth_profit'
            df_out[synth_prof_col] = df_out[rev_col] - df_out[exp_col]
            mapping['profit'] = synth_prof_col
            prof_col = synth_prof_col
            logger.info("Synthesized missing 'profit' column via (revenue - expenses).")

        # 2. Synthesize Expenses if missing but Revenue and Profit exist
        elif rev_col and prof_col and not exp_col:
            synth_exp_col = '_synth_expenses'
            df_out[synth_exp_col] = df_out[rev_col] - df_out[prof_col]
            mapping['expenses'] = synth_exp_col
            exp_col = synth_exp_col
            logger.info("Synthesized missing 'expenses' column via (revenue - profit).")

        # 3. Calculate Period Profit Margin Vector
        if rev_col and prof_col:
            df_out['_profit_margin_pct'] = np.where(
                df_out[rev_col] > 0,
                (df_out[prof_col] / df_out[rev_col]) * 100.0,
                0.0
            )

        # 4. Generate Date & Time Period Attributes
        if date_col and date_col in df_out:
            df_out['_year'] = df_out[date_col].dt.year
            df_out['_month'] = df_out[date_col].dt.month
            df_out['_year_month'] = df_out[date_col].dt.to_period('M')

            # Lagged growth calculations if dataset is chronologically ordered
            if rev_col:
                df_out['_revenue_lag1'] = df_out[rev_col].shift(1)
                df_out['_revenue_growth_pct'] = np.where(
                    df_out['_revenue_lag1'] > 0,
                    ((df_out[rev_col] - df_out['_revenue_lag1']) / df_out['_revenue_lag1']) * 100.0,
                    0.0
                )

        return df_out
