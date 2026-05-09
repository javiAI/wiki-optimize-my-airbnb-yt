# OMAB Wiki — Contract & State

> Phase/optimization history (O1-O12) lives in `docs/MASTER_PLAN.md`. Active design plans in `~/.claude/plans/`. Vault stats are queried live, not stored here.

## Quality testing

End-to-end vault quality testing runs through `/test-vault` (skill at `.claude/skills/test-vault/SKILL.md`). Five-phase pipeline per language: generate questions from MOCs → answer via fresh `/query` subagents → fan out to N independent evaluators → script computes per-Q mean/std + inter-rater stats → aggregator writes a narrative report.

Defaults (overridable per call via CLI flags or per vault via `vault.yml.tests`): 15 questions, mix `5-A / 7-B / 3-C`, 5 evaluators, langs = every enabled lang of the vault, queries cache OFF.

Rubric (5 dims, weights in `vault.yml.tests.rubric`): `completeness` 25%, `accuracy` 25%, `language_purity` 15%, `tone` 15%, `format_compliance` 20%. Weighted average + per-dim std across evaluators are the headline numbers. The framework is reproducible across labels (`questions.{lang}.yaml` is reused unless `--regenerate`).

Outputs land under `vaults/{name}/tests/` (the vault is read-only for test agents). Templates live in `.claude/templates/tests/`. The driver is `scripts/run-test-suite.py` — bump `RUBRIC_VERSION` if rubric/decision logic changes.

Quick reference:

```bash
/test-vault                                    # active vault, all enabled langs, defaults
/test-vault --vault NAME --langs es --count 10
/test-vault --label baseline-2 --phase 5       # re-run only the aggregator
python3 scripts/run-test-suite.py --help       # all subcommands
```

Hard isolation invariants (held by every run): answering agents and evaluators never read `queries/` cache (unless `--read-queries`); evaluators never see each other's outputs; aggregator only synthesizes; each subagent has fresh context.

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

## 0.6 Layout (v1 ⇄ v2, auto-detected)

Las bóvedas nuevas creadas por `init-vault.sh` usan **v2 (lang-first)**. Las viejas siguen en **v1 (kind-first)** hasta que se migren. Los scripts auto-detectan el layout vía filesystem-probing (`kind_dir()` en `config.py`); ambos coexisten sin flag de configuración. Todo es per-lang excepto `meta/`, `log.md` y `state/`.

```text
# v2 — lang-first (default para nuevas bóvedas)
$VAULT_PATH/
├── {lang}/index/index.md
├── {lang}/moc/<topic>.md
├── {lang}/wiki/<topic>--<slug>.md
├── {lang}/raw/<date>--<slug>.md
├── {lang}/queries/<topic>--<q>.md
├── meta/                        # lang-agnostic: contradictions.md, glossary.md, RESPONSE_TEMPLATES.md, videos.md, agent-reports/
└── log.md                       # registro cronológico (auto-append por hook)

# v1 — kind-first (legacy, todavía en producción para oma-test-*, optimize-my-airbnb-yt)
$VAULT_PATH/{wiki,moc,raw,index,queries}/{lang}/...
```

En el resto de este documento los ejemplos de path usan la forma **kind-first** (`wiki/{lang}/...`) por continuidad histórica — significan el mismo fichero en ambos layouts. Wikilinks: `[[{lang}/wiki/<stem>]]` (v2) o `[[wiki/{lang}/<stem>]]` (v1); `auto-link.py` y `propagate_atom.py` emiten la forma correcta según el layout detectado.

`vaults/{name}/` (en este repo) hospeda `vault.yml`, `agents.md`, `state/queue/`, `state/logs/`, `tests/`. Los hooks viven en `.claude/hooks/`, no en la bóveda. La bóveda contiene **datos**, no configuración.

## 0.65 Hubs: entity & comparison

Two new page types coexist with atoms inside `wiki/{lang}/`, discriminated by `type:` frontmatter:

- `wiki/{lang}/entity--<slug>.md` (`type: entity`) — pre-compiled per-tool/company/person/product synthesis. Cites the atoms it summarises via `cited_atoms[]`.
- `wiki/{lang}/comparison--<a>-vs-<b>.md` (`type: comparison`, slug alpha-sorted) — pre-compiled head-to-head decision-tree per peer pair.

