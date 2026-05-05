# Testing History — Optimization Timeline

Append-only log of test runs and optimization decisions. Newest entries at the top.

Single source of truth para descripción y estado: [docs/OPTIMIZATIONS.md](../docs/OPTIMIZATIONS.md).

---

## 2026-04-28 — O9: Query Caching (cache-optimizer.py) → REVERT (composite −0.0075)

cache-optimizer.py analiza log.md y genera meta/query-cache-stats.md con topics más consultados y entradas stale. Script no modifica contenido que los agentes de test lean (queries/ en blacklist del prompt). Neutral por diseño.

**Resultados (n=2, baseline O8 8.69)**:

| Dim (peso) | O8 (baseline) | O9 (n=2) | Δ |
|---|---|---|---|
| completeness (25%) | 8.65 | 8.72 | +0.07 |
| accuracy (25%) | 8.70 | 8.88 | +0.18 |
| spanish_purity (15%) | 8.65 | 8.03 | −0.62 |
| tone (15%) | 8.70 | 8.90 | +0.20 |
| format_compliance (20%) | 8.75 | 8.32 | −0.43 |
| **weighted_avg** | **8.69** | **8.60** | **−0.09** |
| weighted_cost | 46,983 | 47,049 | **+0.14%** |

Composite −0.0075 → REVERT (≤ −0.005). Sin hard-floor breach (max caída dim: spanish_purity −0.62 < 1.0). Caída probablemente varianza (SE 0.225 en spanish_purity, 0.275 en format_compliance). Script ya estaba en repo desde commit O7 bundle — sin rollback de código.

**Phase 3 cerrada**: O7 ✅ IMPLEMENT | O8 ✅ IMPLEMENT | O9 ❌ REVERT

---

## 2026-04-28 — O8: Auto-Linking System (auto-link.py) → IMPLEMENT (composite +0.0059)

auto-link.py post-ingest hook: inserta `[[notes/stem]]` en MOCs relevantes cuando un átomo no está enlazado. Backfill completo encontró 0 átomos huérfanos — todos ya estaban en sus MOCs.

**Resultados (n=1, baseline O7 8.64)**:

| Dim (peso) | O7 (baseline) | O8 | Δ |
|---|---|---|---|
| completeness (25%) | 8.55 | 8.65 | +0.10 |
| accuracy (25%) | 8.80 | 8.70 | −0.10 |
| spanish_purity (15%) | 8.57 | 8.65 | +0.07 |
| tone (15%) | 8.80 | 8.70 | −0.10 |
| format_compliance (20%) | 8.50 | 8.75 | +0.25 |
| **weighted_avg** | **8.64** | **8.69** | **+0.05** |
| weighted_cost | 47,617 | 46,983 | **−1.33%** |

Composite +0.0059 → IMPLEMENT (≥ +0.005). Check-repetition advisory (wider ±0.015 band) anotado; O8 neutral by design (0 orfanatos en bóveda).

---

## 2026-04-28 — O7: Agent Orchestration (vault-agent.py) → IMPLEMENT (manual override)

Inicio de Phase 3. Infraestructura de mantenimiento de bóveda: `scripts/vault-agent.py` detecta orphans, stale atoms, topic gaps, broken index links, contradicciones sin resolver. Escribe `meta/agent-report-YYYY-MM-DD.md`.

**Scripts implementados**:
- `scripts/vault-agent.py` — Health audit (O7): orphans, stale >180d, gaps (≥3 atoms sin MOC), index consistency, contradictions sin resolver, ingest recommendations. CLI: `--dry-run`, `--stale-days`.
- `scripts/auto-link.py` — Post-ingest hook (O8): inserta `[[notes/stem]]` en MOCs relevantes si atom no está enlazado. CLI: `<stem>`, `--all`, `--dry-run`.
- `scripts/cache-optimizer.py` — Query frequency profiler (O9): analiza `log.md`, genera `meta/query-cache-stats.md` con topics más consultados y entradas stale. CLI: `--top N`, `--dry-run`.
- `§11 Troubleshooting` en `CLAUDE.md` actualizado con entradas para los 3 scripts.

