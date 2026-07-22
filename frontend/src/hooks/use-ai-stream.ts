"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { config } from "@/lib/config";
import { getAccessToken } from "@/services/api-client";
import type { AiChatMessage } from "@/services/ai";

type StreamHandlers = {
  onChunk?: (delta: string, full: string) => void;
  onDone?: (full: string) => void;
  onError?: (message: string) => void;
};

function buildWsUrl(): string | null {
  const token = getAccessToken();
  if (!token) return null;
  const base = config.wsUrl;
  const separator = base.includes("?") ? "&" : "?";
  return `${base}${separator}token=${encodeURIComponent(token)}`;
}

export function useAiStream(enabled = true) {
  const [connected, setConnected] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const handlersRef = useRef<Map<string, StreamHandlers>>(new Map());
  const buffersRef = useRef<Map<string, string>>(new Map());

  useEffect(() => {
    if (!enabled) {
      setConnected(false);
      return;
    }

    let closed = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let pingTimer: ReturnType<typeof setInterval> | null = null;
    let attempt = 0;

    const clearTimers = () => {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (pingTimer) clearInterval(pingTimer);
      reconnectTimer = null;
      pingTimer = null;
    };

    const connect = () => {
      if (closed) return;
      clearTimers();
      const url = buildWsUrl();
      if (!url) {
        setConnected(false);
        reconnectTimer = setTimeout(connect, Math.min(10_000, 1000 * 2 ** attempt));
        attempt += 1;
        return;
      }

      let socket: WebSocket;
      try {
        socket = new WebSocket(url);
      } catch {
        setConnected(false);
        reconnectTimer = setTimeout(connect, Math.min(10_000, 1000 * 2 ** attempt));
        attempt += 1;
        return;
      }

      socketRef.current = socket;

      socket.onopen = () => {
        if (closed) return;
        attempt = 0;
        setConnected(true);
        pingTimer = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ action: "PING" }));
          }
        }, 20_000);
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as Record<string, unknown>;
          if (payload.type === "PONG") return;

          const requestId = String(payload.request_id ?? "");
          const handlers = handlersRef.current.get(requestId);
          if (!handlers) return;

          if (payload.type === "ai_chunk") {
            const delta = String(payload.delta ?? "");
            const prev = buffersRef.current.get(requestId) ?? "";
            const full = prev + delta;
            buffersRef.current.set(requestId, full);
            handlers.onChunk?.(delta, full);
          } else if (payload.type === "ai_done") {
            const full = String(payload.full ?? buffersRef.current.get(requestId) ?? "");
            handlers.onDone?.(full);
            handlersRef.current.delete(requestId);
            buffersRef.current.delete(requestId);
            setStreaming(false);
          } else if (payload.type === "ai_error") {
            handlers.onError?.(String(payload.message ?? "AI stream error"));
            handlersRef.current.delete(requestId);
            buffersRef.current.delete(requestId);
            setStreaming(false);
          }
        } catch {
          // ignore malformed
        }
      };

      socket.onclose = () => {
        if (closed) return;
        setConnected(false);
        clearTimers();
        reconnectTimer = setTimeout(connect, Math.min(10_000, 1000 * 2 ** attempt));
        attempt += 1;
      };

      socket.onerror = () => {
        if (!closed) setConnected(false);
      };
    };

    connect();

    return () => {
      closed = true;
      clearTimers();
      socketRef.current?.close();
      socketRef.current = null;
      setConnected(false);
    };
  }, [enabled]);

  const sendChat = useCallback(
    (
      input: {
        messages: AiChatMessage[];
        symbol?: string;
        timeframe?: string;
        requestId?: string;
      },
      handlers: StreamHandlers,
    ) => {
      const socket = socketRef.current;
      if (!socket || socket.readyState !== WebSocket.OPEN) {
        handlers.onError?.("AI stream not connected.");
        return null;
      }
      const requestId = input.requestId ?? `chat-${Date.now()}`;
      handlersRef.current.set(requestId, handlers);
      buffersRef.current.set(requestId, "");
      setStreaming(true);
      socket.send(
        JSON.stringify({
          action: "AI_CHAT",
          request_id: requestId,
          messages: input.messages,
          symbol: input.symbol,
          timeframe: input.timeframe,
        }),
      );
      return requestId;
    },
    [],
  );

  const sendExplain = useCallback(
    (
      input: {
        symbol: string;
        timeframe: string;
        requestId?: string;
      },
      handlers: StreamHandlers,
    ) => {
      const socket = socketRef.current;
      if (!socket || socket.readyState !== WebSocket.OPEN) {
        handlers.onError?.("AI stream not connected.");
        return null;
      }
      const requestId = input.requestId ?? `explain-${Date.now()}`;
      handlersRef.current.set(requestId, handlers);
      buffersRef.current.set(requestId, "");
      setStreaming(true);
      socket.send(
        JSON.stringify({
          action: "AI_EXPLAIN",
          request_id: requestId,
          symbol: input.symbol,
          timeframe: input.timeframe,
        }),
      );
      return requestId;
    },
    [],
  );

  return { connected, streaming, sendChat, sendExplain };
}
