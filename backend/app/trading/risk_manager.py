"""
Athena Risk Manager.

Handles portfolio and account-level risk rules.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.settings import settings


@dataclass(slots=True)
class RiskValidation:

    allowed: bool

    reasons: list[str]


class RiskManager:
    """
    Portfolio risk validation.
    """

    def validate(
        self,
        open_positions: int,
        risk_percent: float,
    ) -> RiskValidation:

        reasons: list[str] = []

        allowed = True

        # ----------------------------------------

        if (
            open_positions >=
            settings.MAX_OPEN_TRADES
        ):

            allowed = False

            reasons.append(
                "Maximum open trades reached."
            )

        # ----------------------------------------

        if (
            risk_percent >
            settings.MAX_RISK_PERCENT
        ):

            allowed = False

            reasons.append(
                "Risk exceeds configured limit."
            )

        # ----------------------------------------

        if allowed:

            reasons.append(
                "Risk validation passed."
            )

        return RiskValidation(

            allowed=allowed,

            reasons=reasons,

        )


risk_manager = RiskManager()