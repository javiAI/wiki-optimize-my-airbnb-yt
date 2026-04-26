# Phase 5: Execution Tasks — Atom Regeneration

**Status**: Phase 5 is `not_started` y depende de Phases 1-4 completas. Es la fase **final**: una vez validadas todas las opts estructurales, regeneramos los 156 átomos desde `sources/` (transcripciones raw) aplicando el contrato consolidado at-creation.

**Principio**: las opts en esta fase modifican el contenido de los átomos. No se aplican retroactivamente — se aplican como **reglas de generación** en el prompt de ingest. Esto evita el problema "vault no es git-tracked, no hay rollback" que hizo que O3 quedara aplicada en main sin manera limpia de revertir.

---

## Pre-requisitos

Antes de entrar en Phase 5, verificar:

1. Phases 1-4 marcadas `complete` en CLAUDE.md frontmatter
2. `tests/results/` con baseline + el último OX estructural (probable: O12) evaluado
3. Inventario actual: `ls $VAULT_PATH/notes/ | wc -l` debe coincidir con `vault_health.atoms_count` en CLAUDE.md (156)
4. `sources/` íntegro: `ls $VAULT_PATH/sources/*.md | wc -l` ≈ 168 transcripciones (173 raw − 5 español excluidas)
5. Backup completo del vault actual antes de regenerar (no es git-tracked):
   ```bash
   tar -czf ~/vault-pre-phase5-$(date +%Y%m%d).tar.gz -C "$(dirname $VAULT_PATH)" "$(basename $VAULT_PATH)"
   ```

---

## Reglas de generación consolidadas

Las reglas que se aplicarán en el prompt de regeneración (acumuladas de O3, O6 y futuras opts atom_content):

### Reglas de O3 — Language Consistency

**Naming**:
- Atoms: `<topic>--<slug>.md` (kebab-case, sin tildes en el slug)
- `<topic>` ∈ lista cerrada de §10.3 (pricing, occupancy, listing-optimization, cleaning-ops, reviews, hospitality, ranking, direct-booking, market-selection, regulations, tools-tech, investing)
- `<slug>` describe el claim en 2-5 palabras

**Casing canónico**:
- Topics y tags: lowercase con guiones (`pricing`, `direct-booking`)
- Nombres propios respetados: `Airbnb`, `Booking`, `Vrbo`, `PriceLabs`, `AirDNA`, `AllTheRooms`, `Superhost`, `Aircover`, `Instant Book`, `Stays`
- Tech estandarizada: `WiFi`, `PMS`, `API`

**Structure**:
- `claim`: una frase declarativa, ≤2 frases si compuesto, en presente español
- `body`: ≤8 líneas, prosa o bullets, sin sub-headers (los átomos son atómicos)
- `excerpt`: cita literal de la fuente entre comillas, ≤50 caracteres
- `confidence`: ∈ {high, medium, low} (no usar "alta"/"media"/"baja"; YAML controlado)
- `last_verified`: YYYY-MM-DD del día de generación

**Anti-anglicismos en el cuerpo** (no en YAML):
- "anfitrión" no "host", "huésped" no "guest", "reseña" no "review"
- "comodidades" no "amenities", "anuncio" no "listing", "reserva" no "booking"
- "valoración" no "rating"

### Reglas de O6 — Executable Checklists

**Atoms procedurales** (los que describen un proceso paso-a-paso):
- Cuerpo en formato Dataview-compatible:
  ```markdown
  ## Procedimiento
  - [ ] Paso 1 (verbo en infinitivo)
  - [ ] Paso 2
  - [ ] Paso 3
  ```
- Incluir block Dataview opcional al pie:
  ```dataview
  TASK
  WHERE file.path = this.file.path
  GROUP BY status
  ```
- Atoms NO procedurales (claims factuales, taxonomías) mantienen prosa.

**Decisión at-creation** (heurística para el ingest):
- Si el claim contiene verbos imperativos secuenciales ("primero…, luego…, finalmente…") → procedural → checklist
- Si el claim es una afirmación factual → prosa
- Si es ambiguo → prosa (default conservador)

### Reglas heredadas de Phases 1-4

Lo que se mantiene del contrato actual (no cambia en Phase 5, solo se reaplica):

- Schema YAML §3 (claim, topics, confidence, sources con locator + excerpt, conflicts_with, last_verified)
- Score §5 / §10.4 (recency 0.40, popularity 0.30, specificity 0.20, authority 0.10) — afecta selección de claims a regenerar
- Response contract §10.7 — aplica al uso de los atoms, no a su generación
- L4 contradiction detection (O4) — al generar, si dos claims del mismo topic son opuestos sin entrada en `meta/contradictions.md`, se crea entrada
- Auto-linking (O8) — backlinks en MOCs se regeneran at-creation

---

