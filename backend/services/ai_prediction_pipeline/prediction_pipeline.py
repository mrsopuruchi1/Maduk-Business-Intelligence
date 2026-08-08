"""
Maduk Business Intelligence - AI Prediction Pipeline
===================================================
File: backend/services/ai_prediction_pipeline/prediction_pipeline.py

Main orchestrator for end-to-end automated time series analysis, 
model selection, scenario modeling, executive advisory generation, 
and interactive visualization spec rendering.
"""

import logging
from typing import Dict, Any, Union, Optional, List
import pandas as pd
import numpy as np

# Subsystem Imports
from .data_profiler import DataProfiler
from .data_validator import DataValidator
from .time_series_detector import TimeSeriesDetector
from .feature_engineering import FeatureEngineering
from .forecasting.model_selector import ModelSelector
from .evaluation.metrics import MetricsEvaluator
from .evaluation.cross_validation import RollingOriginCV
from .scenario_analysis import ScenarioAnalyzer
from .confidence_intervals import ConfidenceIntervalGenerator
from .executive_summary import ExecutiveSummaryGenerator
from .business_recommendations import BusinessRecommendationEngine
from .dashboard_generator import DashboardGenerator
from .visualization_generator import VisualizationGenerator
from .report_generator import ReportGenerator

logger = logging.getLogger("MadukBI.PredictionPipeline")


