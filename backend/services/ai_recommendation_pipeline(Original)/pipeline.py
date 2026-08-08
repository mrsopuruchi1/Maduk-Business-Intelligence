# pipeline.py:

"""
Maduk Business Intelligence - AI Recommendation Pipeline Orchestrator

Main orchestration engine coordinating data profiling, KPI computation,
forecasting, anomaly detection, health scoring, insight generation,
chart rendering, and PDF report compilation.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Union, Optional, List
import pandas as pd

# Pipeline Module Imports
from .data_validator import DataValidator
from .data_profiler import DataProfiler
from .feature_engineering import FeatureEngineering
from .kpi_engine import KPIEngine
from .business_health_engine import BusinessHealthEngine
from .forecasting_engine import ForecastingEngine
from .anomaly_detection import AnomalyDetectionEngine
from .correlation_engine import CorrelationEngine
from .recommendation_engine import RecommendationEngine
from .insight_generator import InsightGenerator
from .dashboard_engine import DashboardEngine
from .chart_generator import ChartGenerator
from .report_generator import ReportGenerator
from .llm_report_writer import LLMReportWriter
from .pdf_exporter import PDFExporter

# Pydantic Schemas
from .models.schemas import (
    BusinessHealthAssessment,
    MetricDriver,
    DriverAnalysis,
    AnomalyItem,
    RiskAssessment,
    TimePhasedActionPlan,
    ExecutiveReportData
)

# Logging configuration
logger = logging.getLogger("MadukBI.Pipeline")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)


class BusinessIntelligencePipeline:
    """
    Main Business Intelligence Orchestrator.
    
    Coordinates the execution of all analytical, predictive, 
    recommendation, visualization, and PDF generation modules.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        
        # Directories Setup
        self.templates_dir = os.path.join(self.base_dir, "templates")
        self.charts_dir = os.path.join(self.base_dir, "charts")
        self.reports_dir = os.path.join(self.base_dir, "reports")
        self.models_dir = os.path.join(self.base_dir, "models")
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.output_dir = self.reports_dir  # Alias for report generation output
        
        for directory in [self.charts_dir, self.reports_dir, self.models_dir, self.assets_dir, self.output_dir]:
            os.makedirs(directory, exist_ok=True)

        # Module Initializations
        self.data_validator = DataValidator()
        self.data_profiler = DataProfiler()
        self.feature_engineering = FeatureEngineering()
        self.kpi_engine = KPIEngine()
        self.business_health_engine = BusinessHealthEngine()
        self.forecasting_engine = ForecastingEngine()
        self.anomaly_detection = AnomalyDetectionEngine()
        self.correlation_engine = CorrelationEngine()
        self.llm_writer = LLMReportWriter()
        self.recommendation_engine = RecommendationEngine(llm_writer=self.llm_writer)
        self.insight_generator = InsightGenerator(llm_writer=self.llm_writer)
        self.dashboard_engine = DashboardEngine()
        self.chart_generator = ChartGenerator(output_dir=self.charts_dir)
        self.report_generator = ReportGenerator(template_dir=self.templates_dir)
        self.pdf_exporter = PDFExporter()


    def run(
        self,
        input_data: Union[str, pd.DataFrame],
        output_pdf_filename: str = "Executive_Intelligence_Report.pdf",
        company_name: str = "Enterprise Client",
        custom_logo_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs the end-to-end AI Business Intelligence pipeline.
        """
        logger.info(f"Starting Business Intelligence Execution Pipeline for: {company_name}")

        # ------------------------------------------------------------------
        # Stage 1: Data Ingestion & Data Validation
        # ------------------------------------------------------------------
        logger.info("[Stage 1/12] Ingesting and validating dataset schema...")
        if isinstance(input_data, str):
            if input_data.endswith('.csv'):
                df_raw = pd.read_csv(input_data)
            elif input_data.endswith(('.xls', '.xlsx')):
                df_raw = pd.read_excel(input_data)
            else:
                raise ValueError(f"Unsupported file format for path: {input_data}")
        elif isinstance(input_data, pd.DataFrame):
            df_raw = input_data.copy()
        else:
            raise TypeError("Input data must be a valid file path or pandas DataFrame.")

        df_validated, mapped_cols = self.data_validator.process(df_raw)

        # ------------------------------------------------------------------
        # Stage 2: Data Profiling & Quality Scoring
        # ------------------------------------------------------------------
        logger.info("[Stage 2/12] Computing data quality scores and profiling data...")
        profile_results = self.data_profiler.profile(df_validated, mapped_cols)
        quality_score = profile_results.get("data_quality_score", 100.0)

        # ------------------------------------------------------------------
        # Stage 3: Feature Engineering
        # ------------------------------------------------------------------
        logger.info("[Stage 3/12] Engineering synthetic financial and operational features...")
        df_engineered = self.feature_engineering.transform(df_validated, mapped_cols)

        # ------------------------------------------------------------------
        # Stage 4: KPI Computation
        # ------------------------------------------------------------------
        logger.info("[Stage 4/12] Computing primary business KPIs...")
        computed_kpis = self.kpi_engine.compute(df_engineered, mapped_cols)

        # ------------------------------------------------------------------
        # Stage 5: Anomaly Detection
        # ------------------------------------------------------------------
        logger.info("[Stage 5/12] Detecting anomalies, outliers, and revenue risks...")
        anomalies = self.anomaly_detection.detect(df_engineered, mapped_cols)

        # ------------------------------------------------------------------
        # Stage 6: Correlation & Driver Analysis
        # ------------------------------------------------------------------
        logger.info("[Stage 6/12] Running correlation analysis and driver identification...")
        correlations = self.correlation_engine.analyze(df_engineered, mapped_cols)

        # ------------------------------------------------------------------
        # Stage 7: Business Health Prediction Scoring
        # ------------------------------------------------------------------
        logger.info("[Stage 7/12] Evaluating Business Health Score (0-100 scale)...")
        health_assessment = self.business_health_engine.evaluate(
            kpis=computed_kpis, 
            quality_score=quality_score
        )

        # ------------------------------------------------------------------
        # Stage 8: Time-Series Forecasting
        # ------------------------------------------------------------------
        logger.info("[Stage 8/12] Generating revenue, expense, and profit forecasts...")
        forecasts = self.forecasting_engine.forecast(df_engineered, mapped_cols, periods=6)

        # ------------------------------------------------------------------
        # Stage 9: Executive Dashboard Metric Compilation
        # ------------------------------------------------------------------
        logger.info("[Stage 9/12] Aggregating Core Executive Dashboard Metrics...")
        dashboard_metrics = self.dashboard_engine.build_dashboard(
            df=df_engineered,
            mapping=mapped_cols,
            kpis=computed_kpis,
            health=health_assessment
        )

        # ------------------------------------------------------------------
        # Stage 10: Recommendations & Executive Insights Generation
        # ------------------------------------------------------------------
        logger.info("[Stage 10/12] Generating grounded recommendations and LLM executive narrative...")
        recommendations = self.recommendation_engine.generate(
            dashboard_metrics=dashboard_metrics,
            health=health_assessment,
            anomalies=anomalies
        )
                
        insights = self.insight_generator.generate_insights(
            dashboard_metrics=dashboard_metrics,
            correlations=correlations,
            forecasts=forecasts
        )
        
        summary_narrative = self.llm_writer.generate_narrative_summary(
            dashboard=dashboard_metrics,
            health=health_assessment,
            insights=insights
        )

        # ------------------------------------------------------------------
        # Stage 11: Dynamic Chart Generation
        # ------------------------------------------------------------------
        logger.info("[Stage 11/12] Rendering trend line charts, bar plots, and scatter charts...")
        generated_charts = self.chart_generator.generate_all(
            df=df_engineered,
            mapping=mapped_cols,
            forecasts=forecasts
        )

        # ------------------------------------------------------------------
        # Stage 12: PDF Executive Report Compilation & Export
        # ------------------------------------------------------------------
        logger.info("[Stage 12/12] Assembling HTML layout and compiling final PDF report...")

        # 1. Standardize recommendations array
        formatted_rules = []
        raw_rules = []

        if isinstance(recommendations, dict):
            raw_rules = recommendations.get("rules_triggered", [])
        elif hasattr(recommendations, "rules_triggered"):
            raw_rules = getattr(recommendations, "rules_triggered", [])
        elif isinstance(recommendations, list):
            raw_rules = recommendations

        for item in raw_rules:
            if isinstance(item, dict):
                formatted_rules.append({
                    "category": item.get("category", "Strategy"),
                    "finding": item.get("finding", str(item)),
                    "action": item.get("action", str(item)),
                    "impact": item.get("impact", "Operational optimization"),
                    "time_horizon": item.get("time_horizon", "Immediate")
                })
            elif hasattr(item, "dict"):
                formatted_rules.append(item.dict())
            else:
                formatted_rules.append({
                    "category": "Strategic Recommendation",
                    "finding": str(item),
                    "action": str(item),
                    "impact": "Operational optimization",
                    "time_horizon": "Immediate"
                })

        if not formatted_rules:
            formatted_rules = [{
                "category": "Operational Strategy",
                "finding": "Standard performance monitoring active.",
                "action": "Maintain automated financial tracking.",
                "impact": "Baseline stability",
                "time_horizon": "Ongoing"
            }]

        # 2. Extract Action Plan Safely
        action_plan = {}
        if isinstance(recommendations, dict):
            action_plan = recommendations.get("action_plan", {})
        elif hasattr(recommendations, "action_plan"):
            action_plan = getattr(recommendations, "action_plan", {})

        # 3. Standardize Health Assessment
        if hasattr(health_assessment, "dict"):
            health_dict = health_assessment.dict()
        elif isinstance(health_assessment, dict):
            health_dict = health_assessment
        else:
            health_dict = {
                "health_score": getattr(health_assessment, "health_score", 0.0),
                "status": getattr(health_assessment, "status", "N/A"),
                "confidence_score": getattr(health_assessment, "confidence_score", 0.0),
                "risk_level": getattr(health_assessment, "risk_level", "Medium"),
                "data_quality_score": getattr(health_assessment, "data_quality_score", 100.0),
            }

        # 4. Resolve Logo Path Safely (Multiple Fallbacks)
        logo_path = None
                
        # Determine the exact directory where pipeline.py lives
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        candidate_logo_paths = [
            custom_logo_path,
            os.path.join(current_dir, "assets", "madukai_logo.png"),
            os.path.join(current_dir, "assets", "logo.png"),
            os.path.join(current_dir, "madukai_logo.png"),
            os.path.join(self.assets_dir, "madukai_logo.png"),
            os.path.abspath(os.path.join(current_dir, "../../../frontend/assets/madukai_logo.png")),
        ]
        
        for path in candidate_logo_paths:
            if path and os.path.exists(path):
                logo_path = os.path.abspath(path)
                logger.info(f"Resolved brand logo at: {logo_path}")
                break
        
        if not logo_path:
            logger.warning(f"Brand logo image file not found! Checked locations relative to {current_dir}. Defaulting to text header.")

        report_context = {
            "company_name": company_name,
            "logo_path": logo_path,
            "generation_date": datetime.now().strftime("%B %d, %Y"),
            "generation_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "health": health_dict,
            "dashboard": dashboard_metrics if isinstance(dashboard_metrics, dict) else {},
            "summary_narrative": summary_narrative if summary_narrative else "Executive summary unavailable.",
            "insights": insights if isinstance(insights, list) else [],
            "recommendations": formatted_rules,
            "rules_triggered": formatted_rules,
            "action_plan": action_plan,
            "forecasts": forecasts if isinstance(forecasts, dict) else {},
            "anomalies": anomalies if isinstance(anomalies, list) else [],
            "charts": generated_charts if isinstance(generated_charts, dict) else {},
            "profile": profile_results if hasattr(profile_results, "dict") else profile_results
        }

        # 5. Render Template and Generate PDF
        output_pdf_filename = f"Executive_Report_{company_name.replace(' ', '_')}.pdf"
        pdf_output_path = os.path.join(self.output_dir, output_pdf_filename)

        rendered_html = self.report_generator.render_template(
            template_name="executive_report.html",
            context=report_context
        )

        pdf_path = self.report_generator.compile_pdf(
            html_content=rendered_html,
            output_path=pdf_output_path
        )

        return {
            "status": "success",
            "company_name": company_name,
            "health_assessment": health_dict,
            "dashboard_metrics": dashboard_metrics,
            "insights": insights,
            "recommendations": formatted_rules,
            "forecasts": forecasts,
            "pdf_report_path": pdf_path or pdf_output_path
        }
