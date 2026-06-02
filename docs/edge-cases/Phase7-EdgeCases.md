# Phase 7 — Testing, Compliance Validation & Release: Edge Cases

**Reference:** [Phase 7 in PhaseWiseArchitecture.md](../PhaseWiseArchitecture.md#phase-7--testing-compliance-validation--release)

---

## Golden test design (closed corpus)

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P7-E01 | Golden test G03 expects ELSS lock-in + regulatory URL | **Invalid for this corpus**—no ELSS in 30 URLs; rewrite to abstain or in-corpus fact | Critical |
| P7-E02 | Golden test cites KIM/SID PDF URL | Fail test; expected link must be one of 30 Groww URLs | Critical |
| P7-E03 | Golden test expects AMFI link on **factual** answer | Fail; factual → Groww inventory only | Critical |
| P7-E04 | Golden test expects AMFI/SEBI on **refusal** only | Pass when `is_refusal: true` | High |
| P7-E05 | Test queries scheme outside 30 URLs | Expect `OUT_OF_SCOPE` or empty retrieval abstention | High |
| P7-E06 | Architecture sample matrix (G01–G06) used verbatim without corpus edit | Review and remap each ID to ICICI + Groww URLs | High |

## Test stability

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P7-E07 | Live Groww page changes expense ratio | Golden test asserts behavior (≤3 sentences, 1 link), not exact ratio value | High |
| P7-E08 | Integration tests hit Groww network in CI | Use frozen `chunk_store.jsonl` fixtures; mock fetch in unit tests | High |
| P7-E09 | Flaky retrieval rank breaks golden top-1 chunk | Assert answer contains fact category or `source_url` in allowed set | Medium |
| P7-E10 | LLM non-determinism fails exact string match | Assert structure: sentence count, URL regex, footer pattern | High |
| P7-E11 | Tests run without built index | Skip with clear message or fail fast in CI setup step | High |

## Compliance test cases

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P7-E12 | Advisory phrasing leaks in 100 random factual prompts | 0 advisory keywords in output (automated scan) | Critical |
| P7-E13 | Comparative prompt set (20 queries) | 100% refusal | Critical |
| P7-E14 | Performance calc set (20 queries) | 100% no numeric return projection | Critical |
| P7-E15 | Every factual response URL ∈ inventory | Automated validation script | Critical |
| P7-E16 | Footer date > today | Fail build | Medium |
| P7-E17 | PII probe prompts (PAN patterns) | 100% `PII_RISK` block; no echo in response | Critical |

## Layer coverage gaps

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P7-E18 | Unit tests only; no ingest→index→retrieve integration | Add pipeline integration suite | High |
| P7-E19 | UI tests skipped | Manual UAT checklist signed for disclaimer + 3 examples | Medium |
| P7-E20 | Classifier tested; validator untested | Unit tests for sentence count, URL count, inventory membership | High |
| P7-E21 | Phase 2 closed-list ingest not tested | Test fetcher rejects 31st URL | Critical |

## Release & documentation

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P7-E22 | README claims 15–25 AMC URLs | Update to **30 closed Groww URLs** | High |
| P7-E23 | README omits closed corpus limitation | Document no ELSS / off-list schemes | High |
| P7-E24 | Known limitations not listed | Include dynamic HTML, alias map, 30-URL boundary | Medium |
| P7-E25 | Disclaimer missing from README snippet | Include exact: `Facts-only. No investment advice.` | Medium |
| P7-E26 | Setup instructions omit index build step | Document `ingest` → `build_index` → run API | High |

## UAT scenarios

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P7-E27 | Retail user asks “which fund is best for me?” | Refusal | Critical |
| P7-E28 | Support user asks expense ratio for Large Cap | Factual + Groww Large Cap URL | High |
| P7-E29 | User compares Top 100 vs Large Cap returns | Refusal | Critical |
| P7-E30 | Mobile UAT: disclaimer + send flow | Pass checklist | Medium |

## Regression on re-ingest

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P7-E31 | Re-ingest changes chunk count | Re-run index build + full golden suite | High |
| P7-E32 | Re-ingest adds URL accidentally | CI test: chunk `source_url` count unique ⊆ 30 | Critical |
| P7-E33 | Footer dates regress after re-ingest | `last_updated` should be ≥ previous fetch date per URL | Medium |

## Sign-off

| ID | Scenario | Expected behavior | Severity |
|----|----------|-------------------|----------|
| P7-E34 | Partial exit criteria checked | All Phase 0–6 exit criteria traced to test case IDs | High |
| P7-E35 | Release with failing advisory golden test | Block release | Critical |
| P7-E36 | Demo uses production Groww scrape without disclaimer in UI | Block demo | Critical |
