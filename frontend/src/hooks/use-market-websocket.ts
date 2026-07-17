"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { config } from "@/lib/config";

export type MarketWsMessage = Record<string, unknown>;

interface UseMarketWebSocketOptions {
  symbols: string[];
  timeframe: string;
  onMessage: (payload: MarketWsMessage) => void;
  enabled?: boolean;
}

const PING_INTERVAL_MS = 20_000;

export function useMarketWebSocket({
  symbols,
  timeframe,
  onMessage,
  enabled = true,
}: UseMarketWebSocketOptions) {
  const [connected, setConnected] = useState(false);
  const onMessageRef = useRef(onMessage);
  const symbolsKey = symbols.map((s) => s.toUpperCase()).join(",");
  const timeframeRef = useRef(timeframe);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    timeframeRef.current = timeframe;
  }, [timeframe]);

  useEffect(() => {
    if (!enabled || !symbolsKey) {
      setConnected(false);
      return;
    }

    let closed = false;
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let pingTimer: ReturnType<typeof setInterval> | null = null;
    let attempt = 0;

    const symbolList = symbolsKey.split(",").filter(Boolean);

    const clearTimers = () => {
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      if (pingTimer) {
        clearInterval(pingTimer);
        pingTimer = null;
      }
    };

    const subscribe = (ws: WebSocket) => {
      const tf = timeframeRef.current;
      for (const symbol of symbolList) {
        ws.send(
          JSON.stringify({
            action: "SUBSCRIBE",
            symbol,
            timeframe: tf,
          }),
        );
      }
    };

    const startPing = (ws: WebSocket) => {
      if (pingTimer) clearInterval(pingTimer);
      pingTimer = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: "PING" }));
        }
      }, PING_INTERVAL_MS);
    };

    const connect = () => {
      if (closed) return;
      clearTimers();

      try {
        socket = new WebSocket(config.wsUrl);
      } catch {
        setConnected(false);
        const delay = Math.min(10_000, 1_000 * 2 ** attempt);
        attempt += 1;
        reconnectTimer = setTimeout(connect, delay);
        return;
      }

      socket.onopen = () => {
        if (closed) return;
        attempt = 0;
        setConnected(true);
        subscribe(socket!);
        startPing(socket!);
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as MarketWsMessage;
          if (payload.type === "PONG") return;
          onMessageRef.current(payload);
        } catch {
          // ignore malformed payloads
        }
      };

      socket.onclose = () => {
        if (closed) return;
        setConnected(false);
        if (pingTimer) {
          clearInterval(pingTimer);
          pingTimer = null;
        }
        const delay = Math.min(10_000, 1_000 * 2 ** attempt);
        attempt += 1;
        reconnectTimer = setTimeout(connect, delay);
      };

      socket.onerror = () => {
        if (!closed) setConnected(false);
      };
    };

    connect();

    return () => {
      closed = true;
      clearTimers();
      if (socket && socket.readyState <= WebSocket.OPEN) {
        socket.close();
      }
      setConnected(false);
    };
  }, [symbolsKey, timeframe, enabled]);

  return { connected };
}

export function useStableCallback<T extends (...args: never[]) => unknown>(fn: T) {
  const ref = useRef(fn);
  useEffect(() => {
    ref.current = fn;
  }, [fn]);
  return useCallback((...args: Parameters<T>) => ref.current(...args), []) as T;
}
