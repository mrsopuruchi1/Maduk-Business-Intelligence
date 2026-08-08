# data_validator.py

"""
Maduk Business Intelligence - Data Validator Engine
Normalizes dynamic column schemas and maps heterogeneous user inputs to canonical fields.
"""

import re
import logging
from typing import Dict, Tuple, List, Optional, Any
import pandas as pd
import numpy as np

logger = logging.getLogger("MadukBI.DataValidator")


class DataValidator:
    """Validates dynamic datasets and maps column schemas automatically."""

    # Canonical dictionary mapping standardized keys to expected variations/aliases
    CANONICAL_MAPPINGS: Dict[str, List[str]] = {
        'date': [
            'date', 'timestamp', 'created_at', 'order_date', 'transaction_date',
            'month', 'year', 'period', 'invoice_date', 'time'
        ],
        'revenue': [
            'revenue', 'sales', 'turnover', 'gross_sales', 'income',
            'total_amount', 'amount', 'billing', 'top_line'
        ],
        'expenses': [
            'expenses', 'cost', 'cogs', 'spending', 'operating_cost',
            'total_cost', 'opex', 'expenditures', 'cost_of_goods_sold', 'operating_expenses'
        ],
        'gross_profit': [
            'gross_profit', 'gp', 'gross_margin_dollars'
        ],
        'profit': [
            'profit', 'net_income', 'net_profit', 'earnings',
            'bottom_line', 'operating_profit', 'ebitda'
        ],
        'customers': [
            'customers', 'buyers', 'client_count', 'active_users', 'active_customers'
        ],
        'new_customers': [
            'new_customers', 'new_users', 'acquired_customers', 'new_buyers'
        ],
        'churn_rate': [
            'churn_rate', 'churn', 'attrition_rate', 'customer_churn'
        ],
        'churned_customers': [
            'churned_customers', 'churned_users', 'lost_customers'
        ],
        'marketing_spend': [
            'marketing_spend', 'ad_spend', 'marketing', 'advertising',
            'promo_cost', 'ad_budget'
        ],
        'cac': [
            'cac', 'customer_acquisition_cost', 'acquisition_cost'
        ],
        'debt': [
            'debt', 'liabilities', 'loans', 'total_debt', 'short_term_debt',
            'long_term_debt', 'borrowings'
        ],
        'inventory': [
            'inventory', 'stock', 'inventory_level', 'stock_value', 'inventory_valuation'
        ],
        'cash_balance': [
            'cash', 'cash_balance', 'liquidity', 'cash_on_hand', 'cash_equivalents'
        ],
        'equity': [
            'equity', 'shareholders_equity', 'total_equity'
        ],
        'product': [
            'product', 'product_name', 'item', 'sku', 'product_category', 'category'
        ],
        'region': [
            'region', 'country', 'location', 'territory', 'market', 'geography', 'state'
        ],
        'department': [
            'department', 'dept', 'business_unit', 'division', 'team'
        ]
    }

    def process(self, raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """
        Cleans data structure, converts types, and resolves canonical schema mapping.

        Args:
            raw_df: Raw input pandas DataFrame.

        Returns:
            Tuple of (cleaned_df, canonical_mapping)
        """
        if raw_df.empty:
            raise ValueError("Provided dataset is empty.")

        df = raw_df.copy()

        # Normalize column header strings
        df.columns = [
            re.sub(r'[^a-z0-9_]', '', str(col).strip().lower().replace(' ', '_'))
            for col in df.columns
        ]

        mapped_cols: Dict[str, str] = {}
        assigned_df_cols = set()

        # Phase 1: Exact alias matching
        for canonical, aliases in self.CANONICAL_MAPPINGS.items():
            for col in df.columns:
                if col in assigned_df_cols:
                    continue
                if col in aliases:
                    mapped_cols[canonical] = col
                    assigned_df_cols.add(col)
                    logger.info(f"Exact match mapped canonical key '{canonical}' -> DataFrame column '{col}'")
                    break

        # Phase 2: Token partial matching for unassigned columns
        for canonical, aliases in self.CANONICAL_MAPPINGS.items():
            if canonical in mapped_cols:
                continue
            for col in df.columns:
                if col in assigned_df_cols:
                    continue
                if any(alias in col for alias in aliases if len(alias) > 3):
                    mapped_cols[canonical] = col
                    assigned_df_cols.add(col)
                    logger.info(f"Token match mapped canonical key '{canonical}' -> DataFrame column '{col}'")
                    break

        # Convert Date Column if resolved
        if 'date' in mapped_cols:
            date_col = mapped_cols['date']
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col]).sort_values(by=date_col)

        # Clean Numeric Metrics
        numeric_canonicals = [
            'revenue', 'expenses', 'profit', 'gross_profit', 'marketing_spend', 
            'debt', 'inventory', 'cash_balance', 'equity', 'cac', 'churn_rate'
        ]
        
        for key in numeric_canonicals:
            if key in mapped_cols:
                col_name = mapped_cols[key]
                if df[col_name].dtype == 'object':
                    # Handle negative values formatted as ($100) or -$100
                    cleaned_series = df[col_name].astype(str).str.strip()
                    has_parens = cleaned_series.str.startswith('(') & cleaned_series.str.endswith(')')
                    cleaned_series = cleaned_series.str.replace(r'[$,%\(\)\s]', '', regex=True)
                    numeric_series = pd.to_numeric(cleaned_series, errors='coerce')
                    df[col_name] = np.where(has_parens, -numeric_series, numeric_series)
                else:
                    df[col_name] = pd.to_numeric(df[col_name], errors='coerce')

        return df, mapped_cols