## Tareas

### T1: Diseñar el ingest prompt consolidado (3h)

Reescribir `scripts/ingest.sh` (o crear `scripts/regenerate-atoms.py`) con un prompt que reciba:

- Una transcripción de `sources/`
- Las reglas consolidadas (O3 + O6 + heredadas) en el system prompt
- El topic_taxonomy de §10.3
- La lista de nombres propios permitidos

Salida: 0..N atoms en `notes/` con YAML válido y body conforme al contrato.

**Validación**: correr el prompt sobre 1 source de prueba, verificar manualmente que los atoms generados cumplen todas las reglas.

### T2: Plan de regeneración por batches (1h)

- Inventariar atoms actuales por topic (`grep "^topics:" notes/*.md | sort`)
- Generar plan: regenerar topic-by-topic empezando por los menos críticos (`tools-tech`, `investing`) y terminando por los más usados (`pricing`, `occupancy`)
- Decidir si regenerar todo de cero o solo los que no cumplen el contrato (audit-first)

### T3: Audit pre-regeneración (1h)

Correr `scripts/lint-atoms.py` (crear si no existe) que reporta:

- Atoms con naming no conforme
- Atoms con body >8 líneas
- Atoms con excerpts >50 chars o sin comillas
- Atoms procedurales no convertidos a checklist
- Anglicismos en el body

Output: `meta/audit-pre-regen-YYYY-MM-DD.md`. Esto da el "diff esperado" de la regeneración.

### T4: Regenerar batch piloto (2h)

Elegir 1 topic pequeño (ej. `tools-tech`, ~10 atoms). Regenerar.

- Verificar conteo: atoms_after vs atoms_before
- Verificar links no rotos: `grep -r "tools-tech--" notes/ MOC/ index/ queries/`
- Reaplicar response_contract a 5 queries del topic, comparar respuestas pre/post

Si el batch piloto pasa: continuar. Si no: iterar el prompt T1.

### T5: Regenerar resto del vault (4h)

Topic por topic, en el orden definido en T2. Para cada topic:

1. Backup del directorio actual
2. Borrar atoms del topic en `notes/`
3. Regenerar desde `sources/`
4. Re-correr lint
5. Reaplicar tests parciales (5 queries del topic)
6. Commit en el repo (no en el vault) con `Phase5: regenerated <topic>`

### T6: Validación final (2h)

Correr el test suite completo (20 queries × 1 agent) sobre el vault regenerado.

Comparar contra el último punto pre-Phase5 (probable: O12 o el punto estructural más reciente). Esperado:

- `format_compliance` ≥ punto previo (target dim de O3+O6, ahora at-creation)
- `spanish_purity` ≥ punto previo (target de O5 + reglas de O3 anti-anglicismos)
- `weighted_avg` ≥ punto previo (no regression en otras dims)
- Cost: neutro o ligeramente mejor (atoms más limpios → menos noise)

### T7: Update CLAUDE.md y docs (1h)

- Marcar Phase 5 `complete` en frontmatter
- Sincronizar O3, O6 → status: `completed` (con `applied_at: phase_5`)
- Update `docs/OPTIMIZATIONS.md` Status Table (final)
- Append entry a `tests/history.md`
- Commit final: `Phase 5 complete: 156 atoms regenerated with consolidated contract`

---

## Riesgos y mitigaciones

**R1: La regeneración pierde contenido valioso de los atoms actuales**
- Mitigación: backup pre-Phase5; T3 produce un audit comparable; T4 piloto valida el prompt antes de aplicar a todo.

**R2: El prompt consolidado es ambiguo en casos edge**
- Mitigación: T1 incluye validación manual en 1 source; iterar prompt antes de batches grandes.

**R3: Roturas de links cruzados (MOCs, index, queries)**
- Mitigación: O8 (Auto-Linking, Phase 3) ya genera backlinks at-creation. Tras T5, correr `scripts/auto-link.py` sobre el vault regenerado.

**R4: El test suite final regresiona**
- Mitigación: T4 piloto detecta esto temprano. Si el regression es sistémico, congelar Phase 5 y revertir al backup pre-Phase5.

---

## Notas de diseño

- **No es retroactivo**: nunca volveremos a "auditar atoms y modificarlos in-place". Si una nueva opt atom_content surge en el futuro, se anexa a las reglas de generación y se programa una regeneración (Phase 5'). El vault es read-mostly entre regeneraciones.
- **Phase 5 es transferible**: el script de regeneración + las reglas consolidadas son la entrega que cualquier otra bóveda puede reutilizar. El prompt es el activo, no los atoms generados.
- **Frecuencia**: Phase 5 es one-shot por iteración mayor del contrato. No se corre cada vez que se añade un source nuevo (eso es ingest normal, que ya usa el prompt T1 una vez completado).
