"""
Maduk Business Intelligence - Visualization Generator
=====================================================
File: backend/services/ai_prediction_pipeline/visualization_generator.py
"""

import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

logger = logging.getLogger("MadukBI.VisualizationGenerator")


class VisualizationGenerator:
    """Generates interactive Plotly visual specifications ready for frontend rendering."""

    def generate_chart_specs(
        self,
        historical_df: pd.DataFrame,
        forecast_df: pd.DataFrame,
        auxiliary_forecasts: Dict[str, List[Dict[str, Any]]],
        date_col: str,
        target_col: str,
        feature_importance: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Builds reusable Plotly chart specifications.

        Returns:
            Dict containing Plotly JSON specs for forecast, drivers, and auxiliary charts.
        """
        logger.info("Generating Plotly visual specifications...")
        specs = {}

        # 1. Main Interactive Forecast & Scenario Chart
        specs["forecast_chart_plotly"] = self._build_forecast_scenario_chart(
            historical_df=historical_df,
            forecast_df=forecast_df,
            date_col=date_col,
            target_col=target_col
        )

        # 2. Feature Importance / Driver Chart
        if feature_importance:
            specs["feature_drivers_chart_plotly"] = self._build_feature_drivers_chart(feature_importance)

        # 3. Auxiliary Targets Chart (Profit / Cash Flow if available)
        if auxiliary_forecasts:
            specs["auxiliary_forecasts_chart_plotly"] = self._build_auxiliary_chart(auxiliary_forecasts, date_col)

        return specs

    def _build_forecast_scenario_chart(
        self,
        historical_df: pd.DataFrame,
        forecast_df: pd.DataFrame,
        date_col: str,
        target_col: str
    ) -> Dict[str, Any]:
        """Constructs interactive historical vs forecast line chart with confidence bounds and scenarios."""
        fig = go.Figure()

        # Historical Baseline
        hist_dates = pd.to_datetime(historical_df[date_col])
        fig.add_trace(go.Scatter(
            x=hist_dates,
            y=historical_df[target_col],
            mode="lines+markers",
            name="Historical Actuals",
            line=dict(color="#1f77b4", width=2.5),
            marker=dict(size=5)
        ))

        forecast_dates = pd.to_datetime(forecast_df[date_col])

        # Confidence Interval Band
        if "lower_bound" in forecast_df.columns and "upper_bound" in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=list(forecast_dates) + list(forecast_dates)[::-1],
                y=list(forecast_df["upper_bound"]) + list(forecast_df["lower_bound"])[::-1],
                fill="toself",
                fillcolor="rgba(44, 160, 44, 0.15)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                showlegend=True,
                name="Confidence Band"
            ))

        # Expected Baseline Forecast
        fig.add_trace(go.Scatter(
            x=forecast_dates,
            y=forecast_df["forecast"],
            mode="lines+markers",
            name="Expected Forecast",
            line=dict(color="#2ca02c", width=3, dash="dash"),
            marker=dict(size=6)
        ))

        # Strategic Scenarios
        if "optimistic" in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=forecast_dates,
                y=forecast_df["optimistic"],
                mode="lines",
                name="Optimistic Scenario",
                line=dict(color="#ff7f0e", width=1.5, dash="dot")
            ))

        if "conservative" in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=forecast_dates,
                y=forecast_df["conservative"],
                mode="lines",
                name="Conservative Scenario",
                line=dict(color="#d62728", width=1.5, dash="dot")
            ))

        fig.update_layout(
            title="Interactive Forecast & Scenario Trajectory",
            xaxis_title="Date",
            yaxis_title=target_col.replace("_", " ").title(),
            template="plotly_white",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        return fig.to_dict()

    def _build_feature_drivers_chart(self, feature_importance: Dict[str, float]) -> Dict[str, Any]:
        """Constructs horizontal bar chart ranking predictive features."""
        top_features = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:8])
        df_imp = pd.DataFrame(list(top_features.items()), columns=["Driver", "Importance"])

        fig = px.bar(
            df_imp,
            x="Importance",
            y="Driver",
            orientation="h",
            title="Primary Predictive Feature Drivers",
            color="Importance",
            color_continuous_scale="Blues"
        )
        fig.update_layout(
            template="plotly_white",
            yaxis=dict(autorange="reversed"),
            coloraxis_showscale=False
        )
        return fig.to_dict()

    def _build_auxiliary_chart(
        self,
        auxiliary_forecasts: Dict[str, List[Dict[str, Any]]],
        date_col: str
    ) -> Dict[str, Any]:
        """Constructs multi-series forecast comparison for auxiliary targets."""
        fig = go.Figure()

        for target_name, records in auxiliary_forecasts.items():
            if not records:
                continue
            df_aux = pd.DataFrame(records)
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(df_aux["date"]),
                y=df_aux["forecast"],
                mode="lines+markers",
                name=f"Forecast: {target_name.replace('_', ' ').title()}"
            ))

        fig.update_layout(
            title="Auxiliary Operational Forecasts",
            xaxis_title="Date",
            template="plotly_white",
            hovermode="x unified"
        )
        return fig.to_dict()
