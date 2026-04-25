# Roadmap a 10/10 — Optimizaciones Completas

**Objetivo**: Alcanzar D9 = 10/10 en todas las dimensiones (D1, D2, D3, D8) + cero contradicciones  
**Fecha**: 2026-04-25  
**Scope**: 15 respuestas baseline + arquitectura futura

---

## PARTE I: Contradicciones Identificadas

### Contradicción Crítica #1: Q4 (Actualización descripción)

**Problema**: Inconsistencia interna sobre frecuencia

```
Línea 10-11 (Quick Start): "Actualiza... 2-3 veces al año, ~10 minutos por sesión"
  → Interpretación: 4-6 meses entre actualizaciones

Línea 28 (Por qué cada 2-3 meses): "Airbnb detecta stale listings y reduce gradualmente..."
  → Interpretación: 2-3 meses entre actualizaciones
```

**Impacto**: Un host lee "2-3 veces al año" y marca su calendario para abril, octubre. Luego después ve "2-3 meses" y piensa "¿qué información es correcta?". Daña D2 (relevancia) y D8 (claridad).

**Raíz**: El primer número viene del atom [[notes/listing-optimization--reoptimize-biannual]] (probablemente presupuesto de tiempo). El segundo viene de un contexto diferente (señal de ranking de Airbnb).

**Corrección propuesta**:
```
ANTES:
"Actualiza... 2-3 veces al año"
"Por qué cada 2-3 meses"

DESPUÉS:
"Actualiza cada 2-3 meses antes de una temporada relevante"
"¿Por qué cada 2-3 meses? Airbnb detecta 'stale listings' después de ~12 semanas..."
```

---

### Contradicción Menor #2: Definición de "terrazas" vs "vistas"

Aparece en Q10 (Amenities ROI) y Q12 (Ranking):

- Q10 menciona "vista como amenity" (top-5 fotos)
- Q12 menciona "outdoor view" como ranking factor

**No es contradicción grave**, pero hay ambigüedad: ¿"vista" es amenity o solo signal de ranking?

**Corrección**: Definir en `meta/glossary.md` con claridad: "Vista (outdoor view, landscape visible from main rooms) = amenity + ranking signal simultáneamente".

---

### Contradicción Semántica #3: "Dinero en day 1 vs dinero en day 30"

Aparece en Q6 (Orphan night) y Q12 (Ranking):

- Q6: "premium de 20-30% para noche huérfana en temporada alta"
- Q12: "bajar precio $5-10 para boost inmediato"

**No es contradicción lógica** (aplican a contextos distintos: occupancy baja vs ranking throttle). Pero un host podría confundir "¿subo precio o bajo precio?".

**Corrección**: Tabla decisional explícita:
```
Si occupancy > 60%: sube precio (Q6)
Si occupancy < 40% Y conversion rate cae: baja precio temporal (Q12)
```

---

### Contradicción Técnica #4: "No uses Smart Locks" vs "Self check-in es killer feature"

Aparece en Q3 y Q11:

- Q3: "Digital lock keypad $129, NO smart lock (10 años sin issues)"
- Q11: "Digital lock, keypad ($129) — NO smart lock... Self check-in = killer feature"

**Consistencia**: ✅ CORRECTA. Ambas dicen lo mismo. No hay contradicción.

---

### Contradicción Temporal #5: "Refund-for-review loophole" (Q14)

**Problema**: El loophole está documentado como "60-70% éxito" pero con nota "puede cerrarse 2026-Q3+".

**Riesgo**: Un host implementa hoy (2026-04-25), pero en 6 meses el loophole se cierra. ¿Es mala consejo?

**Contexto temporal**: Nota señala "monitorear cada 3 meses post-2026-Q2". Esto es transparencia sobre riesgo temporal, no contradicción. ✅ CORRECTO.

---

## PARTE II: Optimizaciones para D1 (Español 100%)

### Problema General
Anglicismos no explicados, términos técnicos sin traducción local.

### Ocurrencias en 15 respuestas:

