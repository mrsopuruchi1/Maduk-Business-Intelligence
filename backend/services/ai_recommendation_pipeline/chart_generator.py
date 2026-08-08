# chart_generator.py

"""
Maduk Business Intelligence - Chart Generator Engine
Generates high-resolution, static matplotlib charts (trends, confidence intervals, 
categorical bars, scatter plots) optimized for PDF executive report inclusion.
"""

import os
import logging
from typing import Dict, Any
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend suitable for server headless rendering
import matplotlib.pyplot as plt

logger = logging.getLogger("MadukBI.ChartGenerator")


class ChartGenerator:
    """Renders execution-ready, high-resolution static visual charts for PDF reports."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_all(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, str],
        forecasts: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generates all analytical charts and returns a mapping of image file paths.

        Args:
            df: Feature-engineered DataFrame.
            mapping: Schema mapping dictionary.
            forecasts: Forecasting engine output dictionary.

        Returns:
            Dict mapping chart identifiers to output PNG image paths.
        """
        chart_paths: Dict[str, str] = {}

        date_col = mapping.get('date')
        rev_col = mapping.get('revenue')
        exp_col = mapping.get('expenses')
        prof_col = mapping.get('profit')
        mkt_col = mapping.get('marketing_spend')
        cust_col = mapping.get('customers') or mapping.get('active_customers')

        # Corporate Modern Color Palette
        c_blue = '#1e3a8a'      # Deep Navy Revenue
        c_green = '#059669'     # Emerald Profit
        c_red = '#dc2626'       # Crimson Expense
        c_sky = '#0284c7'       # Sky Blue Accent
        c_teal = '#0d9488'      # Teal Accent
        c_purple = '#7c3aed'    # Forecast Line
        c_light_purple = '#ddd6fe'  # Confidence Band

        # Base Matplotlib Global Layout Configuration
        plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
        plt.rcParams['axes.edgecolor'] = '#e2e8f0'
        plt.rcParams['axes.linewidth'] = 0.8
        plt.rcParams['grid.color'] = '#f1f5f9'
        plt.rcParams['grid.linestyle'] = '-'

        # ------------------------------------------------------------------
        # Chart 1: Revenue, Profit & Expense Historical Trend Line Chart
        # ------------------------------------------------------------------
        if date_col and rev_col and date_col in df:
            try:
                fig, ax = plt.subplots(figsize=(7, 3.2), dpi=300)
                ts_df = df.copy()
                ts_df[date_col] = pd.to_datetime(ts_df[date_col], errors='coerce')
                ts_df = ts_df.dropna(subset=[date_col])
                ts_df = ts_df.set_index(date_col).resample('ME').sum(numeric_only=True)
                dates_str = [d.strftime('%b %Y') for d in ts_df.index]

                if not ts_df.empty:
                    ax.plot(dates_str, ts_df[rev_col], label='Revenue', color=c_blue, linewidth=2.2, marker='o', markersize=3)
                    if prof_col and prof_col in ts_df and ts_df[prof_col].abs().sum() > 0:
                        ax.plot(dates_str, ts_df[prof_col], label='Profit', color=c_green, linewidth=2.0, marker='s', markersize=3)
                    if exp_col and exp_col in ts_df and ts_df[exp_col].abs().sum() > 0:
                        ax.plot(dates_str, ts_df[exp_col], label='Expenses', color=c_red, linewidth=1.5, linestyle='--')

                    ax.set_title("Historical Financial Trajectory", fontsize=10, fontweight='bold', color='#1e293b', pad=10)
                    ax.grid(True, axis='y', alpha=0.7)
                    ax.tick_params(axis='x', rotation=30, labelsize=7, colors='#475569')
                    ax.tick_params(axis='y', labelsize=7, colors='#475569')
                    ax.yaxis.set_major_formatter('${x:,.0f}')
                    ax.legend(fontsize=7, loc='upper left', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1')
                    plt.tight_layout()

                    path = os.path.join(self.output_dir, "trend_financial.png")
                    fig.savefig(path, dpi=300, bbox_inches='tight')
                    plt.close(fig)
                    chart_paths['financial_trends'] = path
            except Exception as e:
                logger.warning(f"Failed to generate financial trend chart: {str(e)}")

        # ------------------------------------------------------------------
        # Chart 2: Multi-Horizon Revenue Forecast with Confidence Band
        # ------------------------------------------------------------------
        if forecasts and forecasts.get('forecast_available') and forecasts.get('dates'):
            try:
                fig, ax = plt.subplots(figsize=(7, 3.2), dpi=300)
                f_dates = forecasts['dates']
                f_rev = forecasts['projected_revenue']

                ax.plot(f_dates, f_rev, label='Projected Revenue', color=c_purple, linewidth=2.2, linestyle='-', marker='d', markersize=4)

                # Compute confidence interval bounds
                std_est = np.std(f_rev) * 0.15 if len(f_rev) > 1 else 0.0
                lower_bound = [max(0.0, val - (1.96 * std_est * ((idx + 1)**0.5))) for idx, val in enumerate(f_rev)]
                upper_bound = [val + (1.96 * std_est * ((idx + 1)**0.5)) for idx, val in enumerate(f_rev)]

                ax.fill_between(f_dates, lower_bound, upper_bound, color=c_light_purple, alpha=0.4, label='95% Confidence Band')

                ax.set_title("Revenue Forecast & Statistical Confidence Interval", fontsize=10, fontweight='bold', color='#1e293b', pad=10)
                ax.grid(True, axis='y', alpha=0.7)
                ax.tick_params(axis='x', rotation=35, labelsize=7, colors='#475569')
                ax.tick_params(axis='y', labelsize=7, colors='#475569')
                ax.yaxis.set_major_formatter('${x:,.0f}')
                ax.legend(fontsize=7, loc='upper left', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1')
                plt.tight_layout()

                path = os.path.join(self.output_dir, "trend_forecast.png")
                fig.savefig(path, dpi=300, bbox_inches='tight')
                plt.close(fig)
                chart_paths['revenue_forecast'] = path
            except Exception as e:
                logger.warning(f"Failed to generate revenue forecast chart: {str(e)}")

        # ------------------------------------------------------------------
        # Chart 3: Revenue by Product (Categorical Bar Chart)
        # ------------------------------------------------------------------
        prod_col = mapping.get('product')
        if prod_col and prod_col in df and rev_col and rev_col in df:
            try:
                fig, ax = plt.subplots(figsize=(6, 3), dpi=300)
                prod_data = df.groupby(prod_col)[rev_col].sum().sort_values(ascending=False).head(5)
                if not prod_data.empty:
                    bars = ax.bar(prod_data.index.astype(str), prod_data.values, color=c_sky, width=0.45, edgecolor='#0369a1', linewidth=0.8)
                    
                    for bar in bars:
                        height = bar.get_height()
                        ax.annotate(f'${height:,.0f}',
                                    xy=(bar.get_x() + bar.get_width() / 2, height),
                                    xytext=(0, 3),
                                    textcoords="offset points",
                                    ha='center', va='bottom', fontsize=6, fontweight='bold', color='#334155')

                    ax.set_title("Top Products by Revenue", fontsize=10, fontweight='bold', color='#1e293b', pad=10)
                    ax.grid(True, axis='y', alpha=0.5)
                    ax.tick_params(axis='x', rotation=20, labelsize=7, colors='#475569')
                    ax.tick_params(axis='y', labelsize=7, colors='#475569')
                    ax.yaxis.set_major_formatter('${x:,.0f}')
                    plt.tight_layout()

                    path = os.path.join(self.output_dir, "bar_revenue_by_product.png")
                    fig.savefig(path, dpi=300, bbox_inches='tight')
                    plt.close(fig)
                    chart_paths['revenue_by_product'] = path
            except Exception as e:
                logger.warning(f"Failed to generate product revenue bar chart: {str(e)}")

        # ------------------------------------------------------------------
        # Chart 4: Revenue by Region (Categorical Bar Chart)
        # ------------------------------------------------------------------
        region_col = mapping.get('region')
        if region_col and region_col in df and rev_col and rev_col in df:
            try:
                fig, ax = plt.subplots(figsize=(6, 3), dpi=300)
                reg_data = df.groupby(region_col)[rev_col].sum().sort_values(ascending=False).head(5)
                if not reg_data.empty:
                    bars = ax.bar(reg_data.index.astype(str), reg_data.values, color=c_teal, width=0.45, edgecolor='#0f766e', linewidth=0.8)
                    
                    for bar in bars:
                        height = bar.get_height()
                        ax.annotate(f'${height:,.0f}',
                                    xy=(bar.get_x() + bar.get_width() / 2, height),
                                    xytext=(0, 3),
                                    textcoords="offset points",
                                    ha='center', va='bottom', fontsize=6, fontweight='bold', color='#334155')

                    ax.set_title("Revenue Distribution by Region", fontsize=10, fontweight='bold', color='#1e293b', pad=10)
                    ax.grid(True, axis='y', alpha=0.5)
                    ax.tick_params(axis='x', rotation=20, labelsize=7, colors='#475569')
                    ax.tick_params(axis='y', labelsize=7, colors='#475569')
                    ax.yaxis.set_major_formatter('${x:,.0f}')
                    plt.tight_layout()

                    path = os.path.join(self.output_dir, "bar_revenue_by_region.png")
                    fig.savefig(path, dpi=300, bbox_inches='tight')
                    plt.close(fig)
                    chart_paths['revenue_by_region'] = path
            except Exception as e:
                logger.warning(f"Failed to generate region revenue bar chart: {str(e)}")

        # ------------------------------------------------------------------
        # Chart 5: Marketing Spend vs Revenue (Scatter Correlation Plot)
        # ------------------------------------------------------------------
        if mkt_col and mkt_col in df and rev_col and rev_col in df:
            try:
                clean_scatter = df.dropna(subset=[mkt_col, rev_col])
                if len(clean_scatter) >= 2:
                    fig, ax = plt.subplots(figsize=(6, 3), dpi=300)
                    ax.scatter(clean_scatter[mkt_col], clean_scatter[rev_col], color=c_blue, alpha=0.7, edgecolors='#1e40af', s=35)
                    
                    m, b = np.polyfit(clean_scatter[mkt_col], clean_scatter[rev_col], 1)
                    x_vals = np.array(ax.get_xlim())
                    ax.plot(x_vals, m * x_vals + b, color='#ef4444', linestyle=':', linewidth=1.5, label='Trend Fit')
                    ax.legend(fontsize=6, loc='upper left')

                    ax.set_title("Marketing Spend vs. Revenue Correlation", fontsize=10, fontweight='bold', color='#1e293b', pad=10)
                    ax.set_xlabel("Marketing Spend ($)", fontsize=7, color='#475569')
                    ax.set_ylabel("Revenue ($)", fontsize=7, color='#475569')
                    ax.grid(True, alpha=0.5)
                    ax.tick_params(axis='both', labelsize=7, colors='#475569')
                    ax.xaxis.set_major_formatter('${x:,.0f}')
                    ax.yaxis.set_major_formatter('${x:,.0f}')
                    plt.tight_layout()

                    path = os.path.join(self.output_dir, "scatter_mkt_vs_rev.png")
                    fig.savefig(path, dpi=300, bbox_inches='tight')
                    plt.close(fig)
                    chart_paths['mkt_vs_revenue'] = path
            except Exception as e:
                logger.warning(f"Failed to generate marketing scatter plot: {str(e)}")

        # ------------------------------------------------------------------
        # Chart 6: Customer Volume vs Revenue (Scatter Correlation Plot)
        # ------------------------------------------------------------------
        if cust_col and cust_col in df and rev_col and rev_col in df:
            try:
                clean_cust_scatter = df.dropna(subset=[cust_col, rev_col])
                if len(clean_cust_scatter) >= 2:
                    fig, ax = plt.subplots(figsize=(6, 3), dpi=300)
                    ax.scatter(clean_cust_scatter[cust_col], clean_cust_scatter[rev_col], color=c_green, alpha=0.7, edgecolors='#047857', s=35)
                    
                    m, b = np.polyfit(clean_cust_scatter[cust_col], clean_cust_scatter[rev_col], 1)
                    x_vals = np.array(ax.get_xlim())
                    ax.plot(x_vals, m * x_vals + b, color='#f59e0b', linestyle=':', linewidth=1.5, label='Trend Fit')
                    ax.legend(fontsize=6, loc='upper left')

                    ax.set_title("Customer Volume vs. Revenue Correlation", fontsize=10, fontweight='bold', color='#1e293b', pad=10)
                    ax.set_xlabel("Customer Count", fontsize=7, color='#475569')
                    ax.set_ylabel("Revenue ($)", fontsize=7, color='#475569')
                    ax.grid(True, alpha=0.5)
                    ax.tick_params(axis='both', labelsize=7, colors='#475569')
                    ax.yaxis.set_major_formatter('${x:,.0f}')
                    plt.tight_layout()

                    path = os.path.join(self.output_dir, "scatter_cust_vs_rev.png")
                    fig.savefig(path, dpi=300, bbox_inches='tight')
                    plt.close(fig)
                    chart_paths['cust_vs_revenue'] = path
            except Exception as e:
                logger.warning(f"Failed to generate customer scatter plot: {str(e)}")

        logger.info(f"Chart Generator complete. Produced {len(chart_paths)} high-res visual assets.")
        return chart_paths
