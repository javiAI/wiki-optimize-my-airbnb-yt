---
automation:
  version: "3.7"
  current_phase: 4
  phase_status: "pending_approval"
  last_update: "2026-04-28T00:00:00Z"
  notes: "Phase 3 complete. O7 IMPLEMENT (manual override 2026-04-28): 8.64 weighted_avg, scripts neutral. O8 IMPLEMENT: composite +0.0059 (8.64→8.69). O9 REVERT: composite -0.0075 (8.69→8.60), no hard floors breached, likely noise (SE 0.225 on spanish_purity) — script stays in repo from O7 bundle commit, no code revert needed. Phase 4 pending_approval: Semantic Gap Detection (O10), Backlink Generation (O11), RAG Fallback (O12)."

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
    status: "complete"
    tasks: [O4, O5]
    completed: [O4, O5]
    deferred: [O6]
    progress: 100
  phase_3:
    name: "Automation"
    status: "complete"
    tasks: [O7, O8, O9]
    completed: [O7, O8]
    failed: [O9]
    progress: 100
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
  O4: { name: "Contradiction Detection v2 (smart resolver + temporal narrator + auto-curate)", phase: 2, hours: 3, status: "complete", quality_delta_custom_rubric: 0.32, cost_delta_pct: 9.4, target_dim: "temporal_narrative", target_dim_delta: 1.20, decision: "IMPLEMENT (user override; nominal ITERATE on weighted_avg, but target-dim near ceiling)", rubric_used: "custom-o4v2-1.0", class: "structural" }
  O5: { name: "Response Format Templates v3 (regimes A/B/C + anti-anglicismo expanded table + refiner loop)", phase: 2, hours: 2.5, status: "complete", cost_delta_pct: 13.7, quality_delta: 0.955, target_dims: ["format_compliance", "spanish_purity"], composite: 0.0606, decision: "IMPLEMENT", class: "structural" }
  O6: { name: "Executable Checklists", phase: 5, hours: 1.5, status: "deferred", reason: "atom_content_opt; modifies atom procedures into Dataview checklists, belongs to atom regeneration phase", class: "atom_content" }
  O7: { name: "Agent Orchestration (vault-agent.py)", phase: 3, hours: 8, status: "complete", quality_delta: 0.22, cost_delta_pct: -23.1, composite: "REVERT_override→IMPLEMENT", decision: "IMPLEMENT (manual override: scripts neutral, O5 baseline n=1 outlier; O7 8.64 > original baseline 8.42 +0.22)", class: "automation_script" }
  O8: { name: "Auto-Linking System (auto-link.py)", phase: 3, hours: 4, status: "complete", quality_delta: 0.05, cost_delta_pct: -1.33, composite: 0.0059, decision: "IMPLEMENT (composite_positive; 0 orphans found, neutral by design)", class: "automation_script" }
  O9: { name: "Query Caching (cache-optimizer.py)", phase: 3, hours: 6, status: "failed", quality_delta: -0.09, cost_delta_pct: 0.14, composite: -0.0075, decision: "REVERT (composite_negative; likely noise — script stays in repo from O7 bundle commit)", class: "automation_script" }
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

# OMAB Wiki — Contract & State

## ROUTER — Autonomous Execution

**Phase status**: Read `automation.current_phase` and `automation.phase_status` from the YAML frontmatter at the top of this file — that is the single source of truth (do not hardcode the phase number or status in this prose).

**Action**: Show summary of the current phase from `docs/PHASE_<N>_SUMMARY.md` (where `<N>` = `automation.current_phase`). To proceed, the user says: `Approve Phase <N>`.

Once approved, I will execute the cycle: **Baseline test → O1 → Test O1 → Compare → Decide → O2 → ...**

For each optimization:

1. Implement changes (per `docs/PHASE_X_TASKS.md`)
2. Declare optimization in `vaults/{name}/tests/prompts/OX/meta.yaml` (`target_dims`, `at_risk_dims`, `neutral_dims`, `predicted_deltas`, `allow_repetition`)
3. Git commit with `OX:` prefix
4. **Run test suite** (per `docs/TEST_PROTOCOL.md` v2):
   - `python3 scripts/run-test-suite.py --prepare --label OX`
   - Launch 20 Agent calls in PARALLEL (single tool_use response) → write `vaults/{name}/tests/raw-responses/OX/run-N/tokens.json`
   - `python3 scripts/run-test-suite.py --prepare-evaluator --label OX`
   - Launch 1 Evaluator Agent → writes `vaults/{name}/tests/raw-responses/OX/run-N/evaluation.json` with 5-dim rubric scores
   - `python3 scripts/run-test-suite.py --consolidate --label OX` (aggregates across all run-N dirs)
   - `python3 scripts/run-test-suite.py --compare --from <prev> --to OX`
5. Read decision from `vaults/{name}/tests/comparisons/OX-vs-<prev>.json` (decision_version 2.0):
   - Composite score: `α·quality_delta_norm + (1−α)·cost_delta_norm`, α=0.85
   - Hard floors override composite (REVERT regardless): `accuracy` abs drop ≥ 1.0, `weighted_avg` abs drop ≥ 7.0, target_dim regression, any-dim abs drop ≥ 1.0
   - **IMPLEMENT** (composite ≥ +0.005, no floor breach) → update state + `docs/OPTIMIZATIONS.md` + `vaults/{name}/tests/history.md`, continue
   - **ITERATE** (composite in noise zone [−0.005, +0.005] AND `allow_repetition: true` AND runs < 3) → run again; consolidate aggregates across runs (mean, SE, 95% CI)
   - **REVERT** (composite ≤ −0.005 or any hard floor breach) → `git revert HEAD`, mark as failed, continue
6. After IMPLEMENT, run `python3 scripts/run-test-suite.py --check-repetition --from <prev> --to OX` to confirm no further runs needed.

**Critical**: Tests use 20 fresh agents in parallel, no cache, no context. See `docs/TEST_PROTOCOL.md`.

**Quick debug**:

- `python3 scripts/run-test-suite.py --help` — all subcommands
- `vaults/{name}/tests/raw-responses/<LABEL>/run-N/Q*.json` — per-question agent output (response + atoms_cited + conflict_detected + proposed_contradictions + self_assessment)
- `vaults/{name}/tests/raw-responses/<LABEL>/run-N/tokens.json` — cost telemetry (total_tokens, tool_uses, duration_ms per Q)
- `vaults/{name}/tests/raw-responses/<LABEL>/run-N/evaluation.json` — evaluator's per-Q + aggregate rubric scores
- `vaults/{name}/tests/comparisons/<TO>-vs-<FROM>.json` — composite score, deltas, decision, hard-floor checks
- `.claude/settings.json` hook reminds to run tests after each `OX:` commit
- `scripts/run-o4v2-test.py` — legacy O4v2-specific runner (use `run-test-suite.py` for new opts)

**Vault is READ-ONLY for agents**: All test writes go to `vaults/{name}/tests/` in THIS repo (not `$VAULT_PATH`). Enforced by `_ensure_under_tests` in `scripts/run-test-suite.py`; agent prompts already carry this constraint.

**Quality evaluation**: External evaluator agent grades each response on a 5-dim rubric (`completeness` 25%, `accuracy` 25%, `spanish_purity` 15%, `tone` 15%, `format_compliance` 20%). Weighted avg feeds the **composite score** (α=0.85 quality, 1−α cost). Hard floors override composite. See `docs/TEST_PROTOCOL.md` v2. Templates: `.claude/templates/tests/_agent_template.md`, `.claude/templates/tests/_evaluator_template.md` (per-run prompts generated from these). If rubric/decision logic changes, bump `RUBRIC_VERSION` / `DECISION_VERSION` in `scripts/run-test-suite.py`.

---

**Before any phase**: ensure baseline exists at `vaults/{name}/tests/results/baseline.json` with `evaluation_source: external_evaluator`. If only a self-assessment baseline exists, regenerate by running steps 4-6 of the protocol (the existing 20 raw responses can be reused for the evaluator pass).

---

**How automation works**:

- Each session, I read this CLAUDE.md
- Router determines action based on `automation.phase_status`
- `pending_approval` → Show summary, wait for approval
- `in_progress` → Execute next task → test → decide → commit → repeat
- `complete` → Advance to next phase
- Hook in `.claude/settings.json` reminds me to run tests after each `OX:` commit
- Auto-memory at `~/.claude/projects/.../memory/MEMORY.md` persists context across sessions (master plan, pending opts)

