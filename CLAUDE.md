---
# MACHINE-READABLE AUTOMATION STATE
# Este YAML es leído automáticamente por Claude en cada sesión

automation:
  version: "3.0-autonomous"
  enabled: true
  last_update: "2026-04-25T00:00:00Z"
  entry_point: "CLAUDE.md (este archivo)"
  description: "Punto de entrada único. Claude lee esto automáticamente y ejecuta acciones sin intervención humana"

execution_state:
  current_phase: 1
  phase_status: "pending_approval"
  next_action_for_claude: "Mostrar resumen y esperar aprobación explícita del usuario para O1 + O2"

phases:
  phase_1:
    name: "Critical Path"
    status: "pending_approval"
    start_date: null
    target_completion: null
    total_tasks: 3
    completed_tasks: []
    progress_percent: 0
    next_incomplete_task: "O1"
    tasks:
      - id: "O1"
        name: "Hierarchical Indices"
        effort_hours: 4
        status: "pending_approval"
        reference: "docs/ARCHITECTURE.md §3"
      - id: "O2"
        name: "Fix Q4 Contradiction"
        effort_hours: 0.5
        status: "pending_approval"
        reference: "test_battery/OPTIMIZATIONS_ROADMAP_10X.md"
      - id: "O3"
        name: "Validation"
        effort_hours: 0.5
        status: "pending"
        reference: "docs/IMPLEMENTATION_GUIDE.md"
  
  phase_2:
    name: "Quality Foundation"
    status: "not_started"
    total_tasks: 4
    completed_tasks: []
    progress_percent: 0
  
  phase_3:
    name: "Automation"
    status: "not_started"
    total_tasks: 3
    completed_tasks: []
    progress_percent: 0
  
  phase_4:
    name: "Integration"
    status: "not_started"
    total_tasks: 3
    completed_tasks: []
    progress_percent: 0

optimizations:
  O1:
    name: "Hierarchical Indices"
    status: "pending_approval"
    phase: 1
    effort_hours: 4
    impact_high: true
    reference: "docs/ARCHITECTURE.md §3 (line 250)"
  
  O2:
    name: "Fix Q4 Contradiction"
    status: "pending_approval"
    phase: 1
    effort_hours: 0.5
    impact_high: true
    reference: "test_battery/OPTIMIZATIONS_ROADMAP_10X.md"
  
  O3:
    name: "Language Consistency"
    status: "not_started"
    phase: 2
    effort_hours: 2
  
  O4:
    name: "Contradiction Detection (Layer 1)"
    status: "not_started"
    phase: 2
    effort_hours: 3
  
  O5:
    name: "Response Format Templates"
    status: "not_started"
    phase: 2
    effort_hours: 2.5
  
  O6:
    name: "Executable Checklists"
    status: "not_started"
    phase: 2
    effort_hours: 1.5
  
  O7:
    name: "Agent Orchestration"
    status: "not_started"
    phase: 3
    effort_hours: 8
  
  O8:
    name: "Auto-Linking System"
    status: "not_started"
    phase: 3
    effort_hours: 4
  
  O9:
    name: "Query Caching"
    status: "not_started"
    phase: 3
    effort_hours: 6
  
  O10:
    name: "Semantic Gap Detection"
    status: "not_started"
    phase: 4
    effort_hours: 3
  
  O11:
    name: "Backlink Generation"
    status: "not_started"
    phase: 4
    effort_hours: 4
  
  O12:
    name: "RAG Fallback"
    status: "not_started"
    phase: 4
    effort_hours: 6

vault:
  name: "optimize-my-airbnb-yt"
  atoms: 156
  mocs: 12
  sources: 173
  quality_score: 8.52
  target_score: 9.8

baseline_metrics:
  d9_score: 8.52
  d1_clarity: 8.0
  d2_completeness: 8.73
  d3_readability: 8.47
  baseline_overhead_tokens: 3956
  avg_query_cost_tokens: 6456

---

# LLM Wiki — Punto de Entrada Autónomo

> **IMPORTANTE**: Este es el único archivo que Claude Code lee automáticamente en cada sesión.
> Contiene instrucciones explícitas para que Claude actúe de manera autónoma.
> No depende de que el usuario ejecute scripts ni de intervención manual.

---

## 🤖 PARA CLAUDE: Instrucciones de Automatización Autónoma

