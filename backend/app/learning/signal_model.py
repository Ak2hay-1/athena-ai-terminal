"""
Lightweight signal scoring model.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# #region agent log
def _agent_dbg(hypothesis_id: str, message: str, data: dict) -> None:
    try:
        payload = {
            "sessionId": "5f6221",
            "runId": "post-fix",
            "hypothesisId": hypothesis_id,
            "location": "signal_model.py:import",
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        log_path = Path(__file__).resolve().parents[3] / "debug-5f6221.log"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass


_pkg_status: dict[str, object] = {
    "executable": sys.executable,
    "prefix": sys.prefix,
    "VIRTUAL_ENV": __import__("os").environ.get("VIRTUAL_ENV"),
}
for _name in ("joblib", "sklearn", "numpy"):
    try:
        __import__(_name)
        _pkg_status[_name] = {"ok": True}
    except Exception as _exc:  # noqa: BLE001
        _pkg_status[_name] = {"ok": False, "error": type(_exc).__name__, "msg": str(_exc)}
_agent_dbg("A", "pre-import package probe", _pkg_status)
_agent_dbg(
    "B",
    "scikit-learn / joblib availability",
    {
        "joblib_ok": _pkg_status.get("joblib", {}).get("ok")
        if isinstance(_pkg_status.get("joblib"), dict)
        else False,
        "sklearn_ok": _pkg_status.get("sklearn", {}).get("ok")
        if isinstance(_pkg_status.get("sklearn"), dict)
        else False,
    },
)
_agent_dbg(
    "C",
    "interpreter / venv identity",
    {
        "executable": sys.executable,
        "prefix": sys.prefix,
        "VIRTUAL_ENV": __import__("os").environ.get("VIRTUAL_ENV"),
        "in_venv": getattr(sys, "base_prefix", sys.prefix) != sys.prefix,
    },
)
# #endregion

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