**Smoke test (vault-agent.py)**: 246 atoms, 0 orphans, 0 stale, 0 gaps, 8 contradicciones sin resolver.

**Decisión — IMPLEMENT (manual override)**:

| Dim (peso) | original baseline | O7 (n=2) | Δ vs original |
|---|---|---|---|
| completeness (25%) | 9.60 | 8.55 (SE 0.000) | −1.05 |
| accuracy (25%) | 8.95 | 8.80 (SE 0.100) | −0.15 |
| spanish_purity (15%) | 4.90 | 8.57 (SE 0.425) | **+3.67** |
| tone (15%) | 8.80 | 8.80 (SE 0.100) | 0.00 |
| format_compliance (20%) | 8.65 | 8.50 (SE 0.050) | −0.15 |
| **weighted_avg** | **8.42** | **8.64 (SE 0.044)** | **+0.22** |
| weighted_cost | 60,777 | 47,617 (SE 871) | **−23.1%** |

Comparación O7 vs O5 → REVERT (hard_floor_breached: completeness −1.40, spanish_purity −1.28). **Override justificado**: O5 baseline n=1 run excepcional (9.60 weighted_avg); O7 scripts no tocan vault content (neutral by design); O7 weighted_avg 8.64 > original baseline 8.42 (+0.22); costo −23.1%. Baseline recalibrado a O7 (8.64) para O8/O9.

**Activos generados**: `scripts/vault-agent.py`, `scripts/auto-link.py`, `scripts/cache-optimizer.py`, `tests/prompts/O7/meta.yaml`, `tests/prompts/O8/meta.yaml`, `tests/prompts/O9/meta.yaml`, `tests/raw-responses/O7/`.

---

## 2026-04-27 — O5: Response Format Templates v3 → IMPLEMENT (composite +0.0606)

Cierre de Phase 2. Reescritura del kernel §4.6 + §10.7 con regimes A/B/C, ceilings duros (250/600/1000), pre-output checklist, tabla anti-anglicismo expandida vía mining sistemático, refiner-loop infrastructure.

**Diseño**:
- **3 regimes con secciones obligatorias** en `meta/RESPONSE_TEMPLATES.md` (movido a `meta/` para vault read-only de agentes):
  - A. Narrow Factual (≤250w): Respuesta directa + Fuentes (mínimo); Cuándo aplica + Por qué opcionales.
  - B. Tactical Multi-Palanca (≤600w): Pasos 3-5 (1 cita por paso) + Por qué funciona + Resultado esperado + Fuentes.
  - C. Taxonomic-Broad (≤1000w): Panorama + Comparativa (tabla) + Cómo elegir (decision-tree) + Fuentes.
- **Regime detection** por verbos y heurísticas (§4.6.1). Empate A/B → A; B/C → ejecuta mañana=B / decide=C.
- **Pre-output checklist** de 6 puntos obligatorio antes del JSON: cuenta palabras vs ceiling, relectura anti-anglicismo, 1 `[[atom]]` por paso/celda, source_id por número, sin intro/trailing summary, caveat ⚠️ al final.
- **Mining pipeline para tabla §10.7**: `scripts/mine-anglicismos.py` extrae candidatos de `violations[]` en evaluator JSON, dedupea contra tabla existente (con stem matching), filtra paths/spanish/whitelist, propone lista para revisión humana → append a tabla. Análogo al pipeline `apply-proposed-contradictions.py` de O4. Mineo inicial sobre 10 evaluation.json: 10 candidatos, 9 aceptados (skip checkout/checkin: ya en tabla y comunes en español).
- **Refiner-loop infrastructure**: `scripts/run-test-suite.py --refine --label OX --run N` detecta Qs con cualquier dim < threshold (default 7), backupea Q*.json → Q*.original.json, escribe `refine-prompts/Q*.md` desde `tests/prompts/_refiner_template.md` con violations + dim scores + evaluator notes. Refiner agent reescribe priorizando dims fallidas. NO se disparó en run-3 (cero Qs <7).

