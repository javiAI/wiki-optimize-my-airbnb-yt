---
automation:
  version: "3.1"
  current_phase: 1
  phase_status: "pending_approval"
  last_update: "2026-04-25T00:00:00Z"

phases:
  phase_1:
    name: "Critical Path"
    status: "pending_approval"
    tasks: [O1, O2, O3]
    completed: []
    progress: 0
  phase_2:
    name: "Quality Foundation"
    status: "not_started"
    tasks: [O3, O4, O5, O6]
    completed: []
    progress: 0
  phase_3:
    name: "Automation"
    status: "not_started"
    tasks: [O7, O8, O9]
    completed: []
    progress: 0
  phase_4:
    name: "Integration"
    status: "not_started"
    tasks: [O10, O11, O12]
    completed: []
    progress: 0

optimizations:
  O1: { name: "Hierarchical Indices", phase: 1, hours: 4, status: "pending_approval" }
  O2: { name: "Fix Q4 Contradiction", phase: 1, hours: 0.5, status: "pending_approval" }
  O3: { name: "Language Consistency", phase: 2, hours: 2, status: "not_started" }
  O4: { name: "Contradiction Detection L1", phase: 2, hours: 3, status: "not_started" }
  O5: { name: "Response Format Templates", phase: 2, hours: 2.5, status: "not_started" }
  O6: { name: "Executable Checklists", phase: 2, hours: 1.5, status: "not_started" }
  O7: { name: "Agent Orchestration", phase: 3, hours: 8, status: "not_started" }
  O8: { name: "Auto-Linking System", phase: 3, hours: 4, status: "not_started" }
  O9: { name: "Query Caching", phase: 3, hours: 6, status: "not_started" }
  O10: { name: "Semantic Gap Detection", phase: 4, hours: 3, status: "not_started" }
  O11: { name: "Backlink Generation", phase: 4, hours: 4, status: "not_started" }
  O12: { name: "RAG Fallback", phase: 4, hours: 6, status: "not_started" }

vault:
  name: "optimize-my-airbnb-yt"
  atoms: 156
  mocs: 12
  sources: 173
  quality_score: 8.52
  target_score: 9.8
---

## ROUTER — Autonomous Execution

**Phase 1 / pending_approval** — Waiting for user approval

**Action**: Show summary of Phase 1. To proceed, say: `Approve Phase 1`

Once approved, I will execute the cycle: **Baseline test → O1 → Test O1 → Compare → Decide → O2 → ...**

For each optimization:
1. Implement changes (per `docs/PHASE_X_TASKS.md`)
2. Git commit with `OX:` prefix
3. **Run test suite** (per `docs/TEST_PROTOCOL.md`):
   - `python3 scripts/run-test-suite.py --prepare --label OX`
   - Launch 20 Agent calls in PARALLEL (single tool_use response)
   - `python3 scripts/run-test-suite.py --consolidate --label OX`
   - `python3 scripts/run-test-suite.py --compare --from <prev> --to OX`
4. Read decision from `<VAULT>/meta/tests/optimizations/OX-comparison.json`:
   - **IMPLEMENT** → Update CLAUDE.md state, continue to next OX
   - **ITERATE** → Refine implementation, retry test
   - **REVERT** → `git revert HEAD`, mark as failed, continue to next OX

**Critical**: Tests use 20 fresh agents in parallel, no cache, no context. See `docs/TEST_PROTOCOL.md`.

---

**Before starting Phase 1**: Run baseline test once (establishes reference metrics).

```bash
python3 scripts/run-test-suite.py --prepare --label baseline
# Then: 20 parallel Agent calls
python3 scripts/run-test-suite.py --consolidate --label baseline
```

---

**How automation works**:
- Each session, I read this CLAUDE.md
- Router determines action based on `automation.phase_status`
- `pending_approval` → Show summary, wait for approval
- `in_progress` → Execute next task → test → decide → commit → repeat
- `complete` → Advance to next phase
- Hook in `.claude/settings.json` reminds me to run tests after each `OX:` commit

---

**See also**:
- `docs/PHASE_{{current_phase}}_SUMMARY.md` — What this phase accomplishes
- `docs/PHASE_{{current_phase}}_TASKS.md` — How to execute each task
- `docs/TEST_PROTOCOL.md` — **How to run parallel tests (read before testing)**
- `docs/TEST_FRAMEWORK.md` — Test framework theory
- `docs/ORCHESTRATOR.md` — Full orchestration design

---

# 0. Filosofía

Esto **no es RAG**. El LLM construye y mantiene una wiki persistente que se enriquece con cada fuente y pregunta.

- **Obsidian es el IDE**; **el LLM es el programador**; **la wiki es la codebase**.
- El humano cura sources. El LLM hace todo el resto: resumir, enlazar, archivar, mantener.
- Tres capas: **Raw** (inmutable) — **Wiki** (LLM-owned) — **Schema** (reglas)

---

## 0.5 Bóveda externa

La bóveda vive en `$VAULT_PATH` (ej. `~/Dev/obsidian_vaults/optimize-my-airbnb-yt`).