class AIPredictionPipeline:
    """
    Production AI Forecasting Pipeline for Maduk Business Intelligence.
    
    Coordinates the pipeline lifecycle:
    1. Ingestion & Profiling
    2. Quality Validation & Cleaning
    3. Time Series Detection & Target Identification
    4. Feature Engineering
    5. Model Training, Backtesting, & Dynamic Selection
    6. Future Horizon Forecast & Confidence Interval Generation
    7. Scenario Analysis (Conservative, Expected, Optimistic)
    8. Executive Advisory & Risk Assessment Generation
    9. Interactive Plotly/ECharts Visualization Spec Building
    10. Complete Structured Payload Output
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize pipeline services with modular configuration parameters.
        """
        self.config = config or {}
        
        # Pipeline Services
        self.profiler = DataProfiler()
        self.validator = DataValidator()
        self.detector = TimeSeriesDetector()
        self.feature_engine = FeatureEngineering()
        self.metrics_evaluator = MetricsEvaluator()
        self.cross_validator = RollingOriginCV(
            n_splits=self.config.get("cv_splits", 3),
            min_train_size=self.config.get("min_train_size", 12)
        )
        self.model_selector = ModelSelector(
            cv_evaluator=self.cross_validator,
            metrics_evaluator=self.metrics_evaluator
        )
        self.scenario_analyzer = ScenarioAnalyzer()
        self.ci_generator = ConfidenceIntervalGenerator()
        self.summary_generator = ExecutiveSummaryGenerator()
        self.recommendation_engine = BusinessRecommendationEngine()
        self.viz_generator = VisualizationGenerator()
        self.dashboard_generator = DashboardGenerator(viz_generator=self.viz_generator)
        self.report_generator = ReportGenerator()

    def run(
        self,
        data_source: Union[str, pd.DataFrame],
        target_column: Optional[str] = None,
        date_column: Optional[str] = None,
        forecast_horizon: int = 12,
        confidence_level: float = 0.95,
        secondary_targets: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes the end-to-end forecasting pipeline and returns a structured executive payload.

        Args:
            data_source: File path (CSV/Excel/Parquet) or Pandas DataFrame.
            target_column: Explicit target variable name (e.g., 'revenue'). Auto-detected if None.
            date_column: Explicit date/time column name. Auto-detected if None.
            forecast_horizon: Number of future periods to predict (e.g., 6, 12, 24 months).
            confidence_level: Confidence interval width (e.g., 0.95 for 95% CI).
            secondary_targets: Optional list of additional columns to forecast (e.g., ['profit', 'cash_flow']).

        Returns:
            Dict[str, Any]: Comprehensive production payload containing structured data profiles,
                            quality metrics, forecast arrays, scenario projections, and interactive
                            chart specifications.
        """
        logger.info("Initializing Maduk BI Prediction Pipeline run...")

        # ------------------------------------------------------------------
        # Step 1: Ingestion & Data Profiling
        # ------------------------------------------------------------------
        df_raw = self._load_data(data_source)
        logger.info(f"Loaded dataset with shape {df_raw.shape}")

        dataset_profile = self.profiler.generate_profile(df_raw)

        # ------------------------------------------------------------------
        # Step 2: Quality Validation & Cleaning
        # ------------------------------------------------------------------
        clean_df, quality_report = self.validator.validate_and_clean(df_raw)
        logger.info(f"Data quality assessment complete. Score: {quality_report.get('quality_score', 'N/A')}")

        # ------------------------------------------------------------------
        # Step 3: Time Series Detection & Validation
        # ------------------------------------------------------------------
        ts_meta = self.detector.detect_structure(
            df=clean_df,
            date_col=date_column,
            target_col=target_column
        )

        if not ts_meta["is_valid_time_series"]:
            raise ValueError(f"Dataset is unsuitable for time series forecasting: {ts_meta.get('reason')}")

        resolved_date_col = ts_meta["date_column"]
        resolved_target_col = ts_meta["target_column"]
        detected_freq = ts_meta["frequency"]

        logger.info(f"Time Series Verified: Target='{resolved_target_col}', Date='{resolved_date_col}', Freq='{detected_freq}'")

        # ------------------------------------------------------------------
        # Step 4: Feature Engineering
        # ------------------------------------------------------------------
        featured_df, feature_metadata = self.feature_engine.transform(
            df=clean_df,
            date_col=resolved_date_col,
            target_col=resolved_target_col,
            freq=detected_freq
        )

        # ------------------------------------------------------------------
        # Step 5 & 6: Cross-Validation, Backtesting & Model Selection
        # ------------------------------------------------------------------
        selection_result = self.model_selector.select_best_model(
            df=featured_df,
            date_col=resolved_date_col,
            target_col=resolved_target_col,
            freq=detected_freq,
            forecast_horizon=forecast_horizon
        )

        best_model = selection_result["winning_model_instance"]
        winning_model_name = selection_result["winning_model_name"]
        selection_rationale = selection_result["selection_rationale"]
        all_candidate_metrics = selection_result["all_model_metrics"]

        logger.info(f"Model selection complete. Winner: {winning_model_name}")

        # Extract Feature Importances / Predictive Drivers if supported
        feature_importance = best_model.get_feature_importance() if hasattr(best_model, "get_feature_importance") else {}

        # ------------------------------------------------------------------
        # Step 7: Final Model Fit & Future Forecasting
        # ------------------------------------------------------------------
        best_model.fit(
            df=featured_df,
            date_col=resolved_date_col,
            target_col=resolved_target_col,
            freq=detected_freq
        )

        base_forecast_df = best_model.predict_horizon(
            horizon=forecast_horizon,
            freq=detected_freq
        )

        # ------------------------------------------------------------------
        # Step 8: Confidence Intervals & Scenario Analysis
        # ------------------------------------------------------------------
        forecast_with_ci = self.ci_generator.calculate_intervals(
            forecast_df=base_forecast_df,
            historical_df=clean_df,
            target_col=resolved_target_col,
            confidence_level=confidence_level,
            residuals=selection_result.get("residuals", np.array([]))
        )

        scenarios_df = self.scenario_analyzer.generate_scenarios(
            forecast_df=forecast_with_ci,
            target_col=resolved_target_col,
            historical_df=clean_df
        )

        # Optional Auxiliary Forecasts (Profit / Cash Flow)
        auxiliary_forecasts = {}
        if secondary_targets:
            for sec_target in secondary_targets:
                if sec_target in clean_df.columns and sec_target != resolved_target_col:
                    auxiliary_forecasts[sec_target] = self._forecast_auxiliary_target(
                        df=clean_df,
                        date_col=resolved_date_col,
                        target_col=sec_target,
                        freq=detected_freq,
                        horizon=forecast_horizon
                    )

        # ------------------------------------------------------------------
        # Step 9: Executive Insights & Recommendations
        # ------------------------------------------------------------------
        exec_summary = self.summary_generator.generate_summary(
            historical_df=clean_df,
            forecast_df=scenarios_df,
            date_col=resolved_date_col,
            target_col=resolved_target_col,
            winning_model_name=winning_model_name,
            metrics=selection_result["best_metrics"]
        )

        business_risks = self.recommendation_engine.assess_risks(
            historical_df=clean_df,
            forecast_df=scenarios_df,
            metrics=selection_result["best_metrics"],
            target_col=resolved_target_col
        )

        recommended_actions = self.recommendation_engine.generate_actions(
            risks=business_risks,
            summary_data=exec_summary,
            scenarios=scenarios_df
        )

        # ------------------------------------------------------------------
        # Step 10: Interactive Visualization & Dashboard Spec Building
        # ------------------------------------------------------------------
        chart_specs = self.viz_generator.generate_chart_specs(
            historical_df=clean_df,
            forecast_df=scenarios_df,
            auxiliary_forecasts=auxiliary_forecasts,
            date_col=resolved_date_col,
            target_col=resolved_target_col,
            feature_importance=feature_importance
        )

        dashboard_config = self.dashboard_generator.build_config(
            historical_df=clean_df,
            forecast_df=scenarios_df,
            date_col=resolved_date_col,
            target_col=resolved_target_col,
            metrics=selection_result["best_metrics"],
            summary_data=exec_summary,
            chart_specs=chart_specs
        )

        # ------------------------------------------------------------------
        # Final Structured Payload Compilation
        # ------------------------------------------------------------------
        forecast_values_records = scenarios_df.to_dict(orient="records")

        payload = {
            "status": "success",
            "pipeline_metadata": {
                "date_column": resolved_date_col,
                "target_column": resolved_target_col,
                "frequency": detected_freq,
                "forecast_horizon": forecast_horizon,
                "confidence_level": confidence_level
            },
            "dataset_profile": dataset_profile,
            "data_quality_report": quality_report,
            "feature_importance": feature_importance,
            "best_model_and_selection": {
                "winning_model": winning_model_name,
                "selection_rationale": selection_rationale,
                "all_candidate_scores": all_candidate_metrics
            },
            "validation_metrics": selection_result["best_metrics"],
            "forecast_values": forecast_values_records,
            "prediction_intervals": {
                "level": confidence_level,
                "lower_bound_col": "lower_bound",
                "upper_bound_col": "upper_bound"
            },
            "auxiliary_forecasts": auxiliary_forecasts,
            "executive_summary": exec_summary["summary_text"],
            "kpi_cards": exec_summary["kpis"],
            "business_risks": business_risks,
            "recommended_actions": recommended_actions,
            "dashboard_configuration": dashboard_config,
            "chart_specifications": chart_specs
        }

        logger.info("AI Prediction Pipeline completed successfully.")
        return payload

    def _load_data(self, data_source: Union[str, pd.DataFrame]) -> pd.DataFrame:
        """Helper function to load data from path or pandas DataFrame."""
        if isinstance(data_source, pd.DataFrame):
            return data_source.copy()
        elif isinstance(data_source, str):
            if data_source.endswith(".csv"):
                return pd.read_csv(data_source)
            elif data_source.endswith((".xls", ".xlsx")):
                return pd.read_excel(data_source)
            elif data_source.endswith(".parquet"):
                return pd.read_parquet(data_source)
            else:
                raise ValueError(f"Unsupported file format: {data_source}")
        else:
            raise TypeError("data_source must be a file path string or a pandas DataFrame.")

    def _forecast_auxiliary_target(
        self,
        df: pd.DataFrame,
        date_col: str,
        target_col: str,
        freq: str,
        horizon: int
    ) -> List[Dict[str, Any]]:
        """Secondary forecast runner for supplementary metrics (e.g. Profit, Cash Flow)."""
        try:
            sec_featured, _ = self.feature_engine.transform(df, date_col, target_col, freq)
            model_result = self.model_selector.select_best_model(
                df=sec_featured,
                date_col=date_col,
                target_col=target_col,
                freq=freq,
                forecast_horizon=horizon
            )
            model = model_result["winning_model_instance"]
            model.fit(sec_featured, date_col, target_col, freq)
            aux_forecast = model.predict_horizon(horizon, freq)
            return aux_forecast.to_dict(orient="records")
        except Exception as e:
            logger.warning(f"Failed auxiliary forecast for '{target_col}': {str(e)}")
            return []
