# OPTIMIZATIONS — Master Overview

**Single source of truth para qué se ha hecho, qué está pendiente, y cuál es el siguiente paso.**

Si necesitas detalle de ejecución, ver `docs/PHASE_<N>_TASKS.md`. Para diseño/justificación, ver `docs/PHASE_<N>_SUMMARY.md`.

State autoritativo: YAML frontmatter en [CLAUDE.md](../CLAUDE.md). Esta tabla es un mirror humano — re-generar cuando cambie el estado.

---

## Principio de optimización (2026-04-26)

**Toda optimización debe ser estructural (root-level, generalizable a otra bóveda)**: cambios al index, MOC, kernel, templates, automatización, response contract, scripts, caching, scoring, etc.

**Las optimizaciones que modifican átomos individuales** (naming, casing, body format, conversión a Dataview, fixes específicos de un átomo) **se difieren a Phase 5 — Atom Regeneration**, donde regeneraremos los 156 átomos desde `sources/` aplicando todas las reglas estructurales validadas en Phases 1-4 + las reglas de regeneración (O3, O6, futuras) at-creation, no retroactivas.

**Por qué**: una optimización estructural se transfiere a otra bóveda con casi cero coste. Una optimización que audita átomos solo aplica a esta bóveda y, si la implementación rompe algún contrato (ver O3), no hay rollback (la bóveda no es git-tracked).

---

## Status Table (12 optimizaciones)

| OX | Phase | Nombre | Class | Status | Cost Δ | Quality Δ (weighted_avg) | Composite | Decisión (v2.0) | Effort |
|----|-------|--------|-------|--------|--------|--------------------------|-----------|------------------|--------|
| O1 | 1 | Hierarchical Indices | structural | ✅ complete | **−25.3%** | −1.2% | **+0.0293** | IMPLEMENT ⚠ | 4h |
| O2 | 1 | Fix Q4 Contradiction | atom_specific | ⏭ skipped | — | — | — | premise_stale | 0.5h |
| O3 | 5 | Language Consistency | atom_content | ⛔ deferred | −3.4% (vault state in place) | +0.067 (n=2) | +0.0088 | **REVERT** (target_dim_regression) → diferida | 2h |
| O4 | 2 | Contradiction Detection L1 | structural | ⏸ not_started | — | — | — | — | 3h |
| O5 | 2 | Response Format Templates | structural | ⏸ not_started | — | — | — | — | 2.5h |
| O6 | 5 | Executable Checklists | atom_content | ⛔ deferred | — | — | — | — → diferida | 1.5h |
| O7 | 3 | Agent Orchestration | structural | ⏸ not_started | — | — | — | — | 8h |
| O8 | 3 | Auto-Linking System | structural | ⏸ not_started | — | — | — | — | 4h |
| O9 | 3 | Query Caching | structural | ⏸ not_started | — | — | — | — | 6h |
| O10 | 4 | Semantic Gap Detection | structural | ⏸ not_started | — | — | — | — | 3h |
| O11 | 4 | Backlink Generation | structural | ⏸ not_started | — | — | — | — | 4h |
| O12 | 4 | RAG Fallback | structural | ⏸ not_started | — | — | — | — | 6h |

**Class**:
- `structural` — cambia infraestructura/automatización; generaliza a otras bóvedas. Ejecutar en Phases 1-4.
- `atom_content` — modifica átomos individuales (naming, body, format). Diferir a Phase 5.
- `atom_specific` — fix específico a un átomo singular; usualmente skipped si la premisa está stale.

**Cost Δ**: weighted cost (input + 6×output) vs punto anterior. Negativo = mejora.
**Quality Δ**: rúbrica de 5 dimensiones evaluada por agente externo (ver [TEST_PROTOCOL.md](TEST_PROTOCOL.md) §Rubric). Métrica primaria: `weighted_avg`.
**Composite** (decision_version 2.0): `α·quality_delta_norm + (1−α)·cost_delta_norm`, α=0.85. Hard floors override composite (REVERT regardless si target dim regresiona, accuracy abs drop ≥1.0, weighted_avg abs drop ≥7.0, o cualquier dim cae ≥1.0 abs).

