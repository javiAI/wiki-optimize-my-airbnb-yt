# Phase 3: Execution Tasks

Execute tasks in order: O7, O8, O9.

---

## Mandatory pre-execution template (A/B/C + meta.yaml)

**Before this phase is approved**, each OX below must have three sections filled in (using the format established in `docs/PHASE_2_TASKS.md` and `docs/TEST_PROTOCOL.md`):

- **A. Concept (intuitivo)** — qué problema resuelve, analogía si ayuda. 2-4 frases.
- **B. Técnica** — qué cambia concretamente: archivos, rutas, mecánica.
- **C. Mejoras esperadas + justificación** — predicción cuantitativa para cada dimensión del rubric (`weighted_cost`, `completeness`, `accuracy`, `spanish_purity`, `tone`, `format_compliance`, `weighted_avg`) con razonamiento. Esta sección es un compromiso con la predicción; tras correr el test se compara predicted-vs-actual.

**Plus: `tests/prompts/OX/meta.yaml`** (decision_version 2.0 — see [TEST_PROTOCOL.md](TEST_PROTOCOL.md) §meta.yaml). Required fields: `target_dims` / `at_risk_dims` / `neutral_dims`, `predicted_deltas` (cost + per-dim abs), `optimization_type`, `allow_repetition`. The script reads meta.yaml to compute composite score and trigger hard-floor breaches (e.g. `target_dim_regression` if a declared target dim drops). Section C is the human narrative; meta.yaml is the machine-readable mirror — they must agree.

Las secciones que siguen contienen `Purpose` / `Implementation` / `Verification` heredadas. Antes de aprobar Phase 3, expandir cada OX con A/B/C + meta.yaml (ver O4/O5/O6 en `PHASE_2_TASKS.md` como referencia).

---

## O7: Agent Orchestration (8 hours)

### A. Concepto

La bóveda acumula 156 átomos, 173 fuentes y 12 MOCs sin ningún proceso de mantenimiento automatizado. Con el tiempo aparecen: átomos huérfanos (ningún MOC los cita), claims no verificados desde hace meses, tópicos emergentes que aún no tienen MOC, y entradas del índice que apuntan a archivos borrados. `vault-agent.py` es el "CI del vault": lo ejecutas una vez y obtienes un informe de salud accionable en < 5 segundos.

### B. Técnica

- **Crear `scripts/vault-agent.py`**: script Python que lee el vault (vault read-only desde `$VAULT_PATH`), ejecuta 5 checks (orphans, stale, consistency, gaps, unresolved contradictions) y escribe `meta/agent-report-YYYY-MM-DD.md` + appends `log.md`.
- **No modifica el kernel ni los átomos**: los agentes de test no leen `meta/agent-report-*.md`, por lo que el impacto en el rubric es neutral por diseño.
- **Referencia en CLAUDE.md §11** (Troubleshooting → añadir línea sobre el script).

### C. Mejoras esperadas + justificación

Este OX es infraestructura pura de mantenimiento. No modifica el kernel de respuesta ni el contenido de los átomos; por tanto, los agentes de test no cambian de comportamiento. Predicciones:

| Dim | Predicción | Razonamiento |
|---|---|---|
| weighted_cost | 0 | No cambia nada que el agente lea |
| completeness | 0 | Sin cambio de átomos disponibles |
| accuracy | 0 | Sin cambio de átomos disponibles |
| spanish_purity | 0 | Sin cambio de kernel §10.7 |
| tone | 0 | Sin cambio de kernel |
| format_compliance | 0 | Sin cambio de kernel §4.6 |
| weighted_avg | 0 | Neutral por diseño |

El test sirve únicamente para confirmar que el script no introduce regresiones (ningún hard floor breach). allow_repetition: false — se acepta en un único run.

### Purpose
Create an autonomous agent script that periodically audits vault health and reports findings.

### Implementation

