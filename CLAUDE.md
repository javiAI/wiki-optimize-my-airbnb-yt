# LLM Wiki — Schema

> Contrato humano↔agente. Define cómo el LLM opera sobre una bóveda en Obsidian construida incrementalmente a partir de fuentes curadas.
>
> **Misión**: segundo cerebro **compuesto incrementalmente** por el LLM. Responder preguntas muy específicas con el mínimo coste de tokens, saltando solo a los fragmentos relevantes — incluso si la respuesta aparece en una porción diminuta de una sola fuente.
>
> **Estructura**: este archivo está dividido en dos capas:
> - **Kernel** (§0–§9): genérico, reutilizable. Copiable tal cual a cualquier otra bóveda.
> - **Capa de dominio** (§10): específica de *este* vault (canal YouTube Optimize My Airbnb).
>
> **Última revisión**: 2026-04-24 (schema revision post-benchmark: §4.2 rediseñado — 3 regímenes A/B/C con clasificación heurística en §4.2.a, coverage self-check obligatorio en step 7, asimetría atoms/fragments explícita, budget-check.sh añadido; revisiones previas: 2026-04-22 post-batch-1)

---

## Quick Start (Sesión Nueva)

Flujo de 30 segundos:

```bash
source scripts/config.sh       # Exporta VAULT_PATH
cd "$VAULT_PATH"              # Navega a la bóveda
```

Luego en Claude Code:

1. Abre `index.md` primero
2. Busca en `queries/` (si existe)
3. Si no hay cached: abre MOC del tema
4. Selecciona atoms por regime (§4.2.a)
5. Responde citando `[[nota]]`
6. Guarda query nueva en `queries/` si aporta síntesis
7. Añade entrada a `log.md`

---

## Prerequisites

Herramientas requeridas (instalar una vez):

```bash
# macOS
brew install yt-dlp jq python3

# Linux (Debian/Ubuntu)
apt-get install yt-dlp jq python3

# Versiones mínimas
yt-dlp ≥ 2024.01   # YouTube transcript download
jq ≥ 1.6           # JSON parsing
python3 ≥ 3.8      # Scripts de limpieza + ranking
bash ≥ 4.0         # Arrays asociativos (budget-check.sh)
```

Verificar: `yt-dlp --version && jq --version && python3 --version`

---

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
superseded_by: []        # IDs que lo contradicen con más recencia/autoridad
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
    locator: <puntero preciso dentro de la fuente — depende del dominio>
    excerpt: "<cita literal corta>"
conflicts_with: []
last_verified: YYYY-MM-DD
---
```

Cuerpo: 3-8 líneas. El `claim` es la respuesta; el resto son condiciones (*"aplica solo si…"*).

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

Cuerpo: respuesta directa + razonamiento abreviado + citas. Se trata como página de referencia desde entonces.

### 3.4 MOC de tema — `MOC/<topic>.md`

- Lista enlazada de notas + queries del tema, agrupadas por subtema.
- Cada link = 1 línea con resumen del claim.
- Sección final `## Conflictos abiertos` con links a `meta/contradictions.md`.

---

## 4. Operaciones

Tres verbos. Cada uno deja rastro en `log.md`.

### 4.1 INGEST (añadir una fuente nueva)

1. Guardar crudo en `sources/` con frontmatter completo (§3.1 + schema de dominio).
2. Extraer claims: **1 claim = 1 nota atómica** en `notes/`.
3. Enlazar cada atómico en el MOC de tema correspondiente.
4. Actualizar tabla maestra en `meta/` e `index.md` (entradas nuevas).
5. Cruzar con atómicos existentes (por `topics` en el MOC correspondiente):
   - **Mismo claim** (semánticamente equivalente) → **extender** `sources:` del atom existente. Nunca crear duplicado.
   - **Claim relacionado pero distinto** (matiz, condición, caso aparte) → crear atom nuevo + link mutuo en el cuerpo (`Ver [[notes/...]]`).
   - **Claim contradictorio** → crear/mantener ambos atoms, anotar `conflicts_with: [otro-atom]` en los dos, y registrar en `meta/contradictions.md` con el score §5 calculado.