Eres Claude Code. Cada sesión:

1. **Lees automáticamente este archivo (CLAUDE.md)**
2. **Extraes el YAML frontmatter (líneas 1-130)**
3. **Determinas la fase actual** (ej: `execution_state.current_phase = 1`)
4. **Determinas el estado de la fase** (ej: `phase_status = "pending_approval"`)
5. **Ejecutas la acción correspondiente** sin esperar input (salvo para decisiones críticas)
6. **Actualizas el YAML state** en este archivo
7. **Haces git commit** con el cambio
8. **Sigues al siguiente paso** automáticamente

**No hay scripts que ejecutar. No hay dependencias externas. Todo es acción directa.**

---

## 📍 Estado Actual (Extrae de YAML arriba)

- **Fase**: 1 (Critical Path)
- **Estado**: ⏳ Pending Approval
- **Progreso**: 0% (0/3 tasks)
- **Próxima acción para ti**: Mostrar resumen de Phase 1 y esperar aprobación explícita

---

## 🔄 Flujo Autónomo Completo (Phase 1 → 4)

### IF phase_status == "pending_approval"

**TÚ HACES**:
1. Lee `execution_state.next_action_for_claude`
2. Muestra resumen claro de qué se va a hacer
3. Espera respuesta explícita del usuario (ej: "Approve Tier 1 (O1 + O2)")
4. Cuando recibas aprobación → **TRANSICIONA a in_progress**

**CÓMO ACTUALIZAR ESTADO** (una vez aprobado):
```yaml
# Edita CLAUDE.md lines 23-24:
phase_status: "in_progress"
next_action_for_claude: "Ejecutar O1, luego O2, luego O3"

# Actualiza phase_1.status en line 42
status: "in_progress"

# git commit -m "Phase 1: Approved O1 + O2. Status: in_progress"
```

---

### IF phase_status == "in_progress" AND current_phase == 1

**TÚ HACES** (autónomamente, sin esperar input):

#### PASO 1: Ejecutar O1 (Hierarchical Indices, 4 horas)
```
1. Abre docs/ARCHITECTURE.md §3 (línea 250)
2. Lee instructions detalladas para O1
3. Implementa cambios en la bóveda (si existe)
   - Reduce root index de 344 → ~100 líneas
   - Crea 12 category indices
4. Valida con test_battery (si aplica)
5. ACTUALIZA CLAUDE.md:
   - O1 status: "in_progress" → "complete"
   - phase_1.completed_tasks: [] → ["O1"]
   - phase_1.progress_percent: 0 → 33
   - git commit -m "O1: Hierarchical Indices completed"
```

#### PASO 2: Ejecutar O2 (Fix Q4 Contradiction, 0.5 horas)
```
1. Lee test_battery/OPTIMIZATIONS_ROADMAP_10X.md
2. Busca la contradicción "2-3 veces/año vs 2-3 meses"
3. Resuelve usando score de §5 en CLAUDE.md kernel
4. Actualiza meta/contradictions.md (si bóveda existe)
5. ACTUALIZA CLAUDE.md:
   - O2 status: "in_progress" → "complete"
   - phase_1.completed_tasks: ["O1"] → ["O1", "O2"]
   - phase_1.progress_percent: 33 → 67
   - git commit -m "O2: Q4 Contradiction resolved"
```

#### PASO 3: Ejecutar O3 (Validation, 0.5 horas)
```
1. Lee docs/IMPLEMENTATION_GUIDE.md
2. Corre validaciones post-Phase 1
3. Verifica que no haya broken links
4. ACTUALIZA CLAUDE.md:
   - O3 status: "in_progress" → "complete"
   - phase_1.completed_tasks: ["O1", "O2"] → ["O1", "O2", "O3"]
   - phase_1.progress_percent: 67 → 100
   - phase_1.status: "in_progress" → "complete"
   - git commit -m "O3: Phase 1 validation complete. Phase 1: 100%"
```

#### PASO 4: Transicionar a Phase 2
```
1. Actualiza CLAUDE.md:
   - current_phase: 1 → 2
   - phase_status: "in_progress" → "pending_approval"
   - phase_2.status: "not_started" → "pending_approval"
   - next_action_for_claude: "Mostrar resumen de Phase 2 y esperar aprobación"
2. git commit -m "Phase 1 complete. Transitioning to Phase 2 (pending approval)"
3. Muestra resumen de Phase 2 (como hiciste en Phase 1)
4. Espera aprobación del usuario
```