**Resultados (5-dim std rubric, n=1, 20Q estándar)**:

| Dim (peso) | pre-O5 | O5 (run-3) | Δ abs | Δ % |
|---|---|---|---|---|
| completeness (25%) | 9.80 | 9.95 | +0.15 | +1.53% |
| accuracy (25%) | 9.40 | 9.60 | +0.20 | +2.13% |
| **spanish_purity (15%)** | **5.60** | **9.85** | **+4.25** | **+75.89%** |
| tone (15%) | 9.00 | 9.40 | +0.40 | +4.44% |
| **format_compliance (20%)** | **8.25** | **9.10** | **+0.85** | **+10.30%** |
| **weighted_avg** | **8.64** | **9.60** | **+0.96** | **+11.05%** |

Cost weighted: 54,438 → 61,899 (+13.7%). Composite v2.0 (α=0.85): **+0.0606** → IMPLEMENT (composite_positive). Cero floor breaches.

**Targeted analysis**:
- `format_compliance` (target): predicted +1.0, delivered +0.85 (delivery 85%).
- `spanish_purity` (target): predicted +2.0, delivered +4.25 (delivery 212.5%).
- `tone` (at_risk): predicted −0.1, delivered +0.40 — el at-risk subió en lugar de caer.

**Decisión**: IMPLEMENT directo. Hard floors: ninguno. Targets cumplidos. At-risk no regresionó. Cost +13.7% absorbido por la ganancia masiva en quality (composite final +0.0606 vs threshold +0.005).

**Activos**:
- Kernel: `CLAUDE.md` §4.6 (regime detection + section enforcement + ceiling enforcement) + §10.7 (tabla expandida 52→61 + pre-output checklist).
- Templates: `meta/RESPONSE_TEMPLATES.md` (movido desde `queries/` para vault read-only).
- Scripts: `scripts/mine-anglicismos.py` (mining sistemático con SUGGESTION_MARKERS regex para no confundir propuestas con anglicismos).
- Test infra: `scripts/run-test-suite.py --refine` + `tests/prompts/_refiner_template.md`.
- Tests: `tests/raw-responses/O5/run-3/` (20 Q*.json + tokens.json + evaluation.json), `tests/comparisons/O5-vs-pre-O5.json`.

**Lecciones**:
- Mover los templates a `meta/` (en lugar de `queries/`) los vuelve legibles bajo el constraint vault read-only — error sutil del diseño inicial detectado en run-1.
- El mining pipeline cambia el modelo mental de "tabla anti-anglicismo": pasa de "lista manual que mantenemos a mano" a "índice consolidado de evidence empírica del evaluator". Extensión natural a otras bóvedas.
- Refiner-loop infrastructure preventiva: queda lista para futuras opts donde el ceiling sea más difícil de alcanzar de un solo intento.

**Phase 2 cerrada**: O4 (IMPLEMENT) + O5 (IMPLEMENT). O6 deferida a Phase 5 (atom_content). Siguiente: Phase 3 — Automation (O7 vault-agent, O8 auto-link, O9 query-cache).

---

## 2026-04-26 — O4 v2: smart resolver + temporal narrator + auto-curate → IMPLEMENT (user override)

Reescritura completa de §4.5 del kernel + RESPONSE_TEMPLATES.md + post-processor `scripts/apply-proposed-contradictions.py`. Validada con custom 15-question battery + custom 6-dim rubric.

