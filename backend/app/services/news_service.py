"""
News ingestion and query service.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from datetime import timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import feedparser
import httpx
from sqlalchemy.orm import Session

from app.analysis.news_sentiment import news_sentiment_engine
from app.core.logger import logger
from app.core.settings import settings
from app.models.news_event import NewsEvent
from app.repositories.news_repository import NewsRepository
from app.services.base_service import BaseService

CURRENCY_TO_SYMBOLS = {
    "USD": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF", "XAUUSD"],
    "EUR": ["EURUSD"],
    "GBP": ["GBPUSD"],
    "JPY": ["USDJPY"],
    "AUD": ["AUDUSD"],
    "CAD": ["USDCAD"],
    "NZD": ["NZDUSD"],
    "CHF": ["USDCHF"],
    "XAU": ["XAUUSD"],
    "GOLD": ["XAUUSD"],
}


class NewsService(BaseService):
    """
    Fetch, store, and query news for trading decisions.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.repository = NewsRepository(db)

    def sync_feeds(self) -> int:
        """
        Fetch configured RSS/calendar feeds and persist events.
        """
        inserted = 0

        for feed_url in settings.NEWS_RSS_FEEDS:
            try:
                inserted += self._sync_feed(feed_url)
            except Exception:
                logger.exception(
                    "News sync failed for %s",
                    feed_url,
                )

        if settings.NEWS_API_KEY:
            try:
                inserted += self._sync_news_api()
            except Exception:
                logger.exception("NewsAPI sync failed.")

        self.commit()
        return inserted

    def _sync_feed(self, feed_url: str) -> int:
        response = httpx.get(feed_url, timeout=30.0)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")

        if "xml" in content_type or feed_url.endswith(".xml"):
            return self._parse_xml_calendar(
                response.text,
                feed_url,
            )

        parsed = feedparser.parse(response.text)
        inserted = 0

        for entry in parsed.entries:
            external_id = getattr(entry, "id", None) or entry.get("link")

            if not external_id:
                continue

            if self.repository.get_by_external_id(external_id):
                continue

            title = entry.get("title", "").strip()

            if not title:
                continue

            summary = entry.get("summary", "")
            published = self._parse_published(entry)
            symbols = self._infer_symbols(title + " " + summary)
            impact = self._infer_impact(title, summary)
            sentiment = news_sentiment_engine.analyze([title])

            event = NewsEvent(
                title=title[:512],
                summary=summary[:2000] if summary else None,
                source=feed_url,
                symbols=symbols,
                impact=impact,
                sentiment_score=sentiment.score,
                published_at=published,
                external_id=external_id,
            )

            self.repository.create(event)
            inserted += 1

        return inserted

    def _parse_xml_calendar(self, xml_text: str, source: str) -> int:
        inserted = 0

        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError:
            return 0

        for event_node in root.iter("event"):
            title = (event_node.findtext("title") or event_node.findtext("name") or "").strip()

            if not title:
                continue

            external_id = hashlib.sha256(
                f"{source}:{title}".encode()
            ).hexdigest()

            if self.repository.get_by_external_id(external_id):
                continue

            currency = (event_node.findtext("currency") or "").upper()
            impact_raw = (event_node.findtext("impact") or "medium").lower()
            impact = {"high": "HIGH", "medium": "MEDIUM", "low": "LOW"}.get(
                impact_raw,
                "MEDIUM",
            )

            symbols = CURRENCY_TO_SYMBOLS.get(currency, settings.MARKET_SYMBOLS)
            published = datetime.now(timezone.utc)
            date_text = event_node.findtext("date") or event_node.findtext("time")

            if date_text:
                try:
                    published = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
                except ValueError:
                    pass

            sentiment = news_sentiment_engine.analyze([title])

            event = NewsEvent(
                title=title[:512],
                summary=event_node.findtext("description"),
                source=source,
                symbols=symbols,
                impact=impact,
                sentiment_score=sentiment.score,
                published_at=published,
                external_id=external_id,
            )

            self.repository.create(event)
            inserted += 1

        return inserted

    def _sync_news_api(self) -> int:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "forex OR gold OR federal reserve OR ECB",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 25,
            "apiKey": settings.NEWS_API_KEY,
        }

        response = httpx.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        inserted = 0

        for article in data.get("articles", []):
            external_id = article.get("url")

            if not external_id or self.repository.get_by_external_id(external_id):
                continue

            title = article.get("title", "").strip()

            if not title:
                continue

            summary = article.get("description") or ""
            published_raw = article.get("publishedAt")

            try:
                published = datetime.fromisoformat(
                    published_raw.replace("Z", "+00:00")
                )
            except (TypeError, ValueError, AttributeError):
                published = datetime.now(timezone.utc)

            symbols = self._infer_symbols(title + " " + summary)
            impact = self._infer_impact(title, summary)
            sentiment = news_sentiment_engine.analyze([title])

            event = NewsEvent(
                title=title[:512],
                summary=summary[:2000] if summary else None,
                source="newsapi",
                symbols=symbols,
                impact=impact,
                sentiment_score=sentiment.score,
                published_at=published,
                external_id=external_id,
            )

            self.repository.create(event)
            inserted += 1

        return inserted

    def get_context_for_symbol(
        self,
        symbol: str,
    ) -> dict:
        """
        Build news context for analysis pipeline.
        """
        symbol = symbol.upper()
        headlines = self.repository.get_latest_for_symbol(symbol, limit=10)
        high_impact = self.repository.get_upcoming_high_impact(
            symbol,
            settings.NEWS_BLOCK_MINUTES,
        )

        titles = [event.title for event in headlines]
        sentiment = news_sentiment_engine.analyze(titles)

        return {
            "headlines": titles,
            "sentiment": sentiment.sentiment,
            "score": sentiment.score,
            "confidence": sentiment.confidence,
            "reasons": sentiment.reasons,
            "high_impact_upcoming": len(high_impact) > 0,
            "upcoming_events": [
                {
                    "title": event.title,
                    "impact": event.impact,
                    "published_at": event.published_at.isoformat(),
                }
                for event in high_impact[:5]
            ],
        }

    def _infer_symbols(self, text: str) -> list[str]:
        text_upper = text.upper()
        symbols: set[str] = set()

        for currency, mapped in CURRENCY_TO_SYMBOLS.items():
            if re.search(rf"\b{re.escape(currency)}\b", text_upper):
                symbols.update(mapped)

        if not symbols:
            symbols.update(settings.MARKET_SYMBOLS[:3])

        return sorted(symbols)

    def _infer_impact(self, title: str, summary: str) -> str:
        text = f"{title} {summary}".lower()
        high_keywords = [
            "nfp",
            "non-farm",
            "fomc",
            "rate decision",
            "cpi",
            "gdp",
            "war",
            "crisis",
        ]

        if any(word in text for word in high_keywords):
            return "HIGH"

        medium_keywords = [
            "inflation",
            "employment",
            "retail sales",
            "pmi",
        ]

        if any(word in text for word in medium_keywords):
            return "MEDIUM"

        return "LOW"

    def _parse_published(self, entry) -> datetime:
        published = entry.get("published_parsed") or entry.get("updated_parsed")

        if published:
            return datetime(*published[:6], tzinfo=timezone.utc)

        raw = entry.get("published") or entry.get("updated")

        if raw:
            try:
                return parsedate_to_datetime(raw)
            except (TypeError, ValueError):
                pass

        return datetime.now(timezone.utc)