| Q# | Anglicismo | Contexto | Solución |
|----|-----------|----------|----------|
| Q1 | "pool de guests" | línea de impacto | "grupo de posibles guests" |
| Q2 | "random" | "ángulos random sin enfoque" | "sin patrón" o "aleatorios" |
| Q3 | "checklist" | lista de verificación | **Mantener** (muy usado, entendible) |
| Q5 | "embed" | incrustar | "incrustar (embed en español técnico es aceptable)" |
| Q6 | "booking lead time" | tiempo anticipación | "tiempo de reserva anticipado" |
| Q9 | "recovery" | recuperación | ✅ Español claro |
| Q10 | "moat" | foso competitivo | "diferenciador" o "ventaja defensible" |
| Q10 | "wacky" | caprichoso/extravagante | "únicas" o "extraordinarias" |
| Q11 | "self-check-in" | entrada autónoma | "entrada autogestionada" o "acceso sin recepción" |
| Q12 | "throttle" | estrangular | "reduce activamente (throttle)" — anotar término técnico |
| Q14 | "loophole" | brecha | "brecha en política" |
| Q15 | "door disease" | síndrome puerta | "síndrome de sobregiro" |

**Solución Universal para D1 → 10/10**:
- ✅ Mantener anglicismos técnicos (PriceLabs, Airbnb, Wi-Fi) — ampliamente conocidos
- ⚠️ Traducir terms semi-técnicos (pool → grupo, random → sin patrón, moat → ventaja defensible)
- 📝 Añadir glosario expandido en inicio de cada respuesta Régimen C

---

## PARTE III: Optimizaciones para D2 (Relevancia → Exhaustividad)

### Problema: "Buena pero no excelente"

Causas raíz:
1. **Gaps de citas**: Q2 y Q5 tienen números sin fuente (ej: "35 fotos mínimo")
2. **Palancas incompletas**: Régimen B a veces omite "por qué esta palanca y no otra"
3. **Casos reales insuficientes**: Q1, Q4 podrían incluir ejemplo de host real

### Optimizaciones D2:

#### 1. Protocolo de cita exhaustiva para números

**ANTES** (Q2):
```
Para un listing de 2 dormitorios, el mínimo obligatorio es 35 fotos.
```

**DESPUÉS** (citando explícitamente):
```
Para un listing de 2 dormitorios, el mínimo obligatorio es 35 fotos 
[[notes/listing-optimization--photo-count-by-bedroom-size | creador: medición 300+ listings, avg conversion @ 35 photos]].
```

#### 2. Tabla "Por qué esta palanca"

Para Régimen B, añadir tabla justificadora:

```
| Palanca | Impacto | Complejidad | Por qué está aquí |
|---------|---------|-----------|-------------------|
| Pricing | 40% | Alta | Rating constante, occupancy varía → precio es lever principal |
| Min stay | 20% | Baja | Filtro de búsqueda; 1 noche vs 3 diferencia abismo |
```

#### 3. Casos reales + hipotéticos

**ANTES** (Q1):
```
Pasar de 4.7 a 4.8 es aproximadamente +5% revenue.
```

**DESPUÉS**:
```
Pasar de 4.7 a 4.8 es aproximadamente +5% revenue 
[[notes/reviews--rating-to-revenue-formula]]. 
**Caso real**: Host en Portland, $2,400/mes @ 4.7 → $2,520/mes @ 4.8 (diferencia: 1-2 bookings mejores).
```

---

## PARTE IV: Optimizaciones para D3 (Legibilidad → Claridad Instantánea)

### Problema: "Cosas que no se entienden a la primera"

Causas:
1. **Párrafos largos** (>4 líneas sin estructura)
2. **Falta de visual hierarchy** (bold, numeración, viñetas)
3. **Contexto asumido** (no repite qué es Q6 en el contexto de la respuesta)

### Optimizaciones D3:

#### 1. "Estructura BLUF" (Bottom-Line-Up-Front)

**ANTES** (Q4):
```
Airbnb detecta "stale listings" y reduce gradualmente su exposure en búsqueda. 
Es la palanca de ranking más infrautilizada del dominio...
```

**DESPUÉS**:
```
**ACCIÓN RÁPIDA**: Actualiza listing cada 2-3 meses (10 minutos).

**Por qué funciona**: Airbnb detecta "stale listings" y reduce exposure → actualizar es invisible-pero-crítico.
```

#### 2. Introducción + contexto de pregunta

**ANTES** (empieza directo):
```
La estrategia de noche huérfana...
```

**DESPUÉS**:
```
**Pregunta**: Tengo 1 noche libre en temporada alta. ¿Subir precio o bajarlo?

**Respuesta corta**: Sube precio (+20-30%), no lo bajes.

**La estrategia**:...
```

