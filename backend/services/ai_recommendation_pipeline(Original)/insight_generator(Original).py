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
        roi = dashboard_metrics.get('roi', 0.0)

        # 1. Performance Observations
        if rev_growth > 5.0 and net_margin > 15.0:
            insights.append(
                f"Strong operational efficiency: Revenue growth ({rev_growth}%) is accompanied by strong profit margins ({net_margin}%)."
            )
        elif rev_growth > 5.0 and net_margin <= 5.0:
            insights.append(
                f"Revenue is expanding (+{rev_growth}%), but net profit margin remains constrained ({net_margin}%), indicating high operating costs."
            )
        else:
            insights.append(
                f"Revenue growth is muted at {rev_growth}% while maintaining a net margin profile of {net_margin}%."
            )

        # 2. Driver & Correlation Insights
        drivers = correlations.get("top_revenue_drivers", [])
        if drivers:
            top_driver = drivers[0]
            insights.append(
                f"Primary revenue driver identified: '{top_driver.get('driver_name')}' shows a "
                f"{top_driver.get('relationship_strength').lower()} correlation score of {top_driver.get('correlation_score')} with top-line income."
            )

        # 3. Forecast Trend Insights
        if forecasts.get("forecast_available"):
            trend = forecasts.get("trend", "Stable")
            dates = forecasts.get("dates", [])
            proj_rev = forecasts.get("projected_revenue", [])
            
            if dates and proj_rev:
                insights.append(
                    f"Six-month forecasting indicates a {trend.lower()} trajectory, projecting revenue to reach "
                    f"${proj_rev[-1]:,.2f} by {dates[-1]}."
                )

        # 4. Marketing Efficiency Insight
        mkt_roi = dashboard_metrics.get('marketing_roi', 0.0)
        if mkt_roi > 3.0:
            insights.append(
                f"Marketing activities generate a high return of ${mkt_roi:.2f} in revenue per dollar spent."
            )
        elif mkt_roi > 0.0:
            insights.append(
                f"Marketing ROI stands at {mkt_roi:.2f}x, suggesting room to optimize advertising channel allocation."
            )

        logger.info(f"Generated {len(insights)} analytical insights.")
        return insights
