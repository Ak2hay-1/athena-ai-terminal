/**
 * Collect + normalize signals from AnalysisSnapshot + indicator helpers.
 * Does NOT re-run structure/OB/FVG detectors — consumes intelligence output only.
 */

import type { AnalysisSnapshot } from "../../intelligence/types";
import type { Candlestick } from "../../types";
import {
  computeAtr,
  computeMacd,
  computeRsi,
  computeVwap,
} from "../../engine/indicators/calculations";
import type { DecisionSettings, NormalizedSignal, SignalSource } from "../types";
import { applyWeight } from "../scoring/weights";
import { clamp, lastFinite, stableId } from "../utils/math";
import { resolveProfile } from "../strategies/profiles";

function sig(
  source: SignalSource,
  bias: NormalizedSignal["bias"],
  strength: number,
  label: string,
  settings: DecisionSettings,
  ruleId: string,
  indices: number[] = [],
): NormalizedSignal {
  const profile = resolveProfile(settings);
  const s = clamp(strength, 0, 100);
  const weightedScore = applyWeight(s, source, profile.weights);
  return {
    id: stableId("sig", source, bias, label, ruleId, indices.join(",")),
    source,
    bias,
    strength: s,
    weight: profile.weights[source],
    weightedScore,
    label,
    supporting: bias !== "neutral",
    ruleId,
    candleIndices: indices,
  };
}