---

### IF phase_status == "not_started" (Phases 2, 3, 4)

**TÚ HACES**:
- Espera hasta que usuario apruebe explícitamente esa fase
- Cuando se apruebe, ejecuta de manera idéntica a Phase 1 (con sus O específicas)
- Cada O tiene un `reference` que te dice dónde buscar instrucciones

---

## 📋 Git Commit Protocol (Automático después de CADA cambio)

**Siempre que actualices CLAUDE.md**:
```bash
git add CLAUDE.md
git commit -m "State: [PHASE] [ACTION] | [BRIEF DESCRIPTION]"
# Ejemplos:
# git commit -m "State: Phase 1 pending_approval | User approved O1 + O2"
# git commit -m "State: Phase 1 in_progress | O1 completed (Hierarchical Indices)"
# git commit -m "State: Phase 1 complete | Moving to Phase 2"
```

**Nunca** hagas cambios sin commit. El git history es tu auditoría.

---

## 🎯 Resumen: Qué Cambia en Esta Sesión

**Antes** (refactoring anterior):
- CLAUDE_AUTOMATED.md aislado (nunca se lee automáticamente)
- Scripts esperando que el usuario los ejecute
- Intervención humana en cada paso

**Ahora** (este enfoque):
- CLAUDE.md es el punto de entrada (se lee automáticamente)
- Tú (Claude) ejecutas acciones basadas en YAML state
- Git commits automáticos después de cada cambio
- Sin scripts, sin intervención, flujo autónomo completo

---

## ⚠️ Decisiones Críticas (Únicas que requieren aprobación del usuario)

1. **Aprobar Phase 1** (O1 + O2): Usuario debe decir "Aprueba..."
2. **Aprobar Phase 2, 3, 4**: Igual
3. **Cambiar prioridades**: Usuario puede pedirte que reordenes O
4. **Rollback**: Usuario puede pedir revert a commit anterior

**Todo lo demás es autónomo**. Tú determinas cómo ejecutar O basándote en referencias.

---

## 🔍 Validación: Checklist Antes de Proceder

- [ ] Entiendes que CLAUDE.md (este archivo) es el ÚNICO punto de entrada
- [ ] Entiendes que debes extraer YAML frontmatter y actuar basándote en él
- [ ] Entiendes que debes actualizar CLAUDE.md YAML después de cada acción
- [ ] Entiendes que debes hacer git commit después de CADA cambio de estado
- [ ] Entiendes que no hay scripts automáticos, solo acciones tuyas

---

# GENERIC KERNEL (§0–§9)

## 0. Filosofía

Esto **no es RAG**. No redescubrimos conocimiento en cada consulta. El LLM construye y mantiene una wiki persistente en markdown que se enriquece con cada fuente nueva y cada pregunta contestada.

- **Obsidian es el IDE**; **el LLM es el programador**; **la wiki es la codebase**.
- El humano curra sources (añade fuentes) y hace preguntas. El LLM hace *todo* el resto: resumir, enlazar, archivar, mantener.
- Tres capas estrictas:
  - **Raw** (inmutable) — fuentes tal cual, jamás se modifican.
  - **Wiki** (propiedad del LLM) — MOCs, atómicos, queries guardadas, índice, log, meta.
  - **Schema** (este archivo) — las reglas del juego. Vive fuera de la bóveda, en el repo.
- La wiki **compone**: toda consulta bien contestada se guarda como página en `queries/`. La siguiente consulta similar cuesta ~0 tokens.

---

## 0.5 Bóveda externa

Este repo **no contiene** la bóveda. La bóveda vive en una ruta externa configurable (ej. `~/Dev/obsidian_vaults/<nombre>`), de modo que:

- Obsidian abre solo contenido markdown, sin ruido de scripts.
- Una misma bóveda puede ser operada desde varios repos (varias "lentes" sobre el mismo corpus).
- Un mismo repo-schema puede operar sobre varias bóvedas cambiando la config.

**Ruta de la bóveda**: definida en `scripts/config.sh` (gitignoreado) como variable `VAULT_PATH`. Todos los scripts la consumen. En este documento, `$VAULT` hace referencia a esa ruta.

