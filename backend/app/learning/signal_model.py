"""
Lightweight signal scoring model.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.settings import settings
from app.models.learning import ModelMetric
from app.models.recommendation import Recommendation
from app.repositories.learning_repository import LearningRepository


FEATURE_ORDER = [
    "confluence",
    "rsi",
    "macd_bullish",
    "news_score",
    "multi_tf_bullish",
]


def feature_vector_from_recommendation(
    recommendation: Recommendation | None = None,
    *,
    analysis: dict[str, Any] | None = None,
    confluence: float | int | None = None,
) -> list[float]:
    """
    Build a pre-outcome feature vector matching FEATURE_ORDER.

    Never includes labels or pnl — suitable for train and infer.
    """
    analysis_data: dict[str, Any] = {}
    if analysis and isinstance(analysis, dict):
        analysis_data = analysis
    elif recommendation is not None and isinstance(recommendation.analysis, dict):
        analysis_data = recommendation.analysis

    confluence_val = confluence
    if confluence_val is None and recommendation is not None:
        confluence_val = recommendation.confluence
    if confluence_val is None:
        confluence_val = (analysis_data.get("confluence") or {}).get("score", 0)

    indicators = analysis_data.get("indicators") or {}
    if not isinstance(indicators, dict):
        indicators = {}

    rsi_raw = indicators.get("rsi", indicators.get("rsi_14", 50.0))
    try:
        rsi = float(rsi_raw)
    except (TypeError, ValueError):
        rsi = 50.0

    macd = indicators.get("macd")
    macd_bullish = 0.0
    if isinstance(macd, dict):
        macd_bullish = 1.0 if macd.get("bullish") else 0.0
    elif indicators.get("macd_bullish") is True:
        macd_bullish = 1.0

    news = analysis_data.get("news") or {}
    if not isinstance(news, dict):
        news = {}
    news_score_raw = news.get("score", news.get("sentiment_score", news.get("sentiment", 0.0)))
    try:
        news_score = float(news_score_raw or 0.0)
    except (TypeError, ValueError):
        news_score = 0.0

    mtf = analysis_data.get("multi_timeframe") or {}
    if not isinstance(mtf, dict):
        mtf = {}
    overall = str(mtf.get("overall_trend") or mtf.get("trend") or "").upper()
    multi_tf_bullish = 1.0 if overall == "BULLISH" else 0.0

    return [
        float(confluence_val or 0.0) / 100.0,
        max(0.0, min(1.0, rsi / 100.0)),
        macd_bullish,
        max(-1.0, min(1.0, news_score)),
        multi_tf_bullish,
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

    def has_model(self, symbol: str, timeframe: str) -> bool:
        key = self._key(symbol, timeframe)
        if key in self._models:
            return True
        return self._model_file(symbol, timeframe).exists()

    def train(
        self,
        symbol: str,
        timeframe: str,
    ) -> ModelMetric | None:
        rows = self.repository.list_outcomes_with_recommendations(
            symbol=symbol,
            timeframe=timeframe,
            limit=5000,
        )

        if len(rows) < settings.LEARNING_MIN_SAMPLES:
            logger.info(
                "Not enough samples to train %s %s (%d)",
                symbol,
                timeframe,
                len(rows),
            )
            return None

        features: list[list[float]] = []
        labels: list[int] = []

        for outcome, recommendation in rows:
            if recommendation is None:
                continue
            features.append(
                feature_vector_from_recommendation(recommendation),
            )
            labels.append(1 if outcome.label == "WIN" else 0)

        if len(features) < settings.LEARNING_MIN_SAMPLES:
            logger.info(
                "Not enough joined samples to train %s %s (%d)",
                symbol,
                timeframe,
                len(features),
            )
            return None

        x = np.array(features)
        y = np.array(labels)

        # Need both classes for meaningful logistic regression.
        if len(set(labels)) < 2:
            logger.info(
                "Single-class outcomes; skipping train %s %s",
                symbol,
                timeframe,
            )
            return None

        model = LogisticRegression(max_iter=1000)
        model.fit(x, y)
        accuracy = float(model.score(x, y))

        key = self._key(symbol, timeframe)
        self._models[key] = model
        joblib.dump(model, self._model_file(symbol, timeframe))

        metric = ModelMetric(
            model_version=f"v2-{key}",
            symbol=symbol.upper(),
            timeframe=timeframe.upper(),
            accuracy=accuracy,
            sample_size=len(features),
            notes=json.dumps({"features": FEATURE_ORDER, "version": 2}),
        )

        self.repository.save_metric(metric)
        logger.info(
            "Trained SignalModel v2 %s accuracy=%.3f n=%d",
            key,
            accuracy,
            len(features),
        )
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
        if len(feature_vector) != len(FEATURE_ORDER):
            logger.warning(
                "Feature vector length %s != %s; returning 0.5",
                len(feature_vector),
                len(FEATURE_ORDER),
            )
            return 0.5

        # Reject stale v1 models trained on 5 leaked features of different meaning
        # if n_features_in_ mismatches expected FEATURE_ORDER length after reload.
        n_in = getattr(model, "n_features_in_", len(FEATURE_ORDER))
        if int(n_in) != len(FEATURE_ORDER):
            logger.warning("Stale model feature size for %s; returning 0.5", key)
            return 0.5

        probability = model.predict_proba(
            np.array([feature_vector]),
        )[0][1]

        return float(probability)
