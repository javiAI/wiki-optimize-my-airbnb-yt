---
automation:
  version: "3.0"
  current_phase: 1
  phase_status: "pending_approval"
  last_update: "2026-04-25T00:00:00Z"

phases:
  phase_1:
    status: "pending_approval"
    completed_tasks: []
    progress_percent: 0
    tasks: [O1, O2, O3]
  phase_2:
    status: "not_started"
    completed_tasks: []
    progress_percent: 0
    tasks: [O3, O4, O5, O6]
  phase_3:
    status: "not_started"
    completed_tasks: []
    progress_percent: 0
    tasks: [O7, O8, O9]
  phase_4:
    status: "not_started"
    completed_tasks: []
    progress_percent: 0
    tasks: [O10, O11, O12]

optimizations:
  O1: { name: "Hierarchical Indices", phase: 1, hours: 4, status: "pending_approval", ref: "docs/ARCHITECTURE.md §3" }
  O2: { name: "Fix Q4 Contradiction", phase: 1, hours: 0.5, status: "pending_approval", ref: "test_battery/OPTIMIZATIONS_ROADMAP_10X.md" }
  O3: { name: "Language Consistency", phase: 2, hours: 2, status: "not_started", ref: "docs/ARCHITECTURE.md PART 6" }
  O4: { name: "Contradiction Detection L1", phase: 2, hours: 3, status: "not_started", ref: "docs/ARCHITECTURE.md PART 4" }
  O5: { name: "Response Format Templates", phase: 2, hours: 2.5, status: "not_started" }
  O6: { name: "Executable Checklists", phase: 2, hours: 1.5, status: "not_started" }
  O7: { name: "Agent Orchestration", phase: 3, hours: 8, status: "not_started" }
  O8: { name: "Auto-Linking System", phase: 3, hours: 4, status: "not_started" }
  O9: { name: "Query Caching", phase: 3, hours: 6, status: "not_started" }
  O10: { name: "Semantic Gap Detection", phase: 4, hours: 3, status: "not_started" }
  O11: { name: "Backlink Generation", phase: 4, hours: 4, status: "not_started" }
  O12: { name: "RAG Fallback", phase: 4, hours: 6, status: "not_started" }

vault:
  name: "optimize-my-airbnb-yt"
  atoms: 156
  mocs: 12
  sources: 173
  quality_score: 8.52
  target_score: 9.8
---

## ROUTER: Cómo actúo basándome en estado

IF phase_status == "pending_approval":
  → Mostrar resumen de fase
  → Esperar aprobación explícita del usuario
  → Cuando aprobada: Actualizar YAML, git commit, pasar a "in_progress"

IF phase_status == "in_progress":
  → Ejecutar siguiente task incompleta
  → Actualizar YAML state
  → git commit
  → Siguiente task o transicionar a siguiente fase

---

## FASES Y TAREAS

| Fase | Tareas | Descripción | Ref |
|------|--------|-------------|-----|
| 1 | O1, O2, O3 | Critical Path (4.5h) | docs/ARCHITECTURE.md |
| 2 | O3-O6 | Quality Foundation (9h) | docs/ARCHITECTURE.md |
| 3 | O7-O9 | Automation (18h) | docs/ARCHITECTURE.md |
| 4 | O10-O12 | Integration (13h) | docs/MASTER_PLAN.md |

---

# 0. Filosofía

Esto **no es RAG**. El LLM construye y mantiene una wiki persistente en markdown que se enriquece con cada fuente nueva y cada pregunta contestada.

- **Obsidian es el IDE**; **el LLM es el programador**; **la wiki es la codebase**.
- El humano cura sources. El LLM hace todo el resto: resumir, enlazar, archivar, mantener.
- Tres capas estrictas:
  - **Raw** (inmutable) — fuentes tal cual
  - **Wiki** — MOCs, atómicos, queries, índice, log, meta
  - **Schema** (este archivo) — reglas del juego

---

## 0.5 Bóveda externa

Este repo no contiene la bóveda. La bóveda vive en `VAULT_PATH` (ej. `~/Dev/obsidian_vaults/optimize-my-airbnb-yt`).

```bash
source scripts/config.sh   # exporta VAULT_PATH
cd "$VAULT_PATH"           # opcional
```