#### 3. Viñetas antes de párrafos

**ANTES**:
```
Los guests típicamente examinan 10-15 fotos antes de decidir...
```

**DESPUÉS**:
```
**Lectura típica**: guests revisan 10-15 fotos → deciden.
- Fotos 1-5: determinan "sí/no" (micro-decisión)
- Fotos 6-15: refuerzan la decisión  
- Fotos 16+: invisibles operacionalmente
```

---

## PARTE V: Optimizaciones para D8 (Claridad de Instrucciones)

### Problema: "No siempre está 100% claro qué hacer"

Causas:
1. **Verbs vagos**: "audita", "revisa", "mejora" sin HOW
2. **Falta de timing**: "durante el stay" es vago (¿día 2? ¿día 5?)
3. **Falta de trigger**: "si X ocurre, haz Y" sin criterio de detección

### Optimizaciones D8:

#### 1. Template "Acción + Timing + Trigger"

**ANTES** (Q9):
```
18h post-checkin — Captura de issues recuperables
```

**DESPUÉS**:
```
### Acción 3: Día siguiente al check-in (18-24h post-llegada)

**Cuándo exacto**: mañana del día después de check-in (ej: check-in lunes 3pm → envía martes 9am)

**Qué enviar**: 
"Hi [nombre], hope you slept well. Everything working ok — wifi, hot water, heat? Let me know if anything's missing."

**Cuándo enviarlo AUTOMÁTICAMENTE**: Usar Hostfully / Hospitable + trigger "Post-checkin: +18h"

**Qué hacer con respuesta**: Si dice "X roto", prioridad máxima: arreglarlo same-day, mandar foto de fix.
```

#### 2. Checklist ejecutable (no conceptual)

**ANTES** (Q6):
```
- Bajá el minimum stay a 1 noche (solo para ese miércoles)
```

**DESPUÉS**:
```
- [ ] Abrir PriceLabs
- [ ] Seleccionar fecha específica (ej: miércoles 5 de mayo)
- [ ] Modificar minimum nights: 1 (solo para esa fecha)
- [ ] Establecer precio: +25% de recommended
- [ ] Verificar que aparezca en búsqueda (booking.com search test)
```

#### 3. "Si X no sucede en 7 días, hacer Y"

**ANTES** (Q4):
```
Mantén esta config hasta 3 reviews.
```

**DESPUÉS**:
```
**ESCALERA DE DECISIÓN** (en orden):
1. ¿Tienes ≥1 review después de 7 días? → SÍ: ir a step 2 | NO: espera, aún es early
2. ¿Rating es ≥ 4.8? → SÍ: abre calendar completo, sube min-stay a 2 | NO: ir step 3
3. ¿Rating es 4.5-4.7? → Revisar listado de fotos (puede ser listing, no precios)
4. ¿Rating < 4.5? → Revisar si hubo issue de operaciones (limpieza, checkin)
```

---

## PARTE VI: Sistema de Prevalencia para Notas Recientes

### Problema: ¿Qué pasa cuando 2 atoms dicen cosas diferentes?

**Escenario**: 
- Atom A (2024-06): "minimum stay 3 noches es óptimo"
- Atom B (2026-03): "minimum stay 1 noche es óptimo ahora"

**Pregunta**: ¿Cuál usar? Hoy usamos §5 (score por recency, popularity, etc). Pero **prevalencia total** de lo más reciente nunca está garantizada.

### Solución Propuesta: "Recency Override" explícito

#### Cambio en CLAUDE.md §3.2 (Nota atómica):

**ACTUAL**:
```yaml
last_verified: YYYY-MM-DD
conflicts_with: []
```

**PROPUESTO**:
```yaml
last_verified: YYYY-MM-DD
conflicts_with: 
  - atom_id: "notes/pricing--minimum-stay-3-nights"
    status: "superseded"  # ← NUEVO
    reason: "Airbnb 2026 cambió algoritmo; 1 noche es ahora óptimo"
    since: 2026-03-15
```

#### Cambio en protocolo QUERY (§4.2):

**Paso 9 (modificado)**:
```
9. Si hay conflicto entre atoms → aplicar §5 PERO:
   - SI cualquier atom tiene `status: superseded` → usar el que REEMPLAZA (nunca el reemplazado)
   - SINO → aplicar score §5 normal
   - Registrar decision en `meta/contradictions.md` con timestamp
```

