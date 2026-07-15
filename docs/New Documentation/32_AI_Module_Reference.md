# Athena AI Terminal
# AI Module Reference

---

| Document Information | |
|----------------------|------------------------------------------------|
| Project | Athena AI Terminal |
| Document | AI Module Reference |
| Version | 1.0 |
| Status | Living Document |
| Last Updated | July 2026 |
| Audience | AI Engineers, Backend Developers, Architects, QA Engineers, AI Assistants |

---

# Table of Contents

1. Introduction
2. AI Subsystem Overview
3. AI Request Lifecycle
4. Module Overview
5. client.py
6. prompt_builder.py
7. recommendation_engine.py
8. response_parser.py
9. AI Data Models
10. Prompt Engineering
11. Response Validation
12. Error Handling
13. Retry Strategy
14. Model Configuration
15. Performance Considerations
16. Future AI Architecture
17. Extension Guidelines
18. Related Documents

---

# 1. Introduction

Athena uses Artificial Intelligence to transform deterministic technical analysis into explainable trading recommendations.

The AI subsystem does **not** replace technical analysis.

Instead, it:

- Summarizes analysis
- Weighs confluence
- Produces structured recommendations
- Explains decisions
- Generates human-readable reasoning

Every AI response must be validated before it is accepted by the application.

---

# 2. AI Subsystem Overview

Architecture

```text
MarketService

↓

RecommendationEngine

↓

PromptBuilder

↓

LLM Client

↓

Ollama

↓

JSON Response

↓

Response Parser

↓

Validation

↓

Recommendation
```

The AI subsystem is intentionally isolated from the rest of the application.

---

# 3. AI Request Lifecycle

Complete workflow

```text
Market Data

↓

Indicators

↓

Pattern Detection

↓

Market Analysis

↓

Recommendation Engine

↓

Prompt Builder

↓

LLM Client

↓

AI Model

↓

JSON Response

↓

Response Parser

↓

Pydantic Validation

↓

Recommendation Object

↓

Repository

↓

REST API

↓

WebSocket
```

Each stage has a single responsibility.

---

# 4. Module Overview

Current modules

```
ai/

client.py

prompt_builder.py

recommendation_engine.py

response_parser.py
```

Future modules

```
provider_manager.py

prompt_templates.py

conversation_memory.py

token_counter.py

prompt_versioning.py

model_registry.py
```

---

# 5. client.py

## Purpose

Provides communication with the AI provider.

Current provider

```
Ollama
```

Future providers

```
OpenAI

Anthropic

Google Gemini

Azure OpenAI

Local Llama.cpp

vLLM
```

---

## Responsibilities

- Send prompts
- Receive responses
- Handle timeouts
- Retry transient failures
- Parse HTTP responses
- Return raw model output

---

## Typical Workflow

```text
Prompt

↓

HTTP POST

↓

Ollama

↓

JSON

↓

Return Response
```

---

## Inputs

```
Prompt

Temperature

Model

Timeout
```

---

## Outputs

```
Raw model response
```

---

## Error Conditions

- Connection refused
- Timeout
- Invalid model
- Invalid response
- HTTP error
- Provider unavailable

---

## Logging

Examples

```
Sending prompt to Ollama.

Received AI response.

Retrying request.
```

---

# 6. prompt_builder.py

## Purpose

Generate deterministic prompts for the AI model.

---

## Responsibilities

- Build prompts
- Insert market data
- Insert indicators
- Insert patterns
- Insert trend
- Insert volatility
- Specify required JSON format

---

## Inputs

```
Market Summary

Indicators

Patterns

Confluence

Trend
```

---

## Outputs

```
Prompt String
```

---

## Prompt Structure

Typical sections

```
System Instructions

↓

Market Data

↓

Indicators

↓

Pattern Summary

↓

Trend

↓

Required JSON Schema

↓

Rules
```

---

## Requirements

Prompt should:

- Be deterministic
- Minimize hallucinations
- Require JSON output
- Forbid additional text

---

# 7. recommendation_engine.py

## Purpose

Coordinate the complete AI workflow.

---

## Responsibilities

- Receive market analysis
- Build prompt
- Call AI
- Parse response
- Validate response
- Return recommendation

---

## Dependencies

```
PromptBuilder

OllamaClient

ResponseParser
```

---

## Workflow

```text
Analysis

↓

Prompt Builder

↓

AI Client

↓

Parser

↓

Recommendation
```

---

## Public Methods

Typical methods

```python
analyze()

generate()

validate()

build_recommendation()
```

---

## Outputs

```
AIRecommendation
```

---

## Error Recovery

If AI fails

↓

Generate fallback recommendation

↓

Log error

↓

Continue execution

---

# 8. response_parser.py

## Purpose

Convert raw AI output into validated application objects.

---

## Responsibilities

- Parse JSON
- Validate schema
- Convert types
- Handle malformed output
- Generate fallback objects

---

## Input

```
Raw AI Response
```

---

## Output

