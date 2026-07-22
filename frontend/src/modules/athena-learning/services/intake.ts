import type { TradeOpportunity } from "../../athena-chart/decision-engine/types";
import type {
  OutcomeLabel,
  OutcomeResult,
  RiskMode,
  StrategyKind,
  TradeLearningRecord,
} from "../types";
import { uid } from "../utils/math";

/** Map Decision Engine opportunity closure → learning trade record. */
export function opportunityToTradeRecord(
  userId: string,
  opp: TradeOpportunity,
  opts?: {
    strategy?: StrategyKind;
    riskMode?: RiskMode;
    session?: string;
    pnl?: number;
  },
): TradeLearningRecord | null {
  if (opp.direction === "flat") return null;
  const status = opp.status;
  if (
    status !== "closed" &&
    status !== "stopped" &&
    status !== "tp1" &&
    status !== "tp2" &&
    status !== "tp3" &&
    status !== "cancelled"
  ) {
    return null;
  }

  let outcome: OutcomeLabel = "unknown";
  let result: OutcomeResult = "manual_exit";
  if (status === "cancelled") {
    outcome = "cancelled";
    result = "cancelled";
  } else if (status === "stopped") {
    outcome = "loss";
    result = "sl";
  } else if (status === "tp3") {
    outcome = "win";
    result = "tp3";
  } else if (status === "tp2") {
    outcome = "win";
    result = "tp2";
  } else if (status === "tp1") {
    outcome = "win";
    result = "tp1";
  } else if (status === "closed") {
    if (opp.exit.action === "close_trade" && /stop/i.test(opp.exit.reason)) {
      outcome = "loss";
      result = "sl";
    } else if (/TP3/i.test(opp.exit.reason)) {
      outcome = "win";
      result = "tp3";
    } else if (/TP2/i.test(opp.exit.reason)) {
      outcome = "win";
      result = "tp2";
    } else if (/TP1|Partial/i.test(opp.exit.reason)) {
      outcome = "win";
      result = "tp1";
    } else {
      outcome = "breakeven";
      result = "manual_exit";
    }
  }

  const e = opp.activeEntry;
  const holdMinutes = Math.max(
    1,
    Math.round((opp.updatedAt - opp.createdAt) / 60000),
  );
  const risk = Math.abs(e.entry - e.stopLoss) || 1;
  let realizedRr = 0;
  if (outcome === "win") {
    const tp =
      result === "tp3"
        ? e.takeProfit3
        : result === "tp2"
          ? e.takeProfit2
          : e.takeProfit1;
    realizedRr = Math.abs(tp - e.entry) / risk;
  } else if (outcome === "loss") {
    realizedRr = -1;
  }

  const pnl =
    opts?.pnl ??
    (outcome === "win" ? realizedRr : outcome === "loss" ? -1 : 0);

  const predictionCorrect =
    outcome === "win" ? true : outcome === "loss" ? false : undefined;

  return {
    id: opp.id,
    userId,
    symbol: opp.symbol,
    timeframe: opp.timeframe,
    strategy: opts?.strategy ?? "intraday",
    riskMode: opts?.riskMode ?? "balanced",
    session: opts?.session,
    direction: opp.direction,
    bias: opp.bias,
    grade: opp.grade,
    confidenceAtEntry: opp.confidence.score,
    probabilityBullish: opp.probability.bullish,
    probabilityBearish: opp.probability.bearish,
    entry: e.entry,
    stopLoss: e.stopLoss,
    takeProfit1: e.takeProfit1,
    takeProfit2: e.takeProfit2,
    takeProfit3: e.takeProfit3,
    plannedRr: e.riskReward,
    openedAt: opp.createdAt,
    closedAt: opp.updatedAt,
    outcome,
    result,
    pnl,
    realizedRr,
    holdMinutes,
    supportingSignals: opp.supportingSignals.map((s) => s.label),
    opposingSignals: opp.opposingSignals.map((s) => s.label),
    predictionCorrect,
    manualOverrides: 0,
    stopMoves: opp.exit.action === "move_stop_loss" ? 1 : 0,
    sourceOpportunityId: opp.id,
  };
}

export function seedDemoTrades(userId: string, n = 40): TradeLearningRecord[] {
  const symbols = ["EURUSD", "GBPUSD", "XAUUSD", "USDJPY"];
  const sessions = ["London", "New York", "Tokyo", "New York Afternoon"];
  const strategies: StrategyKind[] = ["scalping", "intraday", "swing"];
  const out: TradeLearningRecord[] = [];
  const now = Date.now();
  for (let i = 0; i < n; i++) {
    const win = Math.random() > 0.38;
    const symbol = symbols[i % symbols.length];
    const session = sessions[i % sessions.length];
    const strategy = strategies[i % strategies.length];
    const conf = 55 + Math.random() * 40;
    const rr = win ? 1.2 + Math.random() * 1.8 : -1;
    out.push({
      id: uid("demo"),
      userId,
      symbol,
      timeframe: i % 2 === 0 ? "15M" : "1H",
      strategy,
      riskMode: "balanced",
      session,
      direction: i % 2 === 0 ? "long" : "short",
      bias: i % 2 === 0 ? "buy" : "sell",
      grade: win ? "A" : "B",
      confidenceAtEntry: conf,
      probabilityBullish: i % 2 === 0 ? 70 : 30,
      probabilityBearish: i % 2 === 0 ? 20 : 65,
      entry: 1.08 + Math.random() * 0.02,
      stopLoss: 1.078,
      takeProfit1: 1.085,
      plannedRr: 1.8,
      openedAt: now - (n - i) * 3600_000 * 6,
      closedAt: now - (n - i) * 3600_000 * 5,
      outcome: win ? "win" : "loss",
      result: win ? "tp1" : "sl",
      pnl: rr,
      realizedRr: rr,
      holdMinutes: 20 + Math.floor(Math.random() * 90),
      supportingSignals: ["Bullish BOS", "Demand zone", "Order block"],
      opposingSignals: win ? [] : ["Bearish FVG"],
      predictionCorrect: win,
      manualOverrides: Math.random() > 0.85 ? 1 : 0,
      stopMoves: Math.random() > 0.8 ? 1 + Math.floor(Math.random() * 2) : 0,
    });
  }
  return out;
}
