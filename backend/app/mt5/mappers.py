"""
MetaTrader 5 Mappers.

Converts MetaTrader5 SDK objects into Athena schemas.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.schemas.mt5 import (
    MT5AccountInfo,
    MT5Quote,
    MT5SymbolInfo,
    MT5TerminalInfo,
    MT5VersionInfo,
)


class MT5Mapper:
    """
    Converts MT5 SDK objects into Athena schemas.
    """

    # ======================================================
    # Helpers
    # ======================================================

    @staticmethod
    def _decimal(value: Any) -> Decimal:
        """
        Safely convert numeric values to Decimal.
        """

        if value is None:
            return Decimal("0")

        return Decimal(str(value))

    @staticmethod
    def _datetime(timestamp: int | float | None) -> datetime | None:
        """
        Convert UNIX timestamp to UTC datetime.
        """

        if timestamp is None:
            return None

        return datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        )

    # ======================================================
    # Account
    # ======================================================

    @classmethod
    def account(
        cls,
        info: Any,
    ) -> MT5AccountInfo:
        """
        Map account_info().
        """

        return MT5AccountInfo(
            login=info.login,
            name=info.name,
            server=info.server,
            company=info.company,
            currency=info.currency,
            leverage=info.leverage,
            balance=cls._decimal(info.balance),
            equity=cls._decimal(info.equity),
            profit=cls._decimal(info.profit),
            credit=cls._decimal(info.credit),
            margin=cls._decimal(info.margin),
            margin_free=cls._decimal(info.margin_free),
            margin_level=cls._decimal(info.margin_level),
            assets=cls._decimal(info.assets),
            liabilities=cls._decimal(info.liabilities),
            commission_blocked=cls._decimal(
                info.commission_blocked,
            ),
            trade_allowed=info.trade_allowed,
            trade_expert=info.trade_expert,
            margin_mode=info.margin_mode,
            fifo_close=info.fifo_close,
            limit_orders=info.limit_orders,
            currency_digits=info.currency_digits,
            connected=True,
            timestamp=datetime.now(timezone.utc),
        )

    # ======================================================
    # Terminal
    # ======================================================

    @staticmethod
    def terminal(
        info: Any,
    ) -> MT5TerminalInfo:
        """
        Map terminal_info().
        """

        return MT5TerminalInfo(
            company=info.company,
            name=info.name,
            language=info.language,
            path=info.path,
            data_path=info.data_path,
            commondata_path=info.commondata_path,
            community_account=info.community_account,
            community_connection=info.community_connection,
            connected=info.connected,
            trade_allowed=info.trade_allowed,
            tradeapi_disabled=info.tradeapi_disabled,
            dlls_allowed=info.dlls_allowed,
            email_enabled=info.email_enabled,
            ftp_enabled=info.ftp_enabled,
            notifications_enabled=info.notifications_enabled,
            mqid=info.mqid,
            build=info.build,
            maxbars=info.maxbars,
            ping_last=info.ping_last,
            codepage=info.codepage,
        )

    # ======================================================
    # Version
    # ======================================================

    @staticmethod
    def version(
        version: tuple[int, int, str],
    ) -> MT5VersionInfo:
        """
        Map version().
        """

        return MT5VersionInfo(
            version=version[0],
            build=version[1],
            release_date=str(version[2]),
        )

    # ======================================================
    # Symbol
    # ======================================================

    @classmethod
    def symbol(
        cls,
        info: Any,
    ) -> MT5SymbolInfo:
        """
        Map symbol_info().
        """

        return MT5SymbolInfo(
            name=info.name,
            description=info.description,
            path=info.path,
            currency_base=info.currency_base,
            currency_profit=info.currency_profit,
            currency_margin=info.currency_margin,
            category=getattr(info, "category", None),
            exchange=getattr(info, "exchange", None),
            isin=getattr(info, "isin", None),
            page=getattr(info, "page", None),
            visible=info.visible,
            select=info.select,
            custom=info.custom,
            bid=cls._decimal(info.bid),
            ask=cls._decimal(info.ask),
            last=cls._decimal(info.last),
            point=cls._decimal(info.point),
            digits=info.digits,
            spread=info.spread,
            spread_float=info.spread_float,
            contract_size=cls._decimal(info.trade_contract_size),
            trade_tick_size=cls._decimal(info.trade_tick_size),
            trade_tick_value=cls._decimal(info.trade_tick_value),
            trade_tick_value_profit=cls._decimal(
                info.trade_tick_value_profit,
            ),
            trade_tick_value_loss=cls._decimal(
                info.trade_tick_value_loss,
            ),
            volume_min=cls._decimal(info.volume_min),
            volume_max=cls._decimal(info.volume_max),
            volume_step=cls._decimal(info.volume_step),
            volume_limit=cls._decimal(info.volume_limit),
            margin_initial=cls._decimal(info.margin_initial),
            margin_maintenance=cls._decimal(
                info.margin_maintenance,
            ),
            margin_hedged=cls._decimal(info.margin_hedged),
            margin_hedged_use_leg=info.margin_hedged_use_leg,
            swap_long=cls._decimal(info.swap_long),
            swap_short=cls._decimal(info.swap_short),
            swap_rollover3days=info.swap_rollover3days,
            trade_stops_level=info.trade_stops_level,
            trade_freeze_level=info.trade_freeze_level,
            trade_mode=info.trade_mode,
            trade_execution=info.trade_exemode,
            filling_mode=info.filling_mode,
            expiration_mode=info.expiration_mode,
            order_mode=info.order_mode,
            order_gtc_mode=info.order_gtc_mode,
            option_mode=info.option_mode,
            option_right=info.option_right,
            session_deals=info.session_deals,
            session_buy_orders=info.session_buy_orders,
            session_sell_orders=info.session_sell_orders,
            session_open=cls._decimal(info.session_open),
            session_close=cls._decimal(info.session_close),
            session_aw=cls._decimal(info.session_aw),
            session_price_settlement=cls._decimal(
                info.session_price_settlement,
            ),
            session_price_limit_min=cls._decimal(
                info.session_price_limit_min,
            ),
            session_price_limit_max=cls._decimal(
                info.session_price_limit_max,
            ),
            session_volume=cls._decimal(info.session_volume),
            session_turnover=cls._decimal(
                info.session_turnover,
            ),
            session_interest=cls._decimal(
                info.session_interest,
            ),
            chart_mode=info.chart_mode,
            background_color=info.background_color,
            basis=getattr(info, "basis", None),
        )

    # ======================================================
    # Tick
    # ======================================================

    @classmethod
    def quote(
        cls,
        tick: Any,
        symbol: str,
    ) -> MT5Quote:
        """
        Map symbol_info_tick().
        """

        spread = int(
            (tick.ask - tick.bid) / tick.point
        ) if hasattr(tick, "point") else 0

        return MT5Quote(
            symbol=symbol,
            bid=cls._decimal(tick.bid),
            ask=cls._decimal(tick.ask),
            last=cls._decimal(tick.last),
            spread=spread,
            timestamp=tick.time,
        )