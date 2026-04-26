# Phase 2: Quality Foundation (Structural)

**Objective**: Build systematic quality assurance into the vault — solo via cambios estructurales (kernel, templates, automatización). Las opts que modifican átomos se han movido a Phase 5.

Tras Phase 1 (mejoras estructurales de indexación), Phase 2 ataca dos vectores: detectar contradicciones en query-time, y estandarizar el formato de respuesta para reducir cognitive load y reforzar `spanish_purity` (el techo bajo de la rúbrica, 4.45-5.12).

---

## What Phase 2 Accomplishes

- **O4 (Contradiction Detection L1)**: Heurística en kernel que flagea conflictos semánticos al leer atoms durante query, no solo en lint sweeps.
- **O5 (Response Format Templates)**: Templates canónicos por régimen (factual / tactical / taxonomic) en `queries/RESPONSE_TEMPLATES.md`. **Aprovecha para añadir reglas anti-anglicismos** que apuntan al `spanish_purity` floor.

**Effort**: ~5.5h total (3h O4 + 2.5h O5)
**Quality target**: weighted_avg estable o ≥ punto pre-O4; `spanish_purity` ≥ 5.5; `format_compliance` ≥ punto pre-O4
**Unlock**: Phase 3 (Automation) depende de Phase 2 quality gates.

---

## Diferidas a Phase 5

- **O3 (Language Consistency)** — atom_content. Re-clasificada y diferida tras n=2 runs (composite +0.0088 pero `target_dim_regression` floor breach en `format_compliance`). Se re-incorpora como regla at-creation en el prompt de regeneración.
- **O6 (Executable Checklists)** — atom_content. Convierte cuerpos de atoms procedurales a Dataview-checklist. Se aplica at-creation en Phase 5.

Razón consolidada: ver principio en [OPTIMIZATIONS.md](OPTIMIZATIONS.md#principio-de-optimización-2026-04-26).

---

## Optimizations

### O4: Contradiction Detection L1 (3 hours)

**What it does**: Heurística que, al leer un atom durante query (step 6 de §4.2), comprueba:
- ¿Existen otros atoms del mismo topic con `claim` opuesto?
- ¿La `confidence` de este atom es menor que la del conflictivo?
- ¿Está resuelto en `meta/contradictions.md`?

Si conflict no resuelto: flag en respuesta con caveat "Note: conflicting advice from [[other-atom]]; confidence high vs medium."

**Por qué**: el usuario ve el conflicto up-front, reduce trust issues, fuerza resolución proactiva.

**Estructural**: lógica del kernel (CLAUDE.md §4.2), generaliza a otra bóveda sin cambios.

**Implementation**: Sub-step en §4.2 step 6 ("Check for conflicts before citing"). Detalle en [PHASE_2_TASKS.md](PHASE_2_TASKS.md).

---

### O5: Response Format Templates (2.5 hours)

**What it does**: Templates canónicos por régimen de consulta:
- **Régimen A (factual)**: Pregunta → Respuesta directa (1-2 frases) → Condiciones/excepciones → Sources → Confidence
- **Régimen B (tactical)**: Pregunta → 3-5 pasos numerados → Por qué → Outcome esperado → Caveats → Sources
- **Régimen C (taxonomic)**: Pregunta → Intro → Tabla/lista comparativa → Cómo elegir → Sources

**Por qué**: estructura consistente reduce cognitive load. Más fácil validar completeness. Y, crucialmente, los templates incluyen una sección anti-anglicismos al pie del prompt: "Solo usa términos en inglés si son nombres propios o tech estandarizada (ver §10.7). En el resto, español: anfitrión/huésped/reseña/comodidades/anuncio/reserva/valoración."

**Estructural**: nuevo artifact `queries/RESPONSE_TEMPLATES.md` + referencia en CLAUDE.md §10.7. Generaliza.

**Implementation**: Crear el artifact, referenciarlo en §10.7. Detalle en [PHASE_2_TASKS.md](PHASE_2_TASKS.md).

---

## Next Steps

1. Approve Phase 2
2. Execute O4 (kernel update)
3. Test O4 → compare → decide
4. Execute O5 (templates artifact)
5. Test O5 → compare → decide
6. Update CLAUDE.md, OPTIMIZATIONS.md, history.md
7. Move to Phase 3
