# Master Optimizations List — 32 Items (Consolidados)

**Objetivo**: Lista única, priorizada, justificada  
**Origen**: 20 items del desarrollo (batches 1-13) + 12 items de esta conversación (2026-04-25)  
**Total**:  32 optimizaciones únicas (duplicados fusionados)  
**Formato**: Prioridad 1-10 (10 = máxima urgencia/impacto)

---

## OPTIMIZACIONES ORDENADAS POR PRIORIDAD (Score 1-10)

---

### 🔴 PRIORIDAD 10/10 (BLOQUEANTE INMEDIATO)

---

#### **#1 — Compactar index.md a ≤150 líneas (BLOQUEANTE)**
**Score: 10/10 — BLOQUEANTE**

**Descripción**: index.md actualmente 344 líneas (~3956 tokens). Consume 99% del ceiling original Régimen A (4k). Ceilings ampliados provisionalmente a 8k/10k/13k post-redesign §4.2. Una vez compactado, revertir ceilings a valores diseñados 4k/6k/8.5k.

**Solución propuesta**:
- Factorizar a sub-MOCs por topic principal (pricing, listing-optimization, ranking)
- O mover detalle a `meta/queries-index.md`
- Target: ≤150 líneas ≈ 1.7k tokens

**Impacto**:
- **Tokens**: Recupera ~2.3k tokens por query (todos los regímenes) — esto es CRÍTICO
- **Baseline**: Hoy cuesta +4k tokens en baseline cada sesión
- **ROI**: Altísimo — toda query lo beneficia

**Por qué 10/10**:
- Bloquea escalabilidad de todo el sistema
- Identificado como critical path en redesign 2026-04-24
- Solución es simple (refactorización mecánica)
- El coste de NO hacerlo es +4k tokens/sesión infinitamente

**Dependencias**: Ninguna

**Esfuerzo**: 3-4 horas

---

#### **#2 — Resolver contradicción Q4 (2-3 veces/año vs 2-3 meses)**
**Score: 10/10 — INTEGRITY CRITICAL**

**Descripción**: Q4 dice "actualiza 2-3 veces al año" (4-6 meses) pero línea siguiente dice "cada 2-3 meses". Contradicción directa.

**Solución**:
```
CORRECCIÓN:
"Actualiza cada 2-3 meses (antes de temporada relevante para tu mercado)"

POR QUÉ:
"Airbnb detecta 'stale listings' después de ~12 semanas sin cambios"
```

**Impacto**:
- **Credibilidad**: Host pierde confianza si hay contradicciones
- **Accionabilidad**: No sabe si aplicar 4-6 meses o 2-3 meses
- **D9 score**: Sube de 7.9 → 8.4+ al resolver

**Por qué 10/10**:
- Es contradicción explícita, no matiz
- Afecta decisión operacional concreta
- Fácil de fijar (20 minutos)
- Sin resolver = respuesta defectuosa formalmente

**Esfuerzo**: 20 minutos

---

---

### 🟠 PRIORIDAD 9/10 (CRÍTICO ESTA SEMANA)

---

#### **#3 — Traducir anglicismos (moat→ventaja, pool→grupo, etc.)**
**Score: 9/10 — D1 SPANISH COMPLETENESS**

**Descripción**: 12 anglicismos sin explicar en 15 respuestas. Ejemplos:
- "pool de guests" → "grupo de posibles guests"
- "moat" → "ventaja defensible" o "diferenciador"
- "random" → "sin patrón" o "aleatorio"
- "loophole" → "brecha en política"
- "wacky" → "únicas" o "extraordinarias"

**Impacto**:
- **D1 Spanish**: 9.0 → 9.5 (100% español impecable)
- **Legibilidad**: Host no traduce mentalmente anglicismos
- **Profesionalismo**: Respuestas suenan más locales

**Por qué 9/10**:
- Afecta todas las 15 respuestas
- Mejora D1 directamente (estándar máximo)
- Fácil implementar (1 hora)
- Válido para futuras respuestas (pattern)

**Excepción permitida**: PriceLabs, Airbnb, Wi-Fi, YouTube (muy conocidos, se explican una vez)

**Esfuerzo**: 1 hora

---

#### **#4 — Protocolo "Acción + Timing + Trigger" para D8 (Claridad)**
**Score: 9/10 — INSTRUCTION CLARITY**

**Descripción**: Muchas instrucciones usan verbos vagos ("audita", "revisa", "mejora") sin HOW exacto. Solución: template estructurado.

**Template**:
```markdown
### [Título de acción]

**Acción exacta**: [Qué hacer, verbo concreto]

**Cuándo ejecutar**: [Fecha exacta, trigger específico]
- ¿Si no sucede en X días?: escalera decisión

**Cómo hacer**: 
- [ ] Paso 1 (con herramienta específica)
- [ ] Paso 2
- [ ] Paso 3

**Trigger de detección**: [Métrica o evento que dispara esta acción]

**Si X no ocurre, hacer Y**: [Escalera de decisión si falla]
```

**Ejemplos**:
- Q9: "18h post-checkin" → especificar horario exacto (9am), qué enviar, cómo verificar
- Q6: "bajar min-stay" → paso a paso en PriceLabs, verificar en búsqueda

