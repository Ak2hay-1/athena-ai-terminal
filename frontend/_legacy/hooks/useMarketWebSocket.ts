import { useEffect, useRef, useState } from 'react'
import { WS_URL } from '../config'

export function useMarketWebSocket(
  symbol: string,
  timeframe: string,
  onMessage: (payload: Record<string, unknown>) => void,
) {
  const [connected, setConnected] = useState(false)
  const socketRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const socket = new WebSocket(WS_URL)
    socketRef.current = socket

    socket.onopen = () => {
      setConnected(true)
      socket.send(
        JSON.stringify({
          action: 'SUBSCRIBE',
          symbol,
          timeframe,
        }),
      )
    }

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as Record<string, unknown>
        onMessage(payload)
      } catch {
        // ignore malformed messages
      }
    }

    socket.onclose = () => setConnected(false)

    return () => {
      socket.close()
    }
  }, [symbol, timeframe, onMessage])

  return { connected }
}