6. Jerga nueva → `meta/glossary.md`.
7. Entrada en `log.md`: `## [YYYY-MM-DD] ingest | <título>` + páginas tocadas.

**Umbral de atomicidad**: si una nota tiene > 1 claim independiente, partirla. Test: *"¿se puede citar esta nota como respuesta completa a una pregunta concreta?"* Si no → partir.

### 4.1.a Batch extraction (recomendado tras pilot)

Tras validar §4.1 sobre 1 source piloto, atomizar en lotes de 8-12 sources rankeadas por §5 (`scripts/rank-sources.py --top N`).

Flujo:
1. Ranker imprime top-N → seleccionar lote.
2. Leer todos los sources del lote **en paralelo** (§7 permite full-read durante Ingest para sources ≤ 400 líneas).
3. Extraer atoms con dedup **agresivo**: aplicar §4.1 step 5 — antes de crear un atom nuevo, buscar claim equivalente en el MOC y **extender** `sources:` si existe.
4. Medir **saturación**: ratio `atoms_con_≥2_sources / atoms_totales_del_lote`. ≥30% = señal de madurez del corpus (los batches siguientes rendirán menos atoms nuevos y más extensiones).
5. Entrada consolidada en `log.md` al final del lote (no una por source).
6. **Lint sweep obligatorio** (§4.3) entre batches para detectar drift antes de acumular.

### 4.2 QUERY (responder una pregunta)

Ejecutar **en orden** y parar cuando haya respuesta defendible:

1. Abrir `index.md`.
2. **Buscar primero en `queries/`** — si hay una respuesta previa todavía válida (chequear `stale_if`), citarla. Coste ≈ 0.
3. Si no hay query cacheada: identificar tópicos, abrir MOC(s) correspondiente(s).
4. **Clasificar scope del query** (§4.2.a) → regime **A / B / C** → determina atom count inicial del shortlist.
5. Seleccionar atómicos candidatos ordenados por score de §5 (cantidad según regime).
6. Leer solo esos atómicos.
7. **Coverage self-check (obligatorio en todos los regímenes)**: listar palancas del MOC no cubiertas por el shortlist. Si alguna palanca relevante queda sin cubrir → expandir shortlist **+3-5 atoms** dentro del ceiling del regime. Si el ceiling se alcanza con gaps persistentes → declarar la limitación explícitamente en la respuesta.
8. Si un atómico cita un fragmento ambiguo, abrir la fuente con `Read` + `offset`/`limit` centrado en el locator (para transcripciones: ±60 s ≈ 40 líneas). **Asimetría de coste**: atoms ≈ 500 tok c/u, fragments ≈ 1-2k tok c/u. Preferir **+atoms antes que +fragments** — fragments solo para desambiguar citas, no para cubrir palancas.
9. Si hay conflicto entre fuentes → aplicar §5 y registrar en `meta/contradictions.md` si no estaba.
10. Responder citando `[[nota]]` + locator preciso de la fuente. Si la evidencia es escasa, decirlo.
11. **Guardar la respuesta** en `queries/<topic>--<kebab-pregunta>.md` si aporta síntesis nueva (§3.3). Actualizar `index.md` y añadir entrada a `log.md`.

#### 4.2.a Clasificación de scope (heurística explícita, obligatoria en step 4)

Tras abrir MOC(s) en step 3, asignar regime. Un regime gana por **cualquiera** de sus triggers. En empate o ambigüedad → subir un regime (A→B, B→C). Coste extra de tokens < coste de re-plantear.