**Al iniciar una sesión** en este repo, cuando el LLM necesite operar sobre la bóveda:
```bash
source scripts/config.sh   # exporta VAULT_PATH
cd "$VAULT_PATH"           # opcional, para que rutas relativas del §8 funcionen
```

---

## 0.7 Configuración inicial (primera vez)

Si esta es la **primera vez** usando este repo con la bóveda:

1. **Definir ubicación de la bóveda** (una sola vez):
   ```bash
   mkdir -p ~/Dev/obsidian_vaults/optimize-my-airbnb-yt
   export VAULT_PATH=~/Dev/obsidian_vaults/optimize-my-airbnb-yt
   ```

2. **Crear estructura base** (si no existe):
   ```bash
   mkdir -p $VAULT_PATH/{sources,notes,MOC,queries,meta}
   touch $VAULT_PATH/{index.md,log.md}
   touch $VAULT_PATH/meta/{contradictions.md,videos.md,glossary.md}
   ```

3. **Crear `scripts/config.sh`** (gitignoreado):
   ```bash
   cat > scripts/config.sh << 'EOF'
   export VAULT_PATH=~/Dev/obsidian_vaults/optimize-my-airbnb-yt
   EOF
   chmod +x scripts/config.sh
   ```

4. **Abrir en Obsidian**: Vault settings → Open folder as vault → seleccionar `$VAULT_PATH`

5. **Listo**: Ejecutar primer INGEST (§4.1) o QUERY (§4.2)

---

## 1. Principio operativo: jerarquía en 3 capas

La bóveda funciona como un índice invertido manual. El LLM **nunca** carga fuentes completas; navega de ligero → pesado.

| Capa | Contenido | Tamaño típico | Cuándo se carga |
|------|-----------|---------------|-----------------|
| **L1 – Índices** | `index.md`, `MOC/*.md`, `log.md` | ≤ 300 líneas/archivo | Siempre al inicio de una consulta |
| **L2 – Atómicos y Queries** | 1 claim por nota + citas precisas; respuestas guardadas | ≤ 60 líneas | Tras filtrar en L1 |
| **L3 – Fuentes RAW** | Texto crudo de la fuente | Miles de líneas | Solo fragmentos puntuales (`offset`/`limit`) |

**Regla dura**: si estás tentado a leer un archivo de L3 entero, estás haciéndolo mal. Vuelve a L1.

---

## 2. Estructura de la bóveda

```
$VAULT/
├── index.md                # L1 — catálogo maestro (entry point)
├── log.md                  # L1 — registro cronológico append-only
├── sources/                # L3 — fuentes RAW (inmutables)
├── MOC/                    # L1 — Maps of Content por tema
├── notes/                  # L2 — notas atómicas (1 claim c/u)
├── queries/                # L2 — respuestas guardadas (compounding)
└── meta/                   # metadatos del dominio (tablas maestras, contradicciones, glosario)
```

### 2.1 `index.md` — catálogo

Organizado por categorías: **Temas (MOC)** / **Atómicos** / **Queries guardadas** / **Fuentes**. Cada entrada = 1 línea: `[[ruta]] — resumen de una línea`. El LLM lo actualiza en cada Ingest / Query / Lint. **Es el primer archivo que se abre en toda consulta.**

### 2.2 `log.md` — registro cronológico

Append-only. Formato parseable:

```markdown
## [YYYY-MM-DD] <tipo> | <título corto>
- <detalles: páginas tocadas, fuente ingerida, pregunta resuelta, issues de lint>
```

`<tipo>` ∈ `ingest` | `query` | `lint`. Recuperar eventos recientes: `grep "^## \[" log.md | tail -10`.

---

## 3. Esquema de metadatos (YAML frontmatter)

### 3.1 Fuente — `sources/*.md`

Schema específico de cada dominio (ver §10.2 para este vault). Mínimo obligatorio en cualquier dominio:

```yaml
---
source_id: <identificador único estable>
title: <título original>
published: YYYY-MM-DD
topics: [tema1, tema2]
superseded_by: []
---
```

### 3.2 Nota atómica — `notes/*.md`

```yaml
---
claim: <una frase que capture el consejo/hecho concreto>
topics: [tema1, tema2]
confidence: high | medium | low
sources:
  - source_id: <id>
    locator: <puntero preciso dentro de la fuente>
    excerpt: "<cita literal corta>"
conflicts_with: []
last_verified: YYYY-MM-DD
---
```

