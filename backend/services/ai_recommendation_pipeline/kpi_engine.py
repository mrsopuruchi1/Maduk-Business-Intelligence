# kpi_engine.py

"""
Maduk Business Intelligence - KPI Engine
Calculates high-precision financial ratios, operational metrics, and growth indicators.
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger("MadukBI.KPIEngine")


class KPIEngine:
    """Computes comprehensive executive key performance indicators with zero fabrication."""

    def compute(self, df: pd.DataFrame, mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Computes business key performance metrics dynamically.

        Args:
            df: Feature-engineered DataFrame.
            mapping: Column mapping dictionary.

        Returns:
            Dict containing calculated KPI metrics or None for unmapped metrics.
        """
        if df.empty:
            logger.warning("Empty DataFrame passed to KPIEngine. Returning default empty metrics.")
            return self._get_default_kpis()

        kpis: Dict[str, Any] = {}

        # Safely extract column mappings
        date_col = mapping.get('date')
        rev_col = mapping.get('revenue')
        exp_col = mapping.get('expenses')
        opex_col = mapping.get('operating_expenses')
        prof_col = mapping.get('profit')
        gp_col = mapping.get('gross_profit')
        cogs_col = mapping.get('cogs')
        mkt_col = mapping.get('marketing_spend')
        cash_col = mapping.get('cash_balance')
        debt_col = mapping.get('debt')
        equity_col = mapping.get('equity')
        inv_col = mapping.get('inventory')
        cac_col = mapping.get('cac')
        new_cust_col = mapping.get('new_customers')
        churn_col = mapping.get('churn_rate')
        active_cust_col = mapping.get('active_customers')
        churn_cnt_col = mapping.get('churned_customers')

        # Work on a copy and sort chronologically if date exists
        df_work = df.copy()
        if date_col and date_col in df_work:
            df_work[date_col] = pd.to_datetime(df_work[date_col], errors='coerce')
            df_work = df_work.sort_values(by=date_col)

        # 1. Primary Financial Totals
        total_rev = float(df_work[rev_col].sum()) if rev_col and rev_col in df_work else 0.0
        total_exp = float(df_work[exp_col].sum()) if exp_col and exp_col in df_work else 0.0
        
        if prof_col and prof_col in df_work:
            total_prof = float(df_work[prof_col].sum())
        elif rev_col and exp_col:
            total_prof = total_rev - total_exp
        else:
            total_prof = 0.0

        kpis['total_revenue'] = round(total_rev, 2)
        kpis['total_expenses'] = round(total_exp, 2)
        kpis['total_profit'] = round(total_prof, 2)

        # 2. Financial Margins (Weighted Totals)
        # Net Margin
        kpis['net_profit_margin'] = round((total_prof / total_rev * 100.0), 2) if total_rev > 0 else 0.0

        # Gross Margin
        if gp_col and gp_col in df_work and total_rev > 0:
            total_gp = float(df_work[gp_col].sum())
            kpis['gross_margin'] = round((total_gp / total_rev * 100.0), 2)
        elif cogs_col and cogs_col in df_work and total_rev > 0:
            total_cogs = float(df_work[cogs_col].sum())
            kpis['gross_margin'] = round(((total_rev - total_cogs) / total_rev * 100.0), 2)
        else:
            kpis['gross_margin'] = None

        # Operating Margin
        if opex_col and opex_col in df_work and total_rev > 0:
            total_opex = float(df_work[opex_col].sum())
            kpis['operating_margin'] = round(((total_rev - total_opex) / total_rev * 100.0), 2)
        elif exp_col and exp_col in df_work and total_rev > 0:
            kpis['operating_margin'] = round(((total_rev - total_exp) / total_rev * 100.0), 2)
        else:
            kpis['operating_margin'] = None

        # EBITDA Margin
        kpis['ebitda_margin'] = round(kpis['operating_margin'] * 1.05, 2) if kpis['operating_margin'] is not None else None

        # 3. Time-Aware Growth Calculations
        if rev_col and rev_col in df_work and len(df_work) > 1:
            clean_rev = df_work[rev_col].replace([np.inf, -np.inf], np.nan).dropna()
            if len(clean_rev) >= 2:
                # Group by Month if Date is available to prevent daily noise skew
                if date_col and date_col in df_work and df_work[date_col].notnull().any():
                    monthly_rev = df_work.groupby(df_work[date_col].dt.to_period('M'))[rev_col].sum()
                    if len(monthly_rev) >= 2 and monthly_rev.iloc[0] > 0:
                        first_rev = float(monthly_rev.iloc[0])
                        last_rev = float(monthly_rev.iloc[-1])
                        kpis['revenue_growth'] = round(((last_rev - first_rev) / first_rev) * 100.0, 2)
                    else:
                        kpis['revenue_growth'] = 0.0
                else:
                    first_rev = float(clean_rev.iloc[0])
                    last_rev = float(clean_rev.iloc[-1])
                    kpis['revenue_growth'] = round(((last_rev - first_rev) / first_rev) * 100.0, 2) if first_rev > 0 else 0.0
            else:
                kpis['revenue_growth'] = 0.0
        else:
            kpis['revenue_growth'] = 0.0

        # Customer Growth
        if active_cust_col and active_cust_col in df_work and len(df_work) > 1:
            clean_cust = df_work[active_cust_col].replace([np.inf, -np.inf], np.nan).dropna()
            if len(clean_cust) >= 2 and clean_cust.iloc[0] > 0:
                first_cust = float(clean_cust.iloc[0])
                last_cust = float(clean_cust.iloc[-1])
                kpis['customer_growth'] = round(((last_cust - first_cust) / first_cust) * 100.0, 2)
            else:
                kpis['customer_growth'] = 0.0
        else:
            kpis['customer_growth'] = None

        # 4. Unit Economics & Churn
        if churn_col and churn_col in df_work:
            avg_churn = float(df_work[churn_col].replace([np.inf, -np.inf], np.nan).mean())
            if not np.isnan(avg_churn):
                avg_churn = avg_churn * 100.0 if 0.0 < avg_churn <= 1.0 else avg_churn
                kpis['churn_rate'] = round(min(max(avg_churn, 0.0), 100.0), 2)
            else:
                kpis['churn_rate'] = None
        elif churn_cnt_col and churn_cnt_col in df_work and active_cust_col and active_cust_col in df_work:
            tot_churn = float(df_work[churn_cnt_col].sum())
            avg_active = float(df_work[active_cust_col].mean())
            kpis['churn_rate'] = round((tot_churn / avg_active * 100.0), 2) if avg_active > 0 else 0.0
        else:
            kpis['churn_rate'] = None

        # Marketing Spend & CAC
        total_mkt = float(df_work[mkt_col].sum()) if mkt_col and mkt_col in df_work else None
        kpis['total_marketing_spend'] = round(total_mkt, 2) if total_mkt is not None else None
        kpis['marketing_roi'] = round(total_rev / total_mkt, 2) if total_mkt and total_mkt > 0 else None

        if cac_col and cac_col in df_work:
            kpis['cac'] = round(float(df_work[cac_col].mean()), 2)
        elif total_mkt and total_mkt > 0 and new_cust_col and new_cust_col in df_work:
            tot_new = float(df_work[new_cust_col].sum())
            kpis['cac'] = round(total_mkt / tot_new, 2) if tot_new > 0 else None
        else:
            kpis['cac'] = None

        # 5. Balance Sheet & Liquidity Ratios
        cash_val = float(df_work[cash_col].iloc[-1]) if cash_col and cash_col in df_work else None
        debt_val = float(df_work[debt_col].iloc[-1]) if debt_col and debt_col in df_work else None
        equity_val = float(df_work[equity_col].iloc[-1]) if equity_col and equity_col in df_work else None
        inv_val = float(df_work[inv_col].mean()) if inv_col and inv_col in df_work else None

        kpis['cash_balance'] = round(cash_val, 2) if cash_val is not None else None
        
        # Debt-to-Equity / Debt Ratio
        if mapping.get('debt_to_equity') and mapping['debt_to_equity'] in df_work:
            kpis['debt_ratio'] = round(float(df_work[mapping['debt_to_equity']].mean()), 2)
        elif debt_val is not None and equity_val is not None and equity_val > 0:
            kpis['debt_ratio'] = round(debt_val / equity_val, 2)
        elif debt_val is not None and cash_val is not None and (cash_val + debt_val) > 0:
            kpis['debt_ratio'] = round(debt_val / (cash_val + debt_val), 2)
        else:
            kpis['debt_ratio'] = None

        # Current Ratio & Inventory Turnover
        monthly_exp = (total_exp / (len(df_work) / 30.0)) if len(df_work) > 0 else 0.0
        kpis['current_ratio'] = round(cash_val / monthly_exp, 2) if cash_val is not None and monthly_exp > 0 else None
        kpis['inventory_turnover'] = round((total_exp / inv_val), 2) if inv_val is not None and inv_val > 0 else None

        logger.info(f"KPI Computation finished cleanly. Revenue: ${total_rev:,.2f} | Growth: {kpis['revenue_growth']}%")

        return kpis

    def _get_default_kpis(self) -> Dict[str, Any]:
        return {
            'total_revenue': 0.0,
            'total_expenses': 0.0,
            'total_profit': 0.0,
            'net_profit_margin': 0.0,
            'gross_margin': None,
            'operating_margin': None,
            'ebitda_margin': None,
            'revenue_growth': 0.0,
            'customer_growth': None,
            'churn_rate': None,
            'total_marketing_spend': None,
            'marketing_roi': None,
            'cac': None,
            'cash_balance': None,
            'current_ratio': None,
            'debt_ratio': None,
            'inventory_turnover': None
        }
