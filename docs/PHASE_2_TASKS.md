# Phase 2: Execution Tasks — Quality Foundation (Structural)

**Status**: Phase 2 is pending_approval.

Execute tasks in order: **O4, O5**. (O3 was deferred to Phase 5 on 2026-04-26 — atom_content opt; O6 was also moved to Phase 5 — modifies atom procedure format.)

**Phase 2 scope**: solo opts estructurales (kernel logic, templates, response contract). No tocar contenido de átomos. Las opts atom_content viven en Phase 5 (Atom Regeneration), donde se regeneran los 156 átomos desde sources con todas las reglas consolidadas.

---

## Mandatory pre-execution template (A/B/C)

**Before implementing any optimization in this phase**, the three sections (A. Concept, B. Technical, C. Expected improvements) must be filled in below. The Expected-improvements section is a **prediction commitment**: after running the test suite, compare predicted vs actual deltas to validate or invalidate the hypothesis.

**Section C must be mirrored into `tests/prompts/OX/meta.yaml`** (decision_version 2.0 — see [TEST_PROTOCOL.md](TEST_PROTOCOL.md) §meta.yaml). The script reads meta.yaml to (1) classify each rubric dim as `target` / `at_risk` / `neutral`, (2) compute composite score, and (3) trigger hard-floor breaches like `target_dim_regression` if a declared target dim drops. Required fields: `target_dims`, `at_risk_dims`, `neutral_dims`, `predicted_deltas` (cost + per-dim abs deltas), `optimization_type`, `allow_repetition`. Section C in this doc is the human narrative; meta.yaml is the machine-readable mirror — they must agree.

If predictions deviate by more than ~50% from actuals on any rubric dimension, document the surprise in `tests/history.md` and update the hypothesis model for the next OX.

---

## O4: Contradiction Detection L1 (3 hours)

### A. Concept (intuitivo)

Hoy las contradicciones entre atoms solo se detectan en el lint manual (§4.3) — son invisibles durante la query. Esta optimización añade un *guardia en tiempo de lectura*: cuando el agente arma el shortlist de atoms para responder, escanea si hay otros atoms del mismo tópico con claims opuestos. Si los hay y no están resueltos en `meta/contradictions.md`, la respuesta incluye un caveat explícito ("⚠️ Conflicting advice: [[A]] dice X, [[B]] dice Y").

Analogía: pasar de "auditoría anual" a "alarma de incendios". El usuario ve el conflicto en el momento, no después.

### B. Técnica

**Cambios concretos**:

1. Añadir substep §4.2.6a en CLAUDE.md kernel:
   - Para cada atom en el shortlist, scan `MOC/<topic>.md`
   - Comparar `claim:` con otros atoms del mismo tópico
   - Si claim opuesto detectado: cross-check con `meta/contradictions.md`
   - Si NO está resuelto: marcar `potential_conflict` con severity HIGH/MEDIUM/LOW

2. Crear template de display en queries/RESPONSE_TEMPLATES.md (placeholder hasta O5):
   ```markdown
   ⚠️ **Conflicting advice**: [[atom-A]] recomienda X, mientras [[atom-B]] recomienda Y.
   **Confidence**: atom-A es higher-confidence (0.81 vs 0.63).
   **Caveat**: atom-B aplica si [condición].
   See [[meta/contradictions]].
   ```

3. Severity scoring:
   - HIGH: mismo topic, contradicción explícita
   - MEDIUM: mismo topic, evidencia conflictiva
   - LOW: topic relacionado, recomendación distinta

**Archivos tocados**: `CLAUDE.md` (§4.2.6a), `meta/contradictions.md` (existente, sin cambios), opcionalmente `queries/RESPONSE_TEMPLATES.md`.

### C. Mejoras esperadas + justificación

| Métrica | Predicción | Por qué |
|---------|-----------|---------|
| `weighted_cost` | +1% a +3% | Conflict-check añade ~50-200 tokens por query (lectura extra de MOC). Pequeño coste adicional aceptable. |
| `completeness` | +0.3 a +0.5 | Caveats sobre conflictos no anotados son cobertura genuina extra. |
| `accuracy` | +0.2 a +0.4 | Detectar contradicciones evita afirmar como hecho lo que está en disputa. |
| `spanish_purity` | estable | Cambio de logic, no de output language. |
| `tone` | estable o -0.1 | El caveat con ⚠️ puede sentirse alarmista; mitigarlo con redacción cálida. |
| `format_compliance` | estable | Format §10.7 ya admite caveats. |
| **`weighted_avg`** | **+0.15 a +0.30** | Mejora de accuracy + completeness pesa 50% del rubric. |

**Hipótesis principal**: la mayoría de las preguntas del test set NO tocan contradicciones, así que el coste extra solo se paga en ~3-5 de las 20 queries. Si más queries activan el guardia, el coste subirá más; si las contradicciones detectadas no son relevantes, accuracy/completeness no mejorarán y debería ITERATE.

