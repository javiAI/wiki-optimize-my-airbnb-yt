# OMAB Wiki — LLM Wiki for @OptimizeMyAirbnb

Schema + tooling para una bóveda Obsidian construida desde 173 transcripciones del canal [@OptimizeMyAirbnb](https://www.youtube.com/@OptimizeMyAirbnb). Sigue el patrón **LLM Wiki**: el LLM mantiene una wiki persistente que compone con cada fuente nueva y cada pregunta.

## Entry point

[CLAUDE.md](CLAUDE.md) es el contrato y el state. Contiene:

- **YAML frontmatter** (top): estado de optimizaciones (`current_phase`, `phase_status`, per-`OX` status + cost/quality deltas)
- **ROUTER**: lógica de ejecución autónoma — el agente lee el estado, ejecuta la siguiente tarea, testea, decide IMPLEMENT/ITERATE/REVERT
- **Kernel §0–§9**: reglas reutilizables del patrón LLM Wiki
- **Dominio §10**: específico de OMAB (tópicos, schema YAML, response contract)

## Quick Start

Setup primero (sección siguiente). Después, day-to-day:

```bash
# Ver estado actual
grep -E "current_phase|phase_status" CLAUDE.md | head -2

# Plan de la fase actual (N = current_phase)
cat docs/PHASE_<N>_TASKS.md

# Ejecutar test suite (ver docs/TEST_PROTOCOL.md)
python3 scripts/run-test-suite.py --prepare --label <LABEL>
# (Claude lanza 20 Agent calls en paralelo)
python3 scripts/run-test-suite.py --consolidate --label <LABEL>
python3 scripts/run-test-suite.py --compare --from <PREV> --to <LABEL>
```

## Setup (una vez)

```bash
# 1. Dependencias (macOS)
brew install yt-dlp jq              # python3 suele venir instalado

# 2. Configurar la bóveda (WikiForge v2)
#    Crea un bundle en vaults/{name}/ con vault.yml + agents.md
bash .claude/scripts/init-vault.sh

# 3. Resolver $VAULT_PATH automáticamente desde vaults/{name}/vault.yml
source .claude/scripts/config.sh    # exporta $VAULT_PATH y $VAULT_NAME
```

Legacy: `.claude/scripts/config.sh` puede leer `VAULT_PATH` de un env var directo si no quieres usar bundles.

---

## Operaciones

### 1. Ingestar una fuente nueva

**Un solo vídeo**:
```bash
.claude/scripts/ingest.sh <video_id_or_url>
scripts/build-meta.sh                    # OMA-specific: regenera meta/videos.md + log + index
```

**Batch desde un canal**:
```bash
yt-dlp --flat-playlist --print "%(id)s|%(title)s|%(duration)s" \
  "https://www.youtube.com/@<handle>/videos" > /tmp/videos.txt
.claude/scripts/batch-ingest.sh /tmp/videos.txt
scripts/build-meta.sh
```

**Re-ingesta forzada** (si mejoran los subtítulos o cambias el formato):
```bash
.claude/scripts/ingest.sh --force <video_id>
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

## Tests (en este repo, no en la bóveda)

Todo el infrastructure de testing vive en [tests/](tests/). **La bóveda es read-only para los agentes**; cualquier escritura va a `tests/` (enforced por `_ensure_under_tests` en `scripts/run-test-suite.py`).

```
tests/
├── questions.yaml         # 20 preguntas (immutable)
├── prompts/<LABEL>/       # Q1.md ... Q20.md generados por --prepare
├── raw-responses/         # <LABEL>-Q*.json + <LABEL>-tokens.json (manifest)
├── results/<LABEL>.json   # métricas consolidadas (avg/total cost, quality, latency)
└── comparisons/           # <TO>-vs-<FROM>.json + decisión IMPLEMENT/ITERATE/REVERT
```

Workflow detallado: [docs/TEST_PROTOCOL.md](docs/TEST_PROTOCOL.md). Diseño: [docs/ORCHESTRATOR.md](docs/ORCHESTRATOR.md), [docs/TEST_FRAMEWORK.md](docs/TEST_FRAMEWORK.md).

## Estructura del repo

```
wiki-optimize-my-airbnb-yt/
├── CLAUDE.md                  # ⭐ entry point: state + kernel + domain
├── llm-wiki.md                # patrón LLM Wiki — referencia
├── README.md                  # este archivo
├── .env.example
├── .gitignore
├── docs/
│   ├── MASTER_PLAN.md         # roadmap consolidado
│   ├── ORCHESTRATOR.md        # diseño full de orquestación
│   ├── TEST_PROTOCOL.md       # cómo ejecutar tests (4-step protocol)
│   ├── TEST_FRAMEWORK.md      # teoría del framework de tests
│   └── PHASE_{1..4}_{SUMMARY,TASKS}.md
├── .claude/                   # Plugin distribution unit (WikiForge framework)
│   ├── settings.json          # Hook wiring
│   ├── hooks/                 # PostToolUse / Stop / SessionStart shell scripts
│   ├── skills/                # /ingest /qa /audit /translate /query /init-vault
│   ├── scripts/               # Framework scripts (generic, vault-agnostic)
│   │   ├── config.sh          # Resolves $VAULT_PATH from VAULT_NAME or single bundle
│   │   ├── config.py          # Python equivalent — reads vaults/{name}/vault.yml
│   │   ├── init-vault.sh      # Wizard to bootstrap a new vault bundle
│   │   ├── ingest.sh          # 1 vídeo → $VAULT_PATH/raw/
│   │   ├── batch-ingest.sh    # Batch ingest (con log)
│   │   ├── clean_vtt.py       # VTT → markdown con bloques [MM:SS]
│   │   ├── deep_link.py       # locator → YouTube ?t= URL
│   │   ├── atom-qa.py         # Atom QA gate (completeness, urls, anglicisms, acronyms)
│   │   ├── qa_lexicon.py      # Externalized anglicism/acronym tables
│   │   ├── auto-link.py       # Insert [[wiki/{lang}/atom]] in MOCs
│   │   ├── vault-agent.py     # Vault health audit (orphans, stale, gaps)
│   │   └── retrieve.py        # BM25 retrieval (token-free atom shortlist)
│   └── templates/             # vault.yml.template, agents.md.template
├── scripts/                   # OMA-specific (not part of the plugin)
│   ├── build-meta.sh          # Regenera meta/videos.md + log + index
│   ├── extract-meta.py        # Frontmatter → fila de tabla
│   ├── rank-sources.py        # Score §10.4 → top-N sources
│   ├── apply-proposed-contradictions.py
│   ├── run-test-suite.py      # 20-agent test orquestador
│   └── archive/               # Obsolete scripts kept for reference
├── vaults/                    # Per-vault bundles
│   └── {name}/                # vault.yml + agents.md + state/
└── tests/                     # ver sección Tests arriba
```

---

## Mantenimiento y ampliación

### Añadir vídeos del mismo canal con el tiempo

Cuando el canal publique un vídeo nuevo:
```bash
.claude/scripts/ingest.sh <nuevo_video_id>
scripts/build-meta.sh
```

### Recuperar vídeos en español (5 no ingestados)

Pendiente: añadir flag `--sub-lang es` a `ingest.sh`. Los 5 vídeos sin subs EN son interviews/contenido en español. Si los quieres, editar el script para aceptar lang como parámetro.

### Reemplazar transcripciones (mejor calidad)

Si el creador activa subs manuales o mejora los auto-captions:
```bash
.claude/scripts/ingest.sh --force <video_id>
```
Revisar después si los timestamps citados en `notes/` siguen siendo válidos (pueden haberse desplazado).

### Crear una segunda bóveda (otro dominio)

1. `mkdir ~/Dev/obsidian_vaults/<nuevo>` con el mismo layout (`sources/ MOC/ notes/ queries/ meta/ index.md log.md`).
2. Clonar este repo como plantilla (o crear uno nuevo).
3. **Copiar §0-9 de `CLAUDE.md` tal cual** (kernel reutilizable).
4. **Reescribir §10** con el dominio nuevo: tipo de fuente, schema YAML, tópicos iniciales, pesos del score, pipeline de ingesta.
5. Ejecutar `bash .claude/scripts/init-vault.sh` para crear el bundle nuevo en `vaults/{nuevo}/`.

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

Single source of truth: YAML frontmatter en [CLAUDE.md](CLAUDE.md). Lo que sigue es un resumen humano (puede quedar stale — verificar contra CLAUDE.md):

- **173 transcripciones** en `sources/` (2017-11 → 2026-04). 5 vídeos en español excluidos.
- **156 atoms** en `notes/`, **12 MOCs** (per CLAUDE.md `vault.atoms` / `vault.mocs`).
- **Quality score**: 8.52 / 9.8 target.
- **Optimizaciones completadas**: O1 (Hierarchical Indices, −25.3% cost), O3 (Language Consistency, −3.4%). O2 skipped (premise stale).
- **Fase actual**: Phase 2 / pending_approval.

## Referencias

- [CLAUDE.md](CLAUDE.md) — contrato + state. Léelo primero si vas a abrir una sesión de Claude Code.
- [llm-wiki.md](llm-wiki.md) — patrón de referencia (LLM Wiki). Conservado para onboarding de bóvedas futuras.
- [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) — roadmap consolidado (12 optimizaciones, 4 fases).
- [docs/TEST_PROTOCOL.md](docs/TEST_PROTOCOL.md) — protocolo operacional para correr el test suite.
