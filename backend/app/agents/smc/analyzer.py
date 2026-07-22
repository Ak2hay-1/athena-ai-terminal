"""
SMC analyzer — orchestrates structure/liquidity/OB/FVG into evidence payload.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.agents.smc.fair_value_gap import analyze_fvg
from app.agents.smc.liquidity import analyze_liquidity
from app.agents.smc.market_structure import analyze_market_structure
from app.agents.smc.order_blocks import analyze_order_blocks
from app.agents.smc.scorer import score_smc
from app.patterns.premium_discount import premium_discount


def _strip_df(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k != "_dataframe"}


def analyze_smc(dataframe: pd.DataFrame) -> dict[str, Any]:
    """
    Produce JSON-safe SMC evidence and score.
    """
    if dataframe.empty or len(dataframe) < 30:
        return {
            "market_structure": {},
            "bos": {"present": False},
            "choch": {"present": False},
            "liquidity": {},
            "order_blocks": {},
            "fvg": {},
            "premium": False,
            "discount": False,
            "equilibrium": None,
            "score": 0.0,
        }

    structure = analyze_market_structure(dataframe)
    liquidity = analyze_liquidity(dataframe)
    order_blocks = analyze_order_blocks(dataframe)
    fvg = analyze_fvg(dataframe)

    pd_df = premium_discount.detect(dataframe)
    last = pd_df.iloc[-1]
    premium = bool(last.get("premium"))
    discount = bool(last.get("discount"))
    equilibrium = (
        float(last["equilibrium"])
        if not pd.isna(last.get("equilibrium"))
        else None
    )
    premium_percent = (
        float(last["premium_percent"])
        if not pd.isna(last.get("premium_percent"))
        else None
    )

    structure_clean = _strip_df(structure)
    liquidity_clean = _strip_df(liquidity)
    ob_clean = _strip_df(order_blocks)
    fvg_clean = _strip_df(fvg)

    score = score_smc(
        structure=structure_clean,
        liquidity=liquidity_clean,
        order_blocks=ob_clean,
        fvg=fvg_clean,
        premium=premium,
        discount=discount,
        premium_percent=premium_percent,
    )

    return {
        "market_structure": {
            "trend": structure_clean.get("trend"),
            "hh": structure_clean.get("hh"),
            "hl": structure_clean.get("hl"),
            "lh": structure_clean.get("lh"),
            "ll": structure_clean.get("ll"),
            "swing_points": structure_clean.get("swing_points"),
            "internal_bos": structure_clean.get("internal_bos"),
            "external_bos": structure_clean.get("external_bos"),
        },
        "bos": structure_clean.get("bos"),
        "choch": structure_clean.get("choch"),
        "liquidity": liquidity_clean,
        "order_blocks": ob_clean,
        "fvg": fvg_clean,
        "premium": premium,
        "discount": discount,
        "equilibrium": equilibrium,
        "premium_percent": premium_percent,
        "score": score,
    }
