# recommendation_engine.py

"""
Maduk Business Intelligence - Recommendation Engine
Generates rule-grounded strategic recommendations enhanced by optional LLM context.
Outputs time-phased priority action plans across 30-day, 90-day, and 12-month execution horizons.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from backend.services.ai_recommendation_pipeline.models.schemas import TimePhasedActionPlan

logger = logging.getLogger("MadukBI.RecommendationEngine")


class RecommendationEngine:
    """Generates rule-based optimization recommendations and time-phased priority action plans."""

    def __init__(self, llm_writer: Optional[Any] = None):
        self.llm_writer = llm_writer

    def generate(
        self,
        dashboard_metrics: Dict[str, Any],
        health: Dict[str, Any],
        anomalies: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates operational conditions and generates actionable, time-phased strategic recommendations.

        Args:
            dashboard_metrics: Core executive metrics.
            health: Health score evaluation output.
            anomalies: List or Dict container of flagged statistical anomalies.

        Returns:
            Dict containing Pydantic TimePhasedActionPlan model, structured rules list, and functional strategy categories.
        """
        rules_triggered: List[Dict[str, str]] = []
        
        immediate_30_days: List[str] = []
        medium_term_90_days: List[str] = []
        long_term_12_months: List[str] = []

        revenue_improvements: List[str] = []
        profit_improvements: List[str] = []
        risk_reductions: List[str] = []

        # Extract underlying list if anomalies is passed as a wrapper dictionary
        anomaly_list: List[Any] = []
        if isinstance(anomalies, dict):
            anomaly_list = (
                anomalies.get("anomalies_list") 
                or anomalies.get("anomalies") 
                or []
            )
        elif isinstance(anomalies, list):
            anomaly_list = anomalies

        net_margin = float(dashboard_metrics.get('net_profit_margin', 0.0) or 0.0)
        rev_growth = float(dashboard_metrics.get('revenue_growth', 0.0) or 0.0)
        churn = float(dashboard_metrics.get('churn_rate', 0.0) or 0.0)
        curr_ratio = float(dashboard_metrics.get('current_ratio', 1.0) or 1.0)
        mkt_roi = float(dashboard_metrics.get('marketing_roi', 0.0) or 0.0)

        # -------------------------------------------------------------
        # Rule Evaluation & Time-Horizon Classification
        # -------------------------------------------------------------
        
        # Rule 1: Liquidity & Working Capital Management (Immediate 30-day Focus)
        if curr_ratio < 1.25:
            finding = f"Current Liquidity Ratio of {curr_ratio:.2f} indicates potential working capital pressure."
            action = "Offer 2/10 net 30 early payment discounts to accelerate accounts receivable collections and liquidate stagnant inventory."
            impact = "Builds liquid cash reserves and stabilizes immediate operational cash flow."
            
            rules_triggered.append({
                "category": "Liquidity & Working Capital",
                "finding": finding,
                "action": action,
                "impact": impact,
                "time_horizon": "30 Days"
            })
            immediate_30_days.append(f"Working Capital: {action}")
            risk_reductions.append(f"Improve liquidity cushion: {action}")

        # Rule 2: Risk Mitigation from Anomalies (Immediate 30-day Focus)
        if anomaly_list:
            for anomaly in anomaly_list[:2]:
                if isinstance(anomaly, dict):
                    metric_name = anomaly.get('metric', 'Operational Anomaly')
                    period = anomaly.get('date_or_period') or anomaly.get('date', 'Recent Period')
                else:
                    metric_name = getattr(anomaly, 'metric', 'Operational Anomaly')
                    period = getattr(anomaly, 'details', 'Recent Period')

                action = f"Investigate root cause of variance spike in {metric_name} during period {period}."
                
                rules_triggered.append({
                    "category": "Risk Mitigation",
                    "finding": f"Flagged risk event: {metric_name} on {period}.",
                    "action": action,
                    "impact": "Prevents recurring operational cost leakage.",
                    "time_horizon": "30 Days"
                })
                immediate_30_days.append(f"Risk Audit: {action}")
                risk_reductions.append(f"Investigate {metric_name} outlier to prevent margin erosion.")

        # Rule 3: Profit Margin & Cost Optimization (Medium-term 90-day Focus)
        if net_margin < 10.0:
            action = "Conduct a vendor spend audit on top operating expenses and renegotiate COGS supplier contracts."
            rules_triggered.append({
                "category": "Profitability & Cost Control",
                "finding": f"Net Profit Margin stands at {net_margin:.1f}% (Below 10.0% benchmark).",
                "action": action,
                "impact": "Expands net profit margin by +3.0% to +5.0% within 90 days.",
                "time_horizon": "90 Days"
            })
            medium_term_90_days.append(f"Cost Audit: {action}")
            profit_improvements.append(f"COGS Optimization: {action}")

        # Rule 4: Marketing Spend Allocation (Medium-term 90-day Focus)
        if 0.0 < mkt_roi < 2.5:
            action = "Reallocate performance advertising budgets away from underperforming channels toward high-converting segments."
            rules_triggered.append({
                "category": "Marketing Efficiency",
                "finding": f"Marketing ROI of {mkt_roi:.2f}x indicates sub-optimal spend efficiency.",
                "action": action,
                "impact": "Increases customer acquisition efficiency by 25.0%.",
                "time_horizon": "90 Days"
            })
            medium_term_90_days.append(f"Marketing Reallocation: {action}")
            revenue_improvements.append(f"Acquisition Efficiency: {action}")

        # Rule 5: Customer Retention & Churn Mitigation (Medium-term 90-day Focus)
        if churn > 4.0:
            action = "Implement an automated customer success workflow targeting accounts showing decreased product engagement."
            rules_triggered.append({
                "category": "Customer Retention",
                "finding": f"Customer Churn Rate at {churn:.1f}% exceeds healthy retention levels (<3.0%).",
                "action": action,
                "impact": "Protects recurring baseline revenue and lowers customer churn by 1.5%.",
                "time_horizon": "90 Days"
            })
            medium_term_90_days.append(f"Retention Automation: {action}")
            revenue_improvements.append(f"Churn Reduction: {action}")

        # Rule 6: Revenue Expansion & Market Growth (Long-term 12-month Focus)
        if rev_growth < 5.0:
            action = "Introduce tiered value product/service bundles and expand cross-sell channels into adjacent customer segments."
            rules_triggered.append({
                "category": "Revenue Expansion",
                "finding": f"Annualized revenue growth rate is sluggish at {rev_growth:.1f}%.",
                "action": action,
                "impact": "Drives long-term top-line growth by 8.0% to 15.0%.",
                "time_horizon": "12 Months"
            })
            long_term_12_months.append(f"Market Expansion: {action}")
            revenue_improvements.append(f"Product Bundling: {action}")

        # Baseline Fallback Actions if no rules were triggered
        if not immediate_30_days:
            immediate_30_days.append("Establish automated weekly financial performance reporting dashboards for department heads.")
        if not medium_term_90_days:
            medium_term_90_days.append("Optimize customer onboarding workflows to increase 90-day retention and lifetime value.")
        if not long_term_12_months:
            long_term_12_months.append("Evaluate strategic partnership and geographic expansion opportunities to increase enterprise valuation.")

        if not revenue_improvements:
            revenue_improvements.append("Refine sales expansion playbook and introduce cross-sell incentives for existing accounts.")
        if not profit_improvements:
            profit_improvements.append("Audit administrative overhead to identify automation opportunities for recurring operational expenses.")
        if not risk_reductions:
            risk_reductions.append("Conduct quarterly cybersecurity and compliance reviews to mitigate enterprise liability.")

        # Construct Pydantic Action Plan Model
        action_plan_model = TimePhasedActionPlan(
            immediate_30_days=immediate_30_days,
            medium_term_90_days=medium_term_90_days,
            long_term_12_months=long_term_12_months
        )

        # Optional LLM Enhancement Layer
        if self.llm_writer and hasattr(self.llm_writer, 'enhance_recommendations'):
            try:
                enhanced = self.llm_writer.enhance_recommendations(rules_triggered, dashboard_metrics, health)
                if isinstance(enhanced, list) and len(enhanced) > 0:
                    rules_triggered = enhanced
            except Exception as e:
                logger.warning(f"LLM enhancement layer skipped: {str(e)}")

        logger.info(
            f"Generated priority action plan: "
            f"30-Day ({len(immediate_30_days)}), 90-Day ({len(medium_term_90_days)}), 12-Month ({len(long_term_12_months)})."
        )

        return {
            "model": action_plan_model,
            "rules_triggered": rules_triggered,
            "action_plan": {
                "immediate_30_days": immediate_30_days,
                "medium_term_90_days": medium_term_90_days,
                "long_term_12_months": long_term_12_months
            },
            "functional_recommendations": {
                "revenue_improvement": revenue_improvements,
                "profit_improvement": profit_improvements,
                "risk_reduction": risk_reductions
            }
        }