---

## 0.7 Configuración inicial

```bash
mkdir -p ~/Dev/obsidian_vaults/optimize-my-airbnb-yt
mkdir -p $VAULT_PATH/{sources,notes,MOC,queries,meta}
touch $VAULT_PATH/{index.md,log.md}
touch $VAULT_PATH/meta/{contradictions.md,videos.md,glossary.md}
```

---

## 1. Principio operativo: 3 capas

| Capa | Contenido | Cuándo |
|------|-----------|--------|
| L1 – Índices | index.md, MOC/*.md, log.md | Siempre |
| L2 – Atómicos | 1 claim por nota | Tras filtrar L1 |
| L3 – Fuentes RAW | Texto crudo | Solo fragmentos (`offset`/`limit`) |

**Regla**: Si tentado a leer fuente completa → vuelve a L1.

---

## 2. Estructura de la bóveda

```
$VAULT/
├── index.md              # L1 — catálogo
├── log.md                # L1 — cronológico
├── sources/              # L3 — RAW
├── MOC/                  # L1 — Maps of Content
├── notes/                # L2 — atómicas
├── queries/              # L2 — guardadas
└── meta/                 # metadatos
```

### 2.1 `index.md`
Categorías: Temas (MOC) / Atómicos / Queries / Fuentes. Cada entrada = 1 línea: `[[ruta]] — resumen`.

### 2.2 `log.md`
Append-only. Formato:
```markdown
## [YYYY-MM-DD] <tipo> | <título>
- <detalles>
```
`<tipo>` ∈ `ingest` | `query` | `lint`.

---

## 3. Metadatos (YAML frontmatter)

### 3.1 Fuente — `sources/*.md`
```yaml
---
source_id: <id>
title: <título>
published: YYYY-MM-DD
topics: [tema1, tema2]
superseded_by: []
---
```

### 3.2 Nota atómica — `notes/*.md`
```yaml
---
claim: <una frase>
topics: [tema1, tema2]
confidence: high | medium | low
sources:
  - source_id: <id>
    locator: <puntero>
    excerpt: "<cita>"
conflicts_with: []
last_verified: YYYY-MM-DD
---
```
Cuerpo: 3-8 líneas.

### 3.3 Query guardada — `queries/*.md`
```yaml
---
question: <pregunta>
topics: [tema1, tema2]
answered_on: YYYY-MM-DD
sources_used: [[[notes/...]], [[sources/...]]]
confidence: high | medium | low
stale_if: <condición>
---
```

---

## 4. Operaciones

### 4.1 INGEST
1. Guardar en `sources/` con frontmatter.
2. Extraer claims → 1 claim = 1 nota en `notes/`.
3. Enlazar en MOC correspondiente.
4. Cruzar con atómicos existentes (extender si duplicado, crear si distinto, anotar si contradictorio).
5. Jerga nueva → `meta/glossary.md`.
6. Entrada en `log.md`.

### 4.2 QUERY
1. Abrir `index.md`.
2. Buscar en `queries/` primero (cache).
3. Si no cacheada: identificar tópicos, abrir MOC(s).
4. Clasificar scope → regime A/B/C (ver docs/IMPLEMENTATION_GUIDE.md).
5. Seleccionar atómicos.
6. Coverage self-check.
7. Responder citando `[[nota]]`.
8. Guardar en `queries/` si síntesis nueva.

### 4.3 LINT
Revisar: contradicciones, stale claims, huérfanos, gaps, drift del índice.

---

## 5. Priorización y conflictos

```
score = 0.40·recency + 0.30·popularity + 0.20·specificity + 0.10·authority
```

---

## 6. Naming y linking

- Notas: `<topic>--<kebab>.md`
- Queries: `<topic>--<kebab-pregunta>.md`
- Fuentes: `YYYY-MM-DD--<kebab>.md`
- Tags: solo en frontmatter `topics:`
- Links: `[[carpeta/archivo]]`

---

## 7. Reglas duras

- ❌ Leer fuente completa. Siempre `offset`/`limit`.
- ❌ Responder sin citar `[[fuente]]`.
- ❌ Inventar contenido.
- ❌ Resolver conflicto sin registrar en `meta/contradictions.md`.
- ❌ Notas con > 1 claim.
- ❌ Duplicar atómicos.
- ❌ Modificar `sources/` (inmutables).
- ❌ Cerrar operación sin entrada en `log.md`.

---

## 8. Comandos útiles (desde `$VAULT`)

```bash
grep "^## \[" log.md | tail -10                          # Actividad reciente
grep -h "topics:" notes/*.md | sort | uniq -c | sort -rn # Conteo atoms
grep -r "orphan night" index.md MOC/ notes/ queries/     # Localizar concepto
ls -1 sources/ | sort -r | head -20                      # Fuentes recientes
```

---

## 9. Checklist antes de responder

- [ ] Abrí `index.md` primero
- [ ] Consulté `queries/` antes de MOC + notes
- [ ] Cito `[[nota]]` + locator preciso
- [ ] Apliqué score de §5 si hay conflicto
- [ ] No leí ninguna fuente completa
- [ ] Guardé respuesta en `queries/` si síntesis nueva
- [ ] Añadí entrada a `log.md`

---

## 11. Troubleshooting

### Query excede ceiling
Revisar coverage self-check, declarar limitación, descomponer en sub-queries.

### Scripts fallan (yt-dlp, jq, python3)
Instalar con: `brew install yt-dlp jq python3` (macOS) o `apt-get` (Linux).

### index.md tiene links rotos
Verificar targets, limpiar entradas rotas.

### Atom parece stale
Rankear sources recientes, ingestar nuevas, extender atom, actualizar `last_verified`.

### VAULT_PATH no definido
Verificar `scripts/config.sh`, asegurar que contiene `export VAULT_PATH=...`.

---

# 10. Capa de dominio — Optimize My Airbnb (YouTube)

Específico de esta bóveda. Para nueva bóveda, reescribir solo esta sección.

## 10.1 Tipo de fuente

Transcripciones de [@OptimizeMyAirbnb](https://www.youtube.com/@OptimizeMyAirbnb). Creador: Daniel Rusteen. Tema: alquiler corta estancia.

**Estado**: 173 transcripciones (2017-11 → 2026-04). 5 vídeos en español excluidos.

## 10.2 Schema YAML de `sources/*.md`

```yaml
---
video_id: <youtube-id>
title: <título>
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

**Cuerpo**: bloques `[MM:SS]` cada ~20s.

**Locator**: timestamp `MM:SS` → `[[sources/YYYY-MM-DD--slug#t=MM:SS]]`.

## 10.3 Tópicos iniciales

- `MOC/pricing.md` — estrategias precio, noches huérfanas
- `MOC/occupancy.md` — tasas, gap nights
- `MOC/listing-optimization.md` — título, fotos, ranking
- `MOC/cleaning-ops.md` — limpieza, turnover
- `MOC/reviews.md` — mensajes, atributos
- `MOC/hospitality.md` — experience on-site
- `MOC/ranking.md` — factores búsqueda
- `MOC/direct-booking.md` — cuándo sí
- `MOC/market-selection.md` — filtros, perfil
- `MOC/regulations.md` — normativas, impuestos
- `MOC/tools-tech.md` — PriceLabs, Hostfully, etc
- `MOC/investing.md` — evaluación deals, ROI

## 10.4 Score (§5)

```
score = 0.40·recency + 0.30·popularity + 0.20·specificity + 0.10·authority
```

## 10.5 Meta files

- `meta/videos.md` — tabla maestra (auto-generated)
- `meta/contradictions.md` — conflictos + score
- `meta/glossary.md` — jerga (orphan night, gap night, KAT score)

## 10.6 Pipeline ingesta

```bash
scripts/ingest-video.sh <video_id_or_url>
scripts/batch-ingest.sh <list_file>
scripts/build-meta.sh
scripts/rank-sources.py --top 10
```

## 10.7 Response Contract

Audiencia: host. Tono: consultor.

- Sin intro a menos que pida.
- Lista numerada de pasos accionables.
- Una cita `[[atom]]` inline por paso.
- Max 600 (tácticas) / 1000 (estratégicas) palabras.
- Anglicismos: PriceLabs, Airbnb, WiFi, PMS, BLT.
- Sin: rellenos ("clave", "importante"), "cabe destacar", summaries.
- Citar números concretos con source_id.
