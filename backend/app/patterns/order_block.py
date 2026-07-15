"""
Order Block Detection.
"""

from __future__ import annotations

import pandas as pd

from app.patterns.base_pattern import BasePattern
from app.patterns.break_of_structure import break_of_structure


class OrderBlock(BasePattern):
    """
    Detect Bullish and Bearish Order Blocks.

    Rule:
    - Bullish OB:
        Last bearish candle before Bullish BOS

    - Bearish OB:
        Last bullish candle before Bearish BOS
    """

    def detect(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        df = break_of_structure.detect(dataframe)

        df["order_block"] = False
        df["ob_direction"] = None
        df["ob_high"] = None
        df["ob_low"] = None

        for i in range(1, len(df)):

            if not df.iloc[i]["bos"]:
                continue

            previous = df.iloc[i - 1]

            direction = df.iloc[i]["bos_direction"]

            # Bullish Order Block

            if (
                direction == "bullish"
                and previous["close"] < previous["open"]
            ):

                df.at[df.index[i - 1], "order_block"] = True

                df.at[
                    df.index[i - 1],
                    "ob_direction",
                ] = "bullish"

                df.at[
                    df.index[i - 1],
                    "ob_high",
                ] = previous["high"]

                df.at[
                    df.index[i - 1],
                    "ob_low",
                ] = previous["low"]

            # Bearish Order Block

            elif (
                direction == "bearish"
                and previous["close"] > previous["open"]
            ):

                df.at[df.index[i - 1], "order_block"] = True

                df.at[
                    df.index[i - 1],
                    "ob_direction",
                ] = "bearish"

                df.at[
                    df.index[i - 1],
                    "ob_high",
                ] = previous["high"]

                df.at[
                    df.index[i - 1],
                    "ob_low",
                ] = previous["low"]

        return df


order_block = OrderBlock()