**Regime A — Narrow factual** — shortlist 5 atoms, ≤2 fragments, **ceiling ~8k tokens**, score objetivo ≥9.25:
- Trigger léxico: `¿cuándo…?`, `¿cuánto…?`, `¿cuál es…?`, `¿debo hacer X?`, `¿X o Y?` (binaria).
- Trigger estructural: la pregunta menciona 1 palanca específica y pide condición/threshold/valor.
- Trigger MOC: ≤3 atoms claramente relevantes en la sección tocada.

**Regime B — Tactical multi-palanca** — shortlist 6-10 atoms, ≤3 fragments, **ceiling ~10k tokens**, score objetivo ≥9.3:
- Trigger léxico: `¿cómo optimizar X?`, `¿cómo mejorar Y?`, `¿qué pasos para Z?`, `¿cómo gestionar W?`.
- Trigger estructural: 1 proceso o decisión con 3-6 palancas interdependientes.
- Trigger MOC: 4-6 atoms relevantes en las secciones tocadas.

**Regime C — Taxonomic / broad** — shortlist 10-15 atoms, ≤3 fragments, **ceiling ~13k tokens**, score objetivo ≥9.5:
- Trigger léxico: `¿mejor X?`, `¿todas las Y?`, `¿qué amenities/palancas/tácticas…?`, `¿cómo maximizar Z?`, preguntas de ranking o exhaustividad.
- Trigger estructural: la pregunta pide comparativa entre muchas opciones o cobertura completa de un sub-dominio.
- Trigger MOC: 7+ atoms relevantes en la sección tocada (aunque el trigger léxico sea débil).

#### Ejemplo: Clasificación de regime en práctica

**Q: "¿Cuál es la mejor estrategia para una noche huérfana el miércoles?"**

1. Léxico: "mejor estrategia" → exploración amplia → candidate **Regime B**
2. Estructura: 3 palancas (pricing, occupancy, reviews) → **Regime B confirmado**
3. MOC check: pricing + occupancy + hospitality ≈ 6+ atoms relevantes → fit B
4. **Acción**: Shortlist 6-10 atoms, ≤3 fragments, presupuesto ~10k tokens

**Q: "¿4.8 rating es bueno?"**

1. Léxico: "¿Es X bueno?" (binaria) → **Regime A**
2. Estructura: 1 palanca (rating tiers), 1 métrica
3. **Acción**: Shortlist 3-5 atoms, ≤2 fragments, presupuesto ~8k tokens

---

⚠️ **BLOCKER: index.md limita presupuesto de consulta**

**Problema actual**: `index.md` tiene 344 líneas ≈ 4k tokens. Se carga siempre en step 1, consumiendo 50% del presupuesto de Regime A.

**Workaround**: Ceilings ampliados temporalmente a **8k / 10k / 13k** (2026-04-24).

**Solución definitiva**: Completar optimización #4 en `memory/optimizations_pending.md`:
- Compactar `index.md` a ≤150 líneas ≈ 1.7k tokens
- Recuperar ~2.3k tokens por query
- Revertir ceilings a **4k / 6k / 8.5k** (valores diseñados)

**Estado**: Tracked pero no iniciado. Prioritario si las queries regularmente rozan techo.

---

**Presupuesto por consulta**: ≤ `index.md` + 1 query cacheada **o** (regime A/B/C según §4.2.a, respetando su ceiling). Ceilings son **hard caps**; si se exceden con gaps persistentes tras el self-check (step 7), replantear la pregunta — puede requerir descomposición en sub-queries.

**Medición post-query**: `scripts/budget-check.sh --regime <A|B|C> <files-leídos>` — estima tokens (líneas × 11.5) y verifica contra ceiling. Obligatorio para queries que parezcan rozar el ceiling.

### 4.3 LINT (sweep de salud de la wiki)

Ejecutar a petición del usuario o periódicamente. Revisar:

- **Contradicciones** no anotadas.
- **Stale claims**: atómicos con `last_verified` > 6 meses y fuentes más recientes en el mismo tópico.
- **Huérfanos**: páginas sin inbound links desde MOC o `index.md`.
- **Cross-refs faltantes**: conceptos mencionados pero sin página propia.
- **Gaps**: subtemas recurrentes en fuentes sin MOC ni atómicos.
- **Drift del índice**: entradas en `index.md` que apuntan a archivos renombrados o inexistentes.

