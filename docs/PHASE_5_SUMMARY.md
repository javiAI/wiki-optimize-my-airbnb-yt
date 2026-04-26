# Phase 5: Atom Regeneration

**Objective**: Regenerar los 156 átomos desde `sources/` (transcripciones raw) aplicando el contrato consolidado at-creation, no retroactivamente.

Esta es la **fase final**. Solo se ejecuta una vez Phases 1-4 (todas estructurales) están validadas y completas.

---

## Por qué existe esta fase

Durante Phase 1 ejecutamos O3 (Language Consistency) como una opt que auditaba retroactivamente los 156 atoms y los reescribía in-place. Tres problemas emergieron:

1. **No es generalizable**: O3 modifica esta bóveda específica. El mismo "audit + rewrite" no se transfiere a otra bóveda — habría que reaplicar manualmente.
2. **No hay rollback**: el vault no es git-tracked. Una vez aplicado el cambio, revertirlo requiere regeneración manual.
3. **Esconde el impacto real**: O3 declaró `format_compliance` como target dim (predicted +0.3) y entregó −0.25 (delivery −83%). El cost win fue real (−3.4%) pero el target falló — la decisión v2.0 disparó hard floor REVERT.

La conclusión (2026-04-26): **toda opt que modifique átomos individuales pertenece a una fase de regeneración, no a un audit retroactivo**. Phase 5 reúne O3, O6 y futuras opts atom_content como reglas en el prompt de generación de atoms desde `sources/`.

---

## Diferencia clave: estructural vs atom_content

| Tipo | Qué cambia | Generaliza | Rollback | Fase |
|------|-----------|------------|----------|------|
| `structural` | infra (index, MOC, kernel, templates, scripts, scoring, caching, fallback) | sí, copy-paste a otra bóveda | sí, git revert | 1-4 |
| `atom_content` | átomos (naming, body, format) | no, atómico a esta bóveda | no (vault no-git) | 5 (final) |
| `atom_specific` | un átomo concreto | no | no | usually skipped |

**Phase 5** convierte cada `atom_content` en una regla del prompt de ingest, las consolida, y regenera la bóveda entera.

---

## Reglas consolidadas (input a Phase 5)

### O3 — Language Consistency (deferred desde Phase 1)
- Naming: `<topic>--<slug>.md` (kebab-case, slug 2-5 palabras)
- Casing canónico: topics lowercase-hyphen; nombres propios respetados; tech estandarizada
- Structure: claim ≤2 frases, body ≤8 líneas, excerpts ≤50 chars en comillas, confidence ∈ {high, medium, low}
- Anti-anglicismos en el body (no en YAML)

### O6 — Executable Checklists (deferred desde Phase 2)
- Atoms procedurales → bullets `- [ ]` (Dataview-compatible)
- Atoms factuales/taxonómicos → prosa
- Heurística at-creation: verbos imperativos secuenciales → checklist; default → prosa

### Heredadas de Phases 1-4
- Schema YAML (§3)
- Score (§5, §10.4) — afecta priorización de claims
- L4 contradiction detection (O4) — entradas auto en `meta/contradictions.md`
- Auto-linking (O8) — backlinks at-creation
- Response format templates (O5) — afecta uso, no generación

---

## Sequencia de ejecución (resumen)

1. Pre: verificar Phases 1-4 complete + backup del vault
2. T1: diseñar ingest prompt consolidado (3h)
3. T2: plan de regeneración por batches (1h)
4. T3: audit pre-regeneración (1h) — produce el diff esperado
5. T4: batch piloto 1 topic (2h) — valida el prompt en 10 atoms
6. T5: regenerar resto (4h) — topic-by-topic
7. T6: validación final con test suite (2h)
8. T7: update CLAUDE.md y docs (1h)

**Total**: ~14h.

Detalle: [PHASE_5_TASKS.md](PHASE_5_TASKS.md).

---

## Resultados esperados

- `format_compliance` ≥ punto pre-Phase5 (O3 entregado correctamente como regla at-creation)
- `spanish_purity` ≥ punto pre-Phase5 (anti-anglicismos en cuerpo + reforzado por O5 templates)
- `weighted_avg` ≥ punto pre-Phase5 (no regression en otras dims)
- Cost: neutro o ligero win (atoms más limpios → menos noise en context)
- Bóveda en estado canónico, transferible: cualquier nueva opt atom_content se anexa al prompt y se programa una nueva regeneración.

---

## Cuándo se aprueba

Cuando `automation.current_phase = 5` y `phase_status = pending_approval`. El usuario dice `Approve Phase 5` y se ejecuta T1→T7 secuencialmente.

Si el test final (T6) regresiona, no marcar `complete` — restaurar backup pre-Phase5 y reabrir el prompt T1.
