# Phase 3 — Indexing & Retrieval (RAG Core): Edge Cases

**Reference:** [Phase 3 in PhaseWiseArchitecture.md](../PhaseWiseArchitecture.md#phase-3--indexing--retrieval-rag-core)

---

## Index build & reproducibility

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P3-E01 | Index built from `chunk_store.jsonl` missing chunks for failed URL | Detect orphan index; require 30/30 source URLs represented | High |
| P3-E02 | Rebuild index after ingest without re-embed | Full rebuild from latest chunks; version index artifact | High |
| P3-E03 | Embedding model changed between build and query | Version mismatch error; refuse retrieval until rebuild | Critical |
| P3-E04 | Empty vector index (zero chunks) | `build_index` fails; API returns 503 on chat | Critical |
| P3-E05 | Non-deterministic chunk order → different index IDs | Sort chunks by `(source_url, chunk_index)` before embed | Medium |

## Query & scheme disambiguation

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P3-E06 | Query names scheme **not** in 30 URLs (e.g. “HDFC Flexi Cap”) | No match; empty or low scores; Phase 5 abstention path | High |
| P3-E07 | Ambiguous “ICICI large cap” — Large Cap (#3) vs Top 100 (#27) | Prefer keyword/synonym map; if tie, return top-3 from both with generator disambiguation | High |
| P3-E08 | “Nifty fund” — Nifty 50 (#21) vs Nifty IT (#12) vs Nifty Next 50 (#7) | Scheme hint from “IT”, “Next 50”, etc. | High |
| P3-E09 | “Retirement fund” — Hybrid Aggressive (#8) vs Pure Equity (#17) | Require plan name in query or return clarification abstention | High |
| P3-E10 | “Balanced” — Balanced (#25) vs Balanced Advantage (#15) | Synonym map must distinguish | High |
| P3-E11 | Query mentions only “ICICI Prudential” | May retrieve listing (#9); avoid wrong scheme citation | Medium |
| P3-E12 | Typo in scheme name (“Flexi cap” vs “Flexicap”) | Fuzzy match against 30 `scheme_name` values | Medium |

## Retrieval quality

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P3-E13 | All similarity scores below threshold | Return empty list; trigger Phase 5 empty-retrieval handler | High |
| P3-E14 | Top-k all from `amc_listing` for scheme-specific fact | Apply metadata filter to prefer `scheme_page` | High |
| P3-E15 | Same `source_url` fills top-k (duplicate chunks) | Deduplicate; keep highest score per URL | Medium |
| P3-E16 | Correct fact in chunk ranked below k | Increase k or add reranker; golden test failure → tune | Medium |
| P3-E17 | Query “expense ratio” retrieves exit-load chunk (same page) | Acceptable if same `source_url`; answer must still be factual | Low |
| P3-E18 | Cross-scheme contamination (Midcap chunk for Large Cap query) | `scheme_name` filter when hint present | High |

## Query form & language

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P3-E19 | One-word query: “exit load?” | Embed full query; may need scheme from session/context—UI examples provide scheme | Medium |
| P3-E20 | Very long query (>2k chars) | Truncate before embed at API layer (Phase 5) | Medium |
| P3-E21 | Hinglish / Hindi scheme question | Embedding may still retrieve English chunks; abstain if low confidence | Medium |
| P3-E22 | Query includes PII (PAN) with factual ask | Classified Phase 4 `PII_RISK` before retrieval preferred | High |

## Performance & ops

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P3-E23 | Retrieval latency >2s on CPU | Reduce k, smaller embedding model, or warm index | Low |
| P3-E24 | `top_k` = 50 floods LLM context | Cap passages to 3–5 for generator per architecture | High |
| P3-E25 | Index file locked during rebuild while API serves traffic | Blue/green index swap or read-only mode during build | Medium |

## Closed corpus alignment

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P3-E26 | Chunk in store with `source_url` not in inventory (legacy data) | Exclude from index build; log and delete orphan chunks | Critical |
| P3-E27 | Retriever returns chunk URL with UTM params appended | Strip to canonical inventory URL before citation | High |