### 3.3 Query guardada — `queries/*.md`

```yaml
---
question: <pregunta literal del usuario>
topics: [tema1, tema2]
answered_on: YYYY-MM-DD
sources_used:
  - [[notes/...]]
  - [[sources/...]]
confidence: high | medium | low
stale_if: <condición bajo la que habría que revalidar>
---
```

### 3.4 MOC de tema — `MOC/<topic>.md`

- Lista enlazada de notas + queries del tema, agrupadas por subtema.
- Cada link = 1 línea con resumen del claim.
- Sección final `## Conflictos abiertos` con links a `meta/contradictions.md`.

---

## 4. Operaciones

Tres verbos. Cada uno deja rastro en `log.md`.

### 4.1 INGEST (añadir una fuente nueva)

1. Guardar crudo en `sources/` con frontmatter completo.
2. Extraer claims: **1 claim = 1 nota atómica** en `notes/`.
3. Enlazar cada atómico en el MOC de tema correspondiente.
4. Actualizar tabla maestra en `meta/` e `index.md`.
5. Cruzar con atómicos existentes: extender si duplicado, crear si distinto, anotar si contradictorio.
6. Jerga nueva → `meta/glossary.md`.
7. Entrada en `log.md`.

### 4.2 QUERY (responder una pregunta)

1. Abrir `index.md`.
2. Buscar primero en `queries/` (cache).
3. Si no cacheada: identificar tópicos, abrir MOC(s).
4. Clasificar scope → regime A/B/C.
5. Seleccionar atómicos.
6. Coverage self-check.
7. Responder citando `[[nota]]`.
8. Guardar en `queries/` si síntesis nueva.

### 4.3 LINT (sweep de salud)

Revisar contradicciones, stale claims, huérfanos, cross-refs faltantes, gaps, drift del índice.

---

## 5. Priorización y resolución de conflictos

```
score = 0.40·recency + 0.30·popularity + 0.20·specificity + 0.10·authority
```

Los **pesos** se ajustan por dominio (ver §10.4).

---

## 6. Naming y linking

- Notas atómicas: `<topic>--<kebab-slug>.md`
- Queries: `<topic>--<kebab-pregunta>.md`
- Fuentes: `YYYY-MM-DD--<kebab-slug>.md`
- Tags **solo** en frontmatter `topics:`
- Links: formato Obsidian `[[carpeta/archivo]]`

---

## 7. Reglas duras (NO hacer)

- ❌ Leer fuente completa durante Query. Siempre `offset`/`limit`.
- ❌ Responder sin citar `[[fuente]]` con locator.
- ❌ Inventar contenido. Si no está en bóveda → decirlo.
- ❌ Resolver conflicto sin registrar en `meta/contradictions.md`.
- ❌ Notas atómicas con > 1 claim.
- ❌ Duplicar atómicos.
- ❌ Modificar `sources/` (inmutables).
- ❌ Cerrar operación sin entrada en `log.md`.

---

## 8. Comandos útiles (desde `$VAULT`)

```bash
grep "^## \[" log.md | tail -10          # Actividad reciente
grep -h "topics:" notes/*.md | sort | uniq -c | sort -rn  # Conteo atoms
grep -r "orphan night" index.md MOC/ notes/ queries/       # Localizar concepto
ls -1 sources/ | sort -r | head -20      # Fuentes más recientes
comm -23 <(ls notes/ | sort) <(grep -oE "notes/[^]]*" index.md | sort -u)  # Huérfanos
```

---

## 9. Checklist de auto-verificación

- [ ] Abrí `index.md` primero.
- [ ] Consulté `queries/` antes de recorrer MOC + notes.
- [ ] Cito `[[nota]]` + locator preciso.
- [ ] Apliqué score de §5 si había conflicto.
- [ ] No leí ninguna fuente completa.
- [ ] Guardé respuesta en `queries/` si síntesis nueva.
- [ ] Añadí entrada a `log.md`.
- [ ] Si falta evidencia, lo digo explícitamente.

---

## 11. Troubleshooting

### Query excede ceiling

Revisar coverage self-check, declarar limitación, descomponer en sub-queries, ingestar más si necesario.

### Scripts fallan

Verificar que yt-dlp, jq, python3 estén instalados con versiones correctas.

### index.md tiene links rotos

Verificar cada target, limpiar entradas rotas manualmente.