Output: reporte + propuestas de fix. Al aplicar, entrada en `log.md`.

---

## 5. Priorización y resolución de conflictos

Cuando dos fuentes se contradicen, gana el mayor score:

```
score = w_r·recency + w_p·popularity + w_s·specificity + w_a·authority
```

- **recency**: 1 si publicado en los últimos 6 meses, 0 si > 3 años (lineal entre medias).
- **popularity**: normalización `log10(métrica) / log10(max_en_corpus)` usando la métrica de popularidad del dominio.
- **specificity**: 1 = tema principal de la fuente, 0.5 = mención, 0.1 = tangencial.
- **authority**: high=1, medium=0.6, low=0.3. Para fuentes con invitados, colabs o garantía editorial distinta.

Los **pesos** `w_r/w_p/w_s/w_a` se ajustan por dominio (ver §10.4).

**Override explícito**: si la fuente misma dice literalmente *"ya no recomiendo X"* o *"antes decía Y, ahora Z"*, esa fuente supersede a las anteriores. Anotar en `superseded_by`.

**Empate**: gana la más reciente.

**Log obligatorio**: toda resolución no trivial → `meta/contradictions.md` con el score calculado.

---

## 6. Naming y linking

- Notas atómicas: `<topic>--<kebab-slug>.md`.
- Queries: `<topic>--<kebab-pregunta>.md`.
- Fuentes: `YYYY-MM-DD--<kebab-slug>.md` (ISO primero → orden natural por `ls`).
- Tags **solo** en frontmatter `topics:`. No usar `#tag` inline (ruido + índice duplicado).
- Links entre páginas: formato Obsidian `[[carpeta/archivo]]` o `[[carpeta/archivo|alias]]`.

---

## 7. Reglas duras (NO hacer)

- ❌ Leer una fuente completa durante **Query** o **Lint**. Siempre `offset`/`limit`.
  - **Excepción Ingest (§4.1)**: la extracción de átomos sí requiere leer el source. Para sources ≤ 400 líneas, leer completo es aceptable. Para > 400 líneas, chunkear en ventanas de 200 con `offset`/`limit` y consolidar al final.
- ❌ Responder sin citar al menos una `[[fuente]]` con locator preciso.
- ❌ Inventar contenido que no esté en la bóveda. Si no hay evidencia → decirlo.
- ❌ Resolver un conflicto sin registrarlo en `meta/contradictions.md`.
- ❌ Notas atómicas con > 1 claim.
- ❌ Duplicar atómicos: antes de crear uno, buscar por `topics` en el MOC correspondiente.
- ❌ Modificar archivos de `sources/` (inmutables; excepción: timestamps/locators insertados durante la ingesta inicial).
- ❌ Cerrar una operación (Ingest / Query / Lint) sin añadir entrada a `log.md`.

---

## 8. Comandos útiles (desde `$VAULT`)

```bash
# Actividad reciente (últimos 10 eventos)
grep "^## \[" log.md | tail -10

# Conteo de atómicos por tema (sanity check del índice)
grep -h "topics:" notes/*.md | sort | uniq -c | sort -rn

# Localizar un concepto sin conocer el archivo — EMPEZAR SIEMPRE AQUÍ
grep -r "orphan night" index.md MOC/ notes/ queries/

# Fuentes más recientes
ls -1 sources/ | sort -r | head -20

# Huérfanos candidatos (notas no citadas en index.md)
comm -23 <(ls notes/ | sort) <(grep -oE "notes/[^]]*" index.md | sort -u)
```

---

## 9. Checklist de auto-verificación (antes de responder)