**Impacto**:
- **D8 Clarity**: 8.0 → 9.2
- **Host confidence**: Sabe exactamente qué hacer, no interpreta vagamente
- **Execution rate**: Mejora si instrucciones son crystal-clear

**Por qué 9/10**:
- Afecta todas las respuestas Régimen B+C
- ROI muy alto: mismo contenido, mejor presentación
- Pattern aplicable a futuras respuestas

**Esfuerzo**: 2 horas (template + aplicar a Q6, Q7, Q8, Q9)

---

#### **#5 — Citas explícitas para números (Q2, Q5)**
**Score: 9/10 — D2 RELEVANCE/CREDIBILITY**

**Descripción**: Q2 dice "35 fotos mínimo" sin citar fuente. Q5 dice "20-30% premium" sin derivación. Números críticos sin respaldo.

**Solución**:
```
ANTES:
"Para un listing de 2 dormitorios, el mínimo obligatorio es 35 fotos."

DESPUÉS:
"Para un listing de 2 dormitorios, el mínimo obligatorio es 35 fotos 
[[notes/listing-optimization--photo-count-by-bedroom-size | 
creador: medición 300+ listings, promedio conversión @ 35 fotos]]."
```

**Impacto**:
- **Credibilidad**: Host ve la fuente, confía más
- **D2 score**: 7.55 (Q2) → 8.5+
- **Reproducibilidad**: Puedo defender cada cifra

**Por qué 9/10**:
- Números son promesas específicas
- Sin cite = sospechas de fabricación
- Host puede verificar fuente independientemente
- Pattern para futuras respuestas

**Esfuerzo**: 1.5 horas

---

#### **#6 — Tabla "Por qué esta palanca" en Régimen B**
**Score: 9/10 — D2 COMPLETENESS**

**Descripción**: Régimen B (Q6-Q9) presenta 3-6 palancas pero no explica por qué esas y no otras. Host entiende qué, pero no por qué.

**Solución**:
```markdown
| Palanca | Impacto | Complejidad | Justificación |
|---------|---------|-----------|---------------|
| Pricing | 40% | Alta | Rating constante, occupancy varía → precio es lever principal |
| Min stay | 20% | Baja | Filtro búsqueda; diferencia 1 vs 3 noches = abismo en pool |
| Messages | 30% | Media | Reciprocidad: doubles completion rate 70%→90% |
```

**Impacto**:
- **D2 completeness**: Cubre "por qué" no solo "qué"
- **Host understanding**: Sabe priorizar si no puede hacer todo
- **Confianza**: Palancas están jerarquizadas, no random

**Por qué 9/10**:
- Régimen B es táctico; hosts quieren entender trade-offs
- Tabla es mecánica (solo ~30 minutos por respuesta)
- Mejora D2 directamente

**Esfuerzo**: 1.5 horas (4 respuestas × 20 min)

---

---

### 🟡 PRIORIDAD 8/10 (ESTA SEMANA — WEEK 2)

---

#### **#7 — Estructura BLUF (Bottom-Line-Up-Front)**
**Score: 8/10 — D3 READABILITY**

**Descripción**: Respuestas empiezan con contexto, no conclusión. Host debe leer 3 párrafos para saber "qué hago". Solución: BLUF = respuesta corta primero.

**Cambio**:
```markdown
ANTES:
"La estrategia de noche huérfana en temporada alta es contra-intuitiva..."
[3 párrafos de explicación]

DESPUÉS:
**RESPUESTA RÁPIDA**: Sube precio +20-30%, no lo bajes.

**Por qué funciona**: 
- Guest que reserva 1 noche a premium es quien quieres...
[explicación expandida]
```

**Impacto**:
- **D3 Readability**: 8.3 → 9.0+
- **Usabilidad**: Host entiende conclusión en primeras 10 segundos
- **Estructura**: Permite scanning vs lectura lineal

**Por qué 8/10**:
- Afecta experiencia de lectura
- No cambia contenido, solo orden
- Mejora D3 significantly
- Pattern para todas respuestas futuras

**Esfuerzo**: 2 horas (aplicar patrón a 15 respuestas)

---

#### **#8 — Sistema "Recency Override" (Prevalencia notas recientes)**
**Score: 8/10 — ARCHITECTURAL**

**Descripción**: Cuando 2 atoms dicen cosas distintas, ¿cuál usar? Hoy aplicamos score §5. Propuesta: si atom B supersede a A, SIEMPRE usar B (aunque A tenga mejor score).

**Implementación**:

En CLAUDE.md §3.2 (Nota atómica), añadir:
```yaml
conflicts_with: 
  - atom_id: "notes/pricing--minimum-stay-3-nights"
    status: "superseded"  # ← NUEVO
    reason: "Airbnb 2026 cambió algoritmo"
    since: 2026-03-15
```

Script helper:
```bash
#!/bin/bash
grep -r "status: superseded" notes/ | while read line; do
  atom=$(echo "$line" | cut -d: -f1)
  echo "⚠️ ALERTA: $atom está reemplazado"
done
```

**Impacto**:
- **Consistency**: Respuestas siempre usan info más reciente
- **Maintenance**: Automatiza decisión de conflicto
- **Clarity**: Documento explícito de "esto era viejo"

**Por qué 8/10**:
- Asegura no citamos info obsoleta
- Escalable (funciona con corpus que crece)
- Previene bugs de información stale
- Importante pero no urgente (hoy hay pocos conflictos)

**Esfuerzo**: 2-3 horas

---

#### **#9 — Añadir casos reales + hipotéticos (Q1, Q4)**
**Score: 8/10 — D2 RELEVANCE**

**Descripción**: Q1 dice "cada +0.1 rating = +5% revenue" (abstracto). Mejor: "Host en Portland: $2,400/mes @ 4.7 → $2,520/mes @ 4.8 (+$120/mes)".

**Patrón**:
```markdown
**Fórmula**: Rating +0.1 = +5% revenue

**Caso real**: Host SFO, $2,000/mes base, 4.7 rating
→ Mejora a 4.8 = +5% = +$100/mes = $1,200/año

**En tu mercado**: [aproximación para mercado típico]
```

**Impacto**:
- **D2 relevance**: De abstracto a concreto
- **Host motivation**: Ve número en $$$ no puntos
- **Believability**: Caso específico > fórmula general

**Por qué 8/10**:
- Mejora D2 pero no es crítico (ya entienden)
- Requiere investigación (buscar sources específicos)
- Pattern para Q-series estratégicas

**Esfuerzo**: 2 horas (buscar casos, adaptar a 3-4 respuestas)

---

#### **#10 — Checklists ejecutables (no conceptuales)**
**Score: 8/10 — D8 CLARITY**

**Descripción**: "Bajá el minimum stay a 1 noche" vs paso a paso en PriceLabs. Segundo es ejecutable.

**Patrón**:
```markdown
- [ ] Abrir PriceLabs Dashboard
- [ ] Seleccionar fecha específica (ej: 5 mayo)
- [ ] Click en "Date-specific"
- [ ] Cambiar minimum nights: 1
- [ ] Confirmar; aparecerá en búsqueda en 2h
- [ ] Verificar: search booking.com, busca tu listing
```

**Impacto**:
- **D8 Clarity**: Pase del verbo vago al paso concreto
- **Execution**: Host no adivina interface
- **Confidence**: Sabe cuándo está "correcto"

**Por qué 8/10**:
- Mejora D8 significantly
- Fácil implementar (solo detallar)
- Aplicable a todas respuestas operacionales (Q6, Q8, etc.)

**Esfuerzo**: 1.5 horas

---

#### **#11 — Split CLAUDE.md lógico (Tabla rápida §4.1 vs §4.2)**
**Score: 8/10 — ARCHITECTURE / TOKEN EFFICIENCY**

**Descripción**: CLAUDE.md mezcla instrucciones INGEST (§4.1) con QUERY (§4.2). Agent que hace query carga §4.1 innecesariamente. Solución: tabla rápida al inicio.

**Implementación** (sin separar archivos):
```markdown
# CLAUDE.md

## Índice Rápido
- ✅ **Haciendo QUERY?** → Salta a §4.2 (line 255)
- ✅ **Haciendo INGEST?** → Salta a §4.1 (line 228)
- ✅ **Primera vez?** → Lee §0-3 (line 58)

---

## §0-3: Kernel (SIEMPRE LEE)
[~180 líneas — filosofía, estructura]

## §4.1: INGEST (Solo si añades fuentes)
[Instrucciones de ingesta]

## §4.2: QUERY (Para responder preguntas)
[Instrucciones de queries]
```

**Impacto**:
- **Tokens**: Agent QUERY salt §4.1 → lee ~1.8k tokens en lugar de 3.5k
- **Efficiency**: Todas las queries se benefician (recupera ~1.7k tokens)
- **Navigation**: Agent sabe dónde saltar

**Por qué 8/10**:
- Bajo esfuerzo, alto ROI (recupera 1.7k tokens/query)
- No es crítico (ambos ya están ahí) pero mejora UX
- Patrón simple replicable

**Esfuerzo**: 2.5 horas

---

---

### 🟢 PRIORIDAD 7/10 (PRÓXIMAS SEMANAS)

---

#### **#12 — Links interactivos ([[notes/...]] → clickeable)**
**Score: 7/10 — UX IMPROVEMENT**

**Descripción**: Hoy [[notes/slug]] no es clickeable en web Claude Code. User ve texto feo. Solución: referencias numeradas con obsidian:// URIs.

**Opción recomendada (B)**:
```markdown
El rating mínimo es 4.8¹

[1]: obsidian://open?vault=optimize-my-airbnb-yt&file=notes/reviews--four-point-eight-threshold
```

O para Régimen C, tabla centralizada:

```markdown
## Referencias

| Nota | Enlace |
|------|--------|
| Threshold 4.8 | [obsidian://...] |
| Rating → Revenue | [obsidian://...] |
```

**Impacto**:
- **UX**: Links clickeables vs texto plano
- **Navigation**: User salta directamente a Obsidian
- **Traceability**: Fácil auditar fuentes

