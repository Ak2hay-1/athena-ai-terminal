"""
Trading Calculator.

Provides trading and risk calculation utilities.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


class TradingCalculator:
    """
    Trading calculation utilities.
    """

    # ======================================================
    # Pip Value
    # ======================================================

    @staticmethod
    def pip_value(
        price_difference: Decimal,
        point: Decimal,
    ) -> Decimal:
        """
        Convert price difference to pips.
        """

        if point <= 0:
            raise ValueError("Point must be greater than zero.")

        return (
            price_difference / point
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # ======================================================
    # Risk Amount
    # ======================================================

    @staticmethod
    def risk_amount(
        balance: Decimal,
        risk_percent: Decimal,
    ) -> Decimal:
        """
        Calculate monetary risk.
        """

        return (
            balance * risk_percent / Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # ======================================================
    # Position Size
    # ======================================================

    @staticmethod
    def position_size(
        risk_amount: Decimal,
        stop_loss_pips: Decimal,
        pip_value: Decimal,
        minimum_lot: Decimal,
        maximum_lot: Decimal,
        lot_step: Decimal,
    ) -> Decimal:
        """
        Calculate lot size.
        """

        if stop_loss_pips <= 0:
            raise ValueError(
                "Stop loss must be greater than zero."
            )

        if pip_value <= 0:
            raise ValueError(
                "Pip value must be greater than zero."
            )

        lots = risk_amount / (
            stop_loss_pips * pip_value
        )

        if lots < minimum_lot:
            lots = minimum_lot

        if lots > maximum_lot:
            lots = maximum_lot

        if lot_step > 0:
            lots = (
                (lots / lot_step)
                .quantize(
                    Decimal("1"),
                    rounding=ROUND_HALF_UP,
                )
                * lot_step
            )

        return lots.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # ======================================================
    # Risk Reward
    # ======================================================

    @staticmethod
    def risk_reward_ratio(
        entry: Decimal,
        stop_loss: Decimal,
        take_profit: Decimal,
    ) -> Decimal:
        """
        Calculate risk reward ratio.
        """

        risk = abs(entry - stop_loss)

        reward = abs(take_profit - entry)

        if risk == 0:
            raise ValueError(
                "Risk cannot be zero."
            )

        return (
            reward / risk
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # ======================================================
    # Profit
    # ======================================================

    @staticmethod
    def unrealized_profit(
        entry_price: Decimal,
        current_price: Decimal,
        volume: Decimal,
        contract_size: Decimal,
        is_buy: bool,
    ) -> Decimal:
        """
        Calculate floating profit/loss.
        """

        difference = (
            current_price - entry_price
            if is_buy
            else entry_price - current_price
        )

        return (
            difference
            * contract_size
            * volume
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # ======================================================
    # Margin
    # ======================================================

    @staticmethod
    def required_margin(
        volume: Decimal,
        contract_size: Decimal,
        price: Decimal,
        leverage: int,
    ) -> Decimal:
        """
        Estimate required margin.
        """

        if leverage <= 0:
            raise ValueError(
                "Leverage must be greater than zero."
            )

        return (
            volume
            * contract_size
            * price
            / Decimal(leverage)
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # ======================================================
    # Drawdown
    # ======================================================

    @staticmethod
    def drawdown_percent(
        peak_equity: Decimal,
        current_equity: Decimal,
    ) -> Decimal:
        """
        Calculate drawdown percentage.
        """

        if peak_equity <= 0:
            return Decimal("0.00")

        return (
            (
                peak_equity - current_equity
            )
            / peak_equity
            * Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # ======================================================
    # Win Rate
    # ======================================================

    @staticmethod
    def win_rate(
        wins: int,
        total: int,
    ) -> Decimal:
        """
        Calculate win rate.
        """

        if total == 0:
            return Decimal("0.00")

        return (
            Decimal(wins)
            / Decimal(total)
            * Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # ======================================================
    # Expectancy
    # ======================================================

    @staticmethod
    def expectancy(
        win_rate: Decimal,
        average_win: Decimal,
        average_loss: Decimal,
    ) -> Decimal:
        """
        Calculate trading expectancy.
        """

        lose_rate = Decimal("100") - win_rate

        return (
            (
                win_rate / Decimal("100")
            )
            * average_win
            -
            (
                lose_rate / Decimal("100")
            )
            * average_loss
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )