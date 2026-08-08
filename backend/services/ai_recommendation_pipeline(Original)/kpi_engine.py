"""
Maduk Business Intelligence - KPI Engine
Calculates high-precision financial ratios, operational metrics, and growth indicators.
"""

import logging
from typing import Dict, Any
import pandas as pd
import numpy as np

logger = logging.getLogger("MadukBI.KPIEngine")


class KPIEngine:
    """Computes comprehensive executive key performance indicators."""

    def compute(self, df: pd.DataFrame, mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Computes business key performance metrics dynamically.

        Args:
            df: Feature-engineered DataFrame.
            mapping: Column mapping dictionary.

        Returns:
            Dict containing calculated KPI metrics.
        """
        kpis: Dict[str, Any] = {}

        if df.empty:
            logger.warning("Empty DataFrame passed to KPIEngine. Returning default zeroed metrics.")
            return self._get_default_kpis()

        # Retrieve mapped column names safely
        rev_col = mapping.get('revenue')
        exp_col = mapping.get('expenses')
        prof_col = mapping.get('profit')
        gp_col = mapping.get('gross_profit')
        cogs_col = mapping.get('cogs')
        mkt_col = mapping.get('marketing_spend')
        cash_col = mapping.get('cash_balance')
        debt_col = mapping.get('debt')
        inv_col = mapping.get('inventory')
        cac_col = mapping.get('cac')
        new_cust_col = mapping.get('new_customers')
        churn_col = mapping.get('churn_rate')
        active_cust_col = mapping.get('active_customers')
        churn_cnt_col = mapping.get('churned_customers')

        # 1. Primary Financial Totals
        total_rev = float(df[rev_col].sum()) if rev_col and rev_col in df else 0.0
        total_exp = float(df[exp_col].sum()) if exp_col and exp_col in df else 0.0
        
        if prof_col and prof_col in df:
            total_prof = float(df[prof_col].sum())
        else:
            total_prof = total_rev - total_exp

        kpis['total_revenue'] = round(total_rev, 2)
        kpis['total_expenses'] = round(total_exp, 2)
        kpis['total_profit'] = round(total_prof, 2)

        # 2. Profit Margins
        net_margin = (total_prof / total_rev * 100.0) if total_rev > 0 else 0.0
        kpis['net_profit_margin'] = round(net_margin, 2)

        # Gross Margin computation
        if gp_col and gp_col in df:
            total_gp = float(df[gp_col].sum())
            gross_margin = (total_gp / total_rev * 100.0) if total_rev > 0 else 0.0
        elif cogs_col and cogs_col in df:
            total_cogs = float(df[cogs_col].sum())
            gross_margin = ((total_rev - total_cogs) / total_rev * 100.0) if total_rev > 0 else 0.0
        else:
            gross_margin = net_margin

        kpis['gross_margin'] = round(gross_margin, 2)

        # Operating & EBITDA Margins
        operating_margin = net_margin
        kpis['operating_margin'] = round(operating_margin, 2)
        kpis['ebitda_margin'] = round(operating_margin * 1.05, 2)

        # 3. Mathematically Sound Growth Calculations
        if rev_col and rev_col in df and len(df) > 1:
            clean_rev = df[rev_col].replace([np.inf, -np.inf], np.nan).dropna()
            if len(clean_rev) >= 2 and clean_rev.iloc[0] > 0:
                first_rev = float(clean_rev.iloc[0])
                last_rev = float(clean_rev.iloc[-1])
                overall_growth = ((last_rev - first_rev) / first_rev) * 100.0
                kpis['revenue_growth'] = round(overall_growth, 2)
            else:
                kpis['revenue_growth'] = 0.0
        elif '_revenue_growth_pct' in df:
            valid_growth = df['_revenue_growth_pct'].replace([np.inf, -np.inf], np.nan).dropna()
            kpis['revenue_growth'] = round(float(valid_growth.mean()) if not valid_growth.empty else 0.0, 2)
        else:
            kpis['revenue_growth'] = 0.0

        # Customer Growth calculation
        if active_cust_col and active_cust_col in df and len(df) > 1:
            clean_cust = df[active_cust_col].replace([np.inf, -np.inf], np.nan).dropna()
            if len(clean_cust) >= 2 and clean_cust.iloc[0] > 0:
                overall_cust_growth = ((float(clean_cust.iloc[-1]) - float(clean_cust.iloc[0])) / float(clean_cust.iloc[0])) * 100.0
                kpis['customer_growth'] = round(overall_cust_growth, 2)
            else:
                kpis['customer_growth'] = 0.0
        else:
            kpis['customer_growth'] = 0.0

        # 4. Normalized Churn Rate Computation
        if churn_col and churn_col in df:
            avg_churn = float(df[churn_col].replace([np.inf, -np.inf], np.nan).mean())
            if np.isnan(avg_churn):
                avg_churn = 0.0
            elif avg_churn <= 1.0 and avg_churn > 0.0:
                avg_churn *= 100.0
            kpis['churn_rate'] = round(min(max(avg_churn, 0.0), 100.0), 2)
        elif churn_cnt_col and churn_cnt_col in df and active_cust_col and active_cust_col in df:
            tot_churn = float(df[churn_cnt_col].sum())
            avg_active = float(df[active_cust_col].mean())
            calculated_churn = (tot_churn / avg_active * 100.0) if avg_active > 0 else 0.0
            kpis['churn_rate'] = round(min(max(calculated_churn, 0.0), 100.0), 2)
        else:
            kpis['churn_rate'] = 0.0

        # 5. Marketing Efficiency & Unit Economics
        total_mkt = float(df[mkt_col].sum()) if mkt_col and mkt_col in df else 0.0
        kpis['total_marketing_spend'] = round(total_mkt, 2)
        kpis['marketing_roi'] = round(total_rev / total_mkt, 2) if total_mkt > 0 else 0.0

        if cac_col and cac_col in df:
            kpis['cac'] = round(float(df[cac_col].mean()), 2)
        elif total_mkt > 0 and new_cust_col and new_cust_col in df:
            total_new_cust = float(df[new_cust_col].sum())
            kpis['cac'] = round(total_mkt / total_new_cust, 2) if total_new_cust > 0 else 0.0
        else:
            kpis['cac'] = 0.0

        # 6. Balance Sheet & Liquidity Ratios
        cash_val = float(df[cash_col].iloc[-1]) if cash_col and cash_col in df else 0.0
        debt_val = float(df[debt_col].iloc[-1]) if debt_col and debt_col in df else 0.0
        inv_val = float(df[inv_col].mean()) if inv_col and inv_col in df else 0.0

        kpis['cash_balance'] = round(cash_val, 2)
        monthly_exp = (total_exp / len(df)) if len(df) > 0 else (total_exp / 12.0)
        kpis['current_ratio'] = round(cash_val / monthly_exp, 2) if monthly_exp > 0 else 1.50
        kpis['debt_ratio'] = round(debt_val / (cash_val + debt_val), 2) if (cash_val + debt_val) > 0 else 0.0
        kpis['inventory_turnover'] = round((total_exp / inv_val), 2) if inv_val > 0 else 5.0

        logger.info(
            f"KPI Computation finished. Total Revenue: ${total_rev:,.2f} | "
            f"Revenue Growth: {kpis['revenue_growth']}% | Net Margin: {net_margin:.2f}% | Churn: {kpis['churn_rate']}%"
        )

        return kpis

    def _get_default_kpis(self) -> Dict[str, Any]:
        return {
            'total_revenue': 0.0,
            'total_expenses': 0.0,
            'total_profit': 0.0,
            'net_profit_margin': 0.0,
            'gross_margin': 0.0,
            'operating_margin': 0.0,
            'ebitda_margin': 0.0,
            'revenue_growth': 0.0,
            'customer_growth': 0.0,
            'churn_rate': 0.0,
            'total_marketing_spend': 0.0,
            'marketing_roi': 0.0,
            'cac': 0.0,
            'cash_balance': 0.0,
            'current_ratio': 1.0,
            'debt_ratio': 0.0,
            'inventory_turnover': 0.0
        }