---

**See also**:

- `docs/PHASE_<N>_SUMMARY.md` — What phase `<N>` accomplishes (substitute `automation.current_phase`)
- `docs/PHASE_<N>_TASKS.md` — How to execute each task in phase `<N>`
- `docs/TEST_PROTOCOL.md` — **How to run parallel tests (read before testing)**
- `docs/TEST_FRAMEWORK.md` — Test framework theory
- `docs/ORCHESTRATOR.md` — Full orchestration design

---

## 0. Filosofía

Esto **no es RAG**. El LLM construye y mantiene una wiki persistente que se enriquece con cada fuente y pregunta.

- **Obsidian es el IDE**; **el LLM es el programador**; **la wiki es la codebase**.
- El humano cura sources. El LLM hace todo el resto: resumir, enlazar, archivar, mantener.
- Tres capas: **Raw** (inmutable) — **Wiki** (LLM-owned) — **Schema** (reglas)

---

## 0.5 Bóveda externa

La bóveda vive en `$VAULT_PATH` (ej. `~/Dev/obsidian_vaults/optimize-my-airbnb-yt`). Para repos con varias bóvedas, `VAULT_NAME` selecciona el bundle (`vaults/{name}/vault.yml` resuelve `vault_path`); con una sola bóveda, `config.sh` la auto-detecta.

```bash
source .claude/scripts/config.sh && cd "$VAULT_PATH"          # auto-detect o $VAULT_NAME
VAULT_NAME=optimize-my-airbnb-yt source .claude/scripts/config.sh && cd "$VAULT_PATH"
```

---

## 0.6 Layout (WikiForge v2)

Una bóveda nueva creada por `init-vault.sh` tiene esta forma. Todo es per-lang excepto `meta/`, `log.md` y `state/`:

```text
$VAULT_PATH/
├── index/{lang}/index.md       # navegación raíz: tabla de MOCs
├── moc/{lang}/<topic>.md       # un MOC por topic, lista atoms
├── wiki/{lang}/<topic>--<slug>.md   # atoms (1 claim cada uno)
├── raw/{lang}/<date>--<slug>.md     # transcripciones (per-lang)
├── queries/{lang}/<topic>--<q>.md   # cache de queries respondidas
├── meta/                       # contradictions.md, glossary.md, RESPONSE_TEMPLATES.md, videos.md, agent-reports/
└── log.md                      # registro cronológico (auto-append por hook)
```

`vaults/{name}/` (en este repo) hospeda `vault.yml`, `agents.md`, `state/queue/`, `state/logs/`, `tests/`. Los hooks viven en `.claude/hooks/`, no en la bóveda. La bóveda contiene **datos**, no configuración.

> Nota: la bóveda OMA en producción (`optimize-my-airbnb-yt`) está en migración parcial — convive el layout v1 (`notes/`, `sources/`, `MOC/`, `index.md`) con el v2 (`wiki/{lang}/`, `raw/{lang}/`, `moc/{lang}/`, `index/{lang}/`). Para nuevas bóvedas usa siempre v2.

## 0.7 Bootstrap

Para crear una bóveda nueva: `bash .claude/scripts/init-vault.sh` (wizard) o `/init-vault` desde Claude (guiado conversacional). Crea el bundle `vaults/{name}/` y la estructura de datos en el path elegido. Para la OMA original, los comandos legacy están en `docs/PHASE_1_TASKS.md`.

---

## 1-2. Estructura: 3 capas, 3 operaciones

| L1 (siempre) | L2 (tras filtrar L1) | L3 (fragmentos) |
| --- | --- | --- |
| `index/{lang}/index.md`, `moc/{lang}/`, `log.md` | `wiki/{lang}/`, `queries/{lang}/` | `raw/{lang}/` |

**Operaciones**: INGEST (añadir fuentes) → QUERY (responder) → AUDIT (estructura) + QA (contenido). Los dos health-checks viven en slash commands distintos: `/audit` cubre la salud estructural (huérfanos, stale, gaps, propagations, cross-refs); `/qa` cubre el contenido de cada atom (claim, URL, anglicismos). El término histórico "LINT" del documento original se mapea a la combinación `/audit` + `/qa` (cobertura equivalente o superior, separada por scope).

---

## 3. Metadatos YAML

### Fuente (`raw/{lang}/<date>--<slug>.md`)

```yaml
source_id: <id>
video_id: <youtube-id>
title: <título>
url: https://youtube.com/watch?v=...
published: YYYY-MM-DD
language: <lang>           # idioma de ESTE transcript
native_lang: <lang>        # idioma nativo del vídeo (yt-dlp)
subtitle_source: manual | auto
topics: [tema1, tema2]
superseded_by: []
```

### Nota atómica (`wiki/{lang}/<topic>--<slug>.md`)

```yaml
claim: <una frase>
topics: [tema1, tema2]
confidence: high | medium | low
sources:
  - source_id: <id>
    locator: <MM:SS-MM:SS>
    excerpt: "<cita verbatim>"
    excerpt_source: yt_manual | yt_auto | llm_fallback | native_atomization
lang_origin: <lang>            # idioma del transcript que generó este atom
propagated_from: <lang>        # solo si NO es el atom canónico (omitir si lo es)
conflicts_with: []
last_verified: YYYY-MM-DD
```

### Query guardada (`queries/{lang}/<topic>--<pregunta>.md`)

```yaml
question: <pregunta>
topics: [tema1, tema2]
answered_on: YYYY-MM-DD
sources_used: [[[wiki/{lang}/...]], [[raw/{lang}/...]]]
confidence: high | medium | low
stale_if: <condición>
```

---

## 4. Operaciones: INGEST, QUERY, AUDIT + QA

**INGEST**: Fuente → `raw/{lang}/` → Extract claims (`atomization_lang`) → 1 claim = 1 atom en `wiki/{lang}/` → Enlazar (`auto-link.py`) → Propagar a otros lang (`propagate_atom.py`) → Cruzar duplicados/conflictos → `meta/` → `log.md`

**QUERY**: `index/{lang}/index.md` → `queries/{lang}/` (cache) → `moc/{lang}/<topic>.md` → `wiki/{lang}/<atom>.md` → Respuesta citada → Guardar si síntesis nueva

**AUDIT** (estructura, `/audit` → `vault-agent.py`): contradicciones, stale claims, huérfanos, gaps, drift, missing propagations, missing cross-refs.

**QA** (contenido, `/qa` → `atom-qa.py`): claim presente, URL válida, anglicismos, esquema YAML por atom (`--fix` autoresuelve anglicismos).

---

## 4.5 Conflict Check (query-time, real-time) — O4v2

Antes de redactar la respuesta, para cada `[[atom]]` del shortlist ejecuta el ciclo **detect → classify → resolve → surface → curate**.

### 4.5.1 Detect

Escanear `moc/{lang}/<topic>.md` y los `conflicts_with` declarados en cada atom del shortlist. Cross-check `meta/contradictions.md` para saber si el conflicto ya está documentado y si tiene resolución registrada.

### 4.5.2 Classify severity

- **HIGH**: mismo topic, claim opuesto explícito (ej. "5%" vs rechazo explícito de "5%").
- **MEDIUM**: mismo topic, prescripción/evidencia divergente sin oposición literal (ej. flat-price vs base+fee).
- **LOW**: topic relacionado, recomendación distinta — ignorar silenciosamente.

Solo HIGH y MEDIUM disparan los pasos siguientes.

### 4.5.3 Resolve — jerarquía obligatoria

Aplicar criterios EN ESTE ORDEN. El primero que decida gana. No saltar criterios.

1. **temporal_supersession**: un atom supera a otro por hito documentado (policy update, market shift) o por `recency` >0.30 abs en el score §5. El atom nuevo es primario; el viejo se conserva como contexto histórico → narrar evolución (§4.5.6).
2. **contextual_scope**: ambos atoms aplican bajo condiciones distintas (market type, listing-state, host-stage). Ningún ganador universal; describir cuándo usar cada uno.
3. **confidence_tier**: a igual scope, `confidence: high` gana sobre `medium`/`low`.
4. **authority_tier**: a igual confidence, mayor `channel_authority` gana.
5. **specificity_tier**: si todo empata, gana el atom con prescripción más específica (rechazo explícito de la alternativa, números concretos, condiciones acotadas).

El criterio aplicado se registra en `conflict_resolution_applied.resolution_criterion` del output JSON.

### 4.5.4 Surface — cuándo emitir caveat

| Estado del conflicto | Acción |
| --- | --- |
| Documentado en meta + ganador claro + pregunta NO toca dimensión rival | Usa primario, **sin caveat**. |
| Documentado en meta + ganador claro + pregunta TOCA dimensión rival | Caveat informativo (atajo: la condición de aplicabilidad del rival). |
| Documentado en meta sin ganador único (market-dependent / scope) | Caveat estándar con condiciones. |
| NO documentado | Caveat estándar + entrada en `proposed_contradictions[]` (§4.5.5). |

`conflict_detected.found` debe ser `true` siempre que el conflicto sea **activo** en la respuesta — no `false` por el simple hecho de estar documentado en meta. La presencia en meta solo afecta la decisión de surface (qué caveat) y de curate (si proponer entrada nueva o no).

### 4.5.5 Curate — auto-emit de proposed_contradictions

Cuando se detecta conflicto HIGH o MEDIUM **no documentado** en `meta/contradictions.md`, el campo `proposed_contradictions[]` del JSON DEBE incluir una entrada con:

- `atoms`: ambos `[[atom-A]]`, `[[atom-B]]`
- `topic`: topic compartido
- `severity`: HIGH | MEDIUM
- `relation`: `direct` | `temporal` | `contextual` | `mirror`
- `proposed_resolution`: criterio aplicado + ganador propuesto (≤80 palabras)
- `evidence`: observación específica que motivó el flag (≤80 palabras)

NO añadir entradas para conflictos ya documentados — duplicaría meta. El script `scripts/apply-proposed-contradictions.py` consolida estas entradas en `meta/contradictions.md` entre runs.

### 4.5.6 Caveat format (templates en `meta/RESPONSE_TEMPLATES.md`)

- **Estándar** (no temporal): bloque ⚠️ Nota con primario/rival, condición de aplicabilidad, link a meta.
- **Temporal evolution** (cuando criterio = `temporal_supersession`): tres elementos obligatorios — ANTES (estado pre + cita rival), DESDE (transición + hito + razón), HOY (estado actual + cita primaria). Máx 3 frases. El atom viejo aparece como contexto histórico, no como recomendación competidora.

### 4.5.7 Multi-conflicto

Si el shortlist toca 2+ conflictos distintos (ej. una pregunta de pricing global cruza 5%-vs-10%, Thu/Sun, max-occupancy-vs-extra-fee), surface UN caveat por conflicto activo, en orden de relevancia para la pregunta. No agruparlos en un solo bloque difuso.

---

## 4.6 Format Check (query-time, regime-based) — O5

**Antes de redactar, lee `meta/RESPONSE_TEMPLATES.md`** — contiene las plantillas canónicas A/B/C con secciones, ejemplos y reglas. Sin esa lectura no puedes garantizar el formato correcto. Las secciones obligatorias de cada régimen NO son sugerencias, son contrato.

### 4.6.1 Regime detection

| Régimen | Señales | Ceiling | Ejemplos de preguntas |
| --- | --- | --- | --- |
| **A. Narrow Factual** | una sola variable; busca dato/umbral/sí-no; verbos "cuánto", "cuál es", "se permite", "puedo", "qué precio", "qué pongo" | **250 palabras** | "¿Qué precio inicial pongo?" / "¿Cuánto cobro de tarifa de limpieza?" / "¿Activo Instant Book?" / "¿Qué pongo en el título?" / "¿Cuántas fotos subo?" |
| **B. Tactical Multi-Palanca** | pide pasos coordinados para EJECUTAR; verbos "cómo hago", "qué hago para", "cómo manejo", "cómo respondo"; 3-5 palancas | **600 palabras** | "¿Cómo respondo a una reseña negativa?" / "¿Cómo manejo noches huérfanas?" / "¿Qué amenities destaco?" / "¿Cómo filtro huéspedes problemáticos?" |
| **C. Taxonomic / Broad** | pide DECIDIR un marco antes de ejecutar; verbos "cómo elijo entre", "diferencias entre", "panorama", "estrategia para escalar"; comparativa o decision-tree natural | **1000 palabras** | "¿Cómo elijo PMS?" / "¿Cómo paso de 1 a 5 listings?" / "¿Cómo evalúo un mercado?" / "¿Cómo construyo direct bookings?" |

