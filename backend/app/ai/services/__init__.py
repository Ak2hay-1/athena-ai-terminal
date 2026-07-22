"""AI services package.

Import the singleton from the submodule to avoid shadowing:

    from app.ai.services.ai_service import ai_service
"""

from app.ai.services.ai_service import AIService
from app.ai.services.chat_service import ChatService
from app.ai.services.indicator_explainer import IndicatorExplainer
from app.ai.services.market_summary_service import MarketSummaryService
from app.ai.services.session_summary_service import SessionSummaryService
from app.ai.services.strategy_teacher import StrategyTeacher
from app.ai.services.trade_explainer import TradeExplainer

__all__ = [
    "AIService",
    "ChatService",
    "IndicatorExplainer",
    "MarketSummaryService",
    "SessionSummaryService",
    "StrategyTeacher",
    "TradeExplainer",
]
