"""Resolve AI providers from configuration with fallback support."""

from __future__ import annotations

from app.ai.providers.azure_provider import AzureProvider
from app.ai.providers.base import AIProvider
from app.ai.providers.claude_provider import ClaudeProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.local_provider import LocalProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.logger import logger
from app.core.settings import settings

_SUPPORTED = frozenset(
    {"azure", "gemini", "openai", "claude", "deepseek", "grok", "local"}
)
_NO_FALLBACK = frozenset({"", "none", "off", "disabled"})


def _fallback_name() -> str:
    return (settings.AI_FALLBACK_PROVIDER or "").strip().lower()


def resolve_provider(name: str) -> AIProvider:
    """Instantiate a provider by config name."""

    key = (name or "").strip().lower()
    if key not in _SUPPORTED:
        raise ValueError(
            f"Unsupported AI_PROVIDER '{name}'. "
            f"Supported: {', '.join(sorted(_SUPPORTED))}"
        )

    if key == "azure":
        return AzureProvider()
    if key == "gemini":
        return GeminiProvider()
    if key == "claude":
        return ClaudeProvider()
    if key == "local":
        return LocalProvider()
    # openai / deepseek / grok
    return OpenAIProvider(provider_name=key)


def get_primary_provider() -> AIProvider:
    """Return configured primary provider, falling back if unavailable."""

    primary_name = settings.AI_PROVIDER.strip().lower() or "gemini"
    fallback_name = _fallback_name()
    if fallback_name in _NO_FALLBACK:
        fallback_name = ""

    try:
        provider = resolve_provider(primary_name)
        healthy = provider.health()
        if healthy:
            return provider
        if not fallback_name:
            logger.warning(
                "Primary AI provider '%s' unhealthy; no fallback configured",
                primary_name,
            )
            return provider
        logger.warning(
            "Primary AI provider '%s' unhealthy; using fallback '%s'",
            primary_name,
            fallback_name,
        )
    except Exception as exc:
        if not fallback_name:
            raise
        logger.warning(
            "Primary AI provider '%s' unavailable (%s); using fallback '%s'",
            primary_name,
            exc,
            fallback_name,
        )

    return resolve_provider(fallback_name)


def get_fallback_provider(primary: AIProvider | None = None) -> AIProvider | None:
    """Return fallback provider if distinct from primary."""

    fallback_name = _fallback_name()
    if fallback_name in _NO_FALLBACK:
        return None
    if primary is not None and primary.name == fallback_name:
        return None
    try:
        return resolve_provider(fallback_name)
    except Exception as exc:
        logger.warning("Fallback AI provider unavailable: %s", exc)
        return None


def configured_model_name(provider_name: str | None = None) -> str:
    """Return the configured model string for a provider name."""

    key = (provider_name or settings.AI_PROVIDER).strip().lower()
    if key == "azure":
        return settings.AZURE_OPENAI_DEPLOYMENT or "gpt-5-mini"
    if key == "gemini":
        return settings.GEMINI_MODEL
    if key == "claude":
        return settings.CLAUDE_MODEL
    if key == "local":
        return settings.OLLAMA_MODEL
    return settings.OPENAI_MODEL or {
        "deepseek": "deepseek-chat",
        "grok": "grok-2",
    }.get(key, "gpt-4o-mini")