1. **Create `scripts/vault-agent.py`**
   - Input: VAULT_PATH
   - Output: Structured findings in `meta/agent-report-YYYY-MM-DD.md`
   - Tasks:
     - Run lint (orphans, contradictions, stale claims)
     - Detect semantic gaps (topics mentioned but no MOC)
     - Suggest ingest targets (topics lacking recent sources)
     - Check index consistency

2. **Vault health checks**
   - **Orphan detection**: atoms not cited in any MOC or query
   - **Stale claims**: atoms with `last_verified` > 180 days old and newer sources exist
   - **Consistency**: `index.md` entries match actual files
   - **Conflicts**: unresolved contradictions in `meta/contradictions.md`
   - **Gaps**: topics mentioned 3+ times but no dedicated MOC

3. **Gap detection**
   - Parse all atoms' `topics:` fields
   - Find topics appearing 3+ times
   - Check: does `MOC/<topic>.md` exist?
   - If not: flag as "emerging topic with {{N}} atoms, consider creating MOC"

4. **Ingest recommendations**
   - Rank topics by atom count (lower = underrepresented)
   - For each underrepresented topic: suggest keyword for YouTube search
   - Output: `"Consider ingesting 2-3 videos about [topic] (currently only {{N}} atoms)"`

5. **Report format**
   ```markdown
   # Vault Health Report — {{YYYY-MM-DD}}
   
   ## Summary
   - Atoms: 156 | MOCs: 12 | Sources: 173
   - Orphans: 3 | Stale (>180d): 5 | Gaps: 2
   
   ## Issues
   - Orphan atoms: [[atom-1]], [[atom-2]], [[atom-3]]
   - Stale claims: [[atom-x]] (last verified 2025-10-15)
   - Emerging topics (3+ atoms, no MOC): {{topic-1}}, {{topic-2}}
   - Unresolved contradictions: 1 (see meta/contradictions.md)
   
   ## Recommendations
   - Delete or link [[orphan-atom-1]]
   - Re-verify [[stale-atom-x]] or archive
   - Create MOC/{{topic-1}}.md (3 atoms waiting)
   - Ingest 2-3 videos about {{underrep-topic}} (only 2 atoms currently)
   
   ## Generated by
   `scripts/vault-agent.py` on {{timestamp}}
   ```

6. **Schedule execution (optional)**
   - Add to `scripts/config.sh`: `VAULT_AGENT_SCHEDULE=3d` (every 3 days)
   - Or: manual trigger via `scripts/vault-agent.py --run`

7. **Integration with log.md**
   - If agent detects changes, append entry to `log.md`:
   ```
   ## [2026-04-25] agent-report | Vault health check
   - Generated: meta/agent-report-2026-04-25.md
   - Findings: 3 orphans, 1 emerging topic, 5 stale claims
   - User action required: review recommendations
   ```

8. **Git commit**
   ```bash
   git commit -m "O7: Agent orchestration (vault-agent.py + health reports)"
   ```

### Verification Checklist
- [ ] `scripts/vault-agent.py` created and executable
- [ ] Orphan detection working (test: should find orphans if any)
- [ ] Stale detection working (test: should flag atoms with old `last_verified`)
- [ ] Consistency check working (test: should flag broken index links)
- [ ] Gap detection working (test: should suggest topics for new MOCs)
- [ ] Ingest recommendation working (test: should suggest underrep topics)
- [ ] Report generated in `meta/agent-report-YYYY-MM-DD.md`
- [ ] `log.md` entry added
- [ ] Git commit made

---

## O8: Auto-Linking System (4 hours)

### A. Concepto

Cuando se crea un átomo nuevo, hay que acordarse manualmente de añadirlo a los MOCs relevantes. Si se olvida, el átomo queda huérfano — existe pero ningún agente lo descubre al navegar los MOCs. `auto-link.py` es el "post-ingest hook": dado un nombre de átomo, busca qué MOCs cubren sus tópicos y añade la entrada faltante automáticamente.

### B. Técnica