### Steps

1. **Add conflict-check logic to §4.2 step 6**
   - When selecting atom candidates for shortlist, cross-reference each atom's topics
   - For each atom selected, scan MOC for other atoms with same topic
   - Build conflict matrix: does other atom have opposite claim?
   - Mark conflicts for display

2. **Update CLAUDE.md kernel (§4.2.6a — new section)**
   ```
   6a. CONFLICT CHECK (new substep)
       For each candidate atom:
       - Scan MOC[topics[0]] for other atoms
       - If same topic, different claim: flag as "potential_conflict"
       - Check meta/contradictions.md: resolved or unresolved?
       - If unresolved: add caveat to response
   ```

3. **Create scoring for conflict severity**
   - Same topic, explicit contradiction: severity=HIGH
   - Same topic, conflicting evidence: severity=MEDIUM
   - Related topic, different recommendation: severity=LOW
   - Use severity to decide whether to flag in response

4. **Create conflict display template**
   ```markdown
   ⚠️ **Conflicting advice**: [[atom-A]] recommends X, while [[atom-B]] recommends Y.
   **Confidence**: atom-A is higher-confidence (0.81 vs 0.63 based on recency/popularity).
   **Caveat**: atom-B's approach applies if [condition].
   See [[meta/contradictions]] for full analysis.
   ```

5. **Test with known contradictions**
   - Run a query that touches a known contradiction
   - Verify: response includes conflict caveat if both atoms in shortlist
   - Verify: caveat cites higher-confidence atom as primary

6. **Update `log.md`**
   ```
   ## [YYYY-MM-DD] O4 complete | Contradiction detection L1
   - Added §4.2.6a conflict-check substep to CLAUDE.md kernel
   - Implemented severity scoring (HIGH/MEDIUM/LOW)
   - Created conflict caveat template
   ```

7. **Git commit**
   ```bash
   git commit -m "O4: Contradiction detection L1 (real-time conflict flagging)"
   ```

### Verification Checklist

- [ ] §4.2.6a added to CLAUDE.md
- [ ] Severity scoring defined and documented
- [ ] Conflict template created
- [ ] Test query executed against known conflict
- [ ] Response includes caveat with correct format
- [ ] `log.md` updated
- [ ] Git commit made

### Test (per docs/TEST_PROTOCOL.md)

```bash
python3 scripts/run-test-suite.py --prepare --label O4
# 20 parallel Agent calls; write tests/raw-responses/O4-tokens.json
python3 scripts/run-test-suite.py --prepare-evaluator --label O4
# 1 evaluator Agent call
python3 scripts/run-test-suite.py --consolidate --label O4
python3 scripts/run-test-suite.py --compare --from O3 --to O4
```

Read decision from `tests/comparisons/O4-vs-O3.json`. Validate predicted-vs-actual against the C section above.

---

## O5: Response Format Templates (2.5 hours)

### A. Concept (intuitivo)

Hoy las respuestas tienen formato libre dentro de §10.7 — cada agente decide cómo estructurar. Resultado: variabilidad innecesaria en `format_compliance`. Esta optimización **define plantillas canónicas por régimen de pregunta** (factual / tactical / taxonomic) y obliga al kernel a matcheada antes de responder.

Analogía: pasar de "escribe libremente respetando el estilo" a "rellena este formulario". Reduce decisión cognitiva del agente y produce respuestas más predecibles para el usuario.

### B. Técnica

**Tres regímenes**:
- **A (Narrow Factual)**: Question → answer 1-2 frases → conditions → sources → confidence
- **B (Tactical Multi-Palanca)**: Question → approach → 3-5 numbered steps con `[[atom]]` → why this works → expected outcome → caveats → sources → confidence
- **C (Taxonomic/Broad)**: Question → overview → comparison table → how to choose → see also → sources → confidence

**Cambios**:
1. Crear `queries/RESPONSE_TEMPLATES.md` con las 3 plantillas + ejemplos
2. Añadir §4.2.9a (FORMAT CHECK) al kernel: identificar régimen, matchear template, verificar secciones
3. Reformatear queries existentes en `queries/` que no cumplan
4. Documentar criterio de regimen detection (heurística por palabras-clave de la pregunta)

**Archivos tocados**: nuevo `queries/RESPONSE_TEMPLATES.md`, `CLAUDE.md` (§4.2.9a), `queries/*.md` existentes (reformat selectivo).

### C. Mejoras esperadas + justificación

