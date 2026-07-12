"""
Institutional Order Block Detector.

Current Version:
- Bullish Order Blocks
- Bearish Order Blocks
- BOS confirmation

Future Versions:
- Volume confirmation
- Mitigation tracking
- Strength score
- Multi-timeframe confirmation
"""

from __future__ import annotations

import pandas as pd

from app.patterns.base_pattern import BasePattern


class OrderBlock(BasePattern):
    """
    Detect bullish and bearish order blocks.
    """

    name = "Order Block"

    def detect(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        df["order_block"] = False
        df["order_block_type"] = ""
        df["order_block_high"] = None
        df["order_block_low"] = None

        if "bos_direction" not in df.columns:
            return df

        for i in range(1, len(df) - 1):

            previous = df.iloc[i - 1]
            current = df.iloc[i]
            nxt = df.iloc[i + 1]

            # -----------------------------
            # Bullish Order Block
            # -----------------------------
            if (
                previous["close"] < previous["open"]
                and nxt["bos_direction"] == "bullish"
            ):

                df.at[df.index[i], "order_block"] = True
                df.at[df.index[i], "order_block_type"] = "bullish"
                df.at[df.index[i], "order_block_high"] = previous["high"]
                df.at[df.index[i], "order_block_low"] = previous["low"]

            # -----------------------------
            # Bearish Order Block
            # -----------------------------
            elif (
                previous["close"] > previous["open"]
                and nxt["bos_direction"] == "bearish"
            ):

                df.at[df.index[i], "order_block"] = True
                df.at[df.index[i], "order_block_type"] = "bearish"
                df.at[df.index[i], "order_block_high"] = previous["high"]
                df.at[df.index[i], "order_block_low"] = previous["low"]

        return df