- **Crear `scripts/auto-link.py`**: lee el YAML frontmatter del átomo (campo `topics`), busca `MOC/<topic>.md` para cada tópico, comprueba si ya existe `[[notes/<atom>]]` en el MOC, y si no, lo añade en la sección correspondiente.
- **Deduplicación**: antes de insertar, grep por `[[notes/atom-filename]]` para no duplicar.
- **Invocación**: `python3 scripts/auto-link.py <atom_filename>` — manual post-ingest o futuro cron.
- **Impacto en tests**: los átomos previamente huérfanos ahora son descubribles por los agentes (navegan MOCs). Pequeña mejora potencial en completeness si algún átomo faltaba en MOC. Si corremos auto-link.py ANTES del test sobre todos los átomos existentes, el efecto es backfill de MOCs.

### C. Mejoras esperadas + justificación

| Dim | Predicción | Razonamiento |
|---|---|---|
| weighted_cost | 0 | Sin cambio de token budget |
| completeness | +0.1 | Átomos huérfanos ahora descubribles — agentes podrían citarlos |
| accuracy | 0 | No cambia claim content |
| spanish_purity | 0 | Sin cambio kernel §10.7 |
| tone | 0 | Sin cambio kernel |
| format_compliance | 0 | Sin cambio kernel §4.6 |
| weighted_avg | +0.025 | Mejora marginal vía completeness |

allow_repetition: false — resultado de un único run (delta esperado pequeño, cerca del noise zone).

### Purpose
Automatically insert cross-references when new atoms are created.

### Implementation

1. **Create `scripts/auto-link.py`**
   - Input: new atom filename (or last modified atom)
   - Logic:
     - Read atom's `topics:` field
     - For each topic: scan `MOC/<topic>.md`
     - Find atoms already discussing same topic
     - Insert backlinks in those atoms' bodies
   - Output: updated atom files with new links

2. **Link insertion strategy**
   - Add "See also" section if not present:
     ```markdown
     ## See also
     - [[new-atom]] — <new atom's claim, 1 line>
     - [[existing-related-atom]] — description
     ```
   - Or: append to existing "See also" section
   - Never duplicate links; check for existing `[[new-atom]]` before inserting

3. **MOC link insertion**
   - For each MOC covering atom's topics:
   - Add entry if not present: `- [[atom]] — claim summary`
   - Keep MOC organized (grouped by subtopic)

4. **Invoke post-ingest**
   - After atom creation (step 2 of §4.1), call:
   ```bash
   python3 scripts/auto-link.py {{atom_filename}}
   ```
   - Script should update related atoms' bodies + MOCs

5. **Deduplication check**
   - Before inserting link, scan atom's body for existing `[[new-atom]]` reference
   - If found: skip (link already present)
   - Test: create atom with conflicting relationship, run script twice, verify no duplicate links

6. **Git commit**
   ```bash
   git commit -m "O8: Auto-linking system (scripts/auto-link.py)"
   ```

### Verification Checklist
- [ ] `scripts/auto-link.py` created and executable
- [ ] Reads atom's `topics:` correctly
- [ ] Finds related atoms by topic scan
- [ ] Inserts links in related atoms' bodies
- [ ] Updates MOC entries
- [ ] Deduplication working (no duplicate links)
- [ ] Tested with sample atom creation
- [ ] Git commit made

---

## O9: Query Caching (6 hours)

### A. Concepto

Cuando un anfitrión pregunta algo que ya se preguntó antes, el agente re-deriva la respuesta desde cero — gastando tokens y tiempo innecesariamente. `cache-optimizer.py` analiza `log.md`, identifica los tópicos más frecuentes, genera estadísticas de caché y señala qué queries en `queries/` están disponibles para reutilización. El kernel §4.2 ya dice "ir a queries/ primero" — este script asegura que el caché esté poblado y actualizado.

### B. Técnica

- **Crear `scripts/cache-optimizer.py`**: parsea `log.md` buscando líneas `## [YYYY-MM-DD] query`, extrae tópicos, cuenta frecuencia, genera `meta/query-cache-stats.md` con hit-rate, top queries y entradas stale.
- **No modifica queries/ directamente**: señala qué topics deben cachearse; el agente guarda en queries/ al responder (ya existe el mecanismo en §4.2).
- **Impacto en tests**: queries/ está en la blacklist de test agents (CLAUDE.md regla 2) → 0 impacto en rubric. El valor es operacional.

