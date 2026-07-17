"""
Admin operations API.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.core.exceptions import ValidationException
from app.core.market_validation import validate_timeframe
from app.core.settings import settings
from app.database.database import check_database_connection
from app.database.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.scheduler.market_scheduler import market_scheduler
from app.scheduler.news_scheduler import news_scheduler
from app.schemas.admin import (
    AdminConfigSummary,
    AdminHealthSummary,
    AdminLearningSummary,
    AdminMt5Summary,
    AdminOverview,
    AdminSchedulersResponse,
    AdminUsersSummary,
    MarketCleanupResponse,
    NewsSyncResponse,
    SchedulerStatus,
    SchedulerTriggerResponse,
)
from app.services.market_service import MarketService
from app.services.mt5_service import mt5_service
from app.services.news_service import NewsService

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get(
    "/overview",
    response_model=AdminOverview,
    summary="Admin operations overview",
)
def admin_overview(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminOverview:
    database_ok = check_database_connection()

    health = AdminHealthSummary(
        status="healthy" if database_ok else "unhealthy",
        database="connected" if database_ok else "disconnected",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
    )

    try:
        mt5_status = mt5_service.status()
        mt5 = AdminMt5Summary(
            connected=mt5_status.connected,
            initialized=mt5_status.initialized,
            logged_in=mt5_status.logged_in,
            server=mt5_status.server,
            login=mt5_status.login,
            message=mt5_status.message,
        )
    except Exception as exc:
        mt5 = AdminMt5Summary(
            connected=False,
            initialized=False,
            logged_in=False,
            message=f"Unavailable: {exc}",
        )

    users_repo = UserRepository(db)
    users = AdminUsersSummary(
        total=users_repo.count_all(),
        active=users_repo.count_active(),
        admins=users_repo.count_admins(),
    )

    learning = AdminLearningSummary(
        enabled=settings.LEARNING_ENABLED,
        min_samples=settings.LEARNING_MIN_SAMPLES,
        retrain_interval_hours=settings.LEARNING_RETRAIN_INTERVAL_HOURS,
        model_path=settings.LEARNING_MODEL_PATH,
    )

    from app.ai.providers.factory import configured_model_name

    config = AdminConfigSummary(
        app_env=settings.APP_ENV,
        execution_provider=settings.EXECUTION_PROVIDER,
        market_symbols=list(settings.MARKET_SYMBOLS),
        market_timeframes=list(settings.MARKET_TIMEFRAMES),
        ai_provider=settings.AI_PROVIDER,
        ai_model=configured_model_name(settings.AI_PROVIDER),
        ollama_model=settings.OLLAMA_MODEL,
        collector_interval_seconds=settings.COLLECTOR_INTERVAL_SECONDS,
    )

    return AdminOverview(
        health=health,
        mt5=mt5,
        learning=learning,
        users=users,
        config=config,
    )


@router.get(
    "/schedulers",
    response_model=AdminSchedulersResponse,
    summary="Scheduler status",
)
def admin_schedulers(
    _: User = Depends(require_admin),
) -> AdminSchedulersResponse:
    return AdminSchedulersResponse(
        market=SchedulerStatus.model_validate(market_scheduler.status()),
        news_learning=SchedulerStatus.model_validate(news_scheduler.status()),
        timezone=settings.SCHEDULER_TIMEZONE,
    )


@router.post(
    "/schedulers/market/run",
    response_model=SchedulerTriggerResponse,
    summary="Trigger market collection job",
)
def trigger_market_collection(
    timeframe: str = Query(...),
    _: User = Depends(require_admin),
) -> SchedulerTriggerResponse:
    timeframe = validate_timeframe(timeframe)

    try:
        result = market_scheduler.trigger_timeframe(timeframe)
    except ValueError as exc:
        raise ValidationException(str(exc)) from exc

    return SchedulerTriggerResponse.model_validate(result)


@router.post(
    "/schedulers/jobs/{job_id}/run",
    response_model=SchedulerTriggerResponse,
    summary="Trigger scheduler job by id",
)
def trigger_scheduler_job(
    job_id: str,
    _: User = Depends(require_admin),
) -> SchedulerTriggerResponse:
    try:
        if job_id.startswith("collect_"):
            result = market_scheduler.trigger_job(job_id)
        else:
            result = news_scheduler.trigger_job(job_id)
    except ValueError as exc:
        raise ValidationException(str(exc)) from exc

    return SchedulerTriggerResponse.model_validate(result)


@router.post(
    "/news/sync",
    response_model=NewsSyncResponse,
    summary="Sync news feeds now",
)
def admin_news_sync(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> NewsSyncResponse:
    inserted = NewsService(db).sync_feeds()
    return NewsSyncResponse(inserted=inserted)


@router.delete(
    "/market/cleanup",
    response_model=MarketCleanupResponse,
    summary="Delete candles before a timestamp",
)
def admin_market_cleanup(
    before: datetime = Query(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> MarketCleanupResponse:
    deleted = MarketService(db).delete_before(before)
    return MarketCleanupResponse(
        deleted=deleted,
        before=before.isoformat(),
    )
