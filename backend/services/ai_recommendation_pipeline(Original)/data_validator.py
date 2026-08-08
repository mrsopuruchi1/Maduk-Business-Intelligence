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

    # Dynamic fuzzy matching alias dictionary
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
            'total_cost', 'opex', 'expenditures', 'cost_of_goods_sold'
        ],
        'profit': [
            'profit', 'net_income', 'margin', 'earnings', 'net_profit',
            'bottom_line', 'operating_profit', 'ebitda'
        ],
        'customers': [
            'customer_id', 'client_id', 'user_id', 'customers', 'buyers',
            'client_count', 'active_users', 'account_id'
        ],
        'orders': [
            'order_id', 'transaction_id', 'sales_id', 'quantity', 'units_sold',
            'order_count', 'transactions'
        ],
        'marketing_spend': [
            'marketing_spend', 'ad_spend', 'marketing', 'advertising',
            'promo_cost', 'acquisition_cost', 'ad_budget'
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

        # Schema Mapping via Alias Resolution
        for canonical, aliases in self.CANONICAL_MAPPINGS.items():
            for col in df.columns:
                if col in assigned_df_cols:
                    continue
                
                # Direct match or partial token match
                if col in aliases or any(alias in col for alias in aliases):
                    mapped_cols[canonical] = col
                    assigned_df_cols.add(col)
                    logger.info(f"Mapped canonical key '{canonical}' -> DataFrame column '{col}'")
                    break

        # Convert Date Column if resolved
        if 'date' in mapped_cols:
            date_col = mapped_cols['date']
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            # Drop rows where date failed parsing if datetime is primary axis
            df = df.dropna(subset=[date_col]).sort_values(by=date_col)

        # Convert Numeric Metrics
        numeric_canonicals = ['revenue', 'expenses', 'profit', 'marketing_spend', 'debt', 'inventory', 'cash_balance']
        for key in numeric_canonicals:
            if key in mapped_cols:
                col_name = mapped_cols[key]
                # Strip currency symbols or commas if stored as string
                if df[col_name].dtype == 'object':
                    df[col_name] = df[col_name].astype(str).str.replace(r'[$,%]', '', regex=True)
                df[col_name] = pd.to_numeric(df[col_name], errors='coerce').fillna(0.0)

        return df, mapped_cols