**Por qué 7/10**:
- Mejora UX pero no contenido
- Requiere cambio en protocolo de respuesta
- Herramientas existen (obsidian:// scheme)
- Implementación mecánica (buscar-reemplazar)

**Esfuerzo**: 3 horas

---

#### **#13 — YouTube timestamps (Enlazar respuestas con video)**
**Score: 7/10 — CONTEXT / UNDERSTANDING**

**Descripción**: Atoms citan `sources/YYYY-MM-DD--slug#t=MM:SS` pero user no puede ir directo al video. Solución: incluir YouTube link con timestamp exacto.

**Implementación**:

1. Registrar en atoms:
```yaml
sources:
  - source_id: ltV-Qid46n8
    locator: "t=03:45-04:12"
    youtube_url: "https://youtu.be/ltV-Qid46n8?t=225"  # ← NUEVO
```

2. En respuesta:
```markdown
Aplicá un premium de 20-30%¹

[1]: 📹 [Ver en YouTube (3:45-4:12)](https://youtu.be/ltV-Qid46n8?t=225) — 
     [Leer nota](obsidian://...)
```

3. Script helper:
```bash
scripts/extract-youtube-ids.sh  # Genera URLs con timestamps
```

**Impacto**:
- **Understanding**: Host ve/escucha el concepto en VOZ del creador
- **Context**: Tone, énfasis, ejemplos en vivo
- **Validation**: "Ah, por eso lo dijo de esa manera"

**Por qué 7/10**:
- Mejora profundamente pero bajo frecuencia (no cada query)
- Requiere cambio de protocol + script
- Más valuoso para Régimen C (exhaustivo)
- Opcional para A (respuestas rápidas)

**Esfuerzo**: 4 horas

---

#### **#14 — Pre-generar 10-15 queries cacheadas (Hot path)**
**Score: 7/10 — QUERY PERFORMANCE**

**Descripción**: Las preguntas más frecuentes se cachean. Siguientes queries sobre "estrategia temporada alta", "recuperar review negativa", etc. cuestan ~0 tokens.

**Candidatos a pre-generar**:
```
- pricing--estrategia-temporada-alta-vs-baja
- reviews--como-recuperar-de-review-negativa
- hospitality--flujo-de-mensajes-completo
- investing--como-evaluar-un-deal-completo
- ranking--cuales-son-los-factores-confirmados
- listing-optimization--orden-prioridad-upgrades
- cleaning-ops--como-estructurar-equipo-limpieza
- market-selection--criterios-eliminacion-rapida
- direct-booking--cuando-saltar-de-airbnb
- tools-tech--stack-minimo-recomendado
```

**Impacto**:
- **Performance**: Queries cacheadas cuestan ~0 tokens en recompile
- **User speed**: Respuesta instantánea
- **Repetition**: Si 30% de queries son hot-path, compounding es alto

**Por qué 7/10**:
- Alto ROI (recupera ~5k tokens/query hit)
- Pero esfuerzo es alto (genera 10-15 respuestas quality)
- Beneficio acumulativo (primeras queries caras, siguientes gratis)

**Esfuerzo**: 10 horas

---

#### **#15 — Script dedup-query.py (Prevenir duplicados)**
**Score: 7/10 — MAINTENANCE**

**Descripción**: Bug detectado 2026-04-23: queries `amenities-roi` vs `amenities-mayor-valor-menor-coste` son duplicadas. Script fuzzy-match previene.

**Implementación**:
```python
#!/usr/bin/env python3
# Check si nueva query es semánticamente similar a existentes
import os
from difflib import SequenceMatcher

queries_dir = "$VAULT_PATH/queries"
new_query_title = sys.argv[1]

for existing in os.listdir(queries_dir):
    similarity = SequenceMatcher(None, new_query_title, existing).ratio()
    if similarity > 0.75:
        print(f"⚠️ SIMILAR: {existing} ({similarity*100:.0f}%)")
        print("   ¿Es duplicado? Si sí, fusionar o referencing.")
```

**Impacto**:
- **Maintenance**: Previene acumulación de duplicados
- **Search**: index.md no crece innecesariamente
- **Clarity**: 1 pregunta = 1 query (no N queries confusas)

**Por qué 7/10**:
- Bajo impacto en usuario final (es internal)
- Pero importante para corpus health
- Mecánica simple (1 script one-shot)

**Esfuerzo**: 1.5 horas

---

---

### 🔵 PRIORIDAD 6/10 (BATCH 10+)

---

#### **#16 — Dual-representation claim + client_line en atoms**
**Score: 6/10 — RESPONSE COMPRESSION**

**Descripción**: Atoms hoy tienen `claim:` (técnico, interno). Propuesta: añadir `client_line:` (una frase lista para copiar en respuesta, tono consultor).

**Ejemplo**:
```yaml
claim: "No uses más de 5 customizations activas en PriceLabs; interactúan no-obvio"
client_line: "Máximo 5 personalizaciones activas en PriceLabs; más se interfieren"
```

**Uso en §4.2**: Step 5 consume `client_line` por defecto; solo baja a `claim` si profundidad pedida.

**Impacto**:
- **Tokens output**: ~20% reducción adicional (post Response Contract)
- **Speed**: Respuestas generadas más rápido (copiar client_line vs parafrasear)
- **Consistency**: Same wording across queries

**Por qué 6/10**:
- Alto ROI (20% tokens reduction) pero esfuerzo alto (174 atoms × 30s = 90 min)
- Parallelizable (add field en futuras ingestas, retrofit progresively)
- Depende de Response Contract ya estar estable

**Esfuerzo**: 2.5 horas (retrofit batch ej. top-20 atoms)

---

#### **#17 — Lint automático post-batch con convergence loop**
**Score: 6/10 — CORPUS HEALTH**

**Descripción**: Tras `batch-ingest.sh`, dispara §4.3 automáticamente. Loop para cuando se cumplen criterios:
- <3 findings 2 corridas seguidas (broken links, orphans)
- `avg_wikilinks_per_atom ≥ 2` Y `<2-wikilink-atoms < 5%`

**Implementación**:
```bash
scripts/batch-ingest.sh && 
  scripts/auto-lint.sh --convergence
```

**Impacto**:
- **Automation**: No requiere lint manual
- **Health**: Corpus stays clean iteratively
- **Scale**: Funciona sin degradación en batches grandes

**Por qué 6/10**:
- Mejora internals, no user-facing
- Esfuerzo mecánico (shell scripting)
- Más importante conforme corpus crece (>300 atoms)

**Esfuerzo**: 3 horas

---

#### **#18 — Lint gap-detector semántico (Buscar huecos)**
**Score: 6/10 — CORPUS COMPLETENESS**

**Descripción**: Detecta términos frecuentes en sources/ que NO tienen atoms. Ejemplo: "max price" en 12 sources, 0 atoms → flag para crear `pricing--max-price-definition`.

**Implementación**:
```bash
scripts/lint-gaps.py --threshold 5
# Output: "max price" en 12 sources, 0 atoms → crear?
```

**Impacto**:
- **Gaps**: Identifica conceptos mencionados pero no documented
- **Coverage**: Corpus más exhaustivo
- **Auto-discovery**: Sin leer fuentes manualmente

**Por qué 6/10**:
- Improve corpus pero bajo urgencia (hoy coverage es buena)
- Esfuerzo moderado (Python + regex)
- Más valuoso con corpus > 400 atoms

**Esfuerzo**: 2 horas

---

#### **#19 — Lint cross-refs asimétricas**
**Score: 6/10 — GRAPH CONNECTIVITY**

**Descripción**: Si atom A menciona B, pero B no enlaza A → flag. Ejemplo: `pricing--adjacency-factor` cita "orphan nights" sin que `pricing--orphan-night-strategy` enlace back. Causa: query confundió ambos.

**Implementación**:
```bash
scripts/lint-asym-refs.py
# Output: A → B pero NOT B → A; proponer "Ver también: A"
```

**Impacto**:
- **Navigation**: Grafo bidireccional
- **Prevention**: Evita confusiones como la del test 2026-04-23
- **Discoverability**: Si lees B, ves que A te cita

**Por qué 6/10**:
- Previene bugs tipo query-test-3 pero low frequency
- Se vuelve redundante si implementamos backlinks auto-generados (opt #16)
- Útil para auditoría manual

**Esfuerzo**: 2 horas

---

---

### 🟣 PRIORIDAD 5/10 (ESCALABILIDAD — CORPUS 10+)

---

#### **#20 — Híbrido wiki+RAG fallback (Cold-path coverage)**
**Score: 5/10 — CONTINGENCY**

**Descripción**: Cuando §4.2 step 4 no encuentra suficientes atoms, combinar con RAG sobre sources/. No reemplazar atoms, sino sumar.

**Trigger**: `< N` atoms relevantes con score > threshold → RAG sobre sources/

**Implementación**:
```python
# query-hybrid.py: input = query; output = atoms + RAG chunks + suggested atom draft

embeddings = sentence_transformers("multi-qa-distilbert")
vector_store = Qdrant("sources-chunks")

atoms = wiki_query(topic)
if len(atoms) < 3 or min([a.score for a in atoms]) < 0.7:
    rag_chunks = vector_store.search(query, top_k=5)
    atoms.extend(rag_chunks)
    suggest_auto_ingest(rag_chunks)  # Close gap automáticamente
```

**Impacto**:
- **Coverage**: Responde incluso con corpus incompleto
- **Learning**: Auto-ingest suggerences → wiki crece donde se pregunta
- **Robustness**: Never "lo siento, no tengo esa info"

**Por qué 5/10**:
- Alto ROI conceptual pero bajo urgencia (corpus actual cubre 95%+ queries)
- Esfuerzo infrastructure (embeddings + vector DB)
- Más valuoso en 2-3 meses (cuando corpus se estabilice)
- Depende de stabilidad corpus primero

**Esfuerzo**: 6 horas + infra

---

#### **#21 — Bidirectional links auto-generados en notes/**
**Score: 5/10 — GRAPH NAVIGATION**

**Descripción**: Cada atom lleva section final auto-regenerada: "Citado por: [[B]], [[MOC/pricing]], [[C]]". Permite LLM ver grafo en todas direcciones.

**Formato** (entre marcadores):
```markdown
<!-- BACKLINKS:START -->
## Citado por
- [[notes/otro-atom]] — en sección "Customizations"
- [[MOC/pricing]] — lista principal
<!-- BACKLINKS:END -->
```

**Generación**: Extender `build-meta.sh` post-batch.

**Impacto**:
- **Navigation**: LLM no salta entre atoms, ve el grafo local
- **Prevention**: Query-test-3 type bugs evitados (adjacency ↔ orphan-nights hubiera mostrado cross-cites)
- **Discoverability**: "Ah, yo soy citado por N atoms"

**Por qué 5/10**:
- Mejora navegación pero bajo urgencia (current breadth busca funciona)
- Clutter visual en Obsidian (atoms muy citados = largo footer)
- Riesgo: rewrite de archivos cada build → cuidado con marker discipline
- Valida tras stabilización corpus

**Esfuerzo**: 3-4 horas (con marcador discipline)

---

#### **#22 — meta/query-index.md (Tabla de queries cacheadas)**
**Score: 5/10 — PERFORMANCE TRACKING**

**Descripción**: Centralizar lista de queries cacheadas + topics cubiertos + última validación. Acelera step 2 de §4.2.

**Estructura**:
```markdown
| Query | Topics | Answered | Valid until | Status |
|-------|--------|----------|------------|--------|
| `pricing--orphan-night` | pricing, occupancy | 2026-04-24 | 2026-06-24 | ✅ |
| `reviews--recovery` | reviews | 2026-04-22 | 2026-06-22 | ⚠️ Stale |
```

**Impacto**:
- **Speed**: Agent busca tabla, not recursively grepping queries/
- **Maintenance**: Clear view de qué queries existen
- **Staleness**: Automatic reminders para revalidar

**Por qué 5/10**:
- Mejora performance pero corpus aún pequeño (<50 queries hoy)
- Más valuoso cuando queries > 100
- Mecánica simple (tabla manual o auto-generated)

**Esfuerzo**: 1.5 horas (template + primer population)

---

#### **#23 — Declarar corpus maduro (Señal de stabilización)**
**Score: 5/10 — MILESTONE**

**Descripción**: Cuando siguiente batch aportaría <5 atoms nuevos por 10 sources (saturación > 80%), pasar a modo mantenimiento.

**Criterio**:
```bash
(atoms_nuevos / sources_batch) < 0.5  →  "Corpus maduro"
```

**Implicaciones**:
- **Ingest**: Solo vídeos nuevos del canal, no re-ingestion
- **Focus**: Pasar a optimizaciones arquitecturales (opt #16, #17, etc.)
- **Maintenance**: Lint + queries + dedup

**Impacto**:
- **Milestone**: Comunica a usuario state of corpus
- **Clarity**: Sabe cuándo tenemos "enough" vs "keep growing"
- **Strategy shift**: De expansión a refinement

**Por qué 5/10**:
- No es feature, es decision point
- Importante para roadmap planning
- Predicción actual: batch 8-10 ~80% saturación

**Esfuerzo**: 1 hora (análisis + decision)

---

---

### 🔘 PRIORIDAD 4/10 (QUALITY / EDGE CASES)

---

#### **#24 — Response Contract §10.7 (TL;DR + word limits)**
**Score: 4/10 — STANDARDIZATION** (ya implementado experimentalmente 2026-04-23)

**Descripción**: Estandarizar tone, word limits, citation style en respuestas. Fue añadido experimentalmente; necesita validación.

**Reglas iniciales**:
- Regime A: ≤300 palabras, 0 intro, TL;DR primero
- Regime B: ≤600 palabras, intro breve, 3-5 palancas
- Regime C: ≤1000 palabras, intro/conclusión, cuantificación
- Prohibido: adjetivos relleno ("clave", "importante"), anglicismos sin explicar
- Permitido: PriceLabs, Airbnb, Wi-Fi (conocidos)

**Validación pendiente**: 5 queries tácticas + 3 estratégicas. Medir reducción tokens + fidelidad tono.

**Impacto**:
- **Consistency**: Todas respuestas siguen patrón
- **Tokens**: -40-50% output esperado si funciona
- **Quality**: Tono profesional, sin relleno

**Por qué 4/10**:
- Ya implementado (test mode)
- Necesita validación (no finalized)
- Beneficio es output reduction pero no crítico
- Depende de corpus stabilización

**Esfuerzo**: 2 horas (calibración post-validation)

---

#### **#25 — §4.2 Presupuesto query escalado por topic-count**
**Score: 4/10 — DYNAMIC BUDGET**

**Descripción**: Budget actual: "5 atoms" único. Propuesta: escalar por topics.

**Fórmula**: `budget = 3 × topic_count + 1`, capped at 12

```
Single-topic: 4 atoms
2-topic: 7 atoms
3-topic: 10 atoms
4+: 12 atoms (hard cap)
```

**Validación pendiente**: A/B test con queries del set baseline. Medir score vs tokens totales.

**Impacto**:
- **Flexibility**: Preguntas multi-topic no artificialmente limited
- **Accuracy**: Régimen B con 3 topics debería cubrirlas sin exceder presupuesto

**Por qué 4/10**:
- Mejora pero bajo urgencia (current budgets funcionan)
- Números arbitrarios (necesitan calibración empírica)
- Esfuerzo es measurement, no implementation

**Esfuerzo**: 2 horas (A/B setup + measurement)

---

#### **#26 — Lint pre-commit: prohibir `.md` suffix en wikilinks**
**Score: 4/10 — BUG PREVENTION**

**Descripción**: Bug recurrente: escribir `[[notes/X.md]]` en lugar de `[[notes/X]]`. Script detecciona y falla.

**Implementación**:
```bash
#!/bin/bash
# lint-wikilinks.sh
rg "\[\[notes/[^]]+\.md\b" notes/ MOC/ queries/ meta/ index.md && \
  { echo "❌ ERROR: .md suffix en wikilinks encontrado"; exit 1; } || \
  exit 0
```

**Run**: Pre-commit hook o pre-build-meta

**Impacto**:
- **Automation**: Previene bug de una sola línea
- **Consistency**: Jamás .md en wikilinks (nueva convención)
- **Maintenance**: Lint mecánico no lo detecta hasta completo (aquí early detection)

**Por qué 4/10**:
- Bug muy específico (low frequency hoy)
- Fácil implementar (1 one-liner)
- ROI escala con corpus (>500 atoms = importante)

**Esfuerzo**: 0.5 horas

---

#### **#27 — YAML-strict quoting sweep**
**Score: 4/10 — ROBUSTNESS**

**Descripción**: 75% de atoms tienen YAML no-strict. Patterns: `**Bold**` al inicio, `: ` sin comillas. Scripts Python con PyYAML estricto fallan.

**Fix**: One-shot sweep envuelve valores con comillas cuando necesario.

**Implementación**:
```python
#!/usr/bin/env python3
# yaml-strict-sweep.py
for atom in glob.glob("notes/*.md"):
    frontmatter = extract_yaml_header(atom)
    for field in ["claim"]:
        if contains_problematic_chars(frontmatter[field]):
            frontmatter[field] = quote_value(frontmatter[field])
    write_atom(atom, frontmatter, body)
```

**Impacto**:
- **Compatibility**: Scripts estrictos (rank-sources.py, lint-gaps.py) funcionan sin adapters
- **Reliability**: Menos errores de parsing
- **Maintenance**: Futuras scripts pueden asumir PyYAML estricto

**Por qué 4/10**:
- Mejora robustness pero low user impact (ya funciona con tolerant parser)
- One-shot work (no recurrence)
- High long-term ROI (infrastructure)

**Esfuerzo**: 1.5 horas

---

---

### 🔴 PRIORIDAD 3/10 (EDGE CASES)

---

#### **#28 — Phantom topics prevention**
**Score: 3/10 — DATA INTEGRITY**

**Descripción**: Deep lint detectó 13 atoms con topics fuera del canonical de §10.3. Prevención: pre-commit check valida topics contra allowlist.

**Allowlist canonical** (§10.3):
```
pricing, occupancy, listing-optimization, cleaning-ops, reviews, 
hospitality, ranking, direct-booking, market-selection, regulations, 
tools-tech, investing
```

**Implementación**:
```python
# Pre-commit hook
for atom in changed_atoms:
    topics = atom.frontmatter["topics"]
    invalid = set(topics) - CANONICAL_TOPICS
    if invalid:
        print(f"❌ {atom}: topics inválidos: {invalid}")
        exit(1)
```

**Impacto**:
- **Consistency**: Todos atoms usa mismo topic set
- **Reliability**: MOCs no pierden atoms por typos
- **Maintenance**: Category drift prevented

**Por qué 3/10**:
- Bug muy específico (13 ocurrencias, ya fixed)
- Prevención mecánica (pre-commit)
- Low frequency (1 vez per batch si acaso)

**Esfuerzo**: 1 hora

---

#### **#29 — Secondary-topic MOC back-referencing**
**Score: 3/10 — RETRIEVAL COMPLETENESS**

**Descripción**: ~180 atoms multi-topic solo aparecen en MOC principal, no en secundario. Ejemplo: `hospitality--cleaner-entrepreneur` tiene topic `cleaning-ops` pero no en MOC/cleaning-ops.

**Options**:
- (a) Auto back-ref todos ~180 atoms desde MOC secundarios (one-shot, masivo)
- (b) LLM descubre vía grep runtime (caro: +1k tokens/query)

**Recomendación**: (a) con script, una sola vez.

**Implementación**:
```bash
# For each MOC
for moc in MOC/*.md; do
  topic=$(basename $moc .md)
  grep -l "topics:.*$topic" notes/*.md | xargs -I {} \
    echo "- [[{}]] — [snippet]" >> $moc
done
```

**Impacto**:
- **Completeness**: Todos atoms descubribles desde cualquier MOC relevante
- **Query cost**: -1k tokens si queries cross-topic son frecuentes

**Por qué 3/10**:
- Bug conocido pero bajo urgencia (búsqueda principal funciona)
- Esfuerzo muy alto (~180 edits)
- ROI solo si queries cross-topic frecuentes (hoy baja frequency)

**Esfuerzo**: 3-4 horas (puede ser parallelizable)

---

#### **#30 — Backlinks auto-generados en sources/**
**Score: 3/10 — RAW CONNECTIVITY** (opt #8 dari memory)

**Descripción**: Conectar los ~173 nodos sources/ al grafo vía backlinks auto-generados. Sección "Atoms que citan este source" en cada source.

**Formato** (entre marcadores):
```markdown
<!-- BACKLINKS:START -->
## Atoms que citan este source
- [[notes/atom-1]]
- [[notes/atom-2]]
<!-- BACKLINKS:END -->
```

**Impacto**:
- **Connectivity**: 173 isolated sources → connected nodes
- **Navigation**: Source a atoms que lo usan (reverse direction)
- **Schema**: Require exception to immutability (footer regenerable)

**Caveat**: Coste query = 0 (§7 prohíbe full-read sources; reads fragmentados no tocan footer).

**Recomendación** (dari memory): Worth it. Low-risk, high-value.

**Por qué 3/10**:
- Mejora grafo pero bajo user-facing impact
- Requiere schema change (marker discipline)
- Timing: mejor después de corpus stabilización

**Esfuerzo**: 2-3 horas (con discipline)

---

---

### ⚪ PRIORIDAD 2/10 (NICE-TO-HAVE / FUTURE)

---

#### **#31 — Move §10 (domain layer) fuera de CLAUDE.md**
**Score: 2/10 — REFACTORING**

**Descripción**: CLAUDE.md excede convención 200-líneas post-§10.7. Options:
- (a) Split: §0-§9 en CLAUDE.md, §10 en `docs/domain-optimize-my-airbnb.md`
- (b) Compresión: shrink §10 (pierde contexto)
- (c) Dejar como está (aceptar doc larga)

**Recomendación**: (a) cuando §10 > 150 líneas.

**Timing**: Después de Response Contract validado (3-5 queries).

**Impacto**:
- **Clarity**: CLAUDE.md kernel (genérico) vs domain-specifics separado
- **Maintainability**: Domain layer editable sin tocar schema
- **Reusability**: Kernel CLAUDE.md copiable a otros vaults

**Por qué 2/10**:
- Pure refactoring (no feature value)
- Nice-to-have architectural improvement
- No urgency (hoy funciona "ugly but complete")

**Esfuerzo**: 2 horas

---

#### **#32 — Add-on: Glosario expandido (meta/glossary.md enhancement)**
**Score: 2/10 — REFERENCE**

**Descripción**: Ampliar glosario con jerga del creador (orphan-night, gap-night, KAT score, etc.). Hoy tiene 3-4 términos, expandir a 15+.

**Estructura**:
```markdown
| Término | Definición | Contexto | Sinónimos |
|---------|-----------|----------|-----------|
| Orphan night | Noche aislada sin reserva en temporada alta | Pricing | Single-night vacancy |
| Gap night | Similar a orphan, pero en baja temporada | Pricing | — |
```

**Impacto**:
- **Onboarding**: Host nuevo entiende jerga
- **Consistency**: Todos los atom use same terminology
- **Clarity**: Glosario centralizado vs definitions inline

**Por qué 2/10**:
- Reference material (nice-to-have)
- No afecta Q&A functionality
- Low priority comparada con features

**Esfuerzo**: 1.5 horas (compile + organize)

---

---

## RESUMEN EJECUTIVO POR PRIORIDAD

| Prioridad | Cantidad | Esfuerzo Total | Impacto Agregado | Tipo |
|-----------|----------|----------------|------------------|------|
| **10/10** | 2 | 3.5h | Crítico (bloquea todo) | Blocker |
| **9/10** | 4 | 4.5h | Alto (D1-D8) | Quality |
| **8/10** | 5 | 9.0h | Alto (D3-D8) | UX/Content |
| **7/10** | 6 | 12.5h | Medio-alto (perf/ux) | Enhancement |
| **6/10** | 5 | 7.5h | Medio (health/perf) | Maintenance |
| **5/10** | 5 | 12.5h | Medio (contingency) | Infrastructure |
| **4/10** | 3 | 5.5h | Bajo-medio (edge) | Fine-tuning |
| **3/10** | 3 | 7.5h | Bajo (specific) | Bug-prevent |
| **2/10** | 2 | 3.5h | Muy bajo (refactor) | Refactoring |
| **—** | 1 | 1.5h | Reference | Reference |

---

## PLAN RECOMENDADO (Secuencia)

### INMEDIATO (Hoy 2026-04-25)
```
1. #1: Compactar index.md (3-4h) — BLOQUEANTE
2. #2: Resolver contradicción Q4 (20 min) — INTEGRITY
→ D9: 8.52 → 9.0 estimado
```

### ESTA SEMANA (2026-04-25 → 2026-04-29)
```
3. #3: Anglicismos (1h)
4. #4: Protocolo acción+timing+trigger (2h)
5. #5: Citas explícitas Q2, Q5 (1.5h)
6. #6: Tabla "Por qué palanca" (1.5h)
→ D9: 9.0 → 9.6+ estimado
```

### SEMANA 2 (2026-05-01 → 2026-05-08)
```
7. #7: BLUF (2h)
8. #8: Recency Override (2.5h)
9. #9: Casos reales (2h)
10. #10: Checklists (1.5h)
→ D9: 9.6 → 10.0- estimado
```

### PRÓXIMAS SEMANAS (Infraestructura + escalabilidad)
```
11-15: #11-15 (Links, YouTube timestamps, queries cache, dedup, lint)
16-32: Corpus stabilization optimizations
```

---

## CONCLUSIÓN

**32 optimizaciones consolidadas**, puntuadas 2-10 basadas en:
1. **Impacto** en D1-D8-D9
2. **Urgencia** (blocker vs nice-to-have)
3. **Esfuerzo** requerido
4. **Frecuencia** de beneficio

**Tier 1** (prioritarios esta semana) = **7 items, ~7 horas, D9: 8.52 → 9.6+**

**Todos viables en 3-4 semanas** si se aplican en orden recomendado.

---

**Documento generado**: 2026-04-25  
**Próximo paso**: Seleccionar cuál implementar primero (¿todo Tier 10/9? ¿Tier 8+? ¿One by one?)