Both are **per-lang propagated** (same flow as atoms via `propagate_atom.py`). Detected at ingest-time by pattern-match scripts (`entity-detect.py` / `comparison-detect.py`) against `meta/entities-registry.yaml` — no LLM cost. Atoms are stubbed immediately so wikilinks resolve, then enriched in batch when `on-ingest-batch-close.sh` fires `/refresh-hubs`. Slugs are alpha-sorted for comparisons (`pricelabs-vs-wheelhouse`, never `wheelhouse-vs-pricelabs`) — idempotent.

At query time, `retrieve.py` auto-detects shape (entity / comparison / topic / atom) from the question + registered aliases and applies a 4× score boost when a hub matches. Drives ~50% query-cost reduction on entity- and comparison-shape queries because the hub is a pre-compiled answer, not raw atoms re-synthesised on demand.

## 0.7 Bootstrap

Para crear una bóveda nueva: `bash .claude/scripts/init-vault.sh` (wizard) o `/init-vault` desde Claude (guiado conversacional). Crea el bundle `vaults/{name}/` y la estructura de datos en el path elegido. Para la OMA original, los comandos legacy están en `docs/PHASE_1_TASKS.md`.

---

## 1-2. Estructura: 3 capas, 3 operaciones

| L1 (siempre) | L2 (tras filtrar L1) | L3 (fragmentos) |
| --- | --- | --- |
| `index/{lang}/index.md`, `moc/{lang}/`, `log.md` | `wiki/{lang}/`, `queries/{lang}/` | `raw/{lang}/` |

**Operaciones**: INGEST (añadir fuentes) → QUERY (responder) → AUDIT (estructura) + QA (contenido). Los dos health-checks viven en slash commands distintos: `/audit` cubre la salud estructural (huérfanos, stale, gaps, propagations, cross-refs); `/qa` cubre el contenido de cada atom (claim, URL, definición de acrónimos, esquema YAML). El término histórico "LINT" del documento original se mapea a la combinación `/audit` + `/qa` (cobertura equivalente o superior, separada por scope). La pureza de idioma (leakage de anglicismos en atoms no-ingleses) NO se valida aquí: se puntúa estadísticamente en `/test-vault` por N evaluadores independientes.

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

**INGEST**: Fuente → `raw/{lang}/` → Extract claims (`atomization_lang`) → 1 claim = 1 atom en `wiki/{lang}/` → `auto-link.py` (MOC backlinks) → `entity-detect.py` + `comparison-detect.py` (stub hubs, queue enrichment) → `propagate_atom.py` (otros langs) → CONFLICT branch escribe a `meta/contradictions.md` si aplica → `on-ingest-batch-close.sh` drena colas de hubs vía `/refresh-hubs` y dispara `/audit [--deep]` cada N ingests.

**QUERY**: `index/{lang}/index.md` → `queries/{lang}/` (cache) → `retrieve.py` (BM25 + shape-detect + hub boost) → si top-result es hub (`type: entity|comparison`) úsalo como scaffold; si no, `moc/{lang}/<topic>.md` → atoms → Respuesta citada → Guardar si síntesis nueva

**AUDIT** (`/audit` → `vault-agent.py`): dos modos. **Default (estructural)**: orphans, stale, gaps, broken links, missing propagations, missing cross-refs — pattern-match, no LLM. **`--deep`**: estructural + pase semántico LLM que detecta numerical/framework/stance drift, concept-framing collisions y new canonical positions cross-atom.

**QA** (contenido, `/qa` → `atom-qa.py`): claim presente, URL válida, definición de acrónimos en primer uso, esquema YAML por atom (`--fix` autoresuelve definiciones de acrónimos). La pureza de idioma se mide aparte vía `/test-vault`.

---

## 4.5 Conflict Check (query-time, real-time)

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

NO añadir entradas para conflictos ya documentados — duplicaría meta. La consolidación de propuestas en `meta/contradictions.md` se hace manualmente al revisar cada query (ya no hay script automatizado — la propuesta y la curación viven en el ciclo de query/audit).

### 4.5.6 Caveat format (templates en `meta/RESPONSE_TEMPLATES.md`)