**Orden de detección — aplica el primero que matchee**:

1. ¿Busca UN dato concreto / sí-no / umbral? → **A**
2. ¿Pide pasos para ejecutar mañana sobre UN problema acotado? → **B**
3. ¿Pide decidir un marco / comparar opciones / planificar escalado? → **C**

Empates: A/B ambiguo → **A** (favorece concisión). B/C ambiguo: ejecuta mañana → B; decide antes → C.

Registra el régimen en `level` del JSON output: 1=A, 3=B, 4=C.

### 4.6.2 Section enforcement

Cada régimen tiene secciones obligatorias (definidas en `RESPONSE_TEMPLATES.md`):

- **A**: `Respuesta directa` + `Fuentes` (mínimo). `Cuándo aplica` y `Por qué` opcionales.
- **B**: `Pasos` (3-5, una cita por paso) + `Por qué funciona el conjunto` + `Resultado esperado` + `Fuentes`. `Diagnóstico` opcional.
- **C**: `Panorama` + `Comparativa` (tabla) + `Cómo elegir` (decision-tree) + `Fuentes`. `Próximos pasos` opcional.

NO inventar secciones nuevas. NO renombrar las obligatorias. Si una sección no aplica, escoge otro régimen.

### 4.6.3 Caveat integration

El bloque ⚠️ del conflict-check (§4.5) se añade **al final** del cuerpo, después de `Fuentes` (o de `Próximos pasos` en C), antes de cualquier metadata. No sustituye secciones obligatorias.

### 4.6.4 Word ceiling enforcement

Si el cuerpo excede el ceiling del régimen detectado, **antes de devolver**, recorta:

1. Eliminar adjetivos de relleno y "cabe destacar / es importante".
2. Comprimir sub-bullets en una sola frase por paso.
3. Si tras 1+2 sigue excediendo, evaluar si el régimen detectado era el correcto (probablemente C en lugar de B).

No exceder el ceiling es prioridad sobre completeness opcional.

---

## 5-9. Core: Score, Naming, Rules, Commands, Checklist

**Score**: `score = 0.40·recency + 0.30·popularity + 0.20·specificity + 0.10·authority`

**Naming**: atoms: `wiki/{lang}/<topic>--<slug>.md` | queries: `queries/{lang}/<topic>--<pregunta>.md` | sources: `raw/{lang}/<YYYY-MM-DD>--<slug>.md` | MOCs: `moc/{lang}/<topic>.md`

**Rules**: ❌ Full source reads | ❌ No citations | ❌ Invented content | ❌ Unlogged conflicts

**Commands** (from `$VAULT_PATH`, sustituye `<lang>` por `en`/`es`/...):

```bash
grep "^## \[" log.md | tail -10                                       # Recent activity
grep -h "topics:" wiki/<lang>/*.md | sort | uniq -c                   # Atom count by topic
grep -r "orphan night" index/<lang>/index.md moc/<lang>/ wiki/<lang>/ # Locate concept
```

**Checklist**: `index/{lang}/index.md` first → `queries/{lang}/` cache → cite precisely → apply score → no full reads → save if new

---

## 11. Troubleshooting

**Query ceiling exceeded**: Check coverage, declare limits, decompose into sub-queries

**Broken links**: Verify targets, clean stale entries

**Stale atoms**: Rank recent sources, ingest new, extend atom, update `last_verified`

**VAULT_PATH undefined**: Check `.claude/scripts/config.sh` has `export VAULT_PATH=...` (or set `VAULT_NAME` to use a `vaults/{name}/vault.yml`).

**Vault health audit** (O7): `VAULT_NAME=<name> python3 .claude/scripts/vault-agent.py` — detecta orphans, stale, gaps, broken links, missing propagations, missing cross-refs. Escribe `meta/agent-reports/agent-report-YYYY-MM-DD.md`.