| Métrica | Predicción | Por qué |
|---------|-----------|---------|
| `weighted_cost` | -3% a -8% | Templates más estructurados → respuestas más concisas → menos output tokens (que pesan 6×). |
| `completeness` | +0.2 a +0.5 | El template fuerza que aparezcan secciones obligatorias (caveats, conditions). |
| `accuracy` | estable | El cambio es de format, no de contenido. |
| `spanish_purity` | estable | El template es estructural, no léxico. |
| `tone` | -0.2 a +0.1 | Riesgo: templates pueden sentirse rígidos/burocráticos. Mitigación: el template indica tono cálido en cada sección. |
| `format_compliance` | +1.0 a +1.8 | Es el target directo del cambio. Era la dimensión más débil. |
| **`weighted_avg`** | **+0.20 a +0.45** | format_compliance pesa 20%, mejora grande directa. |

**Hipótesis principal**: la variabilidad actual en formato es el principal driver de format_compliance bajo. Si los templates son demasiado rígidos, tone caerá; si son útiles, tone se mantiene.

### Steps

1. **Create templates document**
   ```bash
   touch $VAULT_PATH/queries/RESPONSE_TEMPLATES.md
   ```

2. **Define Regime A (Narrow Factual) template**
   ```markdown
   **Question**: <user question>

   **Answer**: <direct answer, 1-2 sentences>

   **Applies only if**: <conditions where answer is valid>

   **See also**: [[related-atom-1]], [[related-atom-2]]

   **Confidence**: High (based on [[source-id]], 0.9)
   ```

3. **Define Regime B (Tactical Multi-Palanca) template**
   ```markdown
   **Question**: <user question>

   **Approach**: <intro explaining the strategy>

   **Steps**:
   1. [[atom-1]] — <step 1 summary>
   2. [[atom-2]] — <step 2 summary>
   3. [[atom-3]] — <step 3 summary>

   **Why this works**: <explanation of interdependencies>

   **Expected outcome**: <what to expect>

   **Caveats**: [[atom-caveat]] applies if <condition>

   **Confidence**: Medium-High (based on [[source-A]], [[source-B]])
   ```

4. **Define Regime C (Taxonomic/Broad) template**
   ```markdown
   **Question**: <user question>

   **Overview**: <landscape of options/factors>

   **Comparison**:
   | Factor | Option A | Option B | Option C |
   |--------|----------|----------|----------|
   | [[aspect-1]] | ... | ... | ... |
   | [[aspect-2]] | ... | ... | ... |

   **How to choose**: <decision heuristic>
   - Use Option A if [[condition-a]]
   - Use Option B if [[condition-b]]

   **See also**: [[related-topic-1]], [[related-topic-2]]

   **Confidence**: Medium (incomplete coverage; only 8 of 12 aspects covered)
   ```

5. **Audit existing queries**, reformat to match templates as needed.

6. **Add template reference to §4.2 (CLAUDE.md kernel)**
   ```
   9a. FORMAT CHECK
       - Identify query regime (A/B/C from step 4)
       - Match response to {regime}_TEMPLATE from queries/RESPONSE_TEMPLATES.md
       - Verify all required sections present
   ```

7. **Update `log.md`**.

8. **Git commit**
   ```bash
   git commit -m "O5: Response format templates (Regime A/B/C standardization)"
   ```

### Verification Checklist

- [ ] `queries/RESPONSE_TEMPLATES.md` created with 3 templates
- [ ] Regime A template: answer + conditions + sources + confidence
- [ ] Regime B template: steps + why + caveats + sources + confidence
- [ ] Regime C template: comparison + decision heuristic + sources + confidence
- [ ] Existing queries reformatted (or marked legacy)
- [ ] §4.2.9a added to CLAUDE.md
- [ ] `log.md` updated
- [ ] Git commit made

### Test (per docs/TEST_PROTOCOL.md)

```bash
python3 scripts/run-test-suite.py --prepare --label O5
# 20 parallel Agent calls; write tests/raw-responses/O5-tokens.json
python3 scripts/run-test-suite.py --prepare-evaluator --label O5
python3 scripts/run-test-suite.py --consolidate --label O5
python3 scripts/run-test-suite.py --compare --from O4 --to O5
```

Validate predicted-vs-actual deltas against the C section.

---

## O6 — DEFERRED to Phase 5

O6 (Executable Checklists — atoms procedurales → formato Dataview con `- [ ]`) modifica el contenido de los átomos. Bajo el principio de "solo opts estructurales en Phases 1-4", se ha movido a [PHASE_5_TASKS.md](PHASE_5_TASKS.md) donde se aplicará at-creation cuando regeneremos los 156 átomos desde `sources/`.

---

## After Phase 2 Completion

1. **Update CLAUDE.md YAML**:
   ```yaml
   phase_2:
     status: "complete"
     progress: 100
   automation:
     current_phase: 3
     phase_status: "pending_approval"
   ```

2. **Update `docs/OPTIMIZATIONS.md`** status table with final cost/quality deltas.

3. **Append to `tests/history.md`** entries for O4, O5.

4. **Git commit**:
   ```bash
   git commit -m "Phase 2 complete: Quality foundation structural (O4, O5)"
   ```

5. **Show Phase 3 summary** → ready for `Approve Phase 3`.
