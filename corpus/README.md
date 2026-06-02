# Corpus (Phase 0)

| File | Purpose |
|------|---------|
| `scope.yaml` | Locked AMC, corpus policy, UI examples, metadata schema |
| `url_inventory.csv` | **Exactly 30** approved Groww URLs (source of truth) |
| `sources.json` | Machine-readable mirror for ingestion (regenerate via `scripts/sync_sources_json.py`) |

| `curation_report.json` | Phase 1 reachability and content check results |

**Phase 0:** `py -3 scripts/validate_phase0.py`  
**Phase 1:** `py -3 scripts/curate_corpus.py` then `py -3 scripts/validate_phase1.py`