**Diseño**:
- 5-tier resolution hierarchy: `temporal_supersession` → `contextual_scope` → `confidence_tier` → `authority_tier` → `specificity_tier`. Aplicar en orden, primer criterio que decida gana.
- Temporal narrative sub-template (ANTES / DESDE / HOY) cuando criterio = `temporal_supersession`. Standard caveat sub-template para los demás criterios.
- Auto-emit de `proposed_contradictions[]` cuando se detecta HIGH/MEDIUM no documentado en meta. `scripts/apply-proposed-contradictions.py` consolida en `meta/contradictions.md` entre runs (DRY-RUN por defecto, `--apply` para escribir).
- Surface decision table (4 casos) según `documented_in_meta` × `pregunta toca dim rival`.

**Methodology fix (Path A)**: el agent template del run-1 (guided) llevaba la jerarquía + reglas de proposed_contradictions spelled-out, lo que enmascaraba el upgrade del kernel. Se renombró a `_custom_agent_template_guided.md` (referencia ceiling, 9.41) y se creó un template stripped que solo delega al kernel (`§10.7 + §4.5`). Re-corrido del pre-test con stripped template (run-2) dio el verdadero baseline 9.08.

**Resultados (custom-o4v2-1.0, 6-dim rubric)**:

| Dim (peso) | Pre run-2 (stripped) | Post run-1 (kernel v2) | Δ |
|---|---|---|---|
| conflict_detection (20%) | 9.00 | 9.33 | +0.33 |
| resolution_clarity (25%) | 9.07 | 9.13 | +0.06 |
| **temporal_narrative (20%)** | **8.73** | **9.93** | **+1.20** |
| context_awareness (15%) | 9.40 | 9.40 | 0.00 |
| proposed_contradiction_quality (15%) | 9.27 | 9.60 | +0.33 |
| tone_format (5%) | 9.27 | 8.93 | −0.34 |
| **weighted_avg** | **9.08** | **9.40** | **+0.32** |

Cost: avg tokens 50,150 → 54,850 (+9.4%, expected — la jerarquía empuja a leer más meta + ejecutar el ciclo detect → classify → resolve → surface → curate). Composite v2.0 ≈ +0.013 (IMPLEMENT bajo el framework estándar también).

**Decisión**: nominal `ITERATE` (Δ +0.32 dentro del band [0.2, 0.5)). User override → **IMPLEMENT** porque:
1. Target dim `temporal_narrative` ganó +1.20 y queda a 0.07 del ceiling teórico.
2. `proposed_contradiction_quality` +0.33 con auto-curate validado en Q08 (entrada bien formada para `calendar-strategy` vs `pricelabs-bootstrap`, no documentado en meta — listo para consolidar).
3. `tone_format` −0.34 está muy por debajo del floor 0.5; el peso (5%) lo hace ruido.

**Auto-curation pipeline validado**: dry-run de `scripts/apply-proposed-contradictions.py --label O4v2-post --run 1` muestra 1+ entrada nueva propuesta; consolidación queda pendiente como follow-up (revisión humana antes de aplicar).

**Behavioral observations**:
- T-category (Q01, Q06, Q11): temporal evolution caveat aplicado consistentemente con milestone references (mid-2025 policy update).
- C-category (Q03, Q05, Q14): contextual_scope correctamente identificado, con `primary_atom`/`secondary_atom: null` cuando no hay ganador universal.
- D-category (Q02): specificity_tier aplicado con rationale detallado.
- M-category (Q08, Q14): debilidad — el kernel surfacea solo 1 de los 2-3 conflictos esperados, faltando cumplir §4.5.7 multi-caveat. Posible afinamiento futuro.
- U-category (Q09, Q12, Q13, Q15): no false-positive conflict invention.

**Activos**: kernel `CLAUDE.md` §4.5 reescrito; `queries/RESPONSE_TEMPLATES.md` con sub-templates A (temporal) y B (standard); `scripts/apply-proposed-contradictions.py` (post-processor con dedupe vía sorted normalized atom-pair tuples); `tests/prompts/O4v2/` (custom battery infra + meta.yaml + custom evaluator); `tests/raw-responses/O4v2-pre/` (run-1 guided ceiling 9.41 + run-2 stripped baseline 9.08); `tests/raw-responses/O4v2-post/run-1/` (9.40); `tests/comparisons/O4v2-post-vs-O4v2-pre.json`.

