"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { config } from "@/lib/config";
import { getAccessToken } from "@/services/api-client";

export type MarketWsMessage = Record<string, unknown>;

interface UseMarketWebSocketOptions {
  symbols: string[];
  timeframe: string;
  onMessage: (payload: MarketWsMessage) => void;
  /** Fired after a successful open that follows a prior connection (or first open). */
  onReconnect?: () => void;
  enabled?: boolean;
}

const PING_INTERVAL_MS = 20_000;

function buildWsUrl(): string | null {
  const token = getAccessToken();
  if (!token) return null;
  const base = config.wsUrl;
  const separator = base.includes("?") ? "&" : "?";
  return `${base}${separator}token=${encodeURIComponent(token)}`;
}

export function useMarketWebSocket({
  symbols,
  timeframe,
  onMessage,
  onReconnect,
  enabled = true,
}: UseMarketWebSocketOptions) {
  const [connected, setConnected] = useState(false);
  const onMessageRef = useRef(onMessage);
  const onReconnectRef = useRef(onReconnect);
  const symbolsKey = symbols.map((s) => s.toUpperCase()).join(",");
  const timeframeRef = useRef(timeframe);
  const hadConnectionRef = useRef(false);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    onReconnectRef.current = onReconnect;
  }, [onReconnect]);

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
    hadConnectionRef.current = false;

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

      const url = buildWsUrl();
      if (!url) {
        setConnected(false);
        const delay = Math.min(10_000, 1_000 * 2 ** attempt);
        attempt += 1;
        reconnectTimer = setTimeout(connect, delay);
        return;
      }

      try {
        socket = new WebSocket(url);
      } catch {
        setConnected(false);
        const delay = Math.min(10_000, 1_000 * 2 ** attempt);
        attempt += 1;
        reconnectTimer = setTimeout(connect, delay);
        return;
      }

      socket.onopen = () => {
        if (closed) return;
        const isReconnect = hadConnectionRef.current;
        attempt = 0;
        hadConnectionRef.current = true;
        setConnected(true);
        subscribe(socket!);
        startPing(socket!);
        // #region agent log
        fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'e72fc0'},body:JSON.stringify({sessionId:'e72fc0',runId:'pre-fix',hypothesisId:'A',location:'use-market-websocket.ts:onopen',message:'WS open + subscribe',data:{symbols:symbolList.slice(0,20),symbolCount:symbolList.length,timeframe:timeframeRef.current,isReconnect},timestamp:Date.now()})}).catch(()=>{});
        // #endregion
        if (isReconnect) {
          onReconnectRef.current?.();
        }
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as MarketWsMessage;
          if (payload.type === "PONG") return;
          // #region agent log
          const _t = String(payload.type ?? '');
          if (!(globalThis as unknown as {_dbgTickN?: number})._dbgTickN) (globalThis as unknown as {_dbgTickN?: number})._dbgTickN = 0;
          if (_t === 'tick') {
            (globalThis as unknown as {_dbgTickN: number})._dbgTickN += 1;
            if ((globalThis as unknown as {_dbgTickN: number})._dbgTickN <= 5 || (globalThis as unknown as {_dbgTickN: number})._dbgTickN % 50 === 0) {
              fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'e72fc0'},body:JSON.stringify({sessionId:'e72fc0',runId:'pre-fix',hypothesisId:'A',location:'use-market-websocket.ts:onmessage',message:'WS tick sample',data:{n:(globalThis as unknown as {_dbgTickN: number})._dbgTickN,symbol:payload.symbol,mid:payload.mid},timestamp:Date.now()})}).catch(()=>{});
            }
          } else if (_t !== 'candle_update') {
            fetch('http://127.0.0.1:7628/ingest/f3b6af10-4b61-49ec-8948-6d6f0fadcabb',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'e72fc0'},body:JSON.stringify({sessionId:'e72fc0',runId:'pre-fix',hypothesisId:'A',location:'use-market-websocket.ts:onmessage',message:'WS non-tick message',data:{type:_t,symbol:payload.symbol,timeframe:payload.timeframe},timestamp:Date.now()})}).catch(()=>{});
          }
          // #endregion
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