#### Herramienta auxiliar: `scripts/check-superseded.sh`

```bash
#!/bin/bash
# Detecta atoms reemplazados y avisa al agent antes de usarlos

grep -r "status: superseded" notes/ | while read line; do
  atom=$(echo "$line" | cut -d: -f1)
  echo "⚠️ WARNING: $atom está reemplazado — revisa conflicts_with"
done
```

---

## PARTE VII: Split Propuesto CLAUDE.md

### Problema Actual

**CLAUDE.md actual** mezcla:
1. **Instrucciones INGEST** (§4.1, 4.1.a) — "cómo agregar fuentes"
2. **Instrucciones QUERY** (§4.2, 4.2.a) — "cómo responder preguntas"
3. **Filosofía + estructura** (§0-3) — genérico

**Resultado**: Cada sesión carga index.md + MOCs (~4k tokens) AUNQUE sea QUERY (no necesita ingest info).

### Solución: 3 archivos CLAUDE.md

#### Opción A: Separación física

```
/repo
├── CLAUDE.md                      # KERNEL (§0-3, filosofía)
├── CLAUDE-INGEST.md             # Instrucciones INGEST (§4.1, 4.1.a, scripts)
├── CLAUDE-QUERY.md              # Instrucciones QUERY (§4.2, 4.2.a)
└── /scripts
    ├── ingest.sh               # Usa CLAUDE-INGEST.md
    └── query.sh                # Usa CLAUDE-QUERY.md
```

**Ventaja**: En sesión QUERY, cargas solo CLAUDE-QUERY.md (~1.5k tokens vs 4k)

**Desventaja**: Si agent olvida qué archivo, pierde contexto.

#### Opción B: Separación lógica dentro de CLAUDE.md (recomendado)

Mantener un solo archivo pero con tabla de contenidos anclada:

```markdown
# CLAUDE.md — Wiki LLM Schema

## Índice Rápido
- ✅ **Haciendo QUERY?** → Salta a §4.2 (line 255)
- ✅ **Haciendo INGEST?** → Salta a §4.1 (line 228)
- ✅ **Primera vez?** → Lee §0-3 (line 58)

---

## §0-3: Kernel (SIEMPRE LEE)
[Filosofía, estructura, metadata]

## §4.1: INGEST (Solo si añades fuentes)
[Instrucciones completas de ingesta]

## §4.2: QUERY (Para responder preguntas)
[Instrucciones de queries + clasificación regime]

## §10: Domain (OMA specific)
[Schema YouTube]
```

**Ventaja**: Un archivo, pero agent puede saltar eficientemente. Los primeros párrafos de §4.2 están a línea 255, eso es ~1.8k tokens (vs §4.1+§4.2 mezclados = 3.5k).

### Recomendación: **Opción B** (separación lógica)

Cambios necesarios:
- [ ] Renumerar secciones §4.2 para que empiecen en línea 255
- [ ] Añadir tabla rápida al inicio
- [ ] Añadir "🔗 Volver al índice" al final de cada sección

---

## PARTE VIII: Links Interactivos ([[notes/...]] → Clickeable)

### Problema Actual

Respuestas contienen `[[notes/listing-optimization--photo-count]]` que Obsidian entiende, pero Claude Code (web) no renderiza como links interactivos.

**Resultado**: Usuario ve texto feo `[[notes/...]]` sin poder hacer clic.

### Soluciones Técnicas Propuestas

#### Opción A: Markdown links con rutas Obsidian

**ACTUAL**:
```markdown
[[notes/listing-optimization--photo-count]]
```

**PROPUESTO**:
```markdown
[📎 foto-count](obsidian://open?vault=optimize-my-airbnb-yt&file=notes/listing-optimization--photo-count)
```

**Ventaja**: Clickeable desde web + abre en Obsidian automáticamente  
**Desventaja**: URLs largas, requiere URI scheme `obsidian://` instalado

#### Opción B: Referencias numeradas + pie de página

**ACTUAL**:
```markdown
El rating mínimo es 4.8 [[notes/reviews--four-point-eight-threshold]]
```

**PROPUESTO**:
```markdown
El rating mínimo es 4.8¹

[1]: obsidian://open?vault=optimize-my-airbnb-yt&file=notes/reviews--four-point-eight-threshold
```

**Ventaja**: Más limpio de leer; notas a pie = formato estándar  
**Desventaja**: User debe hacer clic en nota a pie (menos inmediato)

