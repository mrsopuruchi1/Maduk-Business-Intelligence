# anomaly_detection.py

"""
Maduk Business Intelligence - Anomaly Detection & Risk Engine
Detects financial and operational anomalies, outliers, and variance spikes using statistical Z-score
and machine learning Isolation Forest models. Categorizes risks by severity level and highlights 
business growth opportunities.
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from backend.services.ai_recommendation_pipeline.models.schemas import AnomalyItem, RiskAssessment

logger = logging.getLogger("MadukBI.AnomalyDetectionEngine")


class AnomalyDetectionEngine:
    """Detects metric anomalies, statistical outliers, categorizes risks, and extracts growth opportunities."""

    def detect(self, df: pd.DataFrame, mapping: Dict[str, str], kpis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Scans numerical indicators, flags statistical anomalies, categorizes risks by severity level,
        and identifies high-leverage business opportunities.

        Args:
            df: Validated/Enriched pandas DataFrame.
            mapping: Canonical column dictionary mapping.
            kpis: Optional dictionary of evaluated key performance metrics.

        Returns:
            Dict containing Pydantic RiskAssessment model, anomalies list, and opportunities list.
        """
        raw_anomalies: List[Dict[str, Any]] = []
        anomaly_models: List[AnomalyItem] = []
        opportunities: List[str] = []

        if df.empty or len(df) < 2:
            empty_risk_assessment = RiskAssessment(anomalies=[], opportunities=[])
            return {
                "model": empty_risk_assessment,
                "anomalies": [],
                "opportunities": []
            }

        rev_col = mapping.get('revenue')
        exp_col = mapping.get('expenses')
        date_col = mapping.get('date')
        profit_col = mapping.get('profit')

        # 1. Statistical Z-Score Outlier Detection for Revenue Drops & Cost Spikes
        for col_key, col_name, label in [
            ('revenue', rev_col, 'Revenue Dropped Significantly'),
            ('expenses', exp_col, 'Expense Spike Detected')
        ]:
            if col_name and col_name in df:
                series = pd.to_numeric(df[col_name], errors='coerce').dropna()
                if len(series) < 3:
                    continue

                mean_val = series.mean()
                std_val = series.std()

                if std_val > 0:
                    z_scores = (series - mean_val) / std_val
                    
                    # Flag Revenue Drops (Z < -2.0) or Expense Spikes (Z > +2.0)
                    threshold_condition = (z_scores < -2.0) if col_key == 'revenue' else (z_scores > 2.0)
                    anomalous_indices = series[threshold_condition].index

                    for idx in anomalous_indices:
                        val = series.loc[idx]
                        z_val = abs(z_scores.loc[idx])
                        
                        date_str = str(df.loc[idx, date_col]) if date_col and date_col in df else f"Row {idx}"
                        if hasattr(df.loc[idx, date_col], 'strftime'):
                            date_str = df.loc[idx, date_col].strftime('%Y-%m-%d')

                        if z_val > 3.0 or (col_key == 'revenue' and val < mean_val * 0.5):
                            severity = "Critical"
                        elif z_val > 2.5:
                            severity = "High"
                        elif z_val > 2.0:
                            severity = "Medium"
                        else:
                            severity = "Low"

                        details_msg = (
                            f"{label} on {date_str}: Recorded value ${val:,.2f} "
                            f"deviated significantly from baseline average (${mean_val:,.2f})."
                        )

                        raw_anomalies.append({
                            "type": "statistical_outlier",
                            "severity": severity,
                            "metric": label,
                            "date_or_period": date_str,
                            "value": round(float(val), 2),
                            "historical_average": round(float(mean_val), 2),
                            "description": details_msg
                        })

                        anomaly_models.append(
                            AnomalyItem(
                                metric=label,
                                severity=severity,
                                anomaly_type="statistical_outlier",
                                details=details_msg
                            )
                        )

        # 2. Multivariate Isolation Forest for Pattern Outliers
        numeric_cols = [c for c in [rev_col, exp_col, profit_col, mapping.get('marketing_spend')] if c and c in df]
        if len(numeric_cols) >= 2 and len(df) >= 10:
            try:
                X = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0.0)
                # Verify non-zero variance before training Isolation Forest
                if X.var().sum() > 0:
                    iso = IsolationForest(contamination=0.05, random_state=42)
                    preds = iso.fit_predict(X)
                    
                    outlier_indices = np.where(preds == -1)[0]
                    for idx in outlier_indices:
                        row_idx = df.index[idx]
                        date_str = str(df.loc[row_idx, date_col]) if date_col and date_col in df else f"Row {row_idx}"
                        if hasattr(df.loc[row_idx, date_col], 'strftime'):
                            date_str = df.loc[row_idx, date_col].strftime('%Y-%m-%d')

                        details_msg = f"Unusual multivariate metric distribution detected around period {date_str}."
                        
                        raw_anomalies.append({
                            "type": "multivariate_anomaly",
                            "severity": "Medium",
                            "metric": "Multivariate Pattern Anomaly",
                            "date_or_period": date_str,
                            "value": 0.0,
                            "historical_average": 0.0,
                            "description": details_msg
                        })

                        anomaly_models.append(
                            AnomalyItem(
                                metric="Multivariate Pattern Anomaly",
                                severity="Medium",
                                anomaly_type="multivariate_anomaly",
                                details=details_msg
                            )
                        )
            except Exception as e:
                logger.warning(f"Isolation Forest execution skipped: {str(e)}")

        # 3. KPI Risk Checks (Liquidity, Churn, Margins)
        if kpis:
            curr_ratio = kpis.get('current_ratio')
            if curr_ratio is not None and curr_ratio < 1.0:
                msg = f"Liquidity Warning: Current Ratio is {curr_ratio:.2f} (below recommended threshold of 1.0)."
                raw_anomalies.append({"type": "liquidity_risk", "severity": "Critical", "metric": "Current Ratio", "description": msg})
                anomaly_models.append(AnomalyItem(metric="Current Ratio", severity="Critical", anomaly_type="liquidity_risk", details=msg))

            churn = kpis.get('churn_rate')
            if churn is not None and churn > 10.0:
                msg = f"Customer Churn Spike: Current churn rate of {churn:.1f}% poses customer retention risks."
                raw_anomalies.append({"type": "retention_risk", "severity": "High", "metric": "Customer Churn", "description": msg})
                anomaly_models.append(AnomalyItem(metric="Customer Churn", severity="High", anomaly_type="retention_risk", details=msg))

        # 4. Identification of Positive Business Growth Opportunities
        if rev_col and rev_col in df:
            revenue_growth = kpis.get('revenue_growth', 0.0) if kpis else 0.0
            if revenue_growth > 5.0:
                opportunities.append(f"Capitalize on positive top-line growth (+{revenue_growth:.1f}%) to expand acquisition scale.")

        if exp_col and exp_col in df and rev_col and rev_col in df:
            total_rev = df[rev_col].sum()
            total_exp = df[exp_col].sum()
            if total_rev > 0:
                exp_ratio = total_exp / total_rev
                if exp_ratio > 0.70:
                    opportunities.append("Operating expense ratio exceeds 70%. Vendor contract restructuring presents cost recovery opportunities.")
                else:
                    opportunities.append("Operating margin efficiency provides surplus capital for growth initiatives.")

        mkt_col = mapping.get('marketing_spend')
        if mkt_col and mkt_col in df:
            opportunities.append("Optimize digital acquisition channels to improve Customer Acquisition Cost (CAC) returns.")

        if not opportunities:
            opportunities.append("Establish automated customer retention workflows to unlock upsell expansion opportunities.")

        risk_assessment_model = RiskAssessment(
            anomalies=anomaly_models,
            opportunities=opportunities
        )

        logger.info(
            f"Anomaly Engine complete. Flagged {len(raw_anomalies)} anomalies "
            f"and surfaced {len(opportunities)} growth opportunities."
        )

        return {
            "model": risk_assessment_model,
            "anomalies": raw_anomalies,
            "opportunities": opportunities
        }