export function collectNormalizedSignals(
  analysis: AnalysisSnapshot,
  candles: Candlestick[],
  settings: DecisionSettings,
): NormalizedSignal[] {
  const out: NormalizedSignal[] = [];
  const last = candles.length - 1;
  const close = candles[last]?.close ?? 0;
  const closes = candles.map((c) => c.close);

  // Trend
  const t = analysis.trend;
  out.push(
    sig(
      "trend",
      t.direction,
      t.confidence,
      `Trend ${t.classification.replace(/_/g, " ")}`,
      settings,
      "decision.signal.trend.v1",
    ),
  );

  // Structure BOS / CHOCH
  for (const e of analysis.structure.slice(-6)) {
    if (e.label === "BOS") {
      out.push(
        sig(
          "bos",
          e.direction,
          e.score,
          `BOS ${e.direction}`,
          settings,
          e.trace.ruleId,
          e.trace.candleIndices,
        ),
      );
    }
    if (e.label === "CHOCH") {
      out.push(
        sig(
          "choch",
          e.direction,
          e.score,
          `CHOCH ${e.direction}`,
          settings,
          e.trace.ruleId,
          e.trace.candleIndices,
        ),
      );
    }
    if (e.label === "HH" || e.label === "HL" || e.label === "LH" || e.label === "LL") {
      out.push(
        sig(
          "swing_structure",
          e.direction,
          e.score * 0.7,
          e.label,
          settings,
          e.trace.ruleId,
          e.trace.candleIndices,
        ),
      );
    }
  }

  // Order blocks
  for (const ob of analysis.orderBlocks.filter((o) => o.status === "active").slice(-4)) {
    out.push(
      sig(
        "order_block",
        ob.bias,
        ob.score,
        `${ob.bias} order block`,
        settings,
        ob.trace.ruleId,
        ob.trace.candleIndices,
      ),
    );
  }

  // Supply / Demand
  for (const z of analysis.zones.filter((z) => z.status === "active").slice(-4)) {
    out.push(
      sig(
        "supply_demand",
        z.kind === "demand" ? "bullish" : "bearish",
        z.score,
        `${z.kind} zone`,
        settings,
        z.trace.ruleId,
        z.trace.candleIndices,
      ),
    );
  }

  // FVG
  for (const f of analysis.fvgs
    .filter((x) => x.status === "active" || x.status === "partial")
    .slice(-4)) {
    out.push(
      sig(
        "fvg",
        f.bias,
        f.score * (1 - f.fillRatio * 0.4),
        `${f.bias} FVG (${f.status})`,
        settings,
        f.trace.ruleId,
        f.trace.candleIndices,
      ),
    );
  }

  // Liquidity
  for (const l of analysis.liquidity.slice(0, 5)) {
    const bias =
      l.kind.includes("sweep") || l.kind.includes("hunt")
        ? ("neutral" as const)
        : l.kind.includes("high") || l.kind.includes("eq_high")
          ? ("bearish" as const)
          : l.kind.includes("low") || l.kind.includes("eq_low")
            ? ("bullish" as const)
            : ("neutral" as const);
    out.push(
      sig(
        "liquidity",
        bias,
        l.importance ?? l.score,
        l.kind.replace(/_/g, " "),
        settings,
        l.trace.ruleId,
        l.trace.candleIndices,
      ),
    );
  }

  // Volume intel
  {
    const v = analysis.volume;
    const bias =
      v.pressure === "buying" ? "bullish" : v.pressure === "selling" ? "bearish" : "neutral";
    let strength = v.score;
    if (v.exhaustion) strength *= 0.7;
    if (v.climax) strength = Math.min(100, strength * 1.1);
    out.push(
      sig("volume", bias, strength, `Volume ${v.pressure}`, settings, "decision.signal.volume.v1"),
    );
  }

  // S/R
  for (const lvl of analysis.levels.slice(0, 6)) {
    if (lvl.broken) continue;
    const near = Math.abs(close - lvl.price) / (close || 1) < 0.008;
    out.push(
      sig(
        "support_resistance",
        lvl.kind === "support" ? "bullish" : "bearish",
        near ? lvl.score : lvl.score * 0.6,
        `${lvl.kind} @ ${lvl.price.toFixed(4)}`,
        settings,
        lvl.trace.ruleId,
        lvl.trace.candleIndices,
      ),
    );
  }

  // Patterns
  for (const p of analysis.patterns.slice(-4)) {
    out.push(
      sig(
        "pattern",
        p.direction,
        p.confidence,
        p.kind.replace(/_/g, " "),
        settings,
        p.trace.ruleId,
        p.trace.candleIndices,
      ),
    );
  }

  // Sessions
  const kill = analysis.sessions.find((s) => s.killZone && s.active);
  if (kill) {
    out.push(
      sig(
        "session",
        "neutral",
        70,
        `${kill.name} kill zone`,
        settings,
        "decision.signal.session.v1",
      ),
    );
  } else {
    const active = analysis.sessions.find((s) => s.active);
    if (active) {
      out.push(
        sig("session", "neutral", 40, `${active.name} session`, settings, "decision.signal.session.v1"),
      );
    }
  }

  // Indicators — reuse calculation helpers (not detector duplication)
  const rsi = lastFinite(computeRsi(closes));
  if (rsi != null) {
    const bias = rsi > 55 ? "bullish" : rsi < 45 ? "bearish" : "neutral";
    const strength =
      rsi > 70 || rsi < 30 ? 75 : rsi > 60 || rsi < 40 ? 55 : 35;
    out.push(
      sig("rsi", bias, strength, `RSI ${rsi.toFixed(1)}`, settings, "decision.signal.rsi.v1", [
        last,
      ]),
    );
  }

  const macd = computeMacd(closes);
  const hist = lastFinite(macd.hist);
  const macdLine = lastFinite(macd.macd);
  if (hist != null && macdLine != null) {
    const bias = hist > 0 ? "bullish" : hist < 0 ? "bearish" : "neutral";
    out.push(
      sig(
        "macd",
        bias,
        clamp(Math.abs(hist) / (Math.abs(macdLine) + 1e-9) * 40 + 40, 20, 90),
        `MACD hist ${hist.toFixed(5)}`,
        settings,
        "decision.signal.macd.v1",
        [last],
      ),
    );
  }

  const vwap = lastFinite(computeVwap(candles));
  if (vwap != null && close > 0) {
    const bias = close > vwap ? "bullish" : close < vwap ? "bearish" : "neutral";
    const dist = (Math.abs(close - vwap) / close) * 10000;
    out.push(
      sig(
        "vwap",
        bias,
        clamp(40 + dist, 30, 85),
        close > vwap ? "Above VWAP" : "Below VWAP",
        settings,
        "decision.signal.vwap.v1",
        [last],
      ),
    );
  }

  const atr = lastFinite(computeAtr(candles));
  if (atr != null && close > 0) {
    const atrPct = (atr / close) * 100;
    // ATR is volatility context — high ATR = neutral caution signal
    out.push(
      sig(
        "atr",
        "neutral",
        clamp(atrPct * 25, 20, 80),
        `ATR ${atr.toFixed(5)} (${atrPct.toFixed(2)}%)`,
        settings,
        "decision.signal.atr.v1",
        [last],
      ),
    );
  }

  return out;
}

export function partitionSignals(
  signals: NormalizedSignal[],
  dominant: "bullish" | "bearish" | "neutral",
): { supporting: NormalizedSignal[]; opposing: NormalizedSignal[] } {
  if (dominant === "neutral") {
    return { supporting: signals.filter((s) => s.bias === "neutral"), opposing: [] };
  }
  const supporting = signals.filter((s) => s.bias === dominant);
  const opposing = signals.filter(
    (s) => s.bias !== "neutral" && s.bias !== dominant,
  );
  return {
    supporting: supporting.sort((a, b) => b.weightedScore - a.weightedScore),
    opposing: opposing.sort((a, b) => b.weightedScore - a.weightedScore),
  };
}