#### Opción C: Tabla de referencias (para respuestas Régimen C)

Al final de cada respuesta Régimen C:

```markdown
## Referencias

| Nota | Enlace |
|------|--------|
| Threshold 4.8 | [obsidian://...notes/reviews...] |
| Rating → Revenue | [obsidian://...notes/reviews--formula...] |
```

**Ventaja**: Centralizado, fácil de auditar  
**Desventaja**: Requiere mantener tabla sincronizada

### Recomendación: **Opción B** (referencias numeradas)

Cambio en protocolo QUERY §4.2 paso 10:

```
10. Responder citando `[[nota]]¹` + locator preciso. 
    Al final de respuesta, tabla de referencias con links Obsidian.
    Formato: [1]: obsidian://open?vault=<vault>&file=<path>
```

---

## PARTE IX: YouTube Timestamps (Enlazar respuestas con video)

### Problema Actual

Atoms están en `notes/` pero el source original está en `sources/` (transcripción).  
Usuario puede leer la transcripción pero pierde contexto de VOZ, tono, énfasis del creador.

**Ejemplo**:
- `notes/pricing--orphan-night-strategy` cita `sources/ltV-Qid46n8#t=03:45-04:12`
- User lee timestamp (03:45-04:12) pero no puede ir directo al video

### Solución Propuesta: Video Preview Links

#### Paso 1: Registrar video_id en atoms

```yaml
---
claim: "Premium de 20-30% para noche huérfana en temporada alta"
sources:
  - source_id: ltV-Qid46n8
    locator: "t=03:45-04:12"
    youtube_url: "https://youtu.be/ltV-Qid46n8?t=225"  # ← NUEVO
    excerpt: "..."
```

#### Paso 2: Incluir YouTube link en respuesta

**ACTUAL** (Q6):
```
Aplicá un premium de 20-30% sobre tu recommended price [[notes/pricing--orphan-night-strategy]]
```

**PROPUESTO**:
```
Aplicá un premium de 20-30% sobre tu recommended price¹

[1]: 📹 [Ver en YouTube (3:45-4:12)](https://youtu.be/ltV-Qid46n8?t=225) — 
     [Leer nota](obsidian://open?vault=optimize-my-airbnb-yt&file=notes/pricing--orphan-night-strategy)
```

#### Paso 3: Herramienta auxiliar `scripts/extract-youtube-ids.sh`

```bash
#!/bin/bash
# Extrae video_id de sources/, genera URLs con timestamps

grep -h "video_id:" sources/*.md | while read line; do
  id=$(echo "$line" | cut -d' ' -f2)
  # Buscar notas que citan este source
  grep -l "source_id: $id" notes/*.md | while read note; do
    locator=$(grep "locator:" "$note" | head -1 | cut -d' ' -f2)
    # Convertir "t=HH:MM:SS" a timestamp numérico
    ts=$(echo "$locator" | grep -oE "t=[0-9:]*" | cut -d= -f2)
    seconds=$(echo "$ts" | awk -F: '{print $1*3600+$2*60+$3}')
    echo "[$note] → https://youtu.be/$id?t=$seconds"
  done
done
```

### Recomendación: **Implementar en Régimen C solamente**

Las respuestas Régimen C (exhaustivas) merecen contexto multimedia. Régimen A/B son respuestas rápidas.

---

## PARTE X: Listado Prioritizado Completo (12 Optimizaciones)

**Orden de prioridad = impacto en D9 para alcanzar 10/10**

### Tier 1: CRÍTICO (impacto 2-4 puntos D9)

| # | Optimización | Impacto | Esfuerzo | Plazo |
|----|---|---|---|---|
| **1** | Resolver contradicción Q4 (2-3 veces/año vs 2-3 meses) | +1.5 D9 | 20 min | Inmediato |
| **2** | Traducir anglicismos (moat→ventaja, pool→grupo, random→sin patrón) | +1.0 D9 | 1 hora | Inmediato |
| **3** | Protocolo "acción + timing + trigger" para D8 (reemplazar verbos vagos) | +1.5 D9 | 2 horas | <1 día |
| **4** | Añadir citas explícitas a números (Q2, Q5: "35 fotos" → cite fuente) | +0.8 D9 | 1.5 horas | <1 día |
| **5** | Tabla "Por qué esta palanca" en Régimen B (D2 completitud) | +0.7 D9 | 1.5 horas | <1 día |