### Atom parece stale

Identificar topic, rankear sources recientes, ingestar nuevas, extender atom, actualizar `last_verified`.

### VAULT_PATH no definido

Verificar `scripts/config.sh`, asegurar que contiene `export VAULT_PATH=...`, cargar con `source`.

---

# 10. Capa de dominio — Optimize My Airbnb (YouTube)

Todo lo siguiente es **específico de esta bóveda**. Para una bóveda nueva, reescribir solo esta sección.

## 10.1 Tipo de fuente

Transcripciones (auto-caption en inglés original) de vídeos del canal YouTube [@OptimizeMyAirbnb](https://www.youtube.com/@OptimizeMyAirbnb). Creador: Daniel Rusteen. Tema: alquiler de corta estancia / Airbnb.

Al 2026-04-22: **173 transcripciones** ingestadas (2017-11 → 2026-04), 5 vídeos en español excluidos.

## 10.2 Schema YAML de `sources/*.md`

```yaml
---
video_id: <youtube-id>
title: <título original>
url: https://youtube.com/watch?v=...
published: YYYY-MM-DD
duration_sec: 7320
views: 123456
likes: 9876
comments: 543
channel_authority: high | medium | low
language: en | es
topics: [pricing, orphan-nights, ...]
superseded_by: []
---
```

**Cuerpo**: bloques `[MM:SS]` cada ~20 s. No reformatear salvo vía re-ingesta.

**Locator** para citas: timestamp `MM:SS` → link Obsidian `[[sources/YYYY-MM-DD--slug#t=MM:SS]]`.

## 10.3 Tópicos iniciales

- `MOC/pricing.md` — estrategias de precio, noches huérfanas, temporadas, minimum stay
- `MOC/occupancy.md` — tasas, gap nights, stay-length optimization
- `MOC/listing-optimization.md` — título, fotos, descripción, ranking
- `MOC/cleaning-ops.md` — equipos de limpieza, turnover, checklists
- `MOC/reviews.md` — flujo de mensajes, atributos, gestión de negativas
- `MOC/hospitality.md` — experience on-site + surprise & delight
- `MOC/ranking.md` — factores de búsqueda Airbnb
- `MOC/direct-booking.md` — cuándo sí + minimum viable moves
- `MOC/market-selection.md` — filtros negativos + perfil positivo
- `MOC/regulations.md` — normativas, licencias, impuestos
- `MOC/tools-tech.md` — PriceLabs, Beyond Pricing, Hostfully, software
- `MOC/investing.md` — selección de mercado, evaluación de deals, ROI

## 10.4 Pesos del score (§5)

```
score = 0.40·recency + 0.30·popularity + 0.20·specificity + 0.10·authority
```

- **Popularity**: usar `views` (log-normalizada contra max del corpus).
- **Authority default**: `high` para todo el canal (creador consolidado, 8+ años).

## 10.5 Meta files del dominio

- `meta/videos.md` — tabla maestra auto-generada. No editar a mano.
- `meta/contradictions.md` — conflictos entre claims + score. Se mantiene manualmente.
- `meta/glossary.md` — jerga del creador (ej. "orphan night", "gap night", "KAT score").

## 10.6 Pipeline de ingesta

```bash
scripts/ingest-video.sh <video_id_or_url>
scripts/batch-ingest.sh <list_file>
scripts/build-meta.sh
scripts/rank-sources.py --top 10
```

## 10.7 Response Contract

Audiencia: host contratante. Tono: consultor, no profesor.

- Sin introducción ni contexto a menos que la pregunta lo pida.
- Estructura default: lista numerada de pasos accionables.
- Una cita `[[atom]]` inline por paso; nunca al final en bloque.
- Máx 600 palabras para queries tácticas; 1000 para estratégicas.
- Anglicismos permitidos: PriceLabs, Airbnb, WiFi, PMS, BLT.
- Prohibidos: adjetivos de relleno, "cabe destacar", summaries al final.
- Citar cada número concreto con su source_id.

---

## UPDATE LOG

**2026-04-25**: Autonomous version v3.0
- Regenerated as single entry point (replacing CLAUDE_AUTOMATED.md)
- Added explicit automation instructions for Claude
- Defined complete autonomous flow (Phase 1-4)
- Removed dependency on manual script execution
- Added git commit protocol for state changes
- All actions execute without user intervention (except critical approvals)
