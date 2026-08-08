"""
Maduk Business Intelligence - Insight Generator Engine
Transforms quantitative metrics, correlation matrices, and forecasts into natural language observations.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("MadukBI.InsightGenerator")


class InsightGenerator:
    """Generates natural English executive observations from quantitative analytics."""

    def __init__(self, llm_writer: Optional[Any] = None):
        self.llm_writer = llm_writer

    def generate_insights(
        self,
        dashboard_metrics: Dict[str, Any],
        correlations: Dict[str, Any],
        forecasts: Dict[str, Any]
    ) -> List[str]:
        """
        Transforms analysis matrices into readable narrative bullet observations.

        Args:
            dashboard_metrics: 16 core executive KPIs payload.
            correlations: Correlation matrix and drivers context.
            forecasts: Time-series projection payload.

        Returns:
            List of natural English observation strings.
        """
        insights: List[str] = []

        rev_growth = dashboard_metrics.get('revenue_growth', 0.0)
        net_margin = dashboard_metrics.get('net_profit_margin', 0.0)
        gross_margin = dashboard_metrics.get('gross_margin')
        churn_rate = dashboard_metrics.get('churn_rate', 0.0)

        # 1. Financial Performance Observations
        if rev_growth > 5.0 and net_margin > 15.0:
            insights.append(
                f"Strong operational expansion: Revenue expanded by {rev_growth:.2f}% while sustaining high net profit margins of {net_margin:.2f}%."
            )
        elif rev_growth > 5.0 and net_margin <= 5.0:
            insights.append(
                f"Revenue is expanding (+{rev_growth:.2f}%), but net profit margin remains constrained at {net_margin:.2f}%, indicating operational cost pressures."
            )
        elif rev_growth < 0.0:
            insights.append(
                f"Revenue contracted by {abs(rev_growth):.2f}% over the evaluated timeframe with a net margin profile of {net_margin:.2f}%."
            )
        else:
            gm_text = f" and gross margin of {gross_margin:.2f}%" if gross_margin is not None else ""
            insights.append(
                f"Revenue growth remains stable at {rev_growth:.2f}% with a net margin of {net_margin:.2f}%{gm_text}."
            )

        # 2. Customer Retention Observation
        if churn_rate > 10.0:
            insights.append(
                f"Elevated customer churn risk: Churn rate is currently elevated at {churn_rate:.2f}%, requiring customer retention focus."
            )
        elif churn_rate > 0.0:
            insights.append(
                f"Customer retention is healthy with a churn rate controlled at {churn_rate:.2f}%."
            )

        # 3. Driver & Correlation Insights
        drivers = correlations.get("top_revenue_drivers", []) if correlations else []
        if drivers and isinstance(drivers, list) and len(drivers) > 0:
            top_driver = drivers[0]
            if isinstance(top_driver, dict):
                driver_name = top_driver.get('driver_name', 'Primary Driver')
                strength = str(top_driver.get('relationship_strength', 'moderate')).lower()
                score = top_driver.get('correlation_score')
                score_fmt = f"{score:.2f}" if isinstance(score, (int, float)) else "N/A"

                insights.append(
                    f"Primary revenue driver identified: '{driver_name}' shows a "
                    f"{strength} correlation score of {score_fmt} with top-line income."
                )

        # 4. Forecast Trend Insights
        if forecasts and forecasts.get("forecast_available"):
            trend = str(forecasts.get("trend", "Stable"))
            dates = forecasts.get("dates", [])
            proj_rev = forecasts.get("projected_revenue", [])
            
            if dates and proj_rev and len(dates) == len(proj_rev):
                last_val = proj_rev[-1]
                val_fmt = f"${last_val:,.2f}" if isinstance(last_val, (int, float)) else str(last_val)
                insights.append(
                    f"Forecasting models indicate a {trend.lower()} trajectory, projecting revenue to reach "
                    f"{val_fmt} by {dates[-1]}."
                )

        # 5. Marketing Efficiency Insight
        mkt_roi = dashboard_metrics.get('marketing_roi')
        if mkt_roi is not None and isinstance(mkt_roi, (int, float)):
            if mkt_roi > 3.0:
                insights.append(
                    f"Marketing efficiency is high, generating ${mkt_roi:.2f} in revenue per dollar spent ({mkt_roi:.2f}x ROI)."
                )
            elif mkt_roi > 0.0:
                insights.append(
                    f"Marketing ROI stands at {mkt_roi:.2f}x, suggesting opportunity for acquisition channel optimization."
                )

        # 6. Optional LLM Refinement
        if self.llm_writer and hasattr(self.llm_writer, 'refine_insights'):
            try:
                refined = self.llm_writer.refine_insights(insights, dashboard_metrics)
                if refined and isinstance(refined, list):
                    return refined
            except Exception as e:
                logger.warning(f"LLM refinement failed, falling back to rule-based insights: {e}")

        logger.info(f"Generated {len(insights)} analytical insights.")
        return insights
