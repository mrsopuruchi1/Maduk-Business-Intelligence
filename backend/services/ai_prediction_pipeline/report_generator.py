"""
Maduk Business Intelligence - Executive Report Generator
======================================================
File: backend/services/ai_prediction_pipeline/report_generator.py
"""

import logging
from typing import Dict, Any
import pandas as pd
import json

logger = logging.getLogger("MadukBI.ReportGenerator")


class ReportGenerator:
    """Produces standalone Markdown and HTML executive forecasting reports."""

    def generate_markdown_report(self, payload: Dict[str, Any]) -> str:
        """
        Renders an executive summary report as Markdown text.

        Args:
            payload: Output dictionary from AIPredictionPipeline.run().

        Returns:
            str: Markdown formatted document.
        """
        logger.info("Generating Markdown executive report...")
        
        meta = payload.get("pipeline_metadata", {})
        kpis = payload.get("kpi_cards", {})
        model_info = payload.get("best_model_and_selection", {})
        risks = payload.get("business_risks", [])
        actions = payload.get("recommended_actions", [])

        md = []
        md.append("# Maduk Business Intelligence - Executive Forecast Report")
        md.append(f"**Target Variable:** `{meta.get('target_column')}` | **Horizon:** `{meta.get('forecast_horizon')} Periods`\n")
        md.append("---")
        
        md.append("## Executive Summary")
        md.append(payload.get("executive_summary", "No summary available."))
        md.append("\n### Key Metrics & Indicators")
        md.append(f"- **Current Baseline:** ${kpis.get('current_period_baseline', 0):,.2f}")
        md.append(f"- **Projected Horizon Total:** ${kpis.get('projected_horizon_total', 0):,.2f}")
        md.append(f"- **Projected Growth Shift:** {kpis.get('growth_rate_pct', 0):+.1f}%")
        md.append(f"- **Model Selected:** {model_info.get('winning_model', 'N/A')}")
        
        md.append("\n## Model Rationale & Validation")
        md.append(model_info.get("selection_rationale", ""))
        
        md.append("\n## Risk Assessment")
        for risk in risks:
            md.append(f"- ⚠️ {risk}")
            
        md.append("\n## Recommended Actions")
        for act in actions:
            md.append(f"- ✅ {act}")
            
        return "\n".join(md)

    def generate_html_report(self, payload: Dict[str, Any]) -> str:
        """
        Renders a self-contained HTML executive document.

        Args:
            payload: Complete output pipeline dictionary.

        Returns:
            str: HTML report string.
        """
        logger.info("Generating standalone HTML executive report...")
        md_content = self.generate_markdown_report(payload)
        
        # Format HTML markup
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Maduk BI Executive Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; margin: 40px; color: #333; }}
        h1 {{ color: #003366; border-bottom: 2px solid #003366; padding-bottom: 10px; }}
        h2 {{ color: #0055a5; margin-top: 30px; }}
        .kpi-container {{ display: flex; gap: 20px; margin: 20px 0; }}
        .kpi-card {{ background: #f4f6f9; border-left: 4px solid #0055a5; padding: 15px; flex: 1; border-radius: 4px; }}
        .kpi-value {{ font-size: 20px; font-weight: bold; color: #111; }}
        ul {{ background: #fdfdfd; padding: 20px 40px; border: 1px solid #eee; border-radius: 4px; }}
        li {{ margin-bottom: 8px; }}
    </style>
</head>
<body>
    <div class="report-header">
        <h1>Maduk Business Intelligence Forecast Report</h1>
    </div>
    <div class="content">
        <pre style="white-space: pre-wrap; font-family: inherit;">{md_content}</pre>
    </div>
</body>
</html>"""
        return html_content