```bash
source scripts/config.sh && cd "$VAULT_PATH"
```

---

## 0.7 Configuración inicial

```bash
mkdir -p $VAULT_PATH/{sources,notes,MOC,queries,meta}
touch $VAULT_PATH/{index.md,log.md}
touch $VAULT_PATH/meta/{contradictions.md,videos.md,glossary.md}
```

---

## 1-2. Estructura: 3 capas, 3 operaciones

| L1 | L2 | L3 |
|----|----|-----|
| index.md, MOC/, log.md | notes/, queries/ | sources/ (RAW) |
| Siempre | Tras filtrar L1 | Fragmentos solo |

**Operaciones**: INGEST (añadir fuentes) → QUERY (responder) → LINT (auditar)

---

## 3. Metadatos YAML

### Fuente
```yaml
source_id: <id>
title: <título>
published: YYYY-MM-DD
topics: [tema1, tema2]
superseded_by: []
```

### Nota atómica
```yaml
claim: <una frase>
topics: [tema1, tema2]
confidence: high | medium | low
sources:
  - source_id: <id>
    locator: <puntero>
    excerpt: "<cita>"
conflicts_with: []
last_verified: YYYY-MM-DD
```

### Query guardada
```yaml
question: <pregunta>
topics: [tema1, tema2]
answered_on: YYYY-MM-DD
sources_used: [[[notes/...]], [[sources/...]]]
confidence: high | medium | low
stale_if: <condición>
```

---

## 4. Operaciones: INGEST, QUERY, LINT

**INGEST**: Fuente → `sources/` → Extract claims → 1 claim = 1 nota → Enlazar → Cruzar duplicados/conflictos → `meta/` → `log.md`

**QUERY**: `index.md` → `queries/` (cache) → MOC → notas → Respuesta citada → Guardar si síntesis nueva

**LINT**: Contradicciones, stale claims, huérfanos, gaps, drift

---

## 5-9. Core: Score, Naming, Rules, Commands, Checklist

**Score**: `score = 0.40·recency + 0.30·popularity + 0.20·specificity + 0.10·authority`

**Naming**: notas: `<topic>--<slug>.md` | queries: `<topic>--<pregunta>.md` | sources: `YYYY-MM-DD--<slug>.md`

**Rules**: ❌ Full source reads | ❌ No citations | ❌ Invented content | ❌ Unlogged conflicts

**Commands** (from `$VAULT`):
```bash
grep "^## \[" log.md | tail -10                    # Recent activity
grep -h "topics:" notes/*.md | sort | uniq -c      # Atom count
grep -r "orphan night" index.md MOC/ notes/        # Locate concept
```

**Checklist**: index.md first → queries/ cache → cite precisely → apply score → no full reads → save if new

---

## 11. Troubleshooting

**Query ceiling exceeded**: Check coverage, declare limits, decompose into sub-queries

**Broken links**: Verify targets, clean stale entries

**Stale atoms**: Rank recent sources, ingest new, extend atom, update `last_verified`

**VAULT_PATH undefined**: Check `scripts/config.sh` has `export VAULT_PATH=...`

---

# 10. Capa de dominio — Optimize My Airbnb

Específico de esta bóveda.

## 10.1 Fuentes

Transcripciones de [@OptimizeMyAirbnb](https://www.youtube.com/@OptimizeMyAirbnb). Creador: Daniel Rusteen.

**Estado**: 173 transcripciones (2017-11 → 2026-04). 5 en español excluidas.

## 10.2 Schema YAML

```yaml
video_id: <youtube-id>
title: <título>
url: https://youtube.com/watch?v=...
published: YYYY-MM-DD
duration_sec: 7320
views: 123456
channel_authority: high | medium | low
language: en | es
topics: [pricing, orphan-nights, ...]
superseded_by: []
```

Cuerpo: bloques `[MM:SS]` cada ~20s.

Locator: `[[sources/YYYY-MM-DD--slug#t=MM:SS]]`

## 10.3 Tópicos

pricing | occupancy | listing-optimization | cleaning-ops | reviews | hospitality | ranking | direct-booking | market-selection | regulations | tools-tech | investing

## 10.4 Score (§5)

```
score = 0.40·recency + 0.30·popularity + 0.20·specificity + 0.10·authority
```

## 10.5 Meta

`meta/videos.md` (auto) | `meta/contradictions.md` (manual) | `meta/glossary.md` (manual)

## 10.6 Ingest pipeline

```bash
scripts/ingest.sh <video_id>
scripts/batch-ingest.sh <list_file>
scripts/build-meta.sh
scripts/rank-sources.py --top 10
```

## 10.7 Response contract

Audience: host. Tone: consultant.
- No intro unless asked
- Numbered actionable steps
- One `[[atom]]` cite per step
- Max 600 (tactical) / 1000 (strategic) words
- Allow: PriceLabs, Airbnb, WiFi, PMS
- Forbid: filler adjectives, "cabe destacar", summaries
- Cite numbers with source_id
