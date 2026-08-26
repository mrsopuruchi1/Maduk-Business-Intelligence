"""
Maduk Business Intelligence - AI Prediction Pipeline
===================================================
File: backend/services/ai_prediction_pipeline/prediction_pipeline.py

Fixed:
- case-insensitive date/target resolution
- Revenue/Profit/Gross Profit/Net Income candidate detection
- robust numeric target fallback
- date parsing, sorting and duplicate-date handling before detection
"""
import logging
from typing import Dict, Any, Union, Optional, List
import pandas as pd
import numpy as np

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
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
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

    def run(self, data_source: Union[str, pd.DataFrame], target_column=None,
            date_column=None, forecast_horizon=12, confidence_level=0.95,
            secondary_targets=None) -> Dict[str, Any]:
        logger.info("Initializing Maduk BI Prediction Pipeline run...")
        df_raw = self._load_data(data_source)
        logger.info(f"Loaded dataset with shape {df_raw.shape}")

        dataset_profile = self.profiler.generate_profile(df_raw)
        clean_df, quality_report = self.validator.validate_and_clean(df_raw)

        clean_df, resolved_date_col, resolved_target_col = self._resolve_time_series_columns(
            clean_df, date_column, target_column
        )

        clean_df[resolved_date_col] = pd.to_datetime(clean_df[resolved_date_col], errors="coerce")
        clean_df[resolved_target_col] = pd.to_numeric(
            clean_df[resolved_target_col], errors="coerce"
        )
        clean_df = clean_df.dropna(subset=[resolved_date_col, resolved_target_col]).copy()
        if clean_df.empty:
            raise ValueError("Dataset is unsuitable for time series forecasting: no valid date/target observations remain.")

        clean_df = clean_df.sort_values(resolved_date_col).reset_index(drop=True)
        if clean_df[resolved_date_col].duplicated().any():
            clean_df = self._aggregate_duplicate_dates(clean_df, resolved_date_col)

        ts_meta = self.detector.detect_structure(
            df=clean_df, date_col=resolved_date_col, target_col=resolved_target_col
        )
        if not ts_meta.get("is_valid_time_series", False):
            raise ValueError(
                "Dataset is unsuitable for time series forecasting: "
                f"{ts_meta.get('reason', 'Time series validation failed.')}"
            )

        resolved_date_col = ts_meta.get("date_column", resolved_date_col)
        resolved_target_col = ts_meta.get("target_column", resolved_target_col)
        detected_freq = ts_meta.get("frequency")
        if not detected_freq:
            raise ValueError("Dataset is unsuitable for time series forecasting: unable to determine time frequency.")

        logger.info(
            f"Time Series Verified: Target='{resolved_target_col}', "
            f"Date='{resolved_date_col}', Freq='{detected_freq}'"
        )

        featured_df, feature_metadata = self.feature_engine.transform(
            df=clean_df, date_col=resolved_date_col,
            target_col=resolved_target_col, freq=detected_freq
        )

        selection_result = self.model_selector.select_best_model(
            df=featured_df, date_col=resolved_date_col,
            target_col=resolved_target_col, freq=detected_freq,
            forecast_horizon=forecast_horizon
        )
        best_model = selection_result["winning_model_instance"]
        winning_model_name = selection_result["winning_model_name"]
        feature_importance = (
            best_model.get_feature_importance()
            if hasattr(best_model, "get_feature_importance") else {}
        )

        best_model.fit(featured_df, resolved_date_col, resolved_target_col, detected_freq)
        base_forecast_df = best_model.predict_horizon(forecast_horizon, detected_freq)

        forecast_with_ci = self.ci_generator.calculate_intervals(
            forecast_df=base_forecast_df, historical_df=clean_df,
            target_col=resolved_target_col, confidence_level=confidence_level,
            residuals=selection_result.get("residuals", np.array([]))
        )
        scenarios_df = self.scenario_analyzer.generate_scenarios(
            forecast_df=forecast_with_ci, target_col=resolved_target_col,
            historical_df=clean_df
        )

        auxiliary_forecasts = {}
        for sec_target in secondary_targets or []:
            resolved_secondary = self._resolve_column_case_insensitive(clean_df, sec_target)
            if resolved_secondary and resolved_secondary != resolved_target_col:
                auxiliary_forecasts[resolved_secondary] = self._forecast_auxiliary_target(
                    clean_df, resolved_date_col, resolved_secondary,
                    detected_freq, forecast_horizon
                )

        exec_summary = self.summary_generator.generate_summary(
            historical_df=clean_df, forecast_df=scenarios_df,
            date_col=resolved_date_col, target_col=resolved_target_col,
            winning_model_name=winning_model_name,
            metrics=selection_result["best_metrics"]
        )
        business_risks = self.recommendation_engine.assess_risks(
            historical_df=clean_df, forecast_df=scenarios_df,
            metrics=selection_result["best_metrics"], target_col=resolved_target_col
        )
        recommended_actions = self.recommendation_engine.generate_actions(
            risks=business_risks, summary_data=exec_summary, scenarios=scenarios_df
        )
        chart_specs = self.viz_generator.generate_chart_specs(
            historical_df=clean_df, forecast_df=scenarios_df,
            auxiliary_forecasts=auxiliary_forecasts, date_col=resolved_date_col,
            target_col=resolved_target_col, feature_importance=feature_importance
        )
        dashboard_config = self.dashboard_generator.build_config(
            historical_df=clean_df, forecast_df=scenarios_df,
            date_col=resolved_date_col, target_col=resolved_target_col,
            metrics=selection_result["best_metrics"], summary_data=exec_summary,
            chart_specs=chart_specs
        )

        return {
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
                "selection_rationale": selection_result["selection_rationale"],
                "all_candidate_scores": selection_result["all_model_metrics"]
            },
            "validation_metrics": selection_result["best_metrics"],
            "forecast_values": scenarios_df.to_dict(orient="records"),
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

    @staticmethod
    def _resolve_column_case_insensitive(df, requested):
        if not requested:
            return None
        key = str(requested).strip().casefold()
        for col in df.columns:
            if str(col).strip().casefold() == key:
                return col
        return None

    @classmethod
    def _find_candidate_column(cls, df, candidates, numeric_only=False):
        def norm(x):
            return str(x).strip().casefold().replace("_", "").replace("-", "").replace(" ", "")
        # Exact case-insensitive matches have priority.
        for candidate in candidates:
            found = cls._resolve_column_case_insensitive(df, candidate)
            if found and (not numeric_only or pd.api.types.is_numeric_dtype(df[found])):
                return found
        candidate_norms = {norm(x) for x in candidates}
        for col in df.columns:
            if norm(col) in candidate_norms and (not numeric_only or pd.api.types.is_numeric_dtype(df[col])):
                return col
        return None

    @classmethod
    def _resolve_time_series_columns(cls, df, date_column, target_column):
        date_candidates = [x for x in [
            date_column, "date", "datetime", "timestamp", "time",
            "transaction_date", "period"
        ] if x]
        target_candidates = [x for x in [
            target_column, "revenue", "sales", "net_income",
            "gross_profit", "profit", "income", "cash_flow"
        ] if x]

        resolved_date = cls._find_candidate_column(df, date_candidates)
        if not resolved_date:
            best_col, best_ratio = None, 0.0
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    continue
                sample = df[col].dropna().head(100)
                if sample.empty:
                    continue
                ratio = float(pd.to_datetime(sample, errors="coerce").notna().mean())
                if ratio >= 0.80 and ratio > best_ratio:
                    best_col, best_ratio = col, ratio
            resolved_date = best_col

        if not resolved_date:
            raise ValueError(
                f"Dataset is unsuitable for time series forecasting: No date/time column identified. "
                f"Available columns: {list(df.columns)}"
            )

        resolved_target = cls._find_candidate_column(df, target_candidates, numeric_only=True)
        if not resolved_target:
            excluded = {resolved_date}
            preferred = ("revenue", "sales", "income", "profit", "cash", "amount", "value")
            numeric = [
                c for c in df.columns
                if c not in excluded
                and pd.api.types.is_numeric_dtype(df[c])
                and df[c].nunique(dropna=True) > 1
            ]
            numeric.sort(key=lambda c: (
                not any(t in str(c).casefold() for t in preferred),
                -int(df[c].notna().sum())
            ))
            resolved_target = numeric[0] if numeric else None

        if not resolved_target:
            raise ValueError("Dataset is unsuitable for time series forecasting: No numeric target column identified.")
        return df, resolved_date, resolved_target

    @staticmethod
    def _aggregate_duplicate_dates(df, date_col):
        numeric = df.select_dtypes(include=[np.number]).columns.tolist()
        non_numeric = [c for c in df.columns if c != date_col and c not in numeric]
        agg = {c: "sum" for c in numeric}
        agg.update({c: "first" for c in non_numeric})
        return df.groupby(date_col, as_index=False).agg(agg).sort_values(date_col).reset_index(drop=True)

    def _load_data(self, data_source):
        if isinstance(data_source, pd.DataFrame):
            return data_source.copy()
        if isinstance(data_source, str):
            path = data_source.lower()
            if path.endswith(".csv"):
                return pd.read_csv(data_source)
            if path.endswith((".xls", ".xlsx")):
                return pd.read_excel(data_source)
            if path.endswith(".parquet"):
                return pd.read_parquet(data_source)
            raise ValueError(f"Unsupported file format: {data_source}")
        raise TypeError("data_source must be a file path string or a pandas DataFrame.")

    def _forecast_auxiliary_target(self, df, date_col, target_col, freq, horizon):
        try:
            sec_featured, _ = self.feature_engine.transform(df, date_col, target_col, freq)
            result = self.model_selector.select_best_model(
                sec_featured, date_col, target_col, freq, horizon
            )
            model = result["winning_model_instance"]
            model.fit(sec_featured, date_col, target_col, freq)
            return model.predict_horizon(horizon, freq).to_dict(orient="records")
        except Exception as e:
            logger.warning(f"Failed auxiliary forecast for '{target_col}': {e}")
            return []