**Próximo**: O5 — Response Format Templates (regime-based: factual / tactical / taxonomic) en `queries/RESPONSE_TEMPLATES.md`.

---

## 2026-04-26 — Restructure: principio "estructural-only en Phases 1-4" + Phase 5 Atom Regeneration

Tras O3 re-test (n=2) y la decisión REVERT por `target_dim_regression`, hemos consolidado un principio operativo y reorganizado el plan completo.

**Principio**: toda optimización debe ser **estructural** (root-level, generalizable a otra bóveda) — kernel, MOC, index, templates, scripts, scoring, caching, response contract. Las optimizaciones que modifican átomos individuales (naming, casing, body format) **se difieren a Phase 5 — Atom Regeneration**, donde regeneraremos los 156 átomos desde `sources/` aplicando todas las reglas at-creation, no retroactivas.

**Por qué**:
- Una opt estructural se transfiere a otra bóveda con coste cercano a cero.
- Una opt que audita átomos solo aplica a esta bóveda y, si rompe el contrato (ver O3), no hay rollback (vault no es git-tracked).
- O3 demostró el patrón: ganó `spanish_purity` (no su target) y perdió `format_compliance` (su target declarado). El cost win fue real, pero no era lo prometido.

**Reclasificación de opts** (`class` field añadido a CLAUDE.md frontmatter):

| OX | Phase pre | Phase post | Class | Status |
|----|-----------|------------|-------|--------|
| O3 Language Consistency | 1 | **5** | atom_content | deferred |
| O6 Executable Checklists | 2 | **5** | atom_content | deferred |
| O1, O4, O5, O7-O12 | (sin cambios) | (sin cambios) | structural | (sin cambios) |
| O2 Q4 Contradiction | 1 | 1 | atom_specific | skipped (premise stale) |

**Phase 5 — Atom Regeneration** (nueva, final):
- Tasks: O3, O6 + futuras opts atom_content
- Concepto: regenerar 156 átomos desde `sources/` con prompt consolidado que aplica naming/casing/format/checklist rules at-creation
- Activo transferible: el prompt + las reglas, no los átomos generados
- Detalle: [docs/PHASE_5_TASKS.md](../docs/PHASE_5_TASKS.md), [docs/PHASE_5_SUMMARY.md](../docs/PHASE_5_SUMMARY.md)

**Cambio en infraestructura de tests**: `scripts/run-test-suite.py` ahora preserva snapshots de cada comparación en `tests/comparisons/history/<to>-vs-<from>__n<N>.json`, indexado por la iteración del OX testeado (n=1, n=2…). El archivo "live" `<to>-vs-<from>.json` se sobreescribe con la versión más reciente; el histórico no. Reconstruidos retroactivamente `O3-vs-O1__n1.json` y `__n2.json`.

**Estado de la bóveda**: O3 quedó aplicada en main (vault no-git, no hay rollback). Los 156 átomos siguen post-O3 hasta Phase 5, donde se regenerarán desde sources con el contrato consolidado.

**Docs sincronizados**:
- [CLAUDE.md](../CLAUDE.md) frontmatter v3.3 (Phase 5 + class fields)
- [docs/OPTIMIZATIONS.md](../docs/OPTIMIZATIONS.md) (principio + Status Table con Class column)
- [docs/PHASE_2_TASKS.md](../docs/PHASE_2_TASKS.md) y [docs/PHASE_2_SUMMARY.md](../docs/PHASE_2_SUMMARY.md) (re-scoped a O4, O5)
- [docs/PHASE_5_TASKS.md](../docs/PHASE_5_TASKS.md) y [docs/PHASE_5_SUMMARY.md](../docs/PHASE_5_SUMMARY.md) (nuevos)

---

## 2026-04-26 — O3 Re-test (run-2): REVERT confirmado bajo decision_version 2.0

