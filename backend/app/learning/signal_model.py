"""
Lightweight signal scoring model.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.settings import settings
from app.models.learning import ModelMetric
from app.repositories.learning_repository import LearningRepository


FEATURE_ORDER = [
    "confluence",
    "rsi",
    "macd_bullish",
    "news_score",
    "multi_tf_bullish",
]


class SignalModel:
    """
    Train and apply a simple classifier on recommendation outcomes.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = LearningRepository(db)
        self.model_path = Path(settings.LEARNING_MODEL_PATH)
        self.model_path.mkdir(parents=True, exist_ok=True)
        self._models: dict[str, LogisticRegression] = {}

    def _key(self, symbol: str, timeframe: str) -> str:
        return f"{symbol.upper()}_{timeframe.upper()}"

    def _model_file(self, symbol: str, timeframe: str) -> Path:
        return self.model_path / f"{self._key(symbol, timeframe)}.joblib"

    def train(
        self,
        symbol: str,
        timeframe: str,
    ) -> ModelMetric | None:
        outcomes = self.repository.list_outcomes(
            symbol=symbol,
            timeframe=timeframe,
            limit=5000,
        )

        if len(outcomes) < settings.LEARNING_MIN_SAMPLES:
            logger.info(
                "Not enough samples to train %s %s (%d)",
                symbol,
                timeframe,
                len(outcomes),
            )
            return None

        features: list[list[float]] = []
        labels: list[int] = []

        for outcome in outcomes:
            features.append([
                float(outcome.pnl_proxy),
                1.0 if outcome.label == "WIN" else 0.0,
                1.0 if outcome.predicted_signal == "BUY" else 0.0,
                float(outcome.horizon_candles),
                1.0 if outcome.label != "LOSS" else 0.0,
            ])
            labels.append(1 if outcome.label == "WIN" else 0)

        x = np.array(features)
        y = np.array(labels)

        model = LogisticRegression(max_iter=1000)
        model.fit(x, y)
        accuracy = float(model.score(x, y))

        key = self._key(symbol, timeframe)
        self._models[key] = model
        joblib.dump(model, self._model_file(symbol, timeframe))

        metric = ModelMetric(
            model_version=f"v1-{key}",
            symbol=symbol.upper(),
            timeframe=timeframe.upper(),
            accuracy=accuracy,
            sample_size=len(outcomes),
            notes=json.dumps({"features": FEATURE_ORDER}),
        )

        self.repository.save_metric(metric)
        return metric

    def predict_score(
        self,
        symbol: str,
        timeframe: str,
        feature_vector: list[float],
    ) -> float:
        key = self._key(symbol, timeframe)

        if key not in self._models:
            model_file = self._model_file(symbol, timeframe)

            if model_file.exists():
                self._models[key] = joblib.load(model_file)
            else:
                return 0.5

        model = self._models[key]
        probability = model.predict_proba(
            np.array([feature_vector]),
        )[0][1]

        return float(probability)