- [ ] Abrí `index.md` primero.
- [ ] Consulté `queries/` antes de recorrer MOC + notes.
- [ ] Cito `[[nota]]` o `[[query]]` + locator preciso por cada afirmación.
- [ ] Apliqué el score de §5 si había conflicto.
- [ ] No leí ninguna fuente completa.
- [ ] Guardé la respuesta en `queries/` si aporta síntesis nueva.
- [ ] Añadí entrada a `log.md`.
- [ ] Si falta evidencia, lo digo explícitamente.

---

## 11. Troubleshooting

### Query excede ceiling

**Síntoma**: `budget-check.sh` reporta tokens > ceiling del regime.

**Solución**:
1. Revisar coverage self-check (§4.2 step 7) — ¿hay palancas sin cubrir?
2. Si hay gaps: declarar limitación **explícitamente** en respuesta.
3. Considerar descomposición en 2-3 sub-queries más focalizadas.
4. Si Regime C aún excede: problema es corpus insufficiente, necesita INGEST de más fuentes.

### Scripts fallan (yt-dlp, jq, python3)

**Síntoma**: `scripts/ingest-video.sh` falla con "command not found".

**Solución**:
```bash
# Verificar instalación
which yt-dlp jq python3

# Si falta alguno
brew install yt-dlp jq python3  # macOS
apt-get install yt-dlp jq python3  # Linux

# Verificar versiones
yt-dlp --version && jq --version && python3 --version
```

### index.md tiene links rotos

**Síntoma**: Obsidian muestra 404 en links de `index.md`.

**Solución**:
```bash
# Encontrar refs inválidas
grep -o '\[\[[^]]*\]\]' $VAULT_PATH/index.md | sort -u > /tmp/refs.txt

# Verificar cada target
while read ref; do
  target=$(echo "$ref" | sed 's/\[\[\(.*\)\]\]/\1/')
  [ ! -f "$VAULT_PATH/$target.md" ] && echo "BROKEN: $target"
done < /tmp/refs.txt
```

Limpiar entries rotas de `index.md` manualmente.

### Atom parece stale

**Síntoma**: `last_verified` en atom > 6 meses, pero hay nuevas fuentes sobre el tema.

**Solución**:
1. Identificar topic del atom
2. Rankear sources recientes: `scripts/rank-sources.py --top 5 | grep <topic>`
3. Ingestar fuentes nuevas (§4.1)
4. Extender atom con nuevas fuentes O crear atom nuevo si claim es distinto
5. Actualizar `last_verified` a hoy

### VAULT_PATH no definido

**Síntoma**: `$VAULT_PATH` vacío cuando ejecutas scripts.

**Solución**:
```bash
# Verificar config
cat scripts/config.sh

# Debe contener
export VAULT_PATH=/ruta/correcta

# Si no existe, crear (§0.7)
mkdir -p scripts
echo 'export VAULT_PATH=~/Dev/obsidian_vaults/optimize-my-airbnb-yt' > scripts/config.sh

# Cargar en sesión actual
source scripts/config.sh
echo $VAULT_PATH  # Debe mostrar ruta
```

---

# 10. Capa de dominio — Optimize My Airbnb (YouTube)

Todo lo siguiente es **específico de esta bóveda**. Para una bóveda nueva, reescribir solo esta sección.

## 10.1 Tipo de fuente

