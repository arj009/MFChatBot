# MFChatBot: ICICI Prudential Mutual Fund Assistant

A highly specialized, compliant, and **facts-only** Retrieval-Augmented Generation (RAG) assistant designed to answer factual queries about mutual fund schemes of **ICICI Prudential Mutual Fund**, utilizing **Groww** as the strict reference context.

## ⚠️ Disclaimer
**Facts-only. No investment advice.**
This system provides factual details retrieved exclusively from approved scheme pages on Groww. It does not provide financial advice, recommendations, performance projections, or fund comparisons. Always consult a certified financial advisor before making investment decisions.

---

## 🏗️ Architecture Summary

The system is a strict **linear pipeline** over a **closed set of 30 Groww URLs**. It enforces compliance across 4 deep layers:
1. **Curated Ingestion**: Crawls and chunks exactly 30 approved URLs. Parses Next.js structural data to avoid HTML selector fragility.
2. **Semantic Vector Search**: Uses local `sentence-transformers` embedded into a Chroma vector database with metadata filtering to prevent cross-fund context leakage.
3. **Intent Classification & Routing**: A hybrid Regex/LLM classifier sweeps for PII risks and routes user queries to `FACTUAL`, `ADVISORY` (deflected), `COMPARATIVE` (deflected), or `PERFORMANCE_CALC` (redirected to factsheet).
4. **Constrained Generation**: Uses Groq's `llama3-70b-8192` model at `temperature=0.0`. Validates the output to ensure a maximum of 3 sentences, exactly one citation link, and appends a freshness date footer.

---

## 🚀 Setup & Execution

### Prerequisites
- Python 3.11+
- Groq Cloud API Key (`https://console.groq.com/keys`)

### 1. Install Dependencies
```bash
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
Rename `.env.example` to `.env` and add your Groq API key:
```env
GROQ_API_KEY=your_key_here
```

### 3. Run the Backend API
Start the FastAPI orchestration layer:
```bash
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Run the Frontend UI
In a separate terminal, serve the minimal chat interface:
```bash
cd frontend
python -m http.server 3000
```
Visit `http://localhost:3000` in your browser.

---

## 📂 Scope: Included Schemes (AMC)
The chatbot restricts its knowledge strictly to the following target AMC: **ICICI Prudential Mutual Fund**.
Data is securely fetched from the Groww URL inventory located in `corpus/url_inventory.csv`.

---

## 🚧 Known Limitations
- **Stale Factsheets**: The data freshness relies on the latest automated ingestion pipeline run. Fast-changing metrics (like daily NAV) may experience slight latency based on the synchronization cron schedule.
- **Table Parsing Gaps**: Complex nested tables inside PDFs/Scheme Information Documents (SIDs) are not fully supported for zero-shot text retrieval at this time.
- **Scheme Name Ambiguity**: Users typing extremely generic acronyms that overlap with multiple funds may experience fuzzy-matching ambiguity.

---

## ✅ Test Suite
The project contains 67+ comprehensive Pytest cases validating compliance, extraction, orchestration, and deduplication.
Run them locally via:
```bash
python -m pytest
```
