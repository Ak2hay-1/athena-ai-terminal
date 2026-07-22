"""
News impact labeling and currency/symbol mapping.
"""

from __future__ import annotations

from typing import Any

from app.core.constants import SUPPORTED_SYMBOLS

_CURRENCY_TO_SYMBOLS: dict[str, list[str]] = {
    "USD": [s for s in SUPPORTED_SYMBOLS if "USD" in s],
    "EUR": [s for s in SUPPORTED_SYMBOLS if "EUR" in s],
    "GBP": [s for s in SUPPORTED_SYMBOLS if "GBP" in s],
    "JPY": [s for s in SUPPORTED_SYMBOLS if "JPY" in s],
    "AUD": [s for s in SUPPORTED_SYMBOLS if "AUD" in s],
    "CAD": [s for s in SUPPORTED_SYMBOLS if "CAD" in s],
    "NZD": [s for s in SUPPORTED_SYMBOLS if "NZD" in s],
    "CHF": [s for s in SUPPORTED_SYMBOLS if "CHF" in s],
    "XAU": ["XAUUSD"],
    "GOLD": ["XAUUSD"],
    "XAG": ["XAGUSD"],
    "SILVER": ["XAGUSD"],
}


def normalize_impact(raw: str | None) -> str:
    value = (raw or "LOW").upper()
    if value in {"HIGH", "MEDIUM", "LOW"}:
        return {"HIGH": "High", "MEDIUM": "Medium", "LOW": "Low"}[value]
    return "Low"


def extract_currencies(text: str, symbols: list[str]) -> list[str]:
    found: set[str] = set()
    upper = text.upper()
    for currency in _CURRENCY_TO_SYMBOLS:
        if currency in upper:
            found.add(currency)
    for symbol in symbols:
        name = symbol.upper()
        for currency in ("EUR", "GBP", "USD", "JPY", "AUD", "CAD", "NZD", "CHF", "XAU", "XAG"):
            if currency in name:
                found.add(currency)
    return sorted(found)


def map_symbols(currencies: list[str], existing: list[str]) -> list[str]:
    mapped: set[str] = {s.upper() for s in existing if s}
    for currency in currencies:
        for symbol in _CURRENCY_TO_SYMBOLS.get(currency.upper(), []):
            mapped.add(symbol)
    return sorted(mapped)


def enrich_impact(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for item in items:
        title = str(item.get("title") or "")
        symbols = list(item.get("symbols") or [])
        currencies = extract_currencies(title, symbols)
        mapped = map_symbols(currencies, symbols)
        row = dict(item)
        row["impact"] = normalize_impact(str(item.get("impact")))
        row["currencies"] = currencies
        row["symbols"] = mapped
        row["asset_classes"] = _asset_classes(mapped)
        enriched.append(row)
    return enriched


def _asset_classes(symbols: list[str]) -> list[str]:
    classes: set[str] = set()
    for symbol in symbols:
        if symbol.startswith("XAU") or symbol.startswith("XAG"):
            classes.add("commodities")
        elif "JPY" in symbol or "USD" in symbol or "EUR" in symbol:
            classes.add("fx")
        else:
            classes.add("indices" if symbol.endswith("IDX") else "fx")
    return sorted(classes)