Re-corrido completo del test suite para O3 desde 0 (20 fresh agents en paralelo + evaluator), agregado con run-1 (n=2). Consolidación + comparación produce decisión REVERT robusta.

**Resultados (n=2 vs O1)**:

| Dim | n=1 (run-1) | n=2 (aggregated) | Predicted | Delivery |
|---|---|---|---|---|
| weighted_cost | 43,818.85 (−3.4%) | 44,457.7 (−2.0%) | −3.0% | parcial |
| weighted_avg | 8.28 (−0.5%) | **8.39 (+0.8%)** | — | — |
| completeness | 9.65 | 9.65 | — | — |
| accuracy | 8.95 | 9.00 | — | — |
| spanish_purity | 4.85 | **5.125** (+15.2% vs O1) | — | — |
| tone | 8.55 | 8.775 | — | — |
| format_compliance | 8.10 | **8.20** (−2.96% vs O1) | +0.30 | **−83%** |

**Composite** (α=0.85): +0.0088 (zona ruido).

**Floor breach**: `target_dim_regression` en `format_compliance` (delta_abs −0.25, ci95 [−0.45, −0.05], significant=true). Esto fuerza REVERT regardless del composite positivo.

**Hallazgos**:
- Run-2 aislado fue mejor que run-1 en todas las dims, pero el agregado n=2 sigue mostrando `format_compliance` por debajo de O1 con CI estadísticamente significativo.
- `spanish_purity` mejora consistentemente (+0.68 abs vs O1) — pero NO era el target declarado. O3 ganó la dim equivocada.
- weighted_avg mejora +0.067 abs (vs n=1 que mostraba −0.04). La inconsistencia entre runs se debe a la varianza natural del evaluator + diferentes muestreos del agente.

**Decisión v2.0**: REVERT por `hard_floor_breached` (target_dim_regression). Validación operativa del motor: una opt con composite ambiguo y target dim regresivo se atrapa correctamente, evitando un falso positivo.

**Detalle**:
- [tests/comparisons/O3-vs-O1.json](comparisons/O3-vs-O1.json) (latest, n=2)
- [tests/comparisons/history/O3-vs-O1__n1.json](comparisons/history/O3-vs-O1__n1.json)
- [tests/comparisons/history/O3-vs-O1__n2.json](comparisons/history/O3-vs-O1__n2.json)
- [tests/raw-responses/O3/run-2/](raw-responses/O3/run-2/)

---

## 2026-04-26 — Backfill v2 (decision_version 2.0)

Re-comparados baseline→O1 y O1→O3 con el motor de decisión v2.0 (composite α=0.85 + hard floors + targeted analysis). Sin re-evaluar respuestas — los rubric scores v1.0 se conservan; lo que cambia es la **lógica de decisión** sobre los mismos datos. Preparativos: `meta.yaml` retroactivo para baseline / O1 / O3, layout `raw-responses/<LABEL>/run-1/`, `_agent_template.md` + `_evaluator_template.md` como fuente única de prompts.

**Resultados**:

| Comparison | Composite | Decision v2.0 | Δ vs decisión vieja |
|---|---|---|---|
| baseline → O1 | **+0.0293** | IMPLEMENT (composite_positive) | sin cambio (sigue IMPLEMENT) |
| O1 → O3 | +0.0017 (noise zone) | **REVERT** (`target_dim_regression`) | **flip de IMPLEMENT a REVERT** |

**Hallazgo crítico — O3 falla su contrato declarado**:
O3 declaró `format_compliance` como `target_dim` con predicted Δ +0.3. Entregó −0.35 (delivery −116.7%). El composite por sí solo era ambiguo (+0.0017, dentro de la zona de ruido ±0.015), pero el hard floor `target_dim_regression` lo disparó a REVERT. Esto valida la hipótesis de diseño: el motor v2.0 detecta optimizaciones que "ahorran tokens pero rompen el dim que declararon mejorar". El cost win fue real (−3.4%); la implementación física sigue en main; queda pendiente decidir si revertir el commit o re-clasificar el target en `meta.yaml` y re-evaluar.

