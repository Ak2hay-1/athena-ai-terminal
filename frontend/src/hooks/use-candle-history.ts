"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type Dispatch,
  type SetStateAction,
} from "react";
import {
  HISTORY_BATCH_SIZE,
  INITIAL_CANDLE_LIMIT,
  applyLiveCandleUpdate,
  mergeCandlesChronological,
} from "@/lib/candle-history";
import {
  appendCachedCandle,
  getCachedSeries,
  putCachedSeries,
} from "@/lib/candle-series-cache";
import { preloadRelatedTimeframes } from "@/lib/candle-preload";
import { getCandles } from "@/services/market";
import type { Candle } from "@/types";

interface Options {
  symbol: string;
  timeframe: string;
  enabled?: boolean;
  initialLimit?: number;
  batchSize?: number;
  /** Bump to force a full reload of candle history. */
  refreshKey?: number | string;
}

interface Result {
  candles: Candle[];
  isLoading: boolean;
  isLoadingMore: boolean;
  hasMore: boolean;
  loadOlder: () => void;
  applyLiveCandle: (candle: Candle) => void;
  setCandles: Dispatch<SetStateAction<Candle[]>>;
}

/**
 * Owns chart candle state with infinite historical loading.
 *
 * - Serves from client series cache first (instant TF switch / reopen)
 * - Initial fetch: latest `initialLimit` candles
 * - Scroll-back: batches of `batchSize` before the oldest timestamp
 * - Dedupes by time, keeps chronological order
 * - Guards concurrent requests; stops when a batch returns empty / short
 * - Caches requested `before` cursors to avoid duplicate downloads
 * - Background-preloads related timeframes without blocking paint
 */
