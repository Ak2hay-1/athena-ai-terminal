"use client";

import { useCallback, useEffect, useMemo, useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getMarketHours } from "@/lib/market-hours";
import { currentSession, normalizeSignal, toNumber } from "@/lib/mappers";
import { getQuotes } from "@/services/market";
import { getScannerOpportunities } from "@/services/scanner";
import { useAuthStore } from "@/store/auth-store";
import { useDashboardStore } from "@/store/dashboard-store";
import type { ScannerMeta, ScannerOpportunity, Signal } from "@/types";
import { useMarketWebSocket } from "./use-market-websocket";

/** Skip REST quote if a WS tick for this symbol landed within this window. */
const TICK_FRESH_MS = 3_000;

function decimalPlaces(n: number): number {
  if (!Number.isFinite(n)) return 0;
  const s = String(n);
  const i = s.indexOf(".");
  return i < 0 ? 0 : s.length - i - 1;
}

/** True when quote looks like a truncated/rounded form of the live tick mid. */
function isCoarserQuote(quote: number, live: number): boolean {
  if (quote === live) return false;
  const qDec = decimalPlaces(quote);
  const lDec = decimalPlaces(live);
  if (lDec <= qDec) return false;
  const factor = 10 ** qDec;
  return Math.round(live * factor) / factor === quote;
}

function mergeOpportunity(
  current: ScannerOpportunity,
  patch: Partial<ScannerOpportunity> & Record<string, unknown>,
): ScannerOpportunity {
  const reasons = Array.isArray(patch.reasons)
    ? (patch.reasons as string[])
    : current.reasons;
  const reason =
    patch.reason != null
      ? String(patch.reason)
      : reasons.slice(0, 2).join(" · ") || current.reason;

  return {
    ...current,
    ...patch,
    signal: patch.signal
      ? normalizeSignal(patch.signal)
      : current.signal,
    score:
      patch.score != null ? Math.round(toNumber(patch.score, current.score)) : current.score,
    confidence:
      patch.confidence != null
        ? Math.round(toNumber(patch.confidence, current.confidence))
        : current.confidence,
    price:
      patch.price != null ? toNumber(patch.price, current.price ?? 0) : current.price,
    changePercent:
      patch.changePercent != null
        ? toNumber(patch.changePercent, current.changePercent ?? 0)
        : patch.change_percent != null
          ? toNumber(patch.change_percent, current.changePercent ?? 0)
          : current.changePercent,
    entry:
      patch.entry != null ? toNumber(patch.entry, current.entry ?? 0) : current.entry,
    stopLoss:
      patch.stopLoss != null
        ? toNumber(patch.stopLoss, current.stopLoss ?? 0)
        : patch.stop_loss != null
          ? toNumber(patch.stop_loss, current.stopLoss ?? 0)
          : current.stopLoss,
    takeProfit:
      patch.takeProfit != null
        ? toNumber(patch.takeProfit, current.takeProfit ?? 0)
        : patch.take_profit != null
          ? toNumber(patch.take_profit, current.takeProfit ?? 0)
          : current.takeProfit,
    riskReward:
      patch.riskReward != null
        ? toNumber(patch.riskReward, current.riskReward ?? 0)
        : patch.risk_reward != null
          ? toNumber(patch.risk_reward, current.riskReward ?? 0)
          : current.riskReward,
    marketWatchTag:
      patch.marketWatchTag != null
        ? String(patch.marketWatchTag)
        : patch.market_watch_tag != null
          ? String(patch.market_watch_tag)
          : current.marketWatchTag,
    reasons,
    reason,
    stale: patch.stale != null ? Boolean(patch.stale) : current.stale,
  };
}

