# Configuration Schema

## Overview

`.claude/config/config.yaml` holds vault selection, language choice, and retrieval backend configuration.

**Key principle**: Only fields that are **actually read and used** by scripts are documented as active. Future phases are commented out. This prevents confusion between "declared intention" and "working implementation."

---

## Current (Phase 1) — BM25 Retrieval

### `active_vault` (string)
- **Used by**: config.py, all scripts that need vault resolution
- **Example**: `oma-test-1`
- **What it does**: Tells all scripts which vault bundle to operate on
- **Set by**: `init-vault.sh`, `set-config.sh active_vault <name>`

### `active_lang` (string)
- **Used by**: retrieve.py (as fallback), query routing
- **Example**: `es` or `en`
- **What it does**: Default language when auto-detection fails
- **Set by**: `init-vault.sh`, `set-config.sh active_lang <lang>`

### `retrieval.backend` (string)
- **Used by**: retrieve.py (line 277: `backend = cfg.get("retrieval.backend", "bm25")`)
- **Current options**: `"bm25"` (only option implemented)
- **Future options**: `"llm"`, `"embeddings"`, `"hybrid"`
- **What it does**: Selects which retrieval algorithm to use
- **Default**: `"bm25"`

### `retrieval.bm25.enabled` (bool)
- **Used by**: retrieve.py (guard check)
- **Value**: `true` when backend is `"bm25"`
- **What it does**: Validates backend is in sync

### `retrieval.bm25.topic_boost` (float)
- **Used by**: retrieve.py line 34 (TF-IDF scoring)
- **Range**: 1.0 to 10.0
- **Current value**: 3.0
- **What it does**: Multiplier when query token matches an atom's `topics` field
- **Effect**: Higher value → topic matches rank higher relative to body matches
- **Session 2 change**: Increased from 2.0 to 3.0 after evaluating "mascotas" query

### `retrieval.bm25.claim_boost` (float)
- **Used by**: retrieve.py line 35 (TF-IDF scoring)
- **Range**: 1.0 to 5.0
- **Current value**: 2.0
- **What it does**: Multiplier when query term matches atom's `claim` field (vs body)
- **Effect**: Higher value → claims are weighted heavier than body text
- **Session 2 change**: Increased from 1.5 to 2.0

---

## Future (Phase 2) — LLM Fallback

**Status**: NOT IMPLEMENTED — this section is aspirational

When implemented, these fields will control LLM-based fallback routing:

```yaml
retrieval:
  llm:
    enabled: false
    model: "claude-haiku"      # Actual model selection
    trigger_type: "bm25_confidence"
    threshold: 1.5  # ratio(top1 / top2)
```

**Implementation notes**:
- `model` field is **informational only** until retrieve.py explicitly reads and passes it
- Query: "Sí, pero ¿cómo garantizamos que se use?"
  - Answer: The calling script (retrieve.py or /query skill) must explicitly pass `--model` to the LLM invocation
  - We'll add validation in retrieve.py to check if the model is available before using it
  - If model is invalid, fail loud (don't silently use default)

---

## Future (Phase 3) — Embeddings

**Status**: NOT IMPLEMENTED — this section is placeholder

```yaml
retrieval:
  embeddings:
    enabled: false
    model: "distiluse-base-multilingual-cased-v2"
    storage_type: "memory"  # Options: memory, faiss, disk
    min_similarity: 0.4
    auto_rebuild: true
    rebuild_threshold: 10
```

**Why commented out now**:
- Phase 1 (current) is BM25 only
- Phase 2 will add LLM fallback
- Phase 3 will add embeddings as primary backend
- When each phase ships, uncomment its section

---

## How to Add a New Backend

### Step 1: Declare in config.yaml (commented)

```yaml
retrieval:
  backend: embeddings  # When ready, uncomment and change value

  embeddings:
    enabled: false
    model: "distiluse-base-multilingual-cased-v2"
    # ... other params
```

### Step 2: Update retrieve.py to read config

```python
backend = cfg.get("retrieval.backend", "bm25")  # Already does this
if backend == "embeddings":
    embeddings_config = cfg.get("retrieval.embeddings", {})
    model = embeddings_config.get("model")
    # Use model here
```

### Step 3: Implement backend class

```python
class EmbeddingBackend:
    def __init__(self, config):
        self.model_name = config.get("model")
        self.min_similarity = config.get("min_similarity", 0.4)
        # ...

    def score(self, query: str, top_k: int = 6) -> list:
        # Return [(score, stem), ...]
```

### Step 4: Wire into retrieve.py

```python
if backend == "embeddings":
    index = EmbeddingBackend(cfg.get("retrieval.embeddings"))
    ranked = index.score(query, top_k)
```

### Step 5: Test, then uncomment in config.yaml

Once working, uncomment the section and set `backend: embeddings`.

---

## Migration Notes

### From state.yaml → config.yaml

The old `state.yaml` at `.claude/state/state.yaml` is now legacy. The migration is:

- **Read order**: config.yaml → state.yaml → active-vault (backward compatible)
- **Write order**: All writes go to config.yaml (forward compatible)
- **Deprecation**: state.yaml files will be ignored once all users migrate

Set active vault/lang via:
```bash
bash .claude/scripts/set-config.sh active_vault oma-test-1
bash .claude/scripts/set-config.sh active_lang es
```

---

## Score Clarification

**Q**: "How is the confidence score calculated? Is it reliable?"

**A**: BM25 score is NOT a confidence probability. It's a **relative relevance ranking**:

```
score = Σ(IDF × TF_normalized) for each query term in document

IDF = log((n_docs - df + 0.5) / (df + 0.5))
TF_normalized = (tf × (K1 + 1)) / (tf + K1 × (1 - B + B × dl/avgdl))
```

**What it guarantees**: Among the indexed atoms, these are the highest-scoring matches.

**What it does NOT guarantee**: 
- That these are the objectively "best" atoms (only the highest TF-IDF)
- That no better atom exists outside the index
- Semantic understanding (just keyword matching)

**Limitations with 1M atoms**:
- Still O(n) if no index (we use in-memory index)
- With FAISS indexing, it becomes O(log n) retrieval
- Trade-off: embeddings give true semantic ranking but cost tokens

---

## Testing the Config

Validate that config.yaml is correctly parsed:

```bash
python3 .claude/scripts/config.py --validate
```

Output:
```
[OK] vault.yml valid — oma-test-1 (es, en)
```

Get backend config:
```bash
python3 .claude/scripts/config.py --json | jq '.retrieval'
```

---

## See Also

- `.claude/config/config.yaml` — Active configuration file
- `docs/PHASE_*.md` — Implementation roadmaps for each phase
- `.claude/scripts/retrieve.py` — Reads and uses these config values