**Post-ingest auto-linking** (O8): `VAULT_NAME=<name> python3 .claude/scripts/auto-link.py <atom-stem> --lang <lang>` — inserta `[[wiki/{lang}/atom]]` en MOCs relevantes y regenera `index/{lang}/index.md`. `--all` para backfill completo (ejecutar una vez por lang). `--index-only` regenera el índice sin tocar atoms.

**Bash portability lint**: `bash .claude/scripts/lint-bash-portability.sh` — escanea `.claude/scripts/` y `.claude/hooks/` para idioms de bash 4+ (`declare -A`, `mapfile`, `${var,,}`). macOS ships bash 3.2 — corre tras editar cualquier `.sh`. También se dispara en `on-session-start.sh`.

**Multilingual propagation**: `VAULT_NAME=<name> python3 .claude/scripts/propagate_atom.py <stem> --from <lang> --to <lang>` — re-atomiza el atom canónico al mismo locator usando el transcript target como material primario (no es traducción). Ver §10.6 para el modelo completo.

---

## 10. Capa de dominio — Optimize My Airbnb

Específico de esta bóveda.

### 10.1 Fuentes

Transcripciones de [@OptimizeMyAirbnb](https://www.youtube.com/@OptimizeMyAirbnb). Creador: Daniel Rusteen.

**Estado**: 173 transcripciones (2017-11 → 2026-04). 5 en español excluidas.

### 10.2 Schema YAML

Extiende §3 con campos específicos del canal de YouTube:

```yaml
video_id: <youtube-id>
title: <título>
url: https://youtube.com/watch?v=...
published: YYYY-MM-DD
duration_sec: 7320
views: 123456
channel_authority: high | medium | low
language: <lang>           # idioma de ESTE transcript
native_lang: <lang>        # idioma nativo del vídeo (yt-dlp)
subtitle_source: manual | auto
topics: [pricing, orphan-nights, ...]
superseded_by: []
```

Cuerpo: bloques `[MM:SS]` cada ~20s.

Locator: `[[raw/{lang}/YYYY-MM-DD--slug#t=MM:SS]]`

### 10.3 Tópicos

pricing | occupancy | listing-optimization | cleaning-ops | reviews | hospitality | ranking | direct-booking | market-selection | regulations | tools-tech | investing

### 10.4 Score (§5)

```text
score = 0.40·recency + 0.30·popularity + 0.20·specificity + 0.10·authority
```

### 10.5 Meta

`meta/videos.md` (auto) | `meta/contradictions.md` (manual) | `meta/glossary.md` (manual)

### 10.6 Ingest pipeline

`raw/` es per-lang: `raw/{lang}/{date}--slug.md`, una entrada por idioma de subtítulos disponible. La atomización corre **una vez** en `atomization_lang` (nativo del vídeo si está en `enabled`, si no `enabled[0]`); `propagate_atom.py` re-atomiza al mismo locator en cada otro idioma de `enabled` usando el transcript target como material primario (no es traducción).

```bash
.claude/scripts/ingest.sh <video_id>                                 # baja subs en cada lang de enabled
.claude/scripts/batch-ingest.sh <list_file>
.claude/scripts/extract_excerpt.py --raw-file <raw> --locator MM:SS-MM:SS   # cita verbatim sin LLM
.claude/scripts/propagate_atom.py <stem> --from <lang> --to <lang>   # re-atomiza al locator
.claude/scripts/init-vault.sh                                        # bootstrap nuevo bundle
scripts/build-meta.sh                                                # OMA-specific (video metadata cache)
scripts/rank-sources.py --top 10                                     # OMA-specific (source scoring)
```

### 10.7 Response contract

Audiencia: anfitrión. Tono: consultor — humano, profesional, cálido (no robótico).

**Regime + format (§4.6)**:

- LEE `meta/RESPONSE_TEMPLATES.md` ANTES de redactar. Sin esa lectura no puedes garantizar formato.
- Detecta el régimen (A. Narrow Factual / B. Tactical / C. Taxonomic) por las heurísticas de §4.6.1.
- Ceilings duros: **A=250 / B=600 / C=1000** palabras. No exceder bajo ningún concepto.
- Cita `[[atom]]` por paso (B) o por celda/criterio (C). En A, 1-3 atoms inline.
- Sin intro innecesaria. Sin trailing summary.
- Cita números con `source_id`.

**Lenguaje (Spanish purity)** — ANTES de devolver, releer y substituir uno por uno:

| ❌ Evitar | ✅ Usar |
| --- | --- |
| host / hosts | anfitrión / anfitriones |
| guest / guests | huésped / huéspedes |
| review / reviews | reseña / reseñas |
| rating | calificación |
| amenity / amenities | comodidad / comodidades |
| booking / bookings (sustantivo) | reserva / reservas |
| fee (genérico) | tarifa |
| cleaning fee | tarifa de limpieza |
| listing | anuncio (excepto en "listing nuevo" técnico) |
| check-in / check-out | entrada / salida (en flujo operativo, "self check-in" se mantiene) |
| weekend | fin de semana |
| last-minute | último momento |
| far-out (calendario) | lejos (a 60-90 días) |
| min-stay / minimum stay | estancia mínima |
| max guests | huéspedes máximos |
| base price | precio base |
| comp set / comps | competencia / referentes |
| market | mercado |
| dashboard | panel |
| screenshot | captura |
| red flag | señal de alarma |
| paper trail | rastro escrito |
| refund | reembolso |
| claim | reclamación |
| mid-stay | mitad de estancia |
| turnover | rotación |
| pet-friendly | admite mascotas |
| hot tub | jacuzzi |
| smart-lock | cerradura inteligente |
| workspace | zona de trabajo |
| king bed | cama king |
| review fuel | material para reseñas |
| repeat guest | huésped recurrente |
| follow-up | seguimiento |
| funnel | embudo |
| ranking | posicionamiento |
| occupancy | ocupación |
| revenue | ingresos |
| rate (precio) | tarifa |
| tier | nivel |
| cleaner | personal de limpieza / limpiador |
| sweet spot | punto óptimo |
| discovered (market) | mercado descubierto |
| undiscovered (market) | mercado no descubierto |
| minimum (stay) | mínimo / estancia mínima |
| social proof | prueba social |
| workforce | mano de obra |
| business traveler | viajero de negocios |
| take rate | comisión / tasa de captación |

**Allow proper nouns/tech (NO traducir)**: PriceLabs, Wheelhouse, Beyond, Hostfully, Hospitable, Guesty, OwnerRez, Airbnb, Booking, Vrbo, AllTheRooms, AirDNA, NoiseAware, Minut, Google, YouTube, Superhost, Aircover, Instant Book, Stays, Co-Host, WiFi, PMS, API, URL, OS, JSON, YAML, SEO, ADR, BLT, FPG, TOS, GMB, StayFi.

**Forbid**: filler adjectives, "cabe destacar", "es importante mencionar", "en este sentido", trailing summaries, corporate-speak.

**Conflict caveat (§4.5)**: si el conflict-check arroja HIGH/MEDIUM, añade el bloque ⚠️ al final del cuerpo (template en `meta/RESPONSE_TEMPLATES.md` §A o §B). No omitir.

---

### Pre-output checklist (OBLIGATORIO antes de escribir el JSON final)

Recorre estos 6 puntos en orden. Si algún punto falla, corrige y vuelve a empezar el checklist:

1. **Cuenta palabras** del campo `response` (excluye metadata/citas). Si excede el ceiling de su régimen (A=250/B=600/C=1000), recorta hasta entrar. Prioridad: eliminar adjetivos de relleno, comprimir sub-bullets, fundir frases redundantes. NO devuelvas si excedes.
2. **Releí buscando anglicismos** de la tabla anterior. Substituye uno por uno. Solo permanecen los términos de la whitelist (nombres propios y tech estandarizada).
3. **Cada paso (B) o cada celda comparativa (C) tiene exactamente UNA cita `[[atom]]`**. En A, 1-3 atoms inline.
4. **Cada número** (precio, porcentaje, plazo, umbral) está respaldado por al menos un `source_id` en `sources_cited`.
5. **No hay intro innecesaria** ("Excelente pregunta...", "Te explico...") ni **trailing summary** ("En resumen...", "Para concluir...").
6. **Si hay conflicto HIGH/MEDIUM** activo, el bloque ⚠️ está al final del cuerpo, no intercalado.
