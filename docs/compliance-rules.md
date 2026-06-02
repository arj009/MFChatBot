# Compliance Rules — Query Classification & Response Policy

Phase 0 deliverable. Governs Phase 4 guardrails and Phase 7 golden tests.

**Corpus:** Exactly 30 Groww URLs in `corpus/url_inventory.csv` (closed). Factual answers cite **only** those URLs. AMFI/SEBI links appear **only** in refusal responses (`config/educational_links.yaml`).

---

## Classifier labels

| Label | Description | Pipeline action |
|-------|-------------|-----------------|
| `FACTUAL` | Objective question answerable from scheme page content | Retrieve → generate → validate |
| `ADVISORY` | Investment advice, suitability, “should I”, “good fund” | Refusal template |
| `COMPARATIVE` | Which fund is better, vs, ranking funds | Refusal template |
| `PERFORMANCE_CALC` | Projected returns, CAGR forecasts, “what will X become” | Scheme page link only; no numbers |
| `OUT_OF_SCOPE` | Not mutual funds / not in corpus / unrelated | Refusal + educational link |
| `PII_RISK` | PAN, Aadhaar, account, OTP, email, phone in message | Block; privacy message; no storage |

---

## Rule-based signals (indicative)

### ADVISORY

- should i invest, should i buy, is it good, worth investing, recommend, suggest, advice, suitable for me

### COMPARATIVE

- which is better, better than, vs , versus, compare, comparison, rank, best fund

### PERFORMANCE_CALC

- will become, in 5 years, projected, expected return, calculate return, CAGR, SIP return calculator, how much will i get

### PII_RISK

- PAN patterns, Aadhaar, account number, OTP, `@` email patterns, 10-digit phone patterns

### FACTUAL (examples)

- expense ratio, exit load, minimum sip, lock-in, riskometer, benchmark, download statement (if on page)

---

## Response contract (factual)

| Rule | Value |
|------|--------|
| Max sentences | 3 |
| Citation links | Exactly 1 |
| Citation URL | Must match `source_url` in closed inventory |
| Footer | `Last updated from sources: <YYYY-MM-DD>` |
| Footer date | `max(last_fetched_at)` of chunks used |

---

## Performance-query path

- Do not compute or state returns.
- One sentence pointing to scheme Groww page.
- One link: matching scheme from inventory (or best match from retrieval).
- Apply same footer rules.

---

## Refusal path

1. Polite acknowledgment  
2. State facts-only limitation (one sentence)  
3. One educational link from `config/educational_links.yaml` (not from RAG corpus)

No scheme-specific buy/hold/sell language in refusals.

---

## Content restrictions

- No investment advice or recommendations  
- No performance comparisons between funds  
- No return calculations or projections  
- Do not cite AMC/AMFI/SEBI URLs in **factual** answers (refusals only)

---

## Privacy

- Do not collect, store, or log PAN, Aadhaar, account numbers, OTP, email, or phone  
- Log query hashes or intent labels only where possible