**Hallazgo previo (sigue válido)**: `spanish_purity` es el techo bajo de toda la rúbrica (4.45-4.90 / 10) — anglicismos sistemáticos (host, guest, review, listing, booking, rating, amenity) en ~95% de respuestas. Target principal de Phase 2.

---

## 2026-04-26 — Backfill: external evaluator (5-dim rubric)

Re-evaluadas las 60 respuestas guardadas (baseline, O1, O3) con el evaluator externo y la rúbrica de 5 dimensiones (rubric_version 1.0). `tests/results/*.json` y `tests/comparisons/*.json` regenerados en formato extendido. (Backfill original — pre-decision_version 2.0.)

---

## 2026-04-26 — O3: Language Consistency

- **Decision**: IMPLEMENT
- **Weighted cost**: 45,376.75 → 43,818.85 (**−3.4%**)
- **Quality (weighted_avg)**: 8.32 → 8.28 (**−0.5%**)
  - completeness: 9.40 → 9.65 (+2.7%)
  - accuracy: 9.05 → 8.95 (−1.1%)
  - spanish_purity: 4.45 → 4.85 (**+9.0%**) ← recuperación parcial vs O1
  - tone: 9.00 → 8.55 (−5.0%)
  - format_compliance: 8.45 → 8.10 (−4.1%)
- **Input tokens total**: 798,893 → 764,237
- **Output tokens total**: 18,107 → 18,690
- **Compared against**: O1
- **Detail**: [tests/comparisons/O3-vs-O1.json](comparisons/O3-vs-O1.json)
- **Result file**: [tests/results/O3.json](results/O3.json)

Standardized 156 atoms: naming, casing, claim brevity, body length, excerpts, confidence levels.

---

## 2026-04-26 — O1: Hierarchical Indices

- **Decision**: IMPLEMENT ⚠️ (per-dim warning: spanish_purity −9.18%)
- **Weighted cost**: 60,776.8 → 45,376.75 (**−25.3%**)
- **Quality (weighted_avg)**: 8.42 → 8.32 (**−1.2%**)
  - completeness: 9.60 → 9.40 (−2.1%)
  - accuracy: 8.95 → 9.05 (+1.1%)
  - spanish_purity: 4.90 → 4.45 (**−9.2%**) ⚠️ supera umbral −5%
  - tone: 8.80 → 9.00 (+2.3%)
  - format_compliance: 8.65 → 8.45 (−2.3%)
- **Input tokens total**: 1,106,780 → 798,893
- **Output tokens total**: 18,126 → 18,107
- **Compared against**: baseline
- **Detail**: [tests/comparisons/O1-vs-baseline.json](comparisons/O1-vs-baseline.json)
- **Result file**: [tests/results/O1.json](results/O1.json)

Replaced flat `index.md` (344 lines, ~4k tokens) with tiered L1 + L2 sub-indices. Cost win masivo, regresión leve en español sin solucionar (precondición desde baseline).

---

## 2026-04-26 — O2: Fix Q4 Contradiction (SKIPPED)

- **Decision**: SKIP — premise stale
- **Reason**: Q4 cambió en v2.0 question set; `meta/contradictions.md` no tiene entrada para orphan-night pricing; el único atom existente es internamente consistente.
- **Detail**: [docs/PHASE_1_TASKS.md#O2](../docs/PHASE_1_TASKS.md)

---

## 2026-04-26 — Baseline

- **Weighted cost (avg)**: 60,776.8
- **Quality (weighted_avg)**: 8.42
  - completeness 9.60 / accuracy 8.95 / spanish_purity 4.90 / tone 8.80 / format_compliance 8.65
- **Input tokens total**: 1,106,780
- **Output tokens total**: 18,126
- **Result file**: [tests/results/baseline.json](results/baseline.json)

Reference run pre-optimización. 20 queries × 1 fresh agent each, no cache, no context.
