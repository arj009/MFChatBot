# Problem Statement: Mutual Fund FAQ Assistant (Facts-Only Q&A)

## Overview

Build a **facts-only** FAQ assistant for mutual fund schemes, using **Groww** as the reference product context. The assistant answers objective, verifiable questions by retrieving information **only** from official public sources—AMC (Asset Management Company) websites, AMFI, and SEBI.

The system must not provide investment advice, opinions, or recommendations. Every factual answer must include exactly one clear source link and follow defined rules for clarity, accuracy, and compliance.

---

## Objective

Design and implement a lightweight **Retrieval-Augmented Generation (RAG)** assistant that:

- Answers factual queries about mutual fund schemes
- Uses a curated corpus of official documents
- Returns concise, source-backed responses

---

## Target Users

- Retail investors comparing mutual fund schemes
- Customer support and content teams handling repetitive mutual fund queries

---

## Scope of Work

### 1. Corpus Definition

- Select **one** Asset Management Company (AMC)
- Choose **3–5** mutual fund schemes with category diversity (e.g., large-cap, flexi-cap, ELSS)
- Collect **15–25** official public URLs, including:
  - Scheme factsheets
  - KIM (Key Information Memorandum)
  - SID (Scheme Information Document)
  - AMC FAQ / help pages
  - AMFI / SEBI guidance pages
  - Statement and tax document download guides

### 2. FAQ Assistant Requirements

The assistant must answer **facts-only** queries, for example:

| Topic | Example query |
|-------|----------------|
| Costs | Expense ratio of a scheme |
| Redemption | Exit load details |
| Investment | Minimum SIP amount |
| Tax / lock-in | ELSS lock-in period |
| Risk | Riskometer classification |
| Benchmark | Benchmark index |
| Operations | How to download statements or capital gains reports |

**Response format (every factual answer):**

- Maximum **3 sentences**
- Exactly **one** citation link
- Footer: `Last updated from sources: <date>`

### 3. Refusal Handling

Refuse non-factual or advisory queries, for example:

- *“Should I invest in this fund?”*
- *“Which fund is better?”*

Refusal responses must:

- Be polite and explicit
- State the facts-only limitation
- Include one relevant educational link (e.g., AMFI or SEBI)

### 4. User Interface (Minimal)

Provide a simple UI with:

- A welcome message
- Three example questions
- A visible disclaimer: **“Facts-only. No investment advice.”**

---

## Constraints

### Data and Sources

- Use only official public sources (AMC, AMFI, SEBI)
- Do not use third-party blogs or aggregator sites

### Privacy and Security

Do not collect, store, or process:

- PAN or Aadhaar numbers
- Account numbers
- OTPs
- Email addresses or phone numbers

### Content Restrictions

- No investment advice or recommendations
- No performance comparisons or return calculations
- For performance-related questions, link to the official factsheet only—do not compute or compare returns

### Transparency

- Responses must be short, factual, and verifiable
- Every answer must include a source link and last-updated date

---

## Expected Deliverables

| # | Deliverable | Contents |
|---|-------------|----------|
| 1 | **README** | Setup instructions; selected AMC and schemes; RAG architecture overview; known limitations |
| 2 | **Disclaimer snippet** | `Facts-only. No investment advice.` |

---

## Success Criteria

- Accurate retrieval of factual mutual fund information
- Strict adherence to facts-only responses
- Consistent, valid source citations on every answer
- Correct refusal of advisory queries
- Clean, minimal, user-friendly interface

---

## Summary

Deliver a trustworthy, transparent, and compliant mutual fund FAQ assistant that prioritizes **accuracy over intelligence**. Users should receive only verified, source-backed information—never advisory bias or speculative content.
