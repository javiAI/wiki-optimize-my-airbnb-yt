---
automation:
  version: "3.3"
  current_phase: 2
  phase_status: "pending_approval"
  last_update: "2026-04-26T11:30:00Z"
  notes: "Restructure 2026-04-26: principio de optimización = SOLO estructural/automatización (generaliza a otras bóvedas). Atom-content opts (O3, O6, futuras) movidas a nueva Phase 5 'Atom Regeneration' donde se regeneran los 156 átomos desde cero con el contrato consolidado de todas las opts estructurales. O3 reverted (decision v2.0: target_dim_regression). Vault keep-as-is (no git rollback posible). Test framework v2 (decision v2.0, composite α=0.85, hard floors, comparison history en tests/comparisons/history/<from>-vs-<to>__n<N>.json). Vault read-only para agentes."

phases:
  phase_1:
    name: "Critical Path"
    status: "complete"
    tasks: [O1, O2]
    completed: [O1]
    skipped: [O2]
    deferred: [O3]
    progress: 100
  phase_2:
    name: "Quality Foundation (Structural)"
    status: "pending_approval"
    tasks: [O4, O5]
    completed: []
    deferred: [O6]
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
  phase_5:
    name: "Atom Regeneration"
    status: "not_started"
    tasks: [O3, O6]
    completed: []
    progress: 0
    notes: "Final phase: regenera los 156 átomos desde sources/ con el contrato consolidado (rules de O1+O4+O5+O7+O8+O9+O10+O11+O12 ya validados) + reglas de naming/casing/format de O3 + checklists ejecutables de O6 incorporadas at-creation, no retroactivas."

optimizations:
  O1: { name: "Hierarchical Indices", phase: 1, hours: 4, status: "complete", cost_delta_pct: -25.3, quality_delta: 0, class: "structural" }
  O2: { name: "Fix Q4 Contradiction", phase: 1, hours: 0.5, status: "skipped", reason: "premise_stale", class: "atom_specific" }
  O3: { name: "Language Consistency", phase: 5, hours: 2, status: "deferred", reason: "atom_content_opt; decision v2.0 REVERT (target_dim_regression on format_compliance); to be re-incorporated as a generation-time rule in Phase 5 (atom regeneration), not as a retroactive audit", class: "atom_content" }
  O4: { name: "Contradiction Detection L1", phase: 2, hours: 3, status: "not_started", class: "structural" }
  O5: { name: "Response Format Templates", phase: 2, hours: 2.5, status: "not_started", class: "structural" }
  O6: { name: "Executable Checklists", phase: 5, hours: 1.5, status: "deferred", reason: "atom_content_opt; modifies atom procedures into Dataview checklists, belongs to atom regeneration phase", class: "atom_content" }
  O7: { name: "Agent Orchestration", phase: 3, hours: 8, status: "not_started", class: "structural" }
  O8: { name: "Auto-Linking System", phase: 3, hours: 4, status: "not_started", class: "structural" }
  O9: { name: "Query Caching", phase: 3, hours: 6, status: "not_started", class: "structural" }
  O10: { name: "Semantic Gap Detection", phase: 4, hours: 3, status: "not_started", class: "structural" }
  O11: { name: "Backlink Generation", phase: 4, hours: 4, status: "not_started", class: "structural" }
  O12: { name: "RAG Fallback", phase: 4, hours: 6, status: "not_started", class: "structural" }

vault:
  name: "optimize-my-airbnb-yt"
  atoms: 156
  mocs: 12
  sources: 173
  quality_score: 8.52
  target_score: 9.8
---

## ROUTER — Autonomous Execution

**Phase status**: Read `automation.current_phase` and `automation.phase_status` from the YAML frontmatter at the top of this file — that is the single source of truth (do not hardcode the phase number or status in this prose).

**Action**: Show summary of the current phase from `docs/PHASE_<N>_SUMMARY.md` (where `<N>` = `automation.current_phase`). To proceed, the user says: `Approve Phase <N>`.

Once approved, I will execute the cycle: **Baseline test → O1 → Test O1 → Compare → Decide → O2 → ...**

For each optimization:
1. Implement changes (per `docs/PHASE_X_TASKS.md`)
2. Declare optimization in `tests/prompts/OX/meta.yaml` (`target_dims`, `at_risk_dims`, `neutral_dims`, `predicted_deltas`, `allow_repetition`)
3. Git commit with `OX:` prefix
4. **Run test suite** (per `docs/TEST_PROTOCOL.md` v2):
   - `python3 scripts/run-test-suite.py --prepare --label OX`
   - Launch 20 Agent calls in PARALLEL (single tool_use response) → write `tests/raw-responses/OX/run-N/tokens.json`
   - `python3 scripts/run-test-suite.py --prepare-evaluator --label OX`
   - Launch 1 Evaluator Agent → writes `tests/raw-responses/OX/run-N/evaluation.json` with 5-dim rubric scores
   - `python3 scripts/run-test-suite.py --consolidate --label OX` (aggregates across all run-N dirs)
   - `python3 scripts/run-test-suite.py --compare --from <prev> --to OX`
5. Read decision from `tests/comparisons/OX-vs-<prev>.json` (decision_version 2.0):
   - Composite score: `α·quality_delta_norm + (1−α)·cost_delta_norm`, α=0.85
   - Hard floors override composite (REVERT regardless): `accuracy` abs drop ≥ 1.0, `weighted_avg` abs drop ≥ 7.0, target_dim regression, any-dim abs drop ≥ 1.0
   - **IMPLEMENT** (composite ≥ +0.005, no floor breach) → update state + `docs/OPTIMIZATIONS.md` + `tests/history.md`, continue
   - **ITERATE** (composite in noise zone [−0.005, +0.005] AND `allow_repetition: true` AND runs < 3) → run again; consolidate aggregates across runs (mean, SE, 95% CI)
   - **REVERT** (composite ≤ −0.005 or any hard floor breach) → `git revert HEAD`, mark as failed, continue
6. After IMPLEMENT, run `python3 scripts/run-test-suite.py --check-repetition --from <prev> --to OX` to confirm no further runs needed.

**Critical**: Tests use 20 fresh agents in parallel, no cache, no context. See `docs/TEST_PROTOCOL.md`.

**Vault is READ-ONLY for agents**: All test writes go to `tests/` in THIS repo (not `$VAULT_PATH`). Enforced by `_ensure_under_tests` in `scripts/run-test-suite.py`; agent prompts already carry this constraint.

**Quality evaluation**: External evaluator agent grades each response on a 5-dim rubric (`completeness` 25%, `accuracy` 25%, `spanish_purity` 15%, `tone` 15%, `format_compliance` 20%). Weighted avg feeds the **composite score** (α=0.85 quality, 1−α cost). Hard floors override composite. See `docs/TEST_PROTOCOL.md` v2. Templates: `tests/prompts/_agent_template.md`, `tests/prompts/_evaluator_template.md` (per-run prompts generated from these). If rubric/decision logic changes, bump `RUBRIC_VERSION` / `DECISION_VERSION` in `scripts/run-test-suite.py`.

---

**Before any phase**: ensure baseline exists at `tests/results/baseline.json` with `evaluation_source: external_evaluator`. If only a self-assessment baseline exists, regenerate by running steps 4-6 of the protocol (the existing 20 raw responses can be reused for the evaluator pass).

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
