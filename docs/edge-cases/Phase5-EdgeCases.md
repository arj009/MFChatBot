# Phase 5 — API & Orchestration Layer: Edge Cases

**Reference:** [Phase 5 in PhaseWiseArchitecture.md](../PhaseWiseArchitecture.md#phase-5--api--orchestration-layer)

---

## Request validation

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P5-E01 | `POST /api/chat` with empty `message` | 400 with clear error; no pipeline run | High |
| P5-E02 | `message` missing from JSON body | 400 | High |
| P5-E03 | `message` exceeds length cap (e.g. 2k chars) | 400 or truncate per policy before classifier | High |
| P5-E04 | Non-JSON body / wrong Content-Type | 415 or 400 | Medium |
| P5-E05 | Extra fields in body (`user_email`) | Ignore fields; do not persist | Medium |
| P5-E06 | SQL/script injection in `message` | Treat as text; sanitize display in UI; no eval | Medium |

## Pipeline orchestration

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P5-E07 | Classifier → factual, retrieval returns `[]` | User message per architecture; link only to inventory URL (closest scheme if implemented) | High |
| P5-E08 | LLM timeout during generation | Short user message; optional retry once; no partial advice | High |
| P5-E09 | Validator fails twice | Safe fallback answer + top retrieval `source_url` | High |
| P5-E10 | Validator fails thrice (retry policy exceeded) | Same as P5-E09; log `VALIDATION_EXHAUSTED` | High |
| P5-E11 | Index not loaded on server start | `/api/health` unhealthy; chat returns 503 | Critical |
| P5-E12 | Partial pipeline exception mid-request | 500 with generic message; no stack trace to client | High |
| P5-E13 | Concurrent requests on single-worker server | Queue or async; no corrupted shared index state | Medium |

## Response contract

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P5-E14 | Factual response missing `source_url` | Bug; fix validator/orchestrator before release | Critical |
| P5-E15 | Refusal with `is_refusal: false` | Must set `is_refusal: true` for refusal path | High |
| P5-E16 | `last_updated` null on factual answer | Populate from chunk metadata | High |
| P5-E17 | `source_url` not in closed inventory in JSON response | Block response; internal error | Critical |
| P5-E18 | Performance path returns calculated return fields | Omit numbers; only link + short text | Critical |

## Privacy & logging

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P5-E19 | Full user message written to log file | Hash or omit per policy; never log PAN patterns | Critical |
| P5-E20 | PII detected in message | `PII_RISK` path; log label only, not raw PII | Critical |
| P5-E21 | Request includes email/phone for “support” | Do not store; refuse or ignore field | High |
| P5-E22 | Error handler logs stack with user message | Scrub message from exception logs | High |

## Endpoints

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P5-E23 | `GET /api/health` when dependencies down | 503; body indicates index/LLM status | Medium |
| P5-E24 | `GET /api/examples` when config missing | Return 3 hardcoded Phase 0 example questions | Medium |
| P5-E25 | `GET /api/examples` returns 4 questions | Trim to 3 for UI contract | Low |
| P5-E26 | CORS preflight from local UI | Allow dev origin; restrict in production | Medium |
| P5-E27 | `POST /api/chat` without CORS in production UI | Configure allowed origins | Medium |

## Empty retrieval fallback

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P5-E28 | “Closest scheme” picks wrong fund (Technology vs Pharma) | Prefer abstention over wrong link; document heuristic limits | High |
| P5-E29 | Fallback links to filter page (#9) for scheme-specific miss | Prefer specific scheme from query hint else listing | Medium |
| P5-E30 | Fallback invents URL path not in inventory | Forbidden; pick from retriever or inventory only | Critical |

## Stateless & security

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P5-E31 | Client sends `session_id` expecting memory | Ignore; each request independent unless future scope | Low |
| P5-E32 | API key missing for LLM | 503 or graceful degradation message | High |
| P5-E33 | Rate abuse (100 req/s same IP) | Throttle; 429 | Medium |