```
AIRecommendation
```

---

## Validation

Checks

- Required fields
- Enum values
- Numeric types
- Confidence range
- Stop-loss
- Take-profit
- Risk-reward

---

## Invalid Response

Example

```text
Missing signal

↓

Fallback Recommendation
```

---

## Logging

```
Validation failed.

Fallback generated.
```

---

# 9. AI Data Models

Primary object

```
AIRecommendation
```

Typical fields

```
signal

entry

stop_loss

take_profit

confidence

risk_reward

summary

reasons
```

Recommended enum

```
BUY

SELL

HOLD
```

The parser should reject unsupported values.

---

# 10. Prompt Engineering

Athena uses deterministic prompting.

Prompt should include

- Market structure
- Trend
- Indicators
- Smart Money Concepts
- Volatility
- Confluence
- Required JSON schema

Prompt should avoid

- Ambiguous wording
- Open-ended questions
- Multiple output formats

Every prompt template should be version controlled.

---

# 11. Response Validation

Validation occurs in multiple stages.

```text
Raw Text

↓

JSON Parsing

↓

Pydantic Validation

↓

Business Rule Validation

↓

Recommendation Object
```

Validation checks include

- Valid JSON
- Required fields
- Allowed enums
- Numeric ranges
- Logical consistency

Example

```
Stop Loss

↓

Must be positive

↓

Must differ from entry

↓

Must be logically placed
```

---

# 12. Error Handling

Common failures

```
Provider unavailable

Timeout

Malformed JSON

Unexpected fields

Empty response

Validation failure
```

Recovery strategy

```
Log

↓

Fallback Recommendation

↓

Continue Scheduler
```

The scheduler should continue operating even if AI is unavailable.

---

# 13. Retry Strategy

Recommended retry policy

Attempt

```
1
```

↓

Delay

```
1 second
```

↓

Attempt

```
2
```

↓

Delay

```
2 seconds
```

↓

Final failure

↓

Fallback recommendation

Retries should be limited to avoid blocking scheduler execution.

---

# 14. Model Configuration

Current configuration

```
OLLAMA_URL

OLLAMA_MODEL

AI_TIMEOUT

AI_RETRIES
```

Future configuration

```
TEMPERATURE

TOP_P

MAX_TOKENS

SEED

SYSTEM_PROMPT_VERSION

PRIMARY_PROVIDER

SECONDARY_PROVIDER
```

All configuration should come from environment variables.

---

# 15. Performance Considerations

Current optimizations

- Deterministic prompts
- Single request per recommendation
- JSON-only responses
- Validation before persistence

Future optimizations

- Prompt caching
- Streaming responses
- Response compression
- Parallel model evaluation
- Local response cache

---

# 16. Future AI Architecture

Future design

```text
Recommendation Engine

↓

Provider Manager

↓

OpenAI

Anthropic

Gemini

Ollama

↓

Response Aggregator

↓

Consensus

↓

Validation
```

Potential enhancements

- Multi-model voting
- Confidence weighting
- Model benchmarking
- Automatic provider failover
- Prompt version selection

---

# 17. Extension Guidelines

When adding a new AI provider

1. Implement provider client

↓

2. Conform to provider interface

↓

3. Register provider

↓

4. Add configuration

↓

5. Add tests

↓

6. Update documentation

When modifying prompts

- Preserve JSON contract
- Version templates
- Test against supported models
- Validate fallback behavior

---

# 18. Related Documents

Architecture

- 08_AI_Architecture.md
- 12_Recommendation_Engine.md

Implementation

- 30_Service_Class_Reference.md
- 31_Repository_Class_Reference.md
- 33_MT5_Module_Reference.md

Operations

- 20_Testing_Strategy.md
- 21_Logging_Observability.md
- 22_Security_Guide.md

---

# AI Module Checklist

Before changing the AI subsystem:

- [ ] Prompt updated
- [ ] JSON schema unchanged (or versioned)
- [ ] Response parser updated
- [ ] Validation rules reviewed
- [ ] Retry behavior verified
- [ ] Timeout tested
- [ ] Fallback recommendation verified
- [ ] Unit tests updated
- [ ] Integration tests updated
- [ ] Documentation updated

---

# AI Module Dependency Matrix

| Module | Depends On | Returns |
|---------|------------|----------|
| client.py | HTTP Client, Configuration | Raw AI Response |
| prompt_builder.py | Analysis Data | Prompt String |
| recommendation_engine.py | Prompt Builder, Client, Parser | AIRecommendation |
| response_parser.py | Pydantic Models | Validated AIRecommendation |

---

# Future Improvements

Future versions of this document should include:

- Complete prompt templates
- Provider interface specification
- Token budgeting strategy
- Prompt version history
- AI benchmark results
- Hallucination mitigation techniques
- Example request/response pairs
- Sequence diagrams
- Provider failover workflow
- Streaming response support

---

# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0 | July 2026 | Initial AI Module Reference |

---

**Document End**

© Athena AI Terminal Project
