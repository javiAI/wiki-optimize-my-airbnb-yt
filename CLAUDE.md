---
automation:
  version: "3.5"
  current_phase: 3
  phase_status: "pending_approval"
  last_update: "2026-04-27T22:30:00Z"
  notes: "Phase 2 complete 2026-04-27. O5 Response Format Templates v3 IMPLEMENT (composite +0.0606): templates A/B/C en meta/RESPONSE_TEMPLATES.md con secciones obligatorias y ceilings 250/600/1000; tabla §10.7 expandida de 52 a 61 mappings vía mine-anglicismos.py (mining sistemático de violations[] del evaluator); refiner-loop infrastructure (scripts/run-test-suite.py --refine + tests/prompts/_refiner_template.md). Run-3 standalone (n=1, 20 fresh agents): weighted_avg 8.64 → 9.60 (+0.96), spanish_purity 5.60 → 9.85 (+4.25, +75.89%), format_compliance 8.25 → 9.10 (+0.85), tone 9.00 → 9.40 (+0.40, at-risk dim improved). Cost 54,438 → 61,899 (+13.7%). Cero Qs por debajo del threshold 7 — refiner no se disparó. Phase 1 complete (O1 implement, O2 skip, O3 deferred → P5). Phase 2 complete (O4, O5 implement; O6 deferred → P5). Siguiente: Phase 3 Automation (O7 vault-agent, O8 auto-link, O9 query-cache)."

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
  O4: { name: "Contradiction Detection v2 (smart resolver + temporal narrator + auto-curate)", phase: 2, hours: 3, status: "complete", quality_delta_custom_rubric: 0.32, cost_delta_pct: 9.4, target_dim: "temporal_narrative", target_dim_delta: 1.20, decision: "IMPLEMENT (user override; nominal ITERATE on weighted_avg, but target-dim near ceiling)", rubric_used: "custom-o4v2-1.0", class: "structural" }
  O5: { name: "Response Format Templates v3 (regimes A/B/C + anti-anglicismo expanded table + refiner loop)", phase: 2, hours: 2.5, status: "complete", cost_delta_pct: 13.7, quality_delta: 0.955, target_dims: ["format_compliance", "spanish_purity"], composite: 0.0606, decision: "IMPLEMENT", class: "structural" }
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

**Quick debug**:

- `python3 scripts/run-test-suite.py --help` — all subcommands
- `tests/raw-responses/<LABEL>/run-N/Q*.json` — per-question agent output (response + atoms_cited + conflict_detected + proposed_contradictions + self_assessment)
- `tests/raw-responses/<LABEL>/run-N/tokens.json` — cost telemetry (total_tokens, tool_uses, duration_ms per Q)
- `tests/raw-responses/<LABEL>/run-N/evaluation.json` — evaluator's per-Q + aggregate rubric scores
- `tests/comparisons/<TO>-vs-<FROM>.json` — composite score, deltas, decision, hard-floor checks
- `.claude/settings.json` hook reminds to run tests after each `OX:` commit
- `scripts/run-o4v2-test.py` — legacy O4v2-specific runner (use `run-test-suite.py` for new opts)

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
- Auto-memory at `~/.claude/projects/.../memory/MEMORY.md` persists context across sessions (master plan, pending opts)

---

**See also**:
- `docs/PHASE_<N>_SUMMARY.md` — What phase `<N>` accomplishes (substitute `automation.current_phase`)
- `docs/PHASE_<N>_TASKS.md` — How to execute each task in phase `<N>`
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

## 0.7 Bootstrap (one-time, ya completo)

Vault structure (`sources/`, `notes/`, `MOC/`, `queries/`, `meta/`) ya existe con 173 sources + 156 atoms. Bootstrap commands en `docs/PHASE_1_TASKS.md` si se replica para otra bóveda.

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

## 4.5 Conflict Check (query-time, real-time) — O4v2

Antes de redactar la respuesta, para cada `[[atom]]` del shortlist ejecuta el ciclo **detect → classify → resolve → surface → curate**.

### 4.5.1 Detect

Escanear `MOC/<topic>.md` y los `conflicts_with` declarados en cada atom del shortlist. Cross-check `meta/contradictions.md` para saber si el conflicto ya está documentado y si tiene resolución registrada.

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
|---|---|
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

### 4.5.6 Caveat format (templates en `queries/RESPONSE_TEMPLATES.md`)

- **Estándar** (no temporal): bloque ⚠️ Nota con primario/rival, condición de aplicabilidad, link a meta.
- **Temporal evolution** (cuando criterio = `temporal_supersession`): tres elementos obligatorios — ANTES (estado pre + cita rival), DESDE (transición + hito + razón), HOY (estado actual + cita primaria). Máx 3 frases. El atom viejo aparece como contexto histórico, no como recomendación competidora.

### 4.5.7 Multi-conflicto

Si el shortlist toca 2+ conflictos distintos (ej. una pregunta de pricing global cruza 5%-vs-10%, Thu/Sun, max-occupancy-vs-extra-fee), surface UN caveat por conflicto activo, en orden de relevancia para la pregunta. No agruparlos en un solo bloque difuso.

---

## 4.6 Format Check (query-time, regime-based) — O5

**Antes de redactar, lee `meta/RESPONSE_TEMPLATES.md`** — contiene las plantillas canónicas A/B/C con secciones, ejemplos y reglas. Sin esa lectura no puedes garantizar el formato correcto. Las secciones obligatorias de cada régimen NO son sugerencias, son contrato.

### 4.6.1 Regime detection

| Régimen | Señales | Ceiling | Ejemplos de preguntas |
|---|---|---|---|
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

Audience: host. Tone: consultant — humano, profesional, cálido (no robótico).

**Regime + format (§4.6)**:
- LEE `meta/RESPONSE_TEMPLATES.md` ANTES de redactar. Sin esa lectura no puedes garantizar formato.
- Detecta el régimen (A. Narrow Factual / B. Tactical / C. Taxonomic) por las heurísticas de §4.6.1.
- Ceilings duros: **A=250 / B=600 / C=1000** palabras. No exceder bajo ningún concepto.
- Cita `[[atom]]` por paso (B) o por celda/criterio (C). En A, 1-3 atoms inline.
- Sin intro innecesaria. Sin trailing summary.
- Cita números con `source_id`.

**Lenguaje (Spanish purity)** — ANTES de devolver, releer y substituir uno por uno:

| ❌ Evitar | ✅ Usar |
|---|---|
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