⚠ **O1**: pasa por composite (+0.0293) pero `spanish_purity` cayó −9.18% (4.90 → 4.45). Bajo decision_version 2.0 esto no dispara floor (drop abs 0.45 < 1.0) pero sigue siendo el punto débil sistémico. Phase 2 (O4, O5) debería atacarlo vía templates.

⛔ **O3 (deferred 2026-04-26)**: dos runs (n=2) confirman que O3 es atom_content. Re-clasificada y diferida a Phase 5. La bóveda mantiene los 156 átomos en estado post-O3 (no hay git rollback); en Phase 5 se regenerarán desde `sources/` con todas las reglas estructurales y de naming consolidadas. **Lección**: una optimización que modifica átomos retroactivamente no generaliza, no se puede revertir, y esconde su impacto real (O3 ganó spanish_purity +0.68 — no su target declarado — y perdió format_compliance −0.25, su target declarado).

---

## Resultados por punto de medida

| Label    | n_runs | Weighted cost | Weighted avg | Completeness | Accuracy | Spanish | Tone | Format | Comparison |
|----------|--------|---------------|--------------|--------------|----------|---------|------|--------|------------|
| baseline | 1      | 60,776.8      | 8.42         | 9.60         | 8.95     | 4.90    | 8.80 | 8.65   | —          |
| O1       | 1      | 45,376.75     | 8.32         | 9.40         | 9.05     | 4.45    | 9.00 | 8.45   | [O1-vs-baseline.json](../tests/comparisons/O1-vs-baseline.json) |
| O3       | 2      | 44,458 (SE 639) | 8.39 (SE 0.107) | 9.65    | 9.00 (SE 0.05) | 5.12 (SE 0.27) | 8.78 (SE 0.22) | 8.20 (SE 0.10) | [O3-vs-O1.json](../tests/comparisons/O3-vs-O1.json) (latest n=2) |

**Histórico de comparaciones**: `tests/comparisons/history/<from>-vs-<to>__n<N>.json` preserva cada iteración (n=1, n=2, …) sin sobreescribir. Ver `tests/comparisons/history/O3-vs-O1__n1.json` y `__n2.json`.

**Patrón transversal**: `spanish_purity` (4.45-5.12 / 10) es el techo bajo de toda la rúbrica. Anglicismos sistemáticos (host, guest, review, listing, booking, rating, amenity) presentes en ~95% de respuestas. Atacar vía O5 (Response Format Templates) — instrucción explícita anti-anglicismos en el output, no en los átomos.

---

## Phases — Estado

| Phase | Nombre | Status | Tasks | Completed | Skipped | Deferred |
|-------|--------|--------|-------|-----------|---------|----------|
| 1 | Critical Path | ✅ complete | O1 | O1 | O2 | O3 |
| 2 | Quality Foundation (Structural) | ⏳ pending_approval | O4, O5 | — | — | O6 |
| 3 | Automation | ⏸ not_started | O7, O8, O9 | — | — | — |
| 4 | Integration | ⏸ not_started | O10, O11, O12 | — | — | — |
| 5 | Atom Regeneration | ⏸ not_started | O3, O6 | — | — | — |

---

## Descripción de cada optimización (resumen)

### Phase 1 — Critical Path (complete)

