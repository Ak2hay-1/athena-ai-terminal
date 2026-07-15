# Athena AI Terminal
# WebSocket Architecture

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | WebSocket Architecture |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | Backend Developers, Frontend Developers, Mobile Developers, DevOps Engineers, AI Assistants |

---

# Table of Contents

1. Introduction
2. Objectives
3. Design Philosophy
4. Architecture
5. Connection Lifecycle
6. Folder Structure
7. WebSocket Components
8. Connection Manager
9. Subscription Model
10. Message Types
11. Broadcast Pipeline
12. Market Streaming
13. Recommendation Streaming
14. Heartbeats
15. Client Reconnection
16. Error Handling
17. Security
18. Performance
19. Scaling Strategy
20. Future Enhancements
21. Best Practices
22. Related Documents

---

# 1. Introduction

Athena uses WebSockets to deliver real-time updates to connected clients.

Unlike REST APIs, which require clients to repeatedly request new data, WebSockets maintain a persistent connection, allowing the server to push updates immediately.

Typical streamed information includes:

- Live market candles
- Market analysis
- AI recommendations
- System status
- Future trade execution updates

---

# 2. Objectives

The WebSocket layer provides:

- Real-time communication
- Low latency
- Persistent connections
- Efficient broadcasting
- Scalable subscriptions
- Event-driven architecture

---

# 3. Design Philosophy

The WebSocket subsystem follows these principles:

- Stateless messages
- Event-driven communication
- Scalable broadcasting
- Symbol-based subscriptions
- Independent from REST
- Minimal network overhead

---

# 4. Architecture

```text
Scheduler

↓

Market Service

↓

Recommendation Engine

↓

WebSocket Manager

↓

Connected Clients

↓

React Dashboard
```

---

# 5. Connection Lifecycle

```mermaid
sequenceDiagram

Client->>Server: WebSocket Connect

Server-->>Client: Connection Accepted

Client->>Server: Subscribe

Server-->>Client: Subscription Confirmed

Server-->>Client: Live Updates

Client->>Server: Disconnect

Server: Remove Connection
```

---

# 6. Folder Structure

```
app/

└── websocket/

    ├── connection_manager.py
    ├── manager.py
    ├── market_stream.py
    ├── routes.py
    ├── __init__.py
```

Responsibilities:

### connection_manager.py

Maintains active WebSocket connections.

### manager.py

Coordinates message delivery.

### market_stream.py

Streams market and recommendation events.

### routes.py

Defines FastAPI WebSocket routes.

---

# 7. WebSocket Components

Current architecture consists of:

- Connection Manager
- Subscription Manager
- Broadcast Engine
- Market Stream
- Recommendation Stream

Future:

- Authentication Layer
- Redis Pub/Sub Adapter
- Presence Tracking

---

# 8. Connection Manager

Responsibilities:

- Accept connections
- Track active clients
- Disconnect clients
- Broadcast messages
- Maintain subscriptions

Current in-memory model:

```text
Client

↓

Connection

↓

Subscription

↓

Broadcast
```

Future deployments may replace in-memory storage with Redis.

---

# 9. Subscription Model

Clients subscribe only to data they require.

Example subscriptions:

```
XAUUSD

EURUSD

BTCUSD

Recommendations

System Events
```

Future subscription examples:

```
{
  "type": "subscribe",
  "symbol": "XAUUSD",
  "timeframe": "M1"
}
```

The server should maintain per-client subscription lists.

---

# 10. Message Types

Current message categories:

### Market Update

```json
{
  "type": "market",
  "symbol": "XAUUSD",
  "timeframe": "M1"
}
```

---

### Recommendation

```json
{
  "type": "recommendation",
  "signal": "BUY"
}
```

---

### Status

```json
{
  "type": "status",
  "message": "Connected"
}
```

---

### Error

```json
{
  "type": "error",
  "message": "Unknown subscription"
}
```

Future message types:

- Portfolio
- Trade
- Alert
- Notification
- AI Status

---

# 11. Broadcast Pipeline

```text
Scheduler

↓

Market Service

↓

Recommendation Engine

↓

Broadcast Event

↓

Connection Manager

↓

Subscribed Clients
```

Broadcasts should only reach clients subscribed to the relevant topic.

---

# 12. Market Streaming

The Market Stream publishes:

- Latest candle
- Indicator values
- Trend
- Market summary

Example payload:

```json
{
  "type": "market",
  "symbol": "XAUUSD",
  "timeframe": "M1",
  "close": 3362.45,
  "trend": "Bullish"
}
```

---

# 13. Recommendation Streaming

Whenever Athena generates a recommendation, it should be broadcast automatically.

Example payload:

```json
{
  "type": "recommendation",
  "symbol": "XAUUSD",
  "timeframe": "M1",
  "signal": "BUY",
  "confidence": 84,
  "entry": 3362.40,
  "stop_loss": 3357.10,
  "take_profit": 3374.80
}
```

---

# 14. Heartbeats

To detect stale connections, periodic heartbeat messages should be exchanged.

Example:

```json
{
  "type": "heartbeat",
  "timestamp": "2026-07-15T14:30:00Z"
}
```

Recommended interval:

```
30 seconds
```

If no heartbeat is received within the timeout window, the server should remove the connection.

---

# 15. Client Reconnection

Recommended frontend behaviour:

1. Detect disconnect.
2. Retry with exponential backoff.
3. Re-authenticate (future).
4. Restore subscriptions.
5. Resume streaming.

Example retry intervals:

```
1 second

2 seconds

5 seconds

10 seconds

30 seconds
```

---

# 16. Error Handling

Possible failures:

- Invalid subscription
- Duplicate subscription
- Unknown symbol
- Malformed JSON
- Connection timeout
- Server shutdown

Errors should always be returned as structured JSON.

---

# 17. Security

Current:

- Local development
- Input validation
- Subscription validation

Future:

- JWT authentication
- Token refresh
- Rate limiting
- Origin validation
- TLS (WSS)
- Per-user permissions

---

# 18. Performance

Current optimizations:

- Persistent connections
- Shared broadcasts
- Symbol filtering

Future optimizations:

- Binary serialization
- Message compression
- Redis Pub/Sub
- Kafka integration
- Horizontal scaling

---

# 19. Scaling Strategy

Current deployment:

```text
FastAPI

↓

In-memory Connections
```

Future production architecture:

```text
FastAPI Instance 1

↓

Redis Pub/Sub

↓

FastAPI Instance 2

↓

Load Balancer

↓

Clients
```

This allows thousands of concurrent WebSocket connections across multiple backend instances.

---

# 20. Future Enhancements

Planned capabilities:

- Portfolio updates
- Order execution events
- Trade lifecycle events
- AI streaming responses
- Notification channels
- User-specific rooms
- Multi-device synchronization
- Market session events

---

# 21. Best Practices

- Keep messages small.
- Use structured JSON.
- Broadcast only to subscribers.
- Remove inactive connections.
- Validate every incoming message.
- Avoid sending duplicate updates.
- Design events to be idempotent where practical.
- Separate transport logic from business logic.

---

# 22. Related Documents

- 05_Backend_Architecture.md
- 07_MT5_Integration.md
- 08_AI_Architecture.md
- 11_Market_Analysis_Engine.md
- 12_Recommendation_Engine.md
- 13_REST_API.md
- 15_Authentication_Authorization.md
- 99_AI_Continuation_Context.md

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial WebSocket architecture documentation |

---

**Document End**

© Athena AI Terminal Project
