# Phase 6 — Minimal User Interface: Edge Cases

**Reference:** [Phase 6 in PhaseWiseArchitecture.md](../PhaseWiseArchitecture.md#phase-6--minimal-user-interface)

---

## Required UI elements

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P6-E01 | Disclaimer scrolled out of view | Disclaimer remains visible (sticky header/footer) | High |
| P6-E02 | Disclaimer hidden on mobile | Responsive layout keeps disclaimer on screen | High |
| P6-E03 | Welcome message missing after load | Show default welcome from static copy | Medium |
| P6-E04 | Fewer than 3 example chips | Fetch `/api/examples`; fallback to Phase 0 three questions | High |
| P6-E05 | More than 3 example chips rendered | Show exactly 3 | Low |

## Chat interaction

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P6-E06 | User clicks example chip | Populate input and send (or populate only—document chosen UX) | Medium |
| P6-E07 | Double-click Send / rapid Enter | Disable send while in-flight; single request | High |
| P6-E08 | Empty send | Disable button or no-op; no API call | Medium |
| P6-E09 | Very long pasted text | UI may truncate display; API enforces cap (Phase 5) | Medium |
| P6-E10 | User message contains HTML/script | Render as escaped text; no `innerHTML` with raw input | Critical |

## API integration

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P6-E11 | `POST /api/chat` network failure | Show neutral error; allow retry; no fake answer | High |
| P6-E12 | API returns 503 (index down) | “Assistant unavailable” message | High |
| P6-E13 | API returns 500 | Generic error; do not expose stack trace | High |
| P6-E14 | API slow (>30s) | Loading indicator; optional timeout message | Medium |
| P6-E15 | Malformed JSON response | Error state; log client-side for debug | High |
| P6-E16 | `source_url` null on factual answer | Show answer without link + log error; prefer fix in API | High |
| P6-E17 | `source_url` invalid URL string | Do not render broken link; show plain text URL | Medium |

## Rendering answers

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P6-E18 | Answer >3 sentences (API bug) | Display as returned but flag in QA; validator should prevent | Medium |
| P6-E19 | Multiple links in markdown answer | UI shows primary `source_url` field; strip extras in display optional | Medium |
| P6-E20 | `last_updated` footer line | Render verbatim below answer | High |
| P6-E21 | Refusal styled as error (red alert) | Neutral informational styling per architecture | Medium |
| P6-E22 | Refusal includes external AMFI/SEBI link | Open in new tab; `rel="noopener noreferrer"` | Low |
| P6-E23 | Long URL overflows mobile layout | `word-break` / wrap on link | Low |

## Accessibility & layout

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P6-E24 | Keyboard-only navigation | Send on Enter; focus management after reply | Medium |
| P6-E25 | Screen reader on disclaimer | Disclaimer in landmark; announced on load | Low |
| P6-E26 | Chat history grows unbounded | Scroll container; optional clear chat | Low |
| P6-E27 | Landscape phone: input hidden by keyboard | Scroll input into view on focus | Medium |

## Bootstrap failures

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P6-E28 | `/api/examples` fails on page load | Use static Phase 0 examples; chat still works | High |
| P6-E29 | Wrong API base URL in dev build | Document env var; clear console error | Medium |
| P6-E30 | Mixed content (HTTPS page, HTTP API) | Blocked by browser; use HTTPS API | High |

## Compliance UX

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P6-E31 | User thinks bot is human advisor | Welcome states facts-only, no advice | High |
| P6-E32 | Copy answer without source | Source link still visible in UI; encourage verification | Low |
| P6-E33 | Print view hides disclaimer | Include disclaimer in print CSS | Low |
