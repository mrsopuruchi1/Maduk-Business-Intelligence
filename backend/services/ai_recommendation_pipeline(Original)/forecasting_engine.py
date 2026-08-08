"""
Maduk Business Intelligence - Forecasting Engine
Performs time-series forecasting for multi-horizon revenue and profit trajectories
including confidence intervals for 30-day, 90-day, and 365-day horizons.
"""

import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from backend.services.ai_recommendation_pipeline.models.schemas import ForecastHorizon, MultiHorizonForecast

logger = logging.getLogger("MadukBI.ForecastingEngine")


class ForecastingEngine:
    """Generates multi-horizon business forecasts with statistical confidence intervals."""

    def forecast(self, df: pd.DataFrame, mapping: Dict[str, str], periods: int = 12) -> Dict[str, Any]:
        """
        Projects primary metrics forward by specified period steps and constructs 
        1-Month (30-day), 1-Quarter (90-day), and 1-Year (365-day) forecasts.

        Args:
            df: Validated time-series pandas DataFrame.
            mapping: Canonical mapping dictionary.
            periods: Monthly forecast steps to compute (defaults to 12 months for 1-year coverage).

        Returns:
            Dict containing Pydantic MultiHorizonForecast model, time-series arrays, and trend metrics.
        """
        date_col = mapping.get('date')
        rev_col = mapping.get('revenue')
        exp_col = mapping.get('expenses')

        if not date_col or not rev_col or rev_col not in df or len(df) < 3:
            logger.warning("Insufficient time-series data available for multi-horizon forecasting.")
            empty_horizon = ForecastHorizon(revenue=0.0, profit=0.0, lower_bound_revenue=0.0, upper_bound_revenue=0.0)
            fallback_model = MultiHorizonForecast(
                next_month=empty_horizon,
                next_quarter=empty_horizon,
                next_year=empty_horizon,
                confidence_interval="N/A (Insufficient Data)"
            )
            return {
                "model": fallback_model,
                "forecast_available": False,
                "dates": [],
                "projected_revenue": [],
                "projected_expenses": [],
                "projected_profit": [],
                "trend": "Undetermined"
            }

        # Resample monthly sum
        ts_df = df.copy()
        ts_df[date_col] = pd.to_datetime(ts_df[date_col])
        ts_df = ts_df.set_index(date_col).resample('ME').sum(numeric_only=True).reset_index()
        ts_df['time_idx'] = np.arange(len(ts_df))

        X = ts_df[['time_idx']]
        y_rev = ts_df[rev_col].values

        # Linear Revenue Regression Model
        model_rev = LinearRegression()
        model_rev.fit(X, y_rev)

        # Standard Error of Residuals for Confidence Interval Calculation
        residuals = y_rev - model_rev.predict(X)
        std_error = float(np.std(residuals)) if len(residuals) > 1 else 0.0

        # Future indices and dates calculation
        future_idx = np.arange(len(ts_df), len(ts_df) + max(periods, 12)).reshape(-1, 1)
        pred_rev = model_rev.predict(future_idx)

        # Project Expenses & Profit
        if exp_col and exp_col in ts_df:
            model_exp = LinearRegression()
            model_exp.fit(X, ts_df[exp_col].values)
            pred_exp = model_exp.predict(future_idx)
        else:
            pred_exp = pred_rev * 0.75  # Standard default assumption if expenses missing

        pred_prof = pred_rev - pred_exp

        # Clean non-negative outputs
        pred_rev_clean = [round(max(0.0, float(val)), 2) for val in pred_rev]
        pred_exp_clean = [round(max(0.0, float(val)), 2) for val in pred_exp]
        pred_prof_clean = [round(float(val), 2) for val in pred_prof]

        # Generate future month string dates
        last_date = ts_df[date_col].iloc[-1]
        future_dates = [
            (pd.to_datetime(last_date) + pd.DateOffset(months=i)).strftime('%Y-%m')
            for i in range(1, len(pred_rev) + 1)
        ]

        # -------------------------------------------------------------
        # Horizon Computations: Next Month (1M), Quarter (3M), Year (12M)
        # -------------------------------------------------------------
        # 1-Month (Index 0)
        m1_rev = pred_rev_clean[0]
        m1_prof = pred_prof_clean[0]
        m1_lower = round(max(0.0, m1_rev - 1.96 * std_error), 2)
        m1_upper = round(m1_rev + 1.96 * std_error, 2)

        # 1-Quarter (Sum of Months 1-3)
        q3_rev = round(sum(pred_rev_clean[:3]), 2)
        q3_prof = round(sum(pred_prof_clean[:3]), 2)
        q3_lower = round(max(0.0, q3_rev - 1.96 * std_error * (3 ** 0.5)), 2)
        q3_upper = round(q3_rev + 1.96 * std_error * (3 ** 0.5), 2)

        # 1-Year (Sum of Months 1-12)
        y12_rev = round(sum(pred_rev_clean[:12]), 2)
        y12_prof = round(sum(pred_prof_clean[:12]), 2)
        y12_lower = round(max(0.0, y12_rev - 1.96 * std_error * (12 ** 0.5)), 2)
        y12_upper = round(y12_rev + 1.96 * std_error * (12 ** 0.5), 2)

        # Build Horizon Models
        next_month_horizon = ForecastHorizon(
            revenue=m1_rev, profit=m1_prof, lower_bound_revenue=m1_lower, upper_bound_revenue=m1_upper
        )
        next_quarter_horizon = ForecastHorizon(
            revenue=q3_rev, profit=q3_prof, lower_bound_revenue=q3_lower, upper_bound_revenue=q3_upper
        )
        next_year_horizon = ForecastHorizon(
            revenue=y12_rev, profit=y12_prof, lower_bound_revenue=y12_lower, upper_bound_revenue=y12_upper
        )

        forecast_model = MultiHorizonForecast(
            next_month=next_month_horizon,
            next_quarter=next_quarter_horizon,
            next_year=next_year_horizon,
            confidence_interval="95% CI"
        )

        slope = model_rev.coef_[0]
        trend = "Upward Acceleration" if slope > 100 else ("Downward Pressure" if slope < -100 else "Stable Horizontal")

        logger.info(
            f"Forecasting Engine generated multi-horizon projections. "
            f"1M Rev: {m1_rev} | 1Q Rev: {q3_rev} | 1Y Rev: {y12_rev}"
        )

        return {
            "model": forecast_model,
            "forecast_available": True,
            "dates": future_dates,
            "projected_revenue": pred_rev_clean,
            "projected_expenses": pred_exp_clean,
            "projected_profit": pred_prof_clean,
            "trend": trend,
            "revenue_slope": round(float(slope), 2)
        }
