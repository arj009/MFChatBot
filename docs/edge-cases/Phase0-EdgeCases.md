# Phase 0 — Foundation & Planning: Edge Cases

**Reference:** [Phase 0 in PhaseWiseArchitecture.md](../PhaseWiseArchitecture.md#phase-0--foundation--planning)

---

## Closed corpus & URL inventory

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P0-E01 | Team proposes adding a 31st Groww scheme URL | Reject; update Phase 0 architecture table first, then re-export inventory | Critical |
| P0-E02 | `url_inventory.csv` has 29 or 31 rows | Block Phase 1 exit; enforce **exactly 30** rows | Critical |
| P0-E03 | Same URL listed twice with different `#` | Deduplicate before export; one row per canonical URL | Critical |
| P0-E04 | URL differs only by trailing `/` or `http` vs `https` | Normalize to canonical form in inventory; document normalization rules | High |
| P0-E05 | Request to ingest another ICICI scheme on Groww not in the table | Out of scope; closed corpus—refuse ingestion design | Critical |
| P0-E06 | Request to add AMC factsheet / AMFI / SEBI to RAG corpus | Deny for ingestion; AMFI/SEBI allowed **only** in refusal templates | Critical |
| P0-E07 | Filter URL (#9) treated as a scheme page in examples | `source_type: amc_listing`, `scheme_name: null`; examples use scheme pages #3, #22, #19 | Medium |

## URL encoding & slugs

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P0-E08 | PHD fund URL contains `(p.h.d)` and encoded characters | Store exact URL from Phase 0 table; ingestion must match encoded form | High |
| P0-E09 | Filter URL query string encoded differently (`%22` vs `"`) | Pick one canonical string in inventory; fetcher normalizes before match | High |
| P0-E10 | `scheme_slug` derived incorrectly from URL (typo: `i-come` vs `income`) | Slug matches path segment in locked URL, not display name | Medium |
| P0-E11 | Two schemes share similar slugs (e.g. Nifty vs Nifty IT vs Nifty Next 50) | Distinct `scheme_name` and slug per row; document in synonym map | High |

## Metadata & scope registry

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P0-E12 | Missing required metadata field in schema | Validation fails at export; no partial `scope.yaml` | High |
| P0-E13 | `scope.yaml` AMC name inconsistent with inventory | Single source of truth: ICICI Prudential Mutual Fund everywhere | Medium |
| P0-E14 | Golden test references HDFC / SBI / scheme outside 30 URLs | Rewrite test to one of 30 schemes or mark `OUT_OF_SCOPE` | High |
| P0-E15 | Golden test asks ELSS lock-in but no ELSS in corpus | Expect abstention/refusal—not AMFI/SID link from outside corpus | High |
| P0-E16 | UI example question points to scheme not in inventory | Examples must use Large Cap (#3), Flexicap (#22), Liquid (#19) only | Medium |

## Compliance & taxonomy

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P0-E17 | Refusal taxonomy missing `PERFORMANCE_CALC` or `PII_RISK` | Document all labels from architecture before Phase 4 | High |
| P0-E18 | Educational link placed in `url_inventory.csv` | Remove from corpus file; keep in `config/educational_links.yaml` only | Critical |
| P0-E19 | Performance policy says “official factsheet” (off-corpus) | Policy: link to matching Groww scheme page from 30 URLs | Medium |
| P0-E20 | Conflicting rules: Problem Statement (AMC sources) vs closed Groww corpus | README/architecture note: **this project** uses closed Groww list only | Medium |

## Deliverables & handoff

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P0-E21 | `corpus/sources.json` contains URLs not in CSV | `sources.json` must mirror CSV exactly (30 URLs) | High |
| P0-E22 | Phase 0 exit marked complete without `url_inventory.csv` | Do not start Phase 2 ingestion | High |
| P0-E23 | Stakeholder asks to “swap” one URL without doc update | Formal Phase 0 revision + full re-ingest and re-index | Medium |
