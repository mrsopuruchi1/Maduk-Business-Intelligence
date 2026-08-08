"""
Maduk Business Intelligence - Dashboard Generator
================================================
File: backend/services/ai_prediction_pipeline/dashboard_generator.py
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd

from .visualization_generator import VisualizationGenerator

logger = logging.getLogger("MadukBI.DashboardGenerator")


class DashboardGenerator:
    """Builds complete executive dashboard metadata and component configurations."""

    def __init__(self, viz_generator: Optional[VisualizationGenerator] = None):
        self.viz_generator = viz_generator or VisualizationGenerator()

    def build_config(
        self,
        historical_df: pd.DataFrame,
        forecast_df: pd.DataFrame,
        date_col: str,
        target_col: str,
        metrics: Dict[str, float],
        summary_data: Dict[str, Any],
        chart_specs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compiles layout configs, card definitions, and chart assignments for frontend consumption.

        Returns:
            Dict containing dashboard configuration and structure metadata.
        """
        logger.info("Building dashboard layout payload configuration...")

        kpis = summary_data.get("kpis", {})

        cards = [
            {
                "id": "card_baseline",
                "label": "Current Baseline",
                "value": kpis.get("current_period_baseline", 0.0),
                "format": "currency",
                "type": "secondary"
            },
            {
                "id": "card_projected_total",
                "label": "Projected Horizon Total",
                "value": kpis.get("projected_horizon_total", 0.0),
                "delta": f"{kpis.get('growth_rate_pct', 0.0):+.1f}%",
                "format": "currency",
                "type": "primary"
            },
            {
                "id": "card_confidence",
                "label": "Forecast Confidence",
                "value": kpis.get("forecast_confidence", "N/A"),
                "subtext": f"Backtest MAPE: {metrics.get('MAPE', 0.0):.2%}",
                "type": "info"
            },
            {
                "id": "card_model",
                "label": "Winning Model",
                "value": kpis.get("selected_model", "Automated"),
                "format": "text",
                "type": "neutral"
            }
        ]

        layout = {
            "grid_columns": 12,
            "sections": [
                {
                    "title": "Executive Summary & Key Indicators",
                    "components": ["kpi_cards", "executive_narrative"]
                },
                {
                    "title": "Forecast Trajectory & Scenario Modeling",
                    "components": ["forecast_chart_plotly"]
                },
                {
                    "title": "Predictive Drivers & Risk Assessment",
                    "components": ["feature_drivers_chart_plotly", "business_risks", "recommended_actions"]
                }
            ]
        }

        return {
            "title": "Maduk BI Executive Predictive Dashboard",
            "kpi_cards": cards,
            "layout": layout,
            "active_theme": "light"
        }
