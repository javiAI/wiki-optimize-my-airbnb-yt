# OMAB Wiki — Repo

Schema + tooling para una bóveda Obsidian construida desde transcripciones del canal [@OptimizeMyAirbnb](https://www.youtube.com/@OptimizeMyAirbnb). Sigue el patrón **LLM Wiki** (ver [`llm-wiki.md`](llm-wiki.md)): el LLM mantiene una wiki persistente que compone con cada fuente nueva y cada pregunta.

## Qué contiene este repo (y qué no)

| Sí | No |
|---|---|
| `CLAUDE.md` — schema/contrato con Claude Code | La bóveda (vive externa, en `VAULT_PATH`) |
| `llm-wiki.md` — doc del patrón, de referencia | Fuentes raw (en `$VAULT/sources/`) |
| `scripts/` — pipeline de ingesta y mantenimiento | Notas atómicas, MOC, queries (en `$VAULT/`) |

La bóveda **no se versiona aquí**. Obsidian la abre en su ruta propia.

## Setup (una vez)

```bash
# 1. Dependencias (macOS)
brew install yt-dlp jq              # python3 suele venir instalado

# 2. Configurar ruta de la bóveda
cp scripts/config.sh.example scripts/config.sh
$EDITOR scripts/config.sh           # ajustar VAULT_PATH

# 3. Crear esqueleto de la bóveda si no existe
source scripts/config.sh
mkdir -p "$VAULT_PATH"/{sources,MOC,notes,queries,meta}
```

`scripts/config.sh` está en `.gitignore` → cada máquina apunta a su bóveda.

---

## Operaciones

### 1. Ingestar una fuente nueva

**Un solo vídeo**:
```bash
scripts/ingest-video.sh <video_id_or_url>
scripts/build-meta.sh                    # regenera meta/videos.md + log + index
```

**Batch desde un canal**:
```bash
yt-dlp --flat-playlist --print "%(id)s|%(title)s|%(duration)s" \
  "https://www.youtube.com/@<handle>/videos" > /tmp/videos.txt
scripts/batch-ingest.sh /tmp/videos.txt
scripts/build-meta.sh
```

**Re-ingesta forzada** (si mejoran los subtítulos o cambias el formato):
```bash
scripts/ingest-video.sh --force <video_id>
```

### 2. Extraer átomos (guiada por Claude)

La extracción de claims **no está automatizada** — la pilota Claude leyendo el source y proponiendo notas. Desde una sesión de Claude Code abierta en este repo:

> *"Extract atomic claims from `sources/2026-04-15--should-you-invest-in-an-airbnb-in-2026.md`"*

Claude sigue §4.1 de `CLAUDE.md`: lee el source, crea `notes/<topic>--<slug>.md` (1 claim cada una), actualiza o crea `MOC/<topic>.md`, añade cross-refs en `index.md`, registra en `log.md`. Fusiona duplicados y detecta contradicciones con atómicos existentes.

Para fuentes > 400 líneas, se chunkea con `offset`/`limit`.

### 3. Hacer una query

Desde Claude Code:

> *"¿Cuál es la mejor estrategia de precio para una noche huérfana en miércoles de temporada alta?"*

Claude ejecuta §4.2: `index.md` → `queries/` (cache) → MOC → notes → fragmentos de source. Responde con citas `[[sources/...#t=MM:SS]]`. Si la síntesis es nueva, la guarda en `queries/` para abaratar consultas futuras.

### 4. Lint — salud de la bóveda

> *"Run a lint pass on the vault"*

Claude revisa contradicciones sin anotar, stale claims, páginas huérfanas, cross-refs faltantes, gaps temáticos, drift de `index.md`. Reporta y propone fixes; al aplicar, entrada en `log.md`.

---

## Estructura del repo

```
wiki-optimize-my-airbnb-yt/
├── CLAUDE.md                  # schema / contrato (kernel §0-9 + dominio §10)
├── llm-wiki.md                # patrón LLM Wiki — referencia
├── README.md                  # este archivo
├── .gitignore
└── scripts/
    ├── config.sh.example      # plantilla
    ├── config.sh              # local, gitignored
    ├── ingest-video.sh        # 1 vídeo → sources/
    ├── batch-ingest.sh        # lista → sources/ (con log)
    ├── build-meta.sh          # regenera meta/videos.md + log + index
    ├── clean_vtt.py           # VTT → markdown con bloques [MM:SS]
    └── extract-meta.py        # frontmatter → fila de tabla
```

---

## Mantenimiento y ampliación

### Añadir vídeos del mismo canal con el tiempo

Cuando el canal publique un vídeo nuevo:
```bash
scripts/ingest-video.sh <nuevo_video_id>
scripts/build-meta.sh
```

### Recuperar vídeos en español (5 no ingestados)

Pendiente: añadir flag `--sub-lang es` a `ingest-video.sh`. Los 5 vídeos sin subs EN son interviews/contenido en español. Si los quieres, editar el script para aceptar lang como parámetro.

### Reemplazar transcripciones (mejor calidad)

Si el creador activa subs manuales o mejora los auto-captions:
```bash
scripts/ingest-video.sh --force <video_id>
```
Revisar después si los timestamps citados en `notes/` siguen siendo válidos (pueden haberse desplazado).

### Crear una segunda bóveda (otro dominio)

1. `mkdir ~/Dev/obsidian_vaults/<nuevo>` con el mismo layout (`sources/ MOC/ notes/ queries/ meta/ index.md log.md`).
2. Clonar este repo como plantilla (o crear uno nuevo).
3. **Copiar §0-9 de `CLAUDE.md` tal cual** (kernel reutilizable).
4. **Reescribir §10** con el dominio nuevo: tipo de fuente, schema YAML, tópicos iniciales, pesos del score, pipeline de ingesta.
5. Ajustar `config.sh` con el `VAULT_PATH` del nuevo vault.

Si las fuentes son de otro tipo (papers, artículos, libros), el pipeline de ingesta cambia — pero la estructura L1/L2/L3 y las operaciones Ingest/Query/Lint se mantienen.

### Salud continua

```bash
cd "$VAULT_PATH"

# Actividad reciente
grep "^## \[" log.md | tail -10

# Conteo de átomos por tema
grep -h "topics:" notes/*.md | sort | uniq -c | sort -rn

# Huérfanos candidatos
comm -23 <(ls notes/ | sort) <(grep -oE "notes/[^]]*" index.md | sort -u)
```

---

## Estado actual (snapshot)

- **173 transcripciones** en `sources/` (2017-11 → 2026-04). 5 vídeos en español excluidos.
- **MOC, notes, queries**: vacíos. Pendiente de primera extracción de átomos (§4.1 paso 2).
- Última ingesta: 2026-04-22.

## Referencias

- [`CLAUDE.md`](CLAUDE.md) — contrato con el LLM. Léelo primero si vas a abrir una sesión de Claude Code sobre la bóveda.
- [`llm-wiki.md`](llm-wiki.md) — patrón de referencia (LLM Wiki). Conservado para onboarding de bóvedas futuras.
