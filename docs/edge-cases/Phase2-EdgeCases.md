# Phase 2 — Ingestion & Document Store: Edge Cases

**Reference:** [Phase 2 in PhaseWiseArchitecture.md](../PhaseWiseArchitecture.md#phase-2--ingestion--document-store)

---

## Closed-list fetcher

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P2-E01 | Ingest script passed URL not in `url_inventory.csv` | Abort fetch; log `CLOSED_CORPUS_VIOLATION`; exit non-zero | Critical |
| P2-E02 | Inventory URL with trailing slash; fetcher normalizes differently | Single normalization function shared with Phase 1 | Critical |
| P2-E03 | Crawler follows relative links to other Groww funds | Do not follow off-list links; ingest only seed URL body | Critical |
| P2-E04 | Batch job ingests 30 + discovers links | Zero chunks with `source_url` outside inventory | Critical |
| P2-E05 | Manual rerun on one URL creates duplicate chunks without dedup | Upsert by `(source_url, chunk_id)` or rebuild store | High |

## Fetch & parse failures

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P2-E06 | JavaScript-heavy page; static HTML empty | Detect low text yield; log warning; optional headless fallback (still same URL) | High |
| P2-E07 | HTML parser strips tables containing exit load / expense ratio | Tune parser rules; spot-check per scheme | High |
| P2-E08 | Page encoding not UTF-8 | Detect encoding; avoid mojibake in chunks | Medium |
| P2-E09 | Inflated HTML (nav, footer, cookie banners) | Normalizer removes boilerplate; factual sections retained | Medium |
| P2-E10 | One of 30 URLs fails; other 29 succeed | Continue with logged failure; Phase 2 exit blocked until 30/30 or documented waiver | High |
| P2-E11 | Empty `text` after parse | No chunk emitted; flag URL in ingest report | High |

## Chunking & metadata

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P2-E12 | Very long page → 100+ tiny chunks | Cap chunks per URL or merge small sections; keep `source_url` on all | Medium |
| P2-E13 | Chunk spans two schemes (listing page) | Listing chunks: `scheme_name: null`; no mixed scheme metadata | High |
| P2-E14 | Chunk missing `source_url` or `source_type` | Reject chunk write; fail validation step | Critical |
| P2-E15 | `content_hash` identical but visible text changed (CDN cache) | Optional raw HTML diff; prefer re-fetch with cache-bust headers | Medium |
| P2-E16 | Overlap causes duplicate factual sentences in adjacent chunks | Acceptable for RAG; dedupe at retrieval (Phase 3) | Low |
| P2-E17 | Token limit splits mid-table (expense ratio row split) | Prefer heading-boundary splits; include header row in both chunks if needed | High |

## AMC listing page (#9)

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P2-E18 | Listing chunks dominate retrieval for scheme-specific queries | Tag `source_type: amc_listing`; down-rank or filter in Phase 3 | High |
| P2-E19 | User question “list all ICICI funds” | May answer from listing chunks only; cite filter URL | Medium |
| P2-E20 | Listing page content changes (fund count) | `content_hash` updates; footer dates refresh on re-ingest | Low |

## Re-ingestion & storage

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P2-E21 | Re-ingest adds 31st URL because “content updated” | URL list unchanged; only refresh 30 | Critical |
| P2-E22 | `data/raw/` contains HTML for non-inventory URL | Delete artifact; audit ingest script | High |
| P2-E23 | `chunk_store.jsonl` corrupted mid-write | Atomic write (temp file + rename) | Medium |
| P2-E24 | Parallel ingest workers race on same output file | File lock or per-URL shards merged deterministically | Medium |

## Privacy

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P2-E25 | Ingest logs accidentally include user query (should not exist in Phase 2) | Batch-only logs; no user PII in ingest pipeline | Low |
| P2-E26 | Cached HTML contains session cookies from manual browser save | Strip cookies; do not commit secrets to `data/raw/` | High |
