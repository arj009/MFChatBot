# Phase 1 — Corpus Curation: Edge Cases

**Reference:** [Phase 1 in PhaseWiseArchitecture.md](../PhaseWiseArchitecture.md#phase-1--corpus-curation)

---

## Inventory integrity

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P1-E01 | CSV has 31 rows (extra URL added during validation) | Reject file; remove extra row; count must be 30 | Critical |
| P1-E02 | CSV missing filter listing (#9) | Incomplete corpus; restore Phase 0 row #9 | Critical |
| P1-E03 | `status=pending` rows remain at Phase 1 exit | All 30 must be `approved` or ingestion blocked | High |
| P1-E04 | URL in CSV not byte-identical to Phase 0 table | Fix to locked URL; no “helpful” URL cleanup | High |
| P1-E05 | Validator script uses domain allowlist only | Must use **exact URL list**; other `groww.in` pages still rejected | Critical |

## Reachability & HTTP

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P1-E06 | HTTP 403 / 401 from Groww (bot protection) | Log failure; retry with backoff/User-Agent policy; document manual fetch fallback | High |
| P1-E07 | HTTP 429 rate limit | Throttle validation; stagger requests; do not skip URLs silently | High |
| P1-E08 | HTTP 301/302 redirect to URL **not** in inventory | Mark failed; do not auto-follow to off-list destination | Critical |
| P1-E09 | Redirect to same page with different query string | Accept only if final URL matches inventory after normalization | High |
| P1-E10 | Timeout / connection reset for one of 30 URLs | Record per-URL failure; block Phase 2 until resolved or documented waiver | High |
| P1-E11 | HTTP 200 but body is CAPTCHA or “access denied” | Treat as unreachable content; flag for manual review | High |

## Content & scheme mapping

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P1-E12 | Page title scheme name ≠ inventory `scheme_name` | Update metadata to match on-page title; keep URL unchanged | Medium |
| P1-E13 | Groww renamed fund; slug URL still works | Update `scheme_name` only; URL stays locked | Medium |
| P1-E14 | Slug URL returns 404 (fund merged/closed) | Escalate—requires Phase 0 URL change, not substitute URL | Critical |
| P1-E15 | AMC filter page loads but lists other fund houses | Verify filter query; fail if house ≠ ICICI Prudential | High |
| P1-E16 | Key facts missing on page (no expense ratio visible) | Flag `content_gap`; still approve URL but note for Phase 2/7 tests | Medium |
| P1-E17 | “Regular Income” slug shows typo `i-come` in URL | Accept locked URL; map display name correctly in metadata | Low |

## Metadata completeness

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P1-E18 | `source_type` wrong (listing marked `scheme_page`) | Correct to `amc_listing` for row #9 only | Medium |
| P1-E19 | `scheme_slug` null for scheme pages | Derive from URL path before Phase 2 | High |
| P1-E20 | `last_reviewed` missing | Block exit criteria until all 30 dated | Medium |
| P1-E21 | Duplicate `scheme_slug` across two rows | Impossible if URLs unique—investigate duplicate URLs | Critical |

## Operational

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P1-E22 | Validator run from CI without network | Use cached reachability report or skip with explicit `network_required` gate | Medium |
| P1-E23 | Partial validation (15/30) deemed “good enough” | Not allowed—all 30 required per exit criteria | Critical |
| P1-E24 | `sources.json` out of sync with CSV | Regenerate from CSV in single script | High |
