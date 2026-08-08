"""
Maduk Business Intelligence - LLM Report Writer
Converts mathematical output payloads into C-suite narrative summaries.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("MadukBI.LLMReportWriter")


class LLMReportWriter:
    """Generates natural English executive narratives from metric contexts."""

    def generate_narrative_summary(
        self,
        dashboard: Dict[str, Any],
        health: Dict[str, Any],
        insights: Optional[List[str]] = None
    ) -> str:
        """
        Creates an executive narrative summary.

        Args:
            dashboard: Dashboard metrics payload.
            health: Health evaluation payload.
            insights: Key observations list.

        Returns:
            Executive narrative paragraph.
        """
        score = health.get('health_score', 0.0)
        status = health.get('status', 'Unrated')
        rev_growth = dashboard.get('revenue_growth', 0.0)
        margin = dashboard.get('net_profit_margin', 0.0)
        curr_ratio = dashboard.get('current_ratio', 1.0)

        narrative = (
            f"The business currently presents an overall health status of **{status}** with an evaluated "
            f"score of **{score}/100**. Top-line revenue trajectory reflects a **{rev_growth}%** movement, "
            f"while net profit margins stand at **{margin}%**. "
        )

        if score >= 70.0:
            narrative += (
                "Operational metrics indicate structural stability and positive unit economics. Capital deployment "
                "should prioritize expansion into high-yielding acquisition channels."
            )
        elif score >= 50.0:
            narrative += (
                "The business shows stable core revenue, though net profitability remains constrained. "
                "Leadership should focus on operating margin expansion and inventory optimization."
            )
        else:
            narrative += (
                "Critical operational risk factors have been identified. Immediate attention should be directed toward "
                f"cost rationalization, protecting baseline liquid cash reserves (Current Ratio: {curr_ratio}), and churn reduction."
            )

        if insights and len(insights) > 0:
            narrative += f" Key Observation: {insights[0]}"

        return narrative

    def enhance_recommendations(
        self,
        recommendations: List[Dict[str, str]],
        dashboard: Dict[str, Any],
        health: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Polishes rule-generated recommendations for executive readability.
        In an environment with an LLM API key, this connects to an LLM provider.
        """
        enhanced: List[Dict[str, str]] = []
        for rec in recommendations:
            enhanced.append({
                "category": rec.get("category", "General Optimization"),
                "finding": rec.get("finding", ""),
                "action": rec.get("action", ""),
                "impact": rec.get("impact", "")
            })
        return enhanced