Transcripciones (auto-caption en inglés original) de vídeos del canal YouTube [@OptimizeMyAirbnb](https://www.youtube.com/@OptimizeMyAirbnb). Creador: Daniel Rusteen. Tema: alquiler de corta estancia / Airbnb.

Al 2026-04-22: **173 transcripciones** ingestadas (2017-11 → 2026-04), 5 vídeos en español excluidos (solo subs ES).

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

**Cuerpo**: bloques `[MM:SS]` cada ~20 s (emitidos por el script de ingesta). **No reformatear** salvo vía re-ingesta.

**Locator** para citas: timestamp `MM:SS` → link Obsidian `[[sources/YYYY-MM-DD--slug#t=MM:SS]]`.

## 10.3 Tópicos iniciales

Plantillas de MOC sugeridas (se irán creando bajo demanda durante la extracción de átomos):

- `MOC/pricing.md` — estrategias de precio, noches huérfanas, temporadas, minimum stay
- `MOC/occupancy.md` — tasas, gap nights, stay-length optimization
- `MOC/listing-optimization.md` — título, fotos, descripción, ranking en Airbnb
- `MOC/cleaning-ops.md` — equipos de limpieza, turnover, checklists
- `MOC/reviews.md` — flujo de mensajes, atributos, gestión de negativas
- `MOC/hospitality.md` — experience on-site + surprise & delight
- `MOC/ranking.md` — factores de búsqueda Airbnb
- `MOC/direct-booking.md` — cuándo sí + minimum viable moves
- `MOC/market-selection.md` — filtros negativos + perfil positivo
- `MOC/regulations.md` — normativas, licencias, impuestos
- `MOC/tools-tech.md` — PriceLabs, Beyond Pricing, Hostfully, software
- `MOC/investing.md` — selección de mercado, evaluación de deals, ROI

**Nota**: `MOC/guest-experience.md` se retiró en el lint 2026-04-22. Su contenido se absorbió en `reviews` (comunicación) + `hospitality` (experience on-site) + `listing-optimization` (amenities). Recrear solo si aparece un sub-tema que no encaje en los tres.

## 10.4 Pesos del score (§5)

```
score = 0.40·recency + 0.30·popularity + 0.20·specificity + 0.10·authority
```

- **Popularity**: usar `views` (log-normalizada contra max del corpus).
- **Authority default**: `high` para todo el canal (creador consolidado, 8+ años). Marcar `medium` o `low` manualmente en colabs con invitados.

## 10.5 Meta files del dominio

- `meta/videos.md` — tabla maestra auto-generada (ver `scripts/build-meta.sh`). No editar a mano.
- `meta/contradictions.md` — conflictos entre claims + score aplicado. Se mantiene manualmente.
- `meta/glossary.md` — jerga del creador (ej. "orphan night", "gap night", "KAT score"). Se amplía al detectar términos nuevos durante la ingesta.

## 10.6 Pipeline de ingesta

Scripts en el repo (fuera del vault):

```bash
# Ingestar 1 vídeo (requiere yt-dlp + jq + python3)
scripts/ingest-video.sh <video_id_or_url>

# Ingestar un listado (formato: video_id|title|duration por línea)
scripts/batch-ingest.sh <list_file>

# Regenerar tablas: meta/videos.md + log entry + sección "Fuentes" de index.md
scripts/build-meta.sh

# Rankear sources por §5 (recency + popularity). Imprime top-N sources
# ordenados por score para seleccionar el siguiente batch de atomización (§4.1.a).
scripts/rank-sources.py --top 10
```

Flujo interno del ingest: `yt-dlp` baja metadata JSON + VTT (auto-caption EN) → `scripts/clean_vtt.py` deduplica + agrupa en bloques de 20 s → se escribe `sources/YYYY-MM-DD--slug.md` con frontmatter de §10.2.

**Fallback para vídeos sin subs EN**: re-ejecutar con `--sub-lang es` manualmente (requeriría flag adicional en el script; no implementado).

## 10.7 Response Contract (este dominio)

Audiencia: host contratante. Tono: consultor, no profesor.

- Sin introducción ni contexto a menos que la pregunta lo pida.
- Estructura default: lista numerada de pasos accionables.
- Una cita [[atom]] inline por paso; nunca al final en bloque.
- Máx 600 palabras para queries tácticas; 1000 para estratégicas.
- Anglicismos permitidos: PriceLabs, Airbnb, WiFi, PMS, BLT (PMS Y BLT explicado 1 vez).
- Prohibidos: adjetivos de relleno ("clave", "importante", "fundamental"), "cabe destacar", summaries al final.
- Citar cada número concreto con su source_id entre paréntesis la primera vez.
