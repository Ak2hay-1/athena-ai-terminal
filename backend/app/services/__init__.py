"""Application services package.

Import concrete modules directly, e.g.::

    from app.services.market_service import MarketService
    from app.services.confidence_breakdown_service import confidence_breakdown_service

Avoid eager imports here to prevent circular dependencies with the
recommendation engine.
"""

__all__: list[str] = []
