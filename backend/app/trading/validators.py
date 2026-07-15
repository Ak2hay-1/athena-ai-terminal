"""
Trading Validators.

Centralized validation logic for all trading operations.
"""

from __future__ import annotations

from decimal import Decimal

from app.mt5.providers import manager
from app.trading.constants import (
    DEFAULT_MAX_OPEN_TRADES,
    DEFAULT_MAX_SYMBOL_TRADES,
)
from app.trading.exceptions import (
    InvalidPriceError,
    InvalidStopLossError,
    InvalidSymbolError,
    InvalidTakeProfitError,
    InvalidVolumeError,
    MarginError,
    MaximumSymbolTradesExceededError,
    MaximumTradesExceededError,
    SpreadTooHighError,
)


class TradingValidator:
    """
    Centralized trade validation.
    """

    # ======================================================
    # Symbol
    # ======================================================

    @staticmethod
    def validate_symbol(
        symbol: str,
    ) -> None:
        """
        Validate trading symbol.
        """

        info = manager.symbol_info(symbol)

        if info is None:
            raise InvalidSymbolError(
                f"Unknown symbol '{symbol}'."
            )

        if not info.visible:
            raise InvalidSymbolError(
                f"Symbol '{symbol}' is not visible."
            )

    # ======================================================
    # Volume
    # ======================================================

    @staticmethod
    def validate_volume(
        symbol: str,
        volume: Decimal,
    ) -> None:
        """
        Validate trading volume.
        """

        info = manager.symbol_info(symbol)

        if volume < Decimal(str(info.volume_min)):
            raise InvalidVolumeError(
                f"Minimum volume is {info.volume_min}"
            )

        if volume > Decimal(str(info.volume_max)):
            raise InvalidVolumeError(
                f"Maximum volume is {info.volume_max}"
            )

        step = Decimal(str(info.volume_step))

        if step > 0:
            remainder = volume % step

            if remainder != 0:
                raise InvalidVolumeError(
                    f"Volume must be a multiple of {step}"
                )

    # ======================================================
    # Price
    # ======================================================

    @staticmethod
    def validate_price(
        price: Decimal,
    ) -> None:
        """
        Validate order price.
        """

        if price <= 0:
            raise InvalidPriceError(
                "Price must be greater than zero."
            )

    # ======================================================
    # Stop Loss
    # ======================================================

    @staticmethod
    def validate_stop_loss(
        stop_loss: Decimal | None,
    ) -> None:

        if stop_loss is None:
            return

        if stop_loss <= 0:
            raise InvalidStopLossError(
                "Invalid stop-loss."
            )

    # ======================================================
    # Take Profit
    # ======================================================

    @staticmethod
    def validate_take_profit(
        take_profit: Decimal | None,
    ) -> None:

        if take_profit is None:
            return

        if take_profit <= 0:
            raise InvalidTakeProfitError(
                "Invalid take-profit."
            )

    # ======================================================
    # Spread
    # ======================================================

    @staticmethod
    def validate_spread(
        symbol: str,
        maximum_spread: int,
    ) -> None:
        """
        Validate market spread.
        """

        tick = manager.symbol_tick(symbol)

        info = manager.symbol_info(symbol)

        spread = int(
            (tick.ask - tick.bid) / info.point
        )

        if spread > maximum_spread:
            raise SpreadTooHighError(
                f"Spread ({spread}) exceeds maximum "
                f"allowed ({maximum_spread})."
            )

    # ======================================================
    # Margin
    # ======================================================

    @staticmethod
    def validate_margin(
        required_margin: Decimal,
    ) -> None:
        """
        Validate free margin.
        """

        account = manager.account_info()

        free_margin = Decimal(
            str(account.margin_free)
        )

        if free_margin < required_margin:
            raise MarginError(
                "Insufficient free margin."
            )

    # ======================================================
    # Open Trades
    # ======================================================

    @staticmethod
    def validate_open_positions(
        max_positions: int = DEFAULT_MAX_OPEN_TRADES,
    ) -> None:
        """
        Validate maximum number of positions.
        """

        positions = manager.positions()

        if len(positions) >= max_positions:
            raise MaximumTradesExceededError(
                "Maximum open positions reached."
            )

    # ======================================================
    # Symbol Positions
    # ======================================================

    @staticmethod
    def validate_symbol_positions(
        symbol: str,
        max_positions: int = DEFAULT_MAX_SYMBOL_TRADES,
    ) -> None:
        """
        Validate positions for a symbol.
        """

        positions = manager.positions(symbol)

        if len(positions) >= max_positions:
            raise MaximumSymbolTradesExceededError(
                f"Maximum positions reached for {symbol}."
            )

    # ======================================================
    # Complete Validation
    # ======================================================

    @classmethod
    def validate_trade(
        cls,
        *,
        symbol: str,
        volume: Decimal,
        price: Decimal,
        stop_loss: Decimal | None = None,
        take_profit: Decimal | None = None,
        maximum_spread: int = 30,
    ) -> None:
        """
        Run complete validation pipeline.
        """

        cls.validate_symbol(symbol)

        cls.validate_volume(
            symbol,
            volume,
        )

        cls.validate_price(price)

        cls.validate_stop_loss(
            stop_loss,
        )

        cls.validate_take_profit(
            take_profit,
        )

        cls.validate_spread(
            symbol,
            maximum_spread,
        )

        cls.validate_open_positions()

        cls.validate_symbol_positions(
            symbol,
        )
