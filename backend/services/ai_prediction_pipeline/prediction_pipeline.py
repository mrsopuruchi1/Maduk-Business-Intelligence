"""
Maduk Business Intelligence - AI Prediction Pipeline
======================================================
File: backend/services/ai_prediction_pipeline/prediction_pipeline.py

Main orchestrator for end-to-end automated time series analysis,
model selection, scenario modeling, executive advisory generation,
and interactive visualization spec rendering.
"""

import logging
from typing import Dict, Any, Union, Optional, List

import numpy as np
import pandas as pd

from .data_profiler import DataProfiler
from .data_validator import DataValidator
from .time_series_detector import TimeSeriesDetector
from .feature_engineering import FeatureEngineering
from .forecasting.model_selector import ModelSelector
from .forecasting.random_forest_model import RandomForestForecaster
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

    Coordinates:
    1. Ingestion & profiling
    2. Validation & cleaning
    3. Time-series detection
    4. Feature engineering
    5. Cross-validation & model selection
    6. Forecasting & confidence intervals
    7. Scenario analysis
    8. Executive summary & recommendations
    9. Visualization/dashboard specifications
    10. Structured API payload generation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        cv_splits = max(2, int(self.config.get("cv_splits", 3)))
        min_train_size = max(3, int(self.config.get("min_train_size", 12)))

        self.profiler = DataProfiler()
        self.validator = DataValidator()
        self.detector = TimeSeriesDetector()
        self.feature_engine = FeatureEngineering()
        self.metrics_evaluator = MetricsEvaluator()

        self.cross_validator = RollingOriginCV(
            n_splits=cv_splits,
            min_train_size=min_train_size,
        )

        self.model_selector = ModelSelector(
            cv_evaluator=self.cross_validator,
            metrics_evaluator=self.metrics_evaluator,
        )

        self.scenario_analyzer = ScenarioAnalyzer()
        self.ci_generator = ConfidenceIntervalGenerator()
        self.summary_generator = ExecutiveSummaryGenerator()
        self.recommendation_engine = BusinessRecommendationEngine()
        self.viz_generator = VisualizationGenerator()
        self.dashboard_generator = DashboardGenerator(
            viz_generator=self.viz_generator
        )
        self.report_generator = ReportGenerator()

    def run(
        self,
        data_source: Union[str, pd.DataFrame],
        target_column: Optional[str] = None,
        date_column: Optional[str] = None,
        forecast_horizon: int = 12,
        confidence_level: float = 0.95,
        secondary_targets: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute the complete forecasting pipeline."""

        logger.info("Initializing Maduk BI Prediction Pipeline run...")

        # ------------------------------------------------------------------
        # 0. INPUT VALIDATION
        # ------------------------------------------------------------------
        try:
            forecast_horizon = int(forecast_horizon)
        except (TypeError, ValueError):
            raise ValueError(
                f"forecast_horizon must be a positive integer; received {forecast_horizon!r}."
            )

        if forecast_horizon < 1:
            raise ValueError("forecast_horizon must be at least 1.")

        try:
            confidence_level = float(confidence_level)
        except (TypeError, ValueError):
            raise ValueError(
                f"confidence_level must be a number; received {confidence_level!r}."
            )

        if not 0.50 <= confidence_level < 1.0:
            raise ValueError(
                "confidence_level must be between 0.50 (inclusive) and 1.0 (exclusive)."
            )

        # ------------------------------------------------------------------
        # Step 1: Ingestion & Data Profiling
        # ------------------------------------------------------------------
        df_raw = self._load_data(data_source)

        if df_raw.empty:
            raise ValueError("The uploaded dataset is empty.")

        df_raw = self._prepare_dataframe(
            df_raw,
            date_column=date_column,
            target_column=target_column,
        )

        logger.info("Loaded dataset with shape %s", df_raw.shape)

        if len(df_raw) < 5:
            raise ValueError(
                "Dataset contains insufficient rows for time-series forecasting. "
                "At least 5 valid observations are required."
            )

        dataset_profile = self.profiler.generate_profile(df_raw)

        # ------------------------------------------------------------------
        # Step 2: Quality Validation & Cleaning
        # ------------------------------------------------------------------
        clean_df, quality_report = self.validator.validate_and_clean(df_raw)

        if clean_df is None or clean_df.empty:
            raise ValueError(
                "Data validation removed all observations. "
                "Please check the uploaded date and target columns."
            )

        logger.info(
            "Data quality assessment complete. Score: %s",
            quality_report.get("quality_score", "N/A"),
        )

        # ------------------------------------------------------------------
        # Step 3: Time Series Detection & Validation
        # ------------------------------------------------------------------
        ts_meta = self.detector.detect_structure(
            df=clean_df,
            date_col=date_column,
            target_col=target_column,
        )

        if not ts_meta.get("is_valid_time_series", False):
            raise ValueError(
                "Dataset is unsuitable for time series forecasting: "
                f"{ts_meta.get('reason', 'Unable to detect a valid time series.')}"
            )

        resolved_date_col = ts_meta.get("date_column")
        resolved_target_col = ts_meta.get("target_column")
        detected_freq = ts_meta.get("frequency")

        if not resolved_date_col:
            raise ValueError("Unable to determine the date/time column.")

        if not resolved_target_col:
            raise ValueError(
                "Unable to determine the forecasting target. "
                "Specify target_column explicitly, for example 'revenue'."
            )

        if resolved_date_col not in clean_df.columns:
            raise ValueError(
                f"Detected date column '{resolved_date_col}' is not present in the dataset."
            )

        if resolved_target_col not in clean_df.columns:
            raise ValueError(
                f"Detected target column '{resolved_target_col}' is not present in the dataset."
            )

        # Normalize the detected date/target before feature engineering.
        clean_df = self._normalize_time_series(
            clean_df,
            date_col=resolved_date_col,
            target_col=resolved_target_col,
        )

        if len(clean_df) < 5:
            raise ValueError(
                "Fewer than 5 valid observations remain after date/target cleaning."
            )

        # Detector implementations may return None/unknown for frequency.
        # Feature/model subsystems need a usable frequency, so infer it here.
        if not detected_freq:
            detected_freq = self._infer_frequency(
                clean_df[resolved_date_col]
            )

        logger.info(
            "Time Series Verified: Target='%s', Date='%s', Freq='%s', Rows=%d",
            resolved_target_col,
            resolved_date_col,
            detected_freq,
            len(clean_df),
        )

        # ------------------------------------------------------------------
        # Step 4: Feature Engineering
        # ------------------------------------------------------------------
        featured_df, feature_metadata = self.feature_engine.transform(
            df=clean_df,
            date_col=resolved_date_col,
            target_col=resolved_target_col,
            freq=detected_freq,
        )

        if featured_df is None or featured_df.empty:
            raise ValueError(
                "Feature engineering produced no usable observations."
            )

        # ------------------------------------------------------------------
        # Step 5: Cross-Validation & Model Selection
        # ------------------------------------------------------------------
        selection_result = self.model_selector.select_best_model(
            df=featured_df,
            date_col=resolved_date_col,
            target_col=resolved_target_col,
            freq=detected_freq,
            forecast_horizon=forecast_horizon,
        )

        if not selection_result:
            raise ValueError("Model selection returned no result.")

        best_model = selection_result.get("winning_model_instance")
        winning_model_name = selection_result.get(
            "winning_model_name", "Automated"
        )
        selection_rationale = selection_result.get(
            "selection_rationale", ""
        )
        all_candidate_metrics = selection_result.get(
            "all_model_metrics", {}
        )

        if best_model is None:
            raise ValueError(
                "No forecasting model could be selected for this dataset."
            )

        logger.info(
            "Model selection complete. Winner: %s",
            winning_model_name,
        )

        best_metrics = selection_result.get("best_metrics", {}) or {}

        # Extract feature importance when supported. Never allow an optional
        # diagnostic to crash an otherwise valid forecast.
        try:
            feature_importance = (
                best_model.get_feature_importance()
                if hasattr(best_model, "get_feature_importance")
                else {}
            )
        except Exception as exc:
            logger.warning(
                "Unable to extract feature importance: %s", exc
            )
            feature_importance = {}

        # ------------------------------------------------------------------
        # Step 6: Final Model Fit & Future Forecast
        # ------------------------------------------------------------------
        best_model.fit(
            df=featured_df,
            date_col=resolved_date_col,
            target_col=resolved_target_col,
            freq=detected_freq,
        )

        base_forecast_df = best_model.predict_horizon(
            horizon=forecast_horizon,
            freq=detected_freq,
        )

        if base_forecast_df is None or base_forecast_df.empty:
            raise ValueError(
                "The selected forecasting model returned no future predictions."
            )

        # ------------------------------------------------------------------
        # Step 7: Confidence Intervals & Scenario Analysis
        # ------------------------------------------------------------------
        residuals = selection_result.get("residuals", np.array([]))

        forecast_with_ci = self.ci_generator.calculate_intervals(
            forecast_df=base_forecast_df,
            historical_df=clean_df,
            target_col=resolved_target_col,
            confidence_level=confidence_level,
            residuals=residuals,
        )

        if forecast_with_ci is None or forecast_with_ci.empty:
            raise ValueError(
                "Confidence interval generation returned no forecast data."
            )

        scenarios_df = self.scenario_analyzer.generate_scenarios(
            forecast_df=forecast_with_ci,
            target_col=resolved_target_col,
            historical_df=clean_df,
        )

        if scenarios_df is None or scenarios_df.empty:
            raise ValueError(
                "Scenario analysis returned no forecast data."
            )

        # ------------------------------------------------------------------
        # Step 8: Optional Auxiliary Forecasts
        # ------------------------------------------------------------------
        auxiliary_forecasts: Dict[str, List[Dict[str, Any]]] = {}

        if secondary_targets:
            for sec_target in secondary_targets:
                if not isinstance(sec_target, str):
                    continue

                sec_target = sec_target.strip()

                if (
                    sec_target
                    and sec_target in clean_df.columns
                    and sec_target != resolved_target_col
                ):
                    auxiliary_forecasts[sec_target] = (
                        self._forecast_auxiliary_target(
                            df=clean_df,
                            date_col=resolved_date_col,
                            target_col=sec_target,
                            freq=detected_freq,
                            horizon=forecast_horizon,
                        )
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
            metrics=best_metrics,
        )

        exec_summary = exec_summary or {}
        business_risks = self.recommendation_engine.assess_risks(
            historical_df=clean_df,
            forecast_df=scenarios_df,
            metrics=best_metrics,
            target_col=resolved_target_col,
        )

        business_risks = business_risks or []

        recommended_actions = self.recommendation_engine.generate_actions(
            risks=business_risks,
            summary_data=exec_summary,
            scenarios=scenarios_df,
        )

        recommended_actions = recommended_actions or []

        # ------------------------------------------------------------------
        # Step 10: Visualization & Dashboard Specs
        # ------------------------------------------------------------------
        chart_specs = self.viz_generator.generate_chart_specs(
            historical_df=clean_df,
            forecast_df=scenarios_df,
            auxiliary_forecasts=auxiliary_forecasts,
            date_col=resolved_date_col,
            target_col=resolved_target_col,
            feature_importance=feature_importance,
        )

        dashboard_config = self.dashboard_generator.build_config(
            historical_df=clean_df,
            forecast_df=scenarios_df,
            date_col=resolved_date_col,
            target_col=resolved_target_col,
            metrics=best_metrics,
            summary_data=exec_summary,
            chart_specs=chart_specs,
        )

        # ------------------------------------------------------------------
        # Final Structured Payload
        # ------------------------------------------------------------------
        forecast_values_records = self._json_safe_records(scenarios_df)

        kpis = exec_summary.get("kpis", {}) or {}
        summary_text = exec_summary.get("summary_text", "")

        payload = {
            "status": "success",
            "pipeline_metadata": {
                "date_column": resolved_date_col,
                "target_column": resolved_target_col,
                "frequency": detected_freq,
                "forecast_horizon": forecast_horizon,
                "confidence_level": confidence_level,
                "input_rows": int(len(df_raw)),
                "valid_rows": int(len(clean_df)),
            },
            "dataset_profile": dataset_profile,
            "data_quality_report": quality_report,
            "feature_metadata": feature_metadata,
            "feature_importance": feature_importance,
            "best_model_and_selection": {
                "winning_model": winning_model_name,
                "selection_rationale": selection_rationale,
                "all_candidate_scores": all_candidate_metrics,
            },
            "validation_metrics": best_metrics,
            "forecast_values": forecast_values_records,
            "prediction_intervals": {
                "level": confidence_level,
                "lower_bound_col": "lower_bound",
                "upper_bound_col": "upper_bound",
            },
            "auxiliary_forecasts": auxiliary_forecasts,
            "executive_summary": summary_text,
            "kpi_cards": kpis,
            "business_risks": business_risks,
            "recommended_actions": recommended_actions,
            "dashboard_configuration": dashboard_config,
            "chart_specifications": chart_specs,
        }

        logger.info(
            "AI Prediction Pipeline completed successfully. "
            "target=%s horizon=%d frequency=%s",
            resolved_target_col,
            forecast_horizon,
            detected_freq,
        )

        return payload

    def _load_data(
        self,
        data_source: Union[str, pd.DataFrame],
    ) -> pd.DataFrame:
        """Load CSV, Excel, Parquet, or an already-created DataFrame."""
        if isinstance(data_source, pd.DataFrame):
            return data_source.copy()

        if isinstance(data_source, str):
            source = data_source.lower().strip()

            if source.endswith(".csv"):
                return pd.read_csv(data_source)
            if source.endswith((".xls", ".xlsx")):
                return pd.read_excel(data_source)
            if source.endswith(".parquet"):
                return pd.read_parquet(data_source)

            raise ValueError(
                f"Unsupported file format: {data_source}. "
                "Supported formats are CSV, Excel, and Parquet."
            )

        raise TypeError(
            "data_source must be a file path string or a pandas DataFrame."
        )

    @staticmethod
    def _prepare_dataframe(
        df: pd.DataFrame,
        date_column: Optional[str] = None,
        target_column: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Perform safe pre-validation cleanup.

        This intentionally does not guess a target or date column; that remains
        the responsibility of TimeSeriesDetector.
        """
        df = df.copy()

        # Normalize duplicate column names only when exact duplicates exist.
        # This prevents ambiguous df["column"] behaviour.
        if df.columns.duplicated().any():
            duplicates = df.columns[df.columns.duplicated()].tolist()
            raise ValueError(
                "Dataset contains duplicate column names: "
                + ", ".join(map(str, duplicates))
                + ". Rename them before forecasting."
            )

        df.columns = [str(col).strip() for col in df.columns]

        if date_column and date_column not in df.columns:
            raise ValueError(
                f"Specified date column '{date_column}' was not found. "
                f"Available columns: {', '.join(df.columns)}"
            )

        if target_column and target_column not in df.columns:
            raise ValueError(
                f"Specified target column '{target_column}' was not found. "
                f"Available columns: {', '.join(df.columns)}"
            )

        # Remove completely empty rows/columns without changing meaningful data.
        df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")

        if df.empty:
            raise ValueError("Dataset contains no usable observations.")

        return df.reset_index(drop=True)

    @staticmethod
    def _normalize_time_series(
        df: pd.DataFrame,
        date_col: str,
        target_col: str,
    ) -> pd.DataFrame:
        """
        Normalize the final detected date/target pair before forecasting.

        - Parses dates safely.
        - Removes invalid dates.
        - Converts the target to numeric.
        - Sorts chronologically.
        - Removes duplicate timestamps.
        """
        out = df.copy()

        out[date_col] = pd.to_datetime(
            out[date_col],
            errors="coerce",
            infer_datetime_format=True,
        )

        out[target_col] = pd.to_numeric(
            out[target_col],
            errors="coerce",
        )

        out = out.dropna(subset=[date_col, target_col])

        if out.empty:
            raise ValueError(
                f"No valid observations remain after parsing date column "
                f"'{date_col}' and numeric target '{target_col}'."
            )

        # A forecasting series must be ordered chronologically.
        out = out.sort_values(date_col).reset_index(drop=True)

        # Duplicate timestamps can break lag/rolling/CV logic. Keep the latest
        # observation for a duplicate timestamp.
        if out[date_col].duplicated().any():
            duplicate_count = int(out[date_col].duplicated().sum())
            logger.warning(
                "Found %d duplicate timestamps in '%s'; keeping the last "
                "observation for each timestamp.",
                duplicate_count,
                date_col,
            )
            out = (
                out.drop_duplicates(subset=[date_col], keep="last")
                .reset_index(drop=True)
            )

        return out

    @staticmethod
    def _infer_frequency(date_series: pd.Series) -> str:
        """Infer a usable pandas frequency from a datetime series."""
        dates = pd.to_datetime(date_series, errors="coerce").dropna()

        if len(dates) < 3:
            # Conservative fallback for short series.
            return "D"

        dates = dates.sort_values().drop_duplicates()

        inferred = pd.infer_freq(dates)

        if inferred:
            return inferred

        deltas = dates.diff().dropna()

        if deltas.empty:
            return "D"

        median_days = deltas.dt.total_seconds().median() / 86400.0

        if median_days <= 1.5:
            return "D"
        if median_days <= 8:
            return "W"
        if median_days <= 31:
            return "MS"
        if median_days <= 92:
            return "QS"
        return "YS"

    @staticmethod
    def _json_safe_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Convert a DataFrame to JSON-safe records.

        This prevents numpy scalar types and NaN/NaT values from leaking into
        FastAPI's JSON response.
        """
        if df is None or df.empty:
            return []

        records = df.copy()

        for col in records.columns:
            if pd.api.types.is_datetime64_any_dtype(records[col]):
                records[col] = records[col].dt.strftime("%Y-%m-%d")

        records = records.replace([np.inf, -np.inf], np.nan)
        records = records.where(pd.notna(records), None)

        return records.to_dict(orient="records")

    def _forecast_auxiliary_target(
        self,
        df: pd.DataFrame,
        date_col: str,
        target_col: str,
        freq: str,
        horizon: int,
    ) -> List[Dict[str, Any]]:
        """Forecast a supplementary metric such as profit or cash flow."""
        try:
            auxiliary_df = df[[date_col, target_col]].copy()
            auxiliary_df[target_col] = pd.to_numeric(
                auxiliary_df[target_col],
                errors="coerce",
            )
            auxiliary_df = auxiliary_df.dropna(
                subset=[date_col, target_col]
            )

            if len(auxiliary_df) < 5:
                logger.warning(
                    "Skipping auxiliary target '%s': only %d valid rows.",
                    target_col,
                    len(auxiliary_df),
                )
                return []

            sec_featured, _ = self.feature_engine.transform(
                auxiliary_df,
                date_col,
                target_col,
                freq,
            )

            # Auxiliary targets (for example profit) should not trigger a
            # second full AutoML/model-selection cycle on the low-resource
            # Render instance. Use the lightweight Random Forest forecaster
            # for secondary metrics while the primary revenue target still
            # receives full model selection.
            model = RandomForestForecaster()
            model.fit(
                sec_featured,
                date_col,
                target_col,
                freq,
            )

            aux_forecast = model.predict_horizon(horizon, freq)

            if aux_forecast is None or aux_forecast.empty:
                return []

            return self._json_safe_records(aux_forecast)

        except Exception as exc:
            logger.warning(
                "Failed auxiliary forecast for '%s': %s",
                target_col,
                exc,
                exc_info=True,
            )
            return []
