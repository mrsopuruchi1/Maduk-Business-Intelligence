"""
Maduk Business Intelligence - PyTorch LSTM Forecaster
======================================================
File: backend/services/ai_prediction_pipeline/forecasting/lstm_model.py
"""

import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

from .base_model import BaseForecaster

logger = logging.getLogger("MadukBI.LSTMModel")


class LSTMForecaster(BaseForecaster):
    """Deep Learning Long Short-Term Memory (LSTM) network using PyTorch."""

    def __init__(self, sequence_length: int = 6, hidden_dim: int = 32, epochs: int = 50):
        super().__init__("LSTM Neural Network")
        self.sequence_length = sequence_length
        self.hidden_dim = hidden_dim
        self.epochs = epochs
        self.model = None
        self.scaler_x = MinMaxScaler()
        self.scaler_y = MinMaxScaler()
        self.feature_cols: List[str] = []
        self.last_date = None
        self.target_col = None
        self.date_col = None
        self.last_sequence = None

    def fit(self, df: pd.DataFrame, date_col: str, target_col: str, freq: str = "MS") -> "LSTMForecaster":
        try:
            import torch
            import torch.nn as nn
            import torch.optim as optim
        except ImportError:
            raise ImportError("PyTorch is required for LSTMForecaster. Run 'pip install torch'.")

        logger.info("Fitting LSTM PyTorch neural network...")
        self.date_col = date_col
        self.target_col = target_col
        
        train_df = df.copy()
        train_df[date_col] = pd.to_datetime(train_df[date_col])
        train_df = train_df.sort_values(by=date_col).reset_index(drop=True)
        self.last_date = train_df[date_col].max()

        self.feature_cols = [c for c in train_df.columns if c not in [date_col, target_col]]
        
        # Scale features and target independently
        X_raw = train_df[self.feature_cols].values
        y_raw = train_df[[target_col]].values

        X_scaled = self.scaler_x.fit_transform(X_raw)
        y_scaled = self.scaler_y.fit_transform(y_raw)

        # Build 3D sequences: (samples, seq_len, num_features)
        X_seq, y_seq = [], []
        if len(train_df) <= self.sequence_length:
            self.sequence_length = max(2, len(train_df) - 1)

        for i in range(len(X_scaled) - self.sequence_length):
            X_seq.append(X_scaled[i : i + self.sequence_length])
            y_seq.append(y_scaled[i + self.sequence_length])

        X_tensor = torch.tensor(np.array(X_seq), dtype=torch.float32)
        y_tensor = torch.tensor(np.array(y_seq), dtype=torch.float32)

        self.last_sequence = X_scaled[-self.sequence_length:]

        # Define PyTorch PyTorch Model Architecture
        class PyTorchLSTM(nn.Module):
            def __init__(self, input_dim, hidden_dim, output_dim=1):
                super().__init__()
                self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
                self.fc = nn.Linear(hidden_dim, output_dim)

            def forward(self, x):
                out, _ = self.lstm(x)
                out = self.fc(out[:, -1, :])
                return out

        num_features = X_raw.shape[1]
        self.model = PyTorchLSTM(input_dim=num_features, hidden_dim=self.hidden_dim)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=0.01)

        # Training loop
        self.model.train()
        for epoch in range(self.epochs):
            if len(X_tensor) == 0:
                break
            optimizer.zero_grad()
            outputs = self.model(X_tensor)
            loss = criterion(outputs, y_tensor)
            loss.backward()
            optimizer.step()

        self.is_fitted = True
        return self

    def predict_horizon(self, horizon: int, freq: str = "MS") -> pd.DataFrame:
        import torch

        if not self.is_fitted:
            raise RuntimeError("LSTM model must be fitted prior to predicting.")

        self.model.eval()
        future_dates = pd.date_range(start=self.last_date, periods=horizon + 1, freq=freq)[1:]
        
        preds_scaled = []
        current_seq = self.last_sequence.copy()

        with torch.no_grad():
            for _ in range(horizon):
                seq_tensor = torch.tensor(current_seq[np.newaxis, :, :], dtype=torch.float32)
                pred_val = self.model(seq_tensor).numpy()[0, 0]
                preds_scaled.append(pred_val)

                # Roll sequence forward for multi-step autoregressive projection
                new_row = current_seq[-1].copy()
                new_row[0] = pred_val  # update primary lag feature slot
                current_seq = np.vstack([current_seq[1:], new_row])

        # Inverse transform scaled projections back to real domain
        preds = self.scaler_y.inverse_transform(np.array(preds_scaled).reshape(-1, 1)).flatten()

        # Variance margin calculation for bounds
        std_err = np.std(preds) * 0.10 if len(preds) > 1 else 0.05 * np.mean(preds)

        return pd.DataFrame({
            "date": future_dates,
            "forecast": preds,
            "lower_bound": preds - (1.645 * std_err),
            "upper_bound": preds + (1.645 * std_err)
        })

    def get_feature_importance(self) -> Dict[str, float]:
        # Equal importance weights across historical sequential memory cells
        if not self.feature_cols:
            return {"temporal_sequence_memory": 1.0}
        
        weight = 1.0 / len(self.feature_cols)
        return {col: round(weight, 3) for col in self.feature_cols}