- **Estándar** (no temporal): bloque ⚠️ Nota con primario/rival, condición de aplicabilidad, link a meta.
- **Temporal evolution** (cuando criterio = `temporal_supersession`): tres elementos obligatorios — ANTES (estado pre + cita rival), DESDE (transición + hito + razón), HOY (estado actual + cita primaria). Máx 3 frases. El atom viejo aparece como contexto histórico, no como recomendación competidora.

### 4.5.7 Multi-conflicto

Si el shortlist toca 2+ conflictos distintos (ej. una pregunta de pricing global cruza 5%-vs-10%, Thu/Sun, max-occupancy-vs-extra-fee), surface UN caveat por conflicto activo, en orden de relevancia para la pregunta. No agruparlos en un solo bloque difuso.

---

## 4.6 Format Check (query-time, regime-based) — O5

**Antes de redactar, lee `meta/RESPONSE_TEMPLATES.md`** del vault activo — contiene las plantillas canónicas A/B/C con secciones, ejemplos y reglas para ese dominio. Sin esa lectura no puedes garantizar el formato correcto. Las secciones obligatorias de cada régimen NO son sugerencias, son contrato.

> Las **reglas de detección de régimen y los ceilings** que siguen son globales (parte del contrato del plugin). Los **ejemplos de preguntas** en la tabla son del dominio OMA (anfitriones de Airbnb hispano-hablantes) por continuidad histórica; cada vault puede añadir patrones de detección propios de su dominio en `vaults/{name}/agents.md`.

### 4.6.1 Regime detection

| Régimen | Señales | Ceiling | Ejemplos de preguntas |
| --- | --- | --- | --- |
| **A. Narrow Factual** | una sola variable; busca dato/umbral/sí-no; verbos "cuánto", "cuál es", "se permite", "puedo", "qué precio", "qué pongo" | **250 palabras** | "¿Qué precio inicial pongo?" / "¿Cuánto cobro de tarifa de limpieza?" / "¿Activo Instant Book?" / "¿Qué pongo en el título?" / "¿Cuántas fotos subo?" |
| **B. Tactical Multi-Palanca** | pide pasos coordinados para EJECUTAR; verbos "cómo hago", "qué hago para", "cómo manejo", "cómo respondo"; 3-5 palancas | **600 palabras** | "¿Cómo respondo a una reseña negativa?" / "¿Cómo manejo noches huérfanas?" / "¿Qué amenities destaco?" / "¿Cómo filtro huéspedes problemáticos?" |
| **C. Taxonomic / Broad** | pide DECIDIR un marco antes de ejecutar; verbos "cómo elijo entre", "cómo decido entre", "diferencias entre", "panorama", "estrategia para escalar"; patrón "X o Y como marco/criterio principal"; comparativa o decision-tree natural | **1000 palabras** | "¿Cómo elijo PMS?" / "¿Cómo paso de 1 a 5 listings?" / "¿Cómo evalúo un mercado?" / "¿Cómo construyo direct bookings?" / "¿Cómo elijo entre gestionar ingresos o gestionar ocupación como marco principal?" |

**Orden de detección — aplica el primero que matchee**:

1. ¿La pregunta contiene "cómo elijo entre X o Y", "cómo decido entre", "X o Y como marco/criterio/eje principal", "diferencias entre X e Y", "comparativa", o nombra **dos sustantivos rivales** y pide elegir uno como marco rector? → **C** (regla disparadora; salta A/B aunque parezca acotado).
2. ¿Busca UN dato concreto / sí-no / umbral, sin pedir comparar opciones? → **A**
3. ¿Pide pasos para ejecutar mañana sobre UN problema acotado? → **B**
4. ¿Pide decidir un marco / comparar opciones / planificar escalado? → **C**

La regla 1 existe porque "Cómo elijo entre X o Y como marco principal" se confundía sistemáticamente con A. La presencia de la conjunción `entre … o …` (o `entre … y …`) emparejada con un verbo de elección (`elijo`, `decido`, `escojo`) o con `como X principal` es señal de C, no de A — el output debe llevar `Comparativa` y `Cómo elegir` aunque la pregunta parezca corta.

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