**O1: Hierarchical Indices** ✅ — Reemplazar `index.md` plano (344 líneas, ~4k tokens) con estructura tiered: L1 overview ≤100 líneas + L2 sub-índices (`index/topics.md`, `index/atoms.md`, `index/queries.md`). Resultado: −25.3% cost, quality estable. Estructural — generaliza a cualquier bóveda. [PHASE_1_TASKS.md#O1](PHASE_1_TASKS.md).

**O2: Fix Q4 Contradiction** ⏭ — Saltado. La premisa estaba stale: la pregunta Q4 cambió en v2.0 del question set, y `meta/contradictions.md` no tenía entrada para orphan-night pricing. Atom-specific. [PHASE_1_TASKS.md#O2](PHASE_1_TASKS.md).

**O3: Language Consistency** ⛔ deferred → Phase 5 — ver descripción en Phase 5.

### Phase 2 — Quality Foundation (Structural) (pending_approval) ← **siguiente**

**O4: Contradiction Detection L1** — Heurística que detecta conflictos semánticos al leer atoms durante query (no solo en lint). Si dos atoms del mismo topic tienen claims opuestos sin resolver en `meta/contradictions.md`, se incluye caveat en la respuesta. Estructural: lógica del kernel.

**O5: Response Format Templates** — Templates canónicos por régimen (factual / tactical / taxonomic) en `queries/RESPONSE_TEMPLATES.md`. Reduce cognitive load. **Aprovechar para añadir reglas anti-anglicismos** (apunta al `spanish_purity` floor). Estructural: nuevo artifact + referencia en CLAUDE.md §10.7.

**O6: Executable Checklists** ⛔ deferred → Phase 5 (modifica átomos a formato Dataview).

### Phase 3 — Automation (not_started)

**O7: Agent Orchestration** — Claude Code agente programado (cada 3 días) que corre lint, detecta gaps, propone ingests. `scripts/vault-agent.py`. Estructural: pure script.

**O8: Auto-Linking System** — Al crear atom nuevo, escanear vault y autoinsertar backlinks en MOCs. `scripts/auto-link.py`. Estructural: automatización at-creation. Backfill retroactivo se hará en Phase 5 si fuera necesario.

**O9: Query Caching** — Cachear top-20% queries con refresh semanal + similarity detection. `scripts/cache-optimizer.py`. Estructural.

### Phase 4 — Integration (not_started)

**O10: Semantic Gap Detection** — Score actionability per atom; flag topics donde el average está debajo del threshold. Estructural: produce reporte `meta/gaps-YYYY-MM-DD.md`, no modifica átomos.

**O11: Backlink Generation** — `meta/backlinks.md` auto-generado con grafo de citas (atom→source, atom→atom, query→atom). Estructural: meta artifact derivado.

**O12: RAG Fallback** — Si atom-search devuelve shortlist vacío, caer a embedding-based retrieval sobre `sources/`. Marcar respuestas como lower confidence. Estructural: fallback layer.

### Phase 5 — Atom Regeneration (not_started, final)

**Concepto**: una vez validadas las opts estructurales, regeneramos los 156 átomos desde `sources/` (transcripciones raw) aplicando todas las reglas en el momento de creación. Esto da: (1) átomos consistentes con el contrato final, (2) la posibilidad de aplicar reglas de naming/casing/format sin riesgo de rollback, (3) un punto de partida limpio para futuras bóvedas que reutilicen este pipeline.

**O3: Language Consistency** — Reglas de naming `<topic>--<slug>.md`, casing canónico, claims ≤2 frases, bodies ≤8 líneas, excerpts ≤50 chars en comillas, confidence ∈ {high, medium, low}. **At-creation**, no audit retroactivo. Aplica como parte del prompt de generación.

**O6: Executable Checklists** — Procedimientos en átomos se generan en formato Dataview-compatible. **At-creation**.

**Futuras opts atom_content** se anexan aquí.

---

## Cómo se actualiza este archivo

1. Tras correr `--compare --from <PREV> --to OX`, leer `tests/comparisons/OX-vs-<PREV>.json` (latest) y `tests/comparisons/history/OX-vs-<PREV>__n<N>.json` (snapshot por iteración)
2. Actualizar la fila de OX en la **Status Table** (cost Δ, quality Δ, composite, decisión)
3. Añadir fila a **Resultados por punto de medida**
4. Si la optimización completa una Phase, actualizar **Phases — Estado**
5. Sincronizar el YAML de [CLAUDE.md](../CLAUDE.md) (`optimizations.OX.status`, `cost_delta_pct`, `quality_delta`, `class`)
6. Append a [tests/history.md](../tests/history.md)
