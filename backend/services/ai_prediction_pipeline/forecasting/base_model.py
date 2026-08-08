"""
Maduk Business Intelligence - Abstract Base Forecaster
=====================================================
File: backend/services/ai_prediction_pipeline/forecasting/base_model.py
"""

import abc
from typing import Dict, Any, Optional
import pandas as pd


class BaseForecaster(abc.ABC):
    """Abstract interface governing all forecasting model adapters."""

    def __init__(self, name: str):
        self.name = name
        self.is_fitted = False

    @abc.abstractmethod
    def fit(self, df: pd.DataFrame, date_col: str, target_col: str, freq: str = "MS") -> "BaseForecaster":
        """Fits model on training data."""
        pass

    @abc.abstractmethod
    def predict_horizon(self, horizon: int, freq: str = "MS") -> pd.DataFrame:
        """
        Generates forecasts for the given horizon.
        
        Returns:
            pd.DataFrame with standard columns: ['date', 'forecast', 'lower_bound', 'upper_bound']
        """
        pass

    @abc.abstractmethod
    def get_feature_importance(self) -> Dict[str, float]:
        """Returns normalized driver/feature importance dictionary."""
        pass
