"""
Athena Qualification package — institutional desk filters.

Runs before RiskEngine to reject weak markets early.
"""

from app.qualification.correlation_filter import filter_correlated
from app.qualification.market_regime import detect_regime
from app.qualification.models import MarketRegime
from app.qualification.models import QualificationResult
from app.qualification.models import SetupQualityGrade
from app.qualification.models import SetupLifecycleState
from app.qualification.qualification_engine import qualification_engine
from app.qualification.recommendation_ranker import rank_opportunities
from app.qualification.setup_quality import setup_quality_service

__all__ = [
    "MarketRegime",
    "QualificationResult",
    "SetupQualityGrade",
    "SetupLifecycleState",
    "detect_regime",
    "qualification_engine",
    "setup_quality_service",
    "rank_opportunities",
    "filter_correlated",
]