### C. Mejoras esperadas + justificación

| Dim | Predicción | Razonamiento |
|---|---|---|
| weighted_cost | 0 | queries/ blacklisted en tests |
| completeness | 0 | Sin cambio |
| accuracy | 0 | Sin cambio |
| spanish_purity | 0 | Sin cambio |
| tone | 0 | Sin cambio |
| format_compliance | 0 | Sin cambio |
| weighted_avg | 0 | Neutral por diseño |

allow_repetition: false — confirmar neutralidad en un único run.

### Purpose
Automatically cache frequently answered questions and implement similarity-based retrieval.

### Implementation

1. **Create `scripts/cache-optimizer.py`**
   - Parses `log.md` for recent queries
   - Counts frequency of each question/topic
   - Identifies top 20% (cache candidates)
   - For each cached query: stores in `queries/` if not present

2. **Query statistics tracking**
   - Read `log.md`, find all `## [DATE] query` entries
   - Extract question text (or topic)
   - Count: how many times has this topic been queried?
   - Output: `meta/query-cache-stats.md` with top queries

3. **Cache refresh strategy**
   - For top 20 queries: regenerate cached response weekly
   - Check: are source atoms still valid? Are there new atoms covering same topic?
   - If yes: update cached query
   - If no: keep cache as-is
   - Mark in cache: `last_verified: 2026-04-25`

4. **Similarity detection (advanced)**
   - Optional: implement simple keyword-based similarity
   - If user asks "¿Mejor estrategia de precio?" and cache has "Cómo optimizar precio"
   - Return cached answer + caveat: "Similar query found in cache; minor differences may apply"
   - Requires: keyword extraction from questions

5. **Cache metadata file**
   ```markdown
   # Query Cache Statistics — {{YYYY-MM-DD}}
   
   **Hit Rate**: {{N}} of {{M}} queries ({{percent}}%) served from cache
   **Most cached topics**: pricing (12), orphan-nights (8), reviews (6)
   **Newest cache entry**: [[queries/pricing--dynamic-adjustments]] (2026-04-24)
   **Stale cache entries**: [[queries/old-query-1]] (needs refresh)
   
   **Top 20 cache candidates**:
   1. pricing-strategy (queried 8 times)
   2. review-management (queried 5 times)
   3. guest-communication (queried 4 times)
   ```

6. **Integration point**
   - After answering a query (§4.2), check:
   - "Is this answer suitable for caching?" (requires synthesis, complex decision)
   - If yes: save to `queries/` + update `query-cache-stats.md`
   - Add to `log.md`: `cache added: [[queries/new-answer]]`

7. **Git commit**
   ```bash
   git commit -m "O9: Query caching (cache-optimizer.py + similarity detection)"
   ```

### Verification Checklist
- [ ] `scripts/cache-optimizer.py` created and executable
- [ ] Parses `log.md` for queries
- [ ] Counts query frequency correctly
- [ ] Identifies top 20% queries
- [ ] Generates `meta/query-cache-stats.md`
- [ ] Caches top queries in `queries/`
- [ ] Refresh logic implemented
- [ ] Similarity detection tested (if implemented)
- [ ] `log.md` entries added
- [ ] Git commit made

---

## After Phase 3 Completion

1. **Update CLAUDE.md YAML**
   ```yaml
   phase_3:
     status: "complete"
     progress: 100
   automation:
     current_phase: 4
     phase_status: "pending_approval"
   ```

2. **Test autonomous execution**
   - Run `scripts/vault-agent.py --run`
   - Create test atom, verify auto-linking works
   - Run `scripts/cache-optimizer.py`, verify cache built

3. **Git commit**
   ```bash
   git commit -m "Phase 3 complete: Automation layer (O7, O8, O9)"
   ```

4. **Show Phase 4 summary**
   - Ready for: "Approve Phase 4"
