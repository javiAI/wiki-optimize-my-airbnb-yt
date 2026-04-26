# Testing History — Optimization Timeline

Append-only log of test runs and optimization decisions. Newest entries at the top.

Single source of truth para descripción y estado: [docs/OPTIMIZATIONS.md](../docs/OPTIMIZATIONS.md).

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