## 5. Core: Score, Naming, Rules, Commands, Checklist

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

## 6. Capa de dominio — Optimize My Airbnb

Específico de esta bóveda. **Para cualquier vault nuevo, el equivalente de esta sección vive en `vaults/{name}/agents.md`** — no aquí. Lo que sigue (fuentes, schema YAML extendido, tópicos, score, meta, ingest pipeline, response contract con audiencia/tono/forbid-list) es la instancia OMA del contrato per-vault. Las skills (`/query`, `/ingest`, `/audit`, `/qa`, `/test-vault`, `/refresh-hubs`, `/suggest-questions`, `/suggest-sources`, `/propagate`, `/init-vault`) son agnósticas al dominio y leen este contenido del `agents.md` del vault activo.

### 6.1 Fuentes

Transcripciones de [@OptimizeMyAirbnb](https://www.youtube.com/@OptimizeMyAirbnb). Creador: Daniel Rusteen.

**Estado**: 173 transcripciones (2017-11 → 2026-04). 5 en español excluidas.

### 6.2 Schema YAML

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

### 6.3 Tópicos

pricing | occupancy | listing-optimization | cleaning-ops | reviews | hospitality | ranking | direct-booking | market-selection | regulations | tools-tech | investing

### 6.4 Score

```text
score = 0.40·recency + 0.30·popularity + 0.20·specificity + 0.10·authority
```

### 6.5 Meta

`meta/videos.md` (auto) | `meta/contradictions.md` (manual) | `meta/glossary.md` (manual)

### 6.6 Ingest pipeline

`raw/` es per-lang: `raw/{lang}/{date}--slug.md`, una entrada por idioma de subtítulos disponible. La atomización corre **una vez** en `atomization_lang` (nativo del vídeo si está en `enabled`, si no `enabled[0]`); `propagate_atom.py` re-atomiza al mismo locator en cada otro idioma de `enabled` usando el transcript target como material primario (no es traducción).

```bash
.claude/scripts/ingest.sh <video_id>                                 # baja subs en cada lang de enabled
.claude/scripts/batch-ingest.sh <list_file>
.claude/scripts/extract_excerpt.py --raw-file <raw> --locator MM:SS-MM:SS   # cita verbatim sin LLM
.claude/scripts/propagate_atom.py <stem> --from <lang> --to <lang>   # re-atomiza al locator
.claude/scripts/init-vault.sh                                        # bootstrap nuevo bundle
```

### 6.7 Response contract

> Audiencia, tono, forbid-list y stance frente a anglicismos son **per-vault** y viven en `vaults/{name}/agents.md`. Lo que sigue es la instancia OMA. Las reglas estructurales (regime detection, ceilings, conflict caveat) sí son globales (§4.5–§4.6).

Audiencia: anfitrión. Tono: consultor — humano, profesional, cálido (no robótico).

**Regime + format** (§4.6):

- LEE `meta/RESPONSE_TEMPLATES.md` ANTES de redactar. Sin esa lectura no puedes garantizar formato.
- Detecta el régimen (A. Narrow Factual / B. Tactical / C. Taxonomic) por las heurísticas de §4.6.1.
- Ceilings duros: **A=250 / B=600 / C=1000** palabras. No exceder bajo ningún concepto.
- Cita `[[atom]]` por paso (B) o por celda/criterio (C). En A, 1-3 atoms inline.
- Sin intro innecesaria. Sin trailing summary.
- Cita números con `source_id`.

**Lenguaje (`language_purity`)** — escribe natively en la lang del output, como un bilingüe nativo redactando para monolingües del idioma target. No traduzcas ni hagas calcos. La pureza se puntúa estadísticamente en `/test-vault` por N evaluadores independientes; no hay tabla de substitución que aplicar a mano. Los nombres propios (marcas, productos, lugares, personas) y los términos técnicos universalmente conocidos por su sigla en inglés (ej. API, URL, JSON, YAML) permanecen verbatim — eso es escritura nativa, no anglicismo. La definición de qué cuenta como nombre propio y qué siglas son universales para tu dominio vive en el `agents.md` per-vault, no aquí.

**Forbid**: filler adjectives, "cabe destacar", "es importante mencionar", "en este sentido", trailing summaries, corporate-speak.

**Conflict caveat (§4.5)**: si el conflict-check arroja HIGH/MEDIUM, añade el bloque ⚠️ al final del cuerpo (template en `meta/RESPONSE_TEMPLATES.md` §A o §B). No omitir.

---

### Pre-output checklist (OBLIGATORIO antes de escribir el JSON final)

Recorre estos 6 puntos en orden. Si algún punto falla, corrige y vuelve a empezar el checklist:

1. **Cuenta palabras** del campo `response` (excluye metadata/citas). Si excede el ceiling de su régimen (A=250/B=600/C=1000), recorta hasta entrar. Prioridad: eliminar adjetivos de relleno, comprimir sub-bullets, fundir frases redundantes. NO devuelvas si excedes.
2. **Relee en `{lang}` buscando calcos del idioma fuente**. Si una frase suena como traducción literal, reescríbela como la diría un nativo. Nombres propios y siglas técnicas universales se mantienen verbatim.
3. **Cada paso (B) o cada celda comparativa (C) tiene exactamente UNA cita `[[atom]]`**. En A, 1-3 atoms inline.
4. **Cada número** (precio, porcentaje, plazo, umbral) está respaldado por al menos un `source_id` en `sources_cited`.
5. **No hay intro innecesaria** ("Excelente pregunta...", "Te explico...") ni **trailing summary** ("En resumen...", "Para concluir...").
6. **Si hay conflicto HIGH/MEDIUM** activo, el bloque ⚠️ está al final del cuerpo, no intercalado.

---

## 7. Multilingüismo

Una bóveda declara los idiomas habilitados en `vault.yml.languages.enabled[]` (lista plana, sin orden jerárquico). NO existe `primary` / `secondary` — todos los idiomas son first-class. Cada source tiene `atomization_lang` (nativo del vídeo si está en `enabled`, si no `enabled[0]`); el atom canónico nace ahí, y `propagate_atom.py` re-atomiza al mismo locator en cada otro idioma habilitado usando el transcript target como material primario (no es traducción).

---

## 8. Troubleshooting

**Query ceiling exceeded**: Check coverage, declare limits, decompose into sub-queries.

**Broken links**: Verify targets, clean stale entries.

**Stale atoms**: Rank recent sources, ingest new, extend atom, update `last_verified`.

**VAULT_PATH undefined**: Check `.claude/scripts/config.sh` has `export VAULT_PATH=...` (or set `VAULT_NAME` to use a `vaults/{name}/vault.yml`).

**Vault health audit**: `VAULT_NAME=<name> python3 .claude/scripts/vault-agent.py` — detects orphans, stale, gaps, broken links, missing propagations, missing cross-refs. Writes `meta/agent-reports/agent-report-YYYY-MM-DD.md`.

**Post-ingest auto-linking**: `VAULT_NAME=<name> python3 .claude/scripts/auto-link.py <atom-stem> --lang <lang>` — inserts `[[wiki/{lang}/atom]]` into relevant MOCs and regenerates `index/{lang}/index.md`. `--all` for full backfill (run once per lang). `--index-only` regenerates the index without touching atoms.

**Bash portability lint**: `bash .claude/scripts/lint-bash-portability.sh` — scans `.claude/scripts/` and `.claude/hooks/` for bash 4+ idioms (`declare -A`, `mapfile`, `${var,,}`). macOS ships bash 3.2 — run after editing any `.sh`. Also fires on `on-session-start.sh`.

**Multilingual propagation**: `VAULT_NAME=<name> python3 .claude/scripts/propagate_atom.py <stem> --from <lang> --to <lang>` — re-atomises the canonical atom at the same locator using the target transcript as primary material (not a translation). See §6.6 for the full model.

**LLM-fallback advisory queue**: `vaults/{name}/state/queue/llm-fallback.txt` lists sources whose `native_lang` is outside `enabled[]`. For these, atomization falls back to `enabled[0]` and the resulting atoms carry `excerpt_source: llm_fallback` (no verbatim transcript in the atomization lang). Surfaced at session start, on-bash-complete after ingest, and at `/ingest` time. Format per line: `<video_id>\t<native_lang>\t<atomization_lang>`. Informational, not blocking.
