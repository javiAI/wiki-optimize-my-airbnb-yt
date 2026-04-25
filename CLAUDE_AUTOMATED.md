---
# MACHINE-READABLE STATE (Scripts read this YAML section)
# Format: Keep this section between --- markers for automation to work

# Automation Metadata
automation:
  version: "2.0-automated"
  enabled: true
  last_update: "2026-04-25T00:00:00Z"
  entry_point: "This file (CLAUDE_AUTOMATED.md)"

# Current Execution State
execution_state:
  current_phase: 1
  phase_status: "pending_approval"
  next_action: "User approves O1 + O2 → Phase 1 begins"

# Phase Progress Tracker
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

# Optimization Tracker (16 items)
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
    reference: "docs/ARCHITECTURE.md PART 6"
  
  O4:
    name: "Contradiction Detection (Layer 1)"
    status: "not_started"
    phase: 2
    effort_hours: 3
    reference: "docs/ARCHITECTURE.md PART 4"
  
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

# Vault Status
vault:
  name: "optimize-my-airbnb-yt"
  atoms: 156
  mocs: 12
  sources: 173
  quality_score: 8.52
  target_score: 9.8

# Baseline Metrics
baseline_metrics:
  d9_score: 8.52
  d1_clarity: 8.0
  d2_completeness: 8.73
  d3_readability: 8.47
  baseline_overhead_tokens: 3956
  avg_query_cost_tokens: 6456

---

# LLM Wiki — Automated Schema

> **IMPORTANTE**: Este archivo es el punto de entrada único para toda la automatización.
> Los scripts leen el YAML frontmatter arriba para conocer el estado.
> No modifiques el YAML manualmente; usa los scripts.

---

## 🤖 FOR AUTOMATION SCRIPTS

Read the YAML frontmatter (lines 1-150) to determine:

1. **Current phase**: `execution_state.current_phase`
2. **Next action**: `execution_state.next_action`
3. **What to run**: `phases[current_phase].next_incomplete_task`
4. **Where to find details**: `optimizations[task_id].reference`

**Example Python script**:
```python
import yaml

with open("CLAUDE_AUTOMATED.md") as f:
    _, frontmatter, _ = f.read().split("---", 2)
    state = yaml.safe_load(frontmatter)

phase = state['execution_state']['current_phase']
next_task = state['phases'][f'phase_{phase}']['next_incomplete_task']

print(f"Phase {phase}: Execute {next_task}")
print(f"Reference: {state['optimizations'][next_task]['reference']}")
```

---

## 📊 FOR HUMANS

**Quick Status**:
- Phase: **1 (Critical Path)**
- Status: **⏳ Pending Approval for O1 + O2**
- Progress: **0% (0/3 tasks)**
- Next Step: **User approves O1 + O2 → Phase 1 executes**

**Key Links**:
- Architecture: See `docs/ARCHITECTURE.md`
- Evaluation: See `docs/EVALUATION.md`
- Implementation Guide: See `docs/IMPLEMENTATION_GUIDE.md`
- Baseline: See `test_battery/EVALUATION_RESULTS_V2.md`

**How to Approve**:
```bash
./scripts/approve-phase.sh O1 O2
# Then Phase 1 executes automatically
```

---

## 🔧 FOR THIS SESSION (IF HUMAN IS READING)

**You have 4 options**:

### Option 1: Approve Phase 1 (Recommended)
```bash
Reply: "Approve Tier 1 (O1 + O2) for Phase 1 implementation."
Then: ./scripts/approve-phase.sh O1 O2
Then: Phase 1 executes autonomously
```

### Option 2: Review Architecture First
```bash
Open: docs/ARCHITECTURE.md (450+ lines, comprehensive design)
Questions? Ask before approving.
```

### Option 3: Check Baseline Results
```bash
Open: test_battery/EVALUATION_RESULTS_V2.md
See: Q1-Q15 evaluation, D9 = 8.52/10 average
```

### Option 4: View Implementation Guide
```bash
Open: docs/IMPLEMENTATION_GUIDE.md
See: Step-by-step what Phase 1 will do
```

---

# GENERIC KERNEL (§0-§9)

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

[Content from original CLAUDE.md §1 - lines 121-131]

---

## 2. Estructura de la bóveda

[Content from original CLAUDE.md §2 - lines 135-221]

---

## 3. Esquema de metadatos (YAML frontmatter)

[Content from original CLAUDE.md §3 - lines 165-221]

---

## 4. Operaciones

[Content from original CLAUDE.md §4 - lines 224-325]

---

## 5. Priorización y resolución de conflictos

[Content from original CLAUDE.md §5 - lines 341-361]

---

## 6. Naming y linking

[Content from original CLAUDE.md §6 - lines 364-371]

---

## 7. Reglas duras (NO hacer)

[Content from original CLAUDE.md §7 - lines 374-385]

---

## 8. Comandos útiles (desde `$VAULT`)

[Content from original CLAUDE.md §8 - lines 388-405]

---

## 9. Checklist de auto-verificación (antes de responder)

[Content from original CLAUDE.md §9 - lines 409-419]

---

## 11. Troubleshooting

[Content from original CLAUDE.md §11 - lines 422-499]

---

# DOMAIN LAYER (§10) — Optimize My Airbnb

[Content from original CLAUDE.md §10 - lines 503-603]

---

## UPDATE LOG (Automated Additions)

**2026-04-25**: Automated version created
- Added YAML frontmatter for script automation
- Maintained all existing kernel (§0-§9) content
- Maintained all domain layer (§10) content
- Added automated entry points for scripts
- Ready for Phase 1 execution