export function useScannerData() {
  const user = useAuthStore((s) => s.user);
  const timeframe = useDashboardStore((s) => s.timeframe);
  const setTimeframe = useDashboardStore((s) => s.setTimeframe);
  const queryClient = useQueryClient();
  const enabled = Boolean(user);

  const scannerQuery = useQuery({
    queryKey: ["scanner", "opportunities", timeframe],
    queryFn: () =>
      getScannerOpportunities({
        timeframe,
      }),
    enabled,
    refetchInterval: 30_000,
  });

  const opportunities = scannerQuery.data?.opportunities ?? [];
  const meta: ScannerMeta | null = scannerQuery.data?.meta ?? null;
  const lastTickAtRef = useRef<Record<string, number>>({});

  // #region agent log
  if (typeof window !== "undefined" && scannerQuery.dataUpdatedAt) {
    const _sigCounts: Record<string, number> = {};
    const _grpCounts: Record<string, number> = {};
    const _priceFp = opportunities.map((o) => `${o.symbol}:${o.price}`).join("|");
    for (const o of opportunities) {
      _sigCounts[o.signal] = (_sigCounts[o.signal] ?? 0) + 1;
      const g = o.scannerGroup ?? "unset";
      _grpCounts[g] = (_grpCounts[g] ?? 0) + 1;
    }
    const _xau = opportunities.find((o) => o.symbol === "XAUUSD");
    const _key = `${timeframe}:${_priceFp}`;
    if ((globalThis as unknown as {_dbgScanBoardKey?: string})._dbgScanBoardKey !== _key) {
      (globalThis as unknown as {_dbgScanBoardKey?: string})._dbgScanBoardKey = _key;
      fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'e72fc0'},body:JSON.stringify({sessionId:'e72fc0',runId:'post-fix',hypothesisId:'F',location:'use-scanner-data.ts:board',message:'Scanner board price fingerprint',data:{timeframe,count:opportunities.length,sigCounts:_sigCounts,grpCounts:_grpCounts,xauPrice:_xau?.price??null,sample:opportunities.slice(0,5).map((o)=>({s:o.symbol,sig:o.signal,g:o.scannerGroup,price:o.price}))},timestamp:Date.now()})}).catch(()=>{});
    }
  }
  // #endregion

  const symbols = useMemo(
    () =>
      meta?.symbolsScanned?.length
        ? meta.symbolsScanned
        : opportunities.map((o) => o.symbol),
    [meta?.symbolsScanned, opportunities],
  );

  const patchOpportunity = useCallback(
    (symbol: string, patch: Partial<ScannerOpportunity> & Record<string, unknown>) => {
      queryClient.setQueryData<{
        opportunities: ScannerOpportunity[];
        meta: ScannerMeta;
      }>(["scanner", "opportunities", timeframe], (current) => {
        if (!current) return current;
        const upper = symbol.toUpperCase();
        let found = false;
        const next = current.opportunities.map((item) => {
          if (item.symbol !== upper) return item;
          found = true;
          return mergeOpportunity(item, patch);
        });
        if (!found && patch.signal) {
          next.push(
            mergeOpportunity(
              {
                id: `${upper}-${timeframe}`,
                symbol: upper,
                signal: normalizeSignal(patch.signal) as Signal,
                score: toNumber(patch.score, 0),
                confidence: toNumber(patch.confidence, 0),
                timeframe,
                session: currentSession(),
                reasons: [],
                reason: "",
              },
              patch,
            ),
          );
        }
        next.sort((a, b) => b.score - a.score || b.confidence - a.confidence);
        return {
          ...current,
          opportunities: next,
          meta: {
            ...current.meta,
            opportunityCount: next.length,
          },
        };
      });
    },
    [queryClient, timeframe],
  );

  const onWsMessage = useCallback(
    (payload: Record<string, unknown>) => {
      const updateSymbol = String(payload.symbol ?? "").toUpperCase();
      if (!updateSymbol) return;

      if (payload.type === "tick") {
        const mid = toNumber(payload.mid);
        if (!mid) return;
        lastTickAtRef.current[updateSymbol] = Date.now();
        // #region agent log
        if (!(globalThis as unknown as {_dbgScanTick?: number})._dbgScanTick) (globalThis as unknown as {_dbgScanTick?: number})._dbgScanTick = 0;
        (globalThis as unknown as {_dbgScanTick: number})._dbgScanTick += 1;
        const _n = (globalThis as unknown as {_dbgScanTick: number})._dbgScanTick;
        const _hist = (globalThis as unknown as {_dbgTickHist?: Record<string, number>})._dbgTickHist ?? {};
        _hist[updateSymbol] = (_hist[updateSymbol] ?? 0) + 1;
        (globalThis as unknown as {_dbgTickHist: Record<string, number>})._dbgTickHist = _hist;
        if (_n <= 8 || _n % 40 === 0) {
          const _syms = (queryClient.getQueryData<{opportunities: ScannerOpportunity[]}>(["scanner", "opportunities", timeframe])?.opportunities ?? []).map((o) => o.symbol);
          fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'e72fc0'},body:JSON.stringify({sessionId:'e72fc0',runId:'post-fix',hypothesisId:'B',location:'use-scanner-data.ts:tick',message:'Scanner tick patch attempt',data:{n:_n,updateSymbol,mid,boardHasSymbol:_syms.includes(updateSymbol),boardSize:_syms.length,timeframe,tickHist:_hist},timestamp:Date.now()})}).catch(()=>{});
        }
        // #endregion
        queryClient.setQueryData<{
          opportunities: ScannerOpportunity[];
          meta: ScannerMeta;
        }>(["scanner", "opportunities", timeframe], (current) => {
          if (!current) return current;
          return {
            ...current,
            opportunities: current.opportunities.map((item) => {
              if (item.symbol !== updateSymbol) return item;
              // Change % vs prior displayed price / session reference — not entry levels.
              const reference =
                item.price && item.price > 0
                  ? item.changePercent != null
                    ? item.price / (1 + item.changePercent / 100)
                    : item.price
                  : mid;
              const changePercent =
                reference > 0 ? ((mid - reference) / reference) * 100 : item.changePercent;
              return { ...item, price: mid, changePercent };
            }),
          };
        });
        return;
      }

      if (payload.type === "scanner_update" || payload.type === "candle_update") {
        const tf = String(payload.timeframe ?? timeframe).toUpperCase();
        if (tf && tf !== timeframe.toUpperCase() && payload.type === "scanner_update") {
          // Still apply MW tag / price for same symbol on other TFs lightly
        }
        const opportunity = payload.opportunity as Record<string, unknown> | undefined;
        const rec = payload.recommendation as Record<string, unknown> | undefined;
        const patch: Partial<ScannerOpportunity> & Record<string, unknown> = {};

        if (opportunity) {
          if (opportunity.market_watch_tag) {
            patch.marketWatchTag = String(opportunity.market_watch_tag);
          }
          if (opportunity.marketWatchTag) {
            patch.marketWatchTag = String(opportunity.marketWatchTag);
          }
          if (opportunity.signal) patch.signal = normalizeSignal(opportunity.signal);
          if (opportunity.confidence != null) patch.confidence = toNumber(opportunity.confidence);
          if (opportunity.score != null) patch.score = toNumber(opportunity.score);
          if (opportunity.entry != null) patch.entry = toNumber(opportunity.entry);
          if (opportunity.stop_loss != null) patch.stopLoss = toNumber(opportunity.stop_loss);
          if (opportunity.take_profit != null) patch.takeProfit = toNumber(opportunity.take_profit);
          if (opportunity.risk_reward != null) patch.riskReward = toNumber(opportunity.risk_reward);
          if (Array.isArray(opportunity.reasons)) {
            patch.reasons = opportunity.reasons.map(String);
          }
          if (opportunity.stale != null) patch.stale = Boolean(opportunity.stale);
        }
        if (rec) {
          // Levels/confidence only — do not overwrite demoted desk signal with raw BUY/SELL.
          if (rec.confidence != null) patch.confidence = toNumber(rec.confidence);
          if (rec.entry != null) patch.entry = toNumber(rec.entry);
          if (rec.stop_loss != null) patch.stopLoss = toNumber(rec.stop_loss);
          if (rec.take_profit != null) patch.takeProfit = toNumber(rec.take_profit);
          if (rec.risk_reward != null) patch.riskReward = toNumber(rec.risk_reward);
          if (rec.trend != null) patch.trend = String(rec.trend);
          if (rec.scanner_group != null) patch.scannerGroup = String(rec.scanner_group);
          if (rec.setup_quality != null) patch.setupQuality = toNumber(rec.setup_quality);
          // Only apply signal when opportunity payload already carries desk group,
          // or when signal is non-actionable.
          const rawSig = normalizeSignal(rec.signal);
          if (
            rawSig === "HOLD" ||
            rawSig === "NO_TRADE" ||
            rawSig === "NEUTRAL" ||
            rec.scanner_group
          ) {
            patch.signal = rawSig;
          }
        }
        if (payload.change_type) {
          patch.marketWatchTag = String(payload.change_type);
        }
        if (payload.price != null) {
          patch.price = toNumber(payload.price);
        }
        const candle = payload.candle as Record<string, unknown> | undefined;
        if (candle?.close != null) {
          patch.price = toNumber(candle.close);
        }

        if (Object.keys(patch).length > 0) {
          patchOpportunity(updateSymbol, patch);
        }

        // Full resync on recommendation so score stays accurate
        if (payload.change_type === "recommendation" || rec) {
          void queryClient.invalidateQueries({
            queryKey: ["scanner", "opportunities", timeframe],
          });
        }
      }
    },
    [patchOpportunity, queryClient, timeframe],
  );

  const { connected: wsConnected } = useMarketWebSocket({
    symbols: symbols.length > 0 ? symbols : ["XAUUSD"],
    timeframe,
    onMessage: onWsMessage,
    enabled,
  });

  // REST quote poll so every symbol keeps moving even when tick stream is sparse.
  const quotesQuery = useQuery({
    queryKey: ["market", "quotes", "scanner", timeframe, symbols.join(",")],
    queryFn: () => getQuotes(symbols.length ? symbols : ["XAUUSD"], timeframe),
    enabled: enabled && symbols.length > 0,
    refetchInterval: wsConnected ? 2_000 : 1_000,
    staleTime: 500,
  });

  useEffect(() => {
    // REST quotes fill gaps for symbols the tick stream rarely updates.
    // Never overwrite a fresh WS tick, and never apply a coarser truncated mid.
    const quotes = quotesQuery.data;
    if (!quotes?.length) return;
    const now = Date.now();
    const quoteMap = new Map(
      quotes.map((q) => [q.symbol.toUpperCase(), q.mid] as const),
    );
    queryClient.setQueryData<{
      opportunities: ScannerOpportunity[];
      meta: ScannerMeta;
    }>(["scanner", "opportunities", timeframe], (current) => {
      if (!current) return current;
      let changed = false;
      let applied = 0;
      let skippedFresh = 0;
      let skippedCoarse = 0;
      const next = current.opportunities.map((item) => {
        const mid = quoteMap.get(item.symbol);
        if (mid == null || mid <= 0 || mid === item.price) return item;
        const lastTick = lastTickAtRef.current[item.symbol];
        if (wsConnected && lastTick && now - lastTick < TICK_FRESH_MS) {
          skippedFresh += 1;
          return item;
        }
        if (
          item.price != null &&
          item.price > 0 &&
          isCoarserQuote(mid, item.price)
        ) {
          skippedCoarse += 1;
          return item;
        }
        changed = true;
        applied += 1;
        const reference =
          item.price && item.changePercent != null && item.price > 0
            ? item.price / (1 + item.changePercent / 100)
            : item.price && item.price > 0
              ? item.price
              : mid;
        return {
          ...item,
          price: mid,
          changePercent:
            reference > 0 ? ((mid - reference) / reference) * 100 : item.changePercent,
        };
      });
      // #region agent log
      fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'e72fc0'},body:JSON.stringify({sessionId:'e72fc0',runId:'post-fix',hypothesisId:'F',location:'use-scanner-data.ts:quotes',message:'Scanner REST quote merge (freshness-gated)',data:{changed,applied,skippedFresh,skippedCoarse,quoteCount:quotes.length,wsConnected,sample:next.slice(0,3).map((o)=>({s:o.symbol,p:o.price,c:o.changePercent}))},timestamp:Date.now()})}).catch(()=>{});
      // #endregion
      if (!changed) return current;
      return { ...current, opportunities: next };
    });
  }, [quotesQuery.data, quotesQuery.dataUpdatedAt, queryClient, timeframe, wsConnected]);

  const marketStatus = useMemo(() => {
    const hours = getMarketHours("XAUUSD");
    return {
      marketOpen: hours.open,
      session: currentSession(),
      reason: hours.reason,
    };
  }, []);

  return {
    timeframe,
    setTimeframe,
    opportunities,
    meta,
    wsConnected,
    marketStatus,
    isLoading: scannerQuery.isLoading,
    isFetching: scannerQuery.isFetching,
    refetch: scannerQuery.refetch,
    error: scannerQuery.error,
  };
}
