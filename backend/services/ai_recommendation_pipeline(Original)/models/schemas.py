"""
Pydantic schemas for the AI Recommendation Pipeline.
Provides strong typing, validation, and serialization across health engine,
forecasting, drivers analysis, risk detection, and report exporter modules.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ==========================================
# 1. Executive Health & Data Quality Schemas
# ==========================================

class BusinessHealthAssessment(BaseModel):
    """Overall business diagnostic score and quality metrics."""
    model_config = ConfigDict(frozen=True)

    health_score: float = Field(
        ..., 
        ge=0.0, 
        le=100.0, 
        description="Composite overall business health score (0-100)."
    )
    status: str = Field(
        ..., 
        description="Health status classification (e.g., Critical, Warning, Stable, Excellent)."
    )
    confidence_score: float = Field(
        ..., 
        ge=0.0, 
        le=100.0, 
        description="Calculated data and model confidence percentage."
    )
    risk_level: str = Field(
        ..., 
        description="Overall business risk severity level (Critical, High, Medium, Low)."
    )
    data_quality_score: float = Field(
        default=100.0, 
        ge=0.0, 
        le=100.0, 
        description="Input data integrity and completeness score."
    )


# ==========================================
# 2. Multi-Horizon Forecasting Schemas
# ==========================================

class ForecastHorizon(BaseModel):
    """Targeted forecast metrics for a given time window."""
    model_config = ConfigDict(frozen=True)

    revenue: float = Field(..., description="Projected revenue amount.")
    profit: float = Field(..., description="Projected profit amount.")
    lower_bound_revenue: Optional[float] = Field(None, description="Lower confidence limit for revenue.")
    upper_bound_revenue: Optional[float] = Field(None, description="Upper confidence limit for revenue.")


class MultiHorizonForecast(BaseModel):
    """Projections across 30-day, 90-day, and 365-day operational horizons."""
    model_config = ConfigDict(frozen=True)

    next_month: ForecastHorizon = Field(..., description="1-Month (30-day) projection.")
    next_quarter: ForecastHorizon = Field(..., description="1-Quarter (90-day) projection.")
    next_year: ForecastHorizon = Field(..., description="1-Year (365-day) projection.")
    confidence_interval: str = Field(
        default="95%", 
        description="Statistical confidence interval band (e.g., '89.4% (±6.2%)')."
    )


# ==========================================
# 3. Attribution & Key Driver Schemas
# ==========================================

class MetricDriver(BaseModel):
    """Individual performance lever or correlation metric."""
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True
    )

    driver_name: str = Field(
        ..., 
        validation_alias="driver_name", 
        alias="name",
        description="Name of the driver or performance lever."
    )
    correlation: Optional[float] = Field(
        default=0.0,
        description="Correlation coefficient strength (-1.0 to 1.0)."
    )
    impact_score: Optional[float] = Field(
        default=0.0,
        description="Calculated impact percentage or score."
    )
    impact_strength: Optional[str] = Field(default=None)
    description: str = Field(default="", description="Detailed summary or metric description.")


class DriverAnalysis(BaseModel):
    """Top key operational levers driving Revenue and Profitability."""
    model_config = ConfigDict(frozen=True)

    top_revenue_drivers: List[MetricDriver] = Field(
        default_factory=list, 
        max_length=5, 
        description="Top 5 key drivers influencing top-line growth."
    )
    top_profit_drivers: List[MetricDriver] = Field(
        default_factory=list, 
        max_length=5, 
        description="Top 5 key drivers influencing bottom-line margins."
    )


# ==========================================
# 4. Risk Categorization & Anomaly Schemas
# ==========================================

class AnomalyItem(BaseModel):
    """Structured operational anomaly or financial outlier."""
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    metric: str = Field(..., description="Metric impacted (e.g., 'Current Ratio', 'Revenue').")
    severity: str = Field(default="Medium", description="Severity level: Critical, High, Medium, Low.")
    anomaly_type: str = Field(default="outlier", description="Classification category (e.g., 'statistical_outlier', 'liquidity_risk').")
    details: str = Field(default="", description="Clear explanation of the detected risk or variance.")


class RiskAssessment(BaseModel):
    """Container for operational risks and positive growth opportunities."""
    model_config = ConfigDict(frozen=True)

    anomalies: List[AnomalyItem] = Field(default_factory=list, description="Categorized risk anomalies.")
    opportunities: List[str] = Field(default_factory=list, description="Surfaced growth and optimization levers.")


# ==========================================
# 5. Action Plan & Recommendations
# ==========================================

class TimePhasedActionPlan(BaseModel):
    """Categorized execution plan across strategic horizons."""
    model_config = ConfigDict(frozen=True)

    immediate_30_days: List[str] = Field(default_factory=list, description="Priority actions for the next 30 days.")
    medium_term_90_days: List[str] = Field(default_factory=list, description="Strategic implementations for 90 days.")
    long_term_12_months: List[str] = Field(default_factory=list, description="Long-term growth and structural planning.")


# ==========================================
# 6. Combined Executive Pipeline Payload
# ==========================================

class ExecutiveReportData(BaseModel):
    """Complete aggregated data context passed directly to rendering engines."""
    model_config = ConfigDict(frozen=True)

    company_name: str = Field(default="Maduk BI Client", description="Target company name.")
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        description="Report generation timestamp."
    )
    health: BusinessHealthAssessment
    forecasts: MultiHorizonForecast
    drivers: DriverAnalysis
    risk_assessment: RiskAssessment
    action_plan: TimePhasedActionPlan
    chart_paths: Dict[str, str] = Field(
        default_factory=dict, 
        description="Mapping of generated chart labels to local absolute image paths."
    )
    company_logo_base64: Optional[str] = Field(
        default=None, 
        description="Base64 encoded string of the company logo asset."
    )
