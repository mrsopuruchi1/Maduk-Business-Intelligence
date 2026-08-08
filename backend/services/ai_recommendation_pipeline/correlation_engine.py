# correlation_engine.py

"""
Maduk Business Intelligence - Correlation Engine
Evaluates numerical cross-correlations, regression statistics, and driver dependencies.
Outputs validated MetricDriver and DriverAnalysis schema payloads.
"""

import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from backend.services.ai_recommendation_pipeline.models.schemas import MetricDriver, DriverAnalysis

logger = logging.getLogger("MadukBI.CorrelationEngine")


class CorrelationEngine:
    """Analyzes linear driver relationships, cross-metric correlations, and driver impacts."""

    def analyze(self, df: pd.DataFrame, mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Computes pairwise correlation matrices and evaluates key metric drivers.

        Args:
            df: Validated pandas DataFrame.
            mapping: Column mapping dictionary.

        Returns:
            Dict containing Pydantic DriverAnalysis model, correlation matrices, and driver insights.
        """
        rev_col = mapping.get('revenue')
        
        # Filter for numeric features with variance > 0
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            numeric_df = numeric_df.loc[:, numeric_df.std() > 0]

        if numeric_df.empty or numeric_df.shape[1] < 2:
            logger.warning("Insufficient variable numerical features for driver correlation analysis.")
            empty_analysis = DriverAnalysis(
                primary_metric=rev_col.replace('_', ' ').title() if rev_col else "Revenue",
                drivers=[],
                insight="Insufficient dynamic numerical data available to establish statistical correlation dependencies."
            )
            return {
                "model": empty_analysis,
                "correlation_matrix": {},
                "top_revenue_drivers": []
            }

        corr_matrix = numeric_df.corr().round(3).fillna(0.0)
        
        drivers_list: List[MetricDriver] = []
        raw_drivers_dict: List[Dict[str, Any]] = []

        target_col = rev_col if (rev_col and rev_col in corr_matrix) else numeric_df.columns[0]

        if target_col in corr_matrix:
            target_corrs = corr_matrix[target_col].drop(labels=[target_col], errors='ignore')
            sorted_corrs = target_corrs.abs().sort_values(ascending=False)
            
            for col_name in sorted_corrs.index[:5]:
                corr_val = float(target_corrs[col_name])
                
                if corr_val > 0.7:
                    relationship = "Strong Positive"
                elif corr_val > 0.3:
                    relationship = "Moderate Positive"
                elif corr_val < -0.7:
                    relationship = "Strong Negative"
                elif corr_val < -0.3:
                    relationship = "Moderate Negative"
                else:
                    relationship = "Weak/Neutral"

                impact_score = round(min(100.0, max(0.0, (corr_val ** 2) * 100.0)), 1)
                
                sample_size = len(numeric_df)
                confidence = round(min(99.0, max(20.0, (abs(corr_val) * 70.0) + min(30.0, sample_size * 0.5))), 1)

                display_name = str(col_name).replace('_', ' ').title()

                driver_model = MetricDriver(
                    driver_name=display_name,
                    impact_score=impact_score,
                    correlation=round(corr_val, 2),
                    confidence=confidence,
                    relationship_strength=relationship
                )
                drivers_list.append(driver_model)

                raw_drivers_dict.append({
                    "driver_name": display_name,
                    "correlation_score": round(corr_val, 2),
                    "impact_score": impact_score,
                    "confidence": confidence,
                    "relationship_strength": relationship
                })

        if drivers_list:
            top_driver = drivers_list[0]
            insight_text = (
                f"Statistical correlation indicates '{top_driver.driver_name}' is the primary "
                f"driver of {target_col.replace('_', ' ').title()} (Correlation: {top_driver.correlation:.2f}, "
                f"Impact: {top_driver.impact_score}%)."
            )
        else:
            insight_text = "No strong metric correlations or drivers were identified in the dataset."

        driver_analysis_model = DriverAnalysis(
            primary_metric=target_col.replace('_', ' ').title(),
            drivers=drivers_list,
            insight=insight_text
        )

        logger.info(
            f"Correlation Engine completed analysis for '{target_col}'. "
            f"Identified {len(drivers_list)} metric drivers."
        )

        return {
            "model": driver_analysis_model,
            "correlation_matrix": corr_matrix.to_dict(),
            "top_revenue_drivers": raw_drivers_dict
        }