export function useCandleHistory({
  symbol,
  timeframe,
  enabled = true,
  initialLimit = INITIAL_CANDLE_LIMIT,
  batchSize = HISTORY_BATCH_SIZE,
  refreshKey = 0,
}: Options): Result {
  const [candles, setCandles] = useState<Candle[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const candlesRef = useRef<Candle[]>([]);
  const loadingRef = useRef(false);
  const hasMoreRef = useRef(true);
  const requestedBeforeRef = useRef(new Set<string>());
  const requestIdRef = useRef(0);

  candlesRef.current = candles;
  hasMoreRef.current = hasMore;

  const resetHistoryState = useCallback(() => {
    requestIdRef.current += 1;
    loadingRef.current = false;
    hasMoreRef.current = true;
    requestedBeforeRef.current = new Set();
    setCandles([]);
    setHasMore(true);
    setIsLoadingMore(false);
  }, []);

  useEffect(() => {
    if (!enabled || !symbol || !timeframe) {
      resetHistoryState();
      setIsLoading(false);
      return;
    }

    const cached = getCachedSeries(symbol, timeframe);
    const hasCache = Boolean(cached && cached.length > 0);

    // Bump request generation and reset pagination cursors without
    // blanking the chart when we can paint from cache immediately.
    requestIdRef.current += 1;
    const requestId = requestIdRef.current;
    loadingRef.current = false;
    hasMoreRef.current = true;
    requestedBeforeRef.current = new Set();
    setHasMore(true);
    setIsLoadingMore(false);
    if (!hasCache) {
      setCandles([]);
    }

    let cancelled = false;

    if (hasCache && cached) {
      const sliced =
        cached.length > initialLimit
          ? cached.slice(cached.length - initialLimit)
          : cached;
      setCandles(sliced);
      candlesRef.current = sliced;
      hasMoreRef.current = cached.length >= initialLimit;
      setHasMore(cached.length >= initialLimit);
      setIsLoading(false);
      loadingRef.current = false;
      preloadRelatedTimeframes(symbol, timeframe, initialLimit);
      // Soft revalidate in background without clearing the chart.
      void (async () => {
        try {
          const batch = await getCandles(symbol, timeframe, initialLimit);
          if (cancelled || requestId !== requestIdRef.current) return;
          if (!batch.length) return;
          const merged = mergeCandlesChronological(sliced, batch);
          setCandles(merged);
          candlesRef.current = merged;
          putCachedSeries(symbol, timeframe, merged);
        } catch {
          // Keep cached series on soft-revalidate failure.
        }
      })();
      return () => {
        cancelled = true;
      };
    }

    setIsLoading(true);
    loadingRef.current = true;

    void (async () => {
      try {
        const batch = await getCandles(symbol, timeframe, initialLimit);
        if (cancelled || requestId !== requestIdRef.current) return;

        const merged = mergeCandlesChronological([], batch);
        setCandles(merged);
        candlesRef.current = merged;
        putCachedSeries(symbol, timeframe, merged);
        preloadRelatedTimeframes(symbol, timeframe, initialLimit);

        const exhausted = batch.length < initialLimit;
        hasMoreRef.current = !exhausted;
        setHasMore(!exhausted);

        if (!cancelled && requestId === requestIdRef.current) {
          loadingRef.current = false;
          setIsLoading(false);
        }

        if (!exhausted && merged.length > 0) {
          const before = merged[0]?.time;
          if (before && !requestedBeforeRef.current.has(before)) {
            requestedBeforeRef.current.add(before);
            setIsLoadingMore(true);
            try {
              const older = await getCandles(symbol, timeframe, batchSize, {
                before,
              });
              if (cancelled || requestId !== requestIdRef.current) return;
              if (older.length === 0) {
                hasMoreRef.current = false;
                setHasMore(false);
              } else {
                const next = mergeCandlesChronological(
                  candlesRef.current,
                  older,
                );
                const added = next.length - candlesRef.current.length;
                setCandles(next);
                candlesRef.current = next;
                putCachedSeries(symbol, timeframe, next);
                if (added <= 0 || older.length < batchSize) {
                  hasMoreRef.current = false;
                  setHasMore(false);
                }
              }
            } catch {
              if (!cancelled && requestId === requestIdRef.current) {
                requestedBeforeRef.current.delete(before);
              }
            } finally {
              if (!cancelled && requestId === requestIdRef.current) {
                setIsLoadingMore(false);
              }
            }
          }
        }
      } catch {
        if (cancelled || requestId !== requestIdRef.current) return;
        setCandles([]);
        candlesRef.current = [];
        hasMoreRef.current = false;
        setHasMore(false);
      } finally {
        const clearLoading =
          !cancelled &&
          requestId === requestIdRef.current &&
          loadingRef.current;
        if (clearLoading) {
          loadingRef.current = false;
          setIsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [
    enabled,
    symbol,
    timeframe,
    initialLimit,
    batchSize,
    refreshKey,
    resetHistoryState,
  ]);

  const loadOlder = useCallback(() => {
    if (!enabled || !symbol || !timeframe) return;
    if (loadingRef.current || !hasMoreRef.current) return;

    const oldest = candlesRef.current[0];
    if (!oldest?.time) return;

    const before = oldest.time;
    if (requestedBeforeRef.current.has(before)) return;

    requestedBeforeRef.current.add(before);
    loadingRef.current = true;
    setIsLoadingMore(true);

    const requestId = requestIdRef.current;

    void (async () => {
      try {
        const batch = await getCandles(symbol, timeframe, batchSize, {
          before,
        });
        if (requestId !== requestIdRef.current) return;

        if (batch.length === 0) {
          hasMoreRef.current = false;
          setHasMore(false);
          return;
        }

        const merged = mergeCandlesChronological(candlesRef.current, batch);
        const added = merged.length - candlesRef.current.length;
        setCandles(merged);
        candlesRef.current = merged;
        putCachedSeries(symbol, timeframe, merged);

        if (added <= 0 || batch.length < batchSize) {
          hasMoreRef.current = false;
          setHasMore(false);
        }
      } catch {
        if (requestId !== requestIdRef.current) return;
        requestedBeforeRef.current.delete(before);
      } finally {
        if (requestId === requestIdRef.current) {
          loadingRef.current = false;
          setIsLoadingMore(false);
        }
      }
    })();
  }, [batchSize, enabled, symbol, timeframe]);

  const applyLiveCandle = useCallback(
    (candle: Candle) => {
      setCandles((current) => {
        const next = applyLiveCandleUpdate(current, candle);
        candlesRef.current = next;
        const prevLast = current[current.length - 1];
        const nextLast = next[next.length - 1];
        if (
          symbol &&
          timeframe &&
          nextLast &&
          prevLast &&
          nextLast.time !== prevLast.time
        ) {
          // Bucket advanced: previous bar is closed — persist it.
          appendCachedCandle(symbol, timeframe, prevLast);
        }
        return next;
      });
    },
    [symbol, timeframe],
  );

  return {
    candles,
    isLoading,
    isLoadingMore,
    hasMore,
    loadOlder,
    applyLiveCandle,
    setCandles,
  };
}