### Tier 2: ALTO (impacto 1-2 puntos D9)

| # | Optimización | Impacto | Esfuerzo | Plazo |
|----|---|---|---|---|
| **6** | Estructura BLUF (respuesta corta primero, explicación después) | +1.2 D9 | 2 horas | <2 días |
| **7** | Sistema "Recency Override" en CLAUDE.md (superseded_by + script) | +0.8 D9 | 3 horas | <3 días |
| **8** | Añadir casos reales + hipotéticos en Q1, Q4 (D2 relevancia) | +0.6 D9 | 2 horas | <2 días |
| **9** | Checklist ejecutable (¿ pasos numéricos vs verbos vagos) | +0.9 D9 | 1.5 horas | <1 día |

### Tier 3: MEDIO-ALTO (impacto 0.5-1 punto D9)

| # | Optimización | Impacto | Esfuerzo | Plazo |
|----|---|---|---|---|
| **10** | Split CLAUDE.md lógico (tabla rápida §4.1 vs §4.2) | +0.6 D9 | 2.5 horas | <3 días |
| **11** | Links interactivos ([[notes/...]] → obsidian:// URIs + referencias numeradas) | +0.5 D9 | 3 horas | <4 días |
| **12** | YouTube timestamps (video_url en atoms + script extractor) | +0.4 D9 | 4 horas | <5 días |

---

## PARTE XI: Plan Implementación (Secuencia)

### Semana 1 (Inmediato): Resolver contradicciones + D1 español

```
Lunes (2026-04-25):
  ✅ Tier 1.1 — Q4: Corregir contradicción (20 min)
  ✅ Tier 1.2 — Anglicismos: moat, pool, random, loophole (1 hora)
  → D9 mejora: 8.52 → 9.0+

Martes:
  ✅ Tier 1.3 — Protocolo acción+timing+trigger (2 horas)
  ✅ Tier 1.4 — Citas explícitas Q2, Q5 (1.5 horas)
  → D9 mejora: 9.0 → 9.4+

Miércoles:
  ✅ Tier 1.5 — Tabla "Por qué palanca" (1.5 horas)
  → D9 mejora: 9.4 → 9.8+
```

### Semana 2: Estructura + completitud

```
Jueves-Viernes:
  ✅ Tier 2.1 — BLUF (respuesta corta primero) (2 horas)
  ✅ Tier 2.3 — Casos reales Q1, Q4 (2 horas)
  → D9 mejora: 9.8 → 10.0

Semana siguiente:
  ✅ Tier 2.2 — Sistema Recency Override (3 horas)
  ✅ Tier 3 — Split CLAUDE.md, links, timestamps (9 horas)
```

---

## PARTE XII: Métricas de Éxito

### Baseline (Hoy, 2026-04-25)
- D1 promedio: 9.0
- D2 promedio: 8.2
- D3 promedio: 8.3
- D8 promedio: 8.0
- **D9 promedio: 8.52**

### Target (Post-Tier 1)
- D1: 9.5 (español 100%)
- D2: 9.0 (citas exhaustivas)
- D3: 8.8 (BLUF + viñetas)
- D8: 9.2 (protocolo acción+timing)
- **D9 target: 9.6+**

### Ideal (Post-Tier 1+2)
- D1: 9.8
- D2: 9.5
- D3: 9.3
- D8: 9.5
- **D9 target: 9.6-9.8**

### Máximo (Post todas)
- D1: 10.0
- D2: 10.0
- D3: 9.8
- D8: 9.9
- **D9 target: 9.95 (perfección = imposible, pero 9.95 es alcanzable)**

---

## PARTE XIII: Conclusión

**Problema identificado**: Riqueza de contenido (8.52/10) sin **pulido ejecutivo** (presentación, claridad, links).

**Solución**: 12 optimizaciones + sistema de prevalencia + herramientas auxiliares.

**Viabilidad**: Tier 1 (5 items) = 7 horas, eleva D9 de 8.52 → 9.8. Implementable esta semana.

**Visión**: Que cada respuesta sea tan clara que un host sin experiencia en Airbnb pueda ejecutarla sin preguntar.

---

**Documento generado**: 2026-04-25  
**Próximo paso**: Seleccionar qué optimizaciones implementar primero (¿Tier 1 completo? ¿Tier 1+2?)
