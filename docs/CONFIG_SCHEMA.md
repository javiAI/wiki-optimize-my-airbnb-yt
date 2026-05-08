# Configuration Schema

## Overview

`.claude/wikiforge/config.yaml` holds vault selection, language choice, and retrieval backend configuration. Plugin distribution ships `.claude/templates/config.yaml.example` — copy it to `.claude/wikiforge/config.yaml` and edit. The live file is gitignored. Pre-migration `.claude/config/config.yaml` is still read as a fallback.

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

## Phase 2 — LLM Backend (Currently Implemented)

**Status**: IMPLEMENTED — LLM is available as primary backend or fallback

### `retrieval.llm.enabled` (bool)
- **Used by**: retrieve.py (backend selection logic)
- **Value**: `false` (default) or `true` to use LLM
- **What it does**: Enables LLM as primary backend for retrieval
- **Current model**: claude-haiku (hardcoded, cannot be selected via config yet)
- **Cost**: ~$0.00011 per query (~$110/year for 1M queries)
- **Latency**: ~1100ms per query (vs 50ms for BM25)

### `retrieval.llm.fallback.enabled` (bool)
- **Used by**: retrieve.py (when backend is "bm25")
- **Value**: `false` (default) or `true` to enable fallback mode
- **What it does**: Uses BM25 as primary, but calls LLM when BM25 is ambiguous
- **When to use**: Want BM25 speed for clear queries, LLM for ambiguous ones

### `retrieval.llm.fallback.trigger` (string)
- **Used by**: retrieve.py (fallback decision)
- **Current value**: `"bm25_confidence"`
- **Options**: `"bm25_confidence"` (only), future: `"always"`
- **What it does**: Triggers LLM only when BM25 is unsure

### `retrieval.llm.fallback.threshold` (float)
- **Used by**: retrieve.py (confidence ratio calculation)
- **Current value**: 1.5
- **Range**: 1.0 to 3.0
- **What it does**: Ratio of top1_score / top2_score
  - If ratio < threshold: BM25 was ambiguous → call LLM
  - If ratio >= threshold: BM25 was confident → use BM25 result
- **Lower threshold**: More likely to trigger LLM (costs more tokens)
- **Higher threshold**: Fewer LLM calls (saves tokens, lower quality on ambiguous queries)

**Example fallback behavior**:
```
Query: "¿Es buena idea aceptar mascotas?"
BM25 results:
  #1: outdoor-spaces (score: 9.5)
  #2: allow-pets (score: 4.9)
  Ratio: 9.5 / 4.9 = 1.94

threshold: 1.5
1.94 >= 1.5 → confident → use BM25, no LLM call
Cost: $0, latency: 50ms

---

Query: "me roban los huéspedes"
BM25 results:
  #1: listing-security (score: 3.2)
  #2: background-check (score: 2.8)
  Ratio: 3.2 / 2.8 = 1.14

threshold: 1.5
1.14 < 1.5 → ambiguous → call LLM for better retrieval
Cost: $0.00011, latency: 1100ms
```

**Model selection**: Currently hardcoded to claude-haiku. Dynamic model selection via config is a future enhancement (requires changes to retrieve.py and /query skill to read and pass `--model` parameter).

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

### State / config split

Runtime state (`active_vault`, `active_lang`) lives in
`.claude/state/wikiforge.yaml` (gitignored, mutates per query). User prefs and
library config (`defaults`, `retrieval`, `regimes`, `evaluation`) live in
`.claude/wikiforge/config.yaml` (committable). `defaults:` is consulted only by
`/init-vault` — runtime scripts read `vault.yml` directly.

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

- `.claude/wikiforge/config.yaml` — Active configuration file
- `docs/PHASE_*.md` — Implementation roadmaps for each phase
- `.claude/scripts/retrieve.py` — Reads and uses these config values
