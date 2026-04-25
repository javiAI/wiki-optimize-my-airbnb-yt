---
name: Test Battery Plan — Sistema de Evaluación Iterativa
description: Planificación completa para batería de test (15 preguntas, evaluación multi-dimensión, iteración sobre optimizaciones)
date: 2026-04-24
---

# Test Battery Plan — Evaluación Sistemática del Vault

## Executive Summary

Este plan establece un proceso riguroso para:
1. **Línea base**: Evaluar calidad actual del sistema (sin optimizaciones)
2. **Iteraciones**: Aplicar optimizaciones ordenadas por ROI (value/effort)
3. **Medición**: Comparar resultados antes/después de cada optimización
4. **Análisis**: Validar qué optimizaciones son efectivas

**Duración estimada**: 5-8 sesiones (batería inicial + 3-4 ciclos de optimización)

---

# PARTE 1: SELECCIÓN DE PREGUNTAS (15 Preguntas)

## Criterio de ordenamiento

**Ordenadas por dificultad (Regime según §4.2 de CLAUDE.md)**:
- **Fácil** (Regime A): 1 palanca específica, respuesta factual simple
- **Medio** (Regime B): 3-6 palancas interdependientes, táctico
- **Difícil** (Regime C): 7+ palancas, estratégico, requiere síntesis

---

## Batería de 15 Preguntas

### Bloque 1: Fácil (Regime A) — Preguntas factticas

**Q1: Rating threshold**
> "¿Cuál es el rating mínimo que debo tener para que los guests me encuentren sin problemas en búsqueda de Airbnb?"

*Tipo*: Threshold / fact
*Palancas*: 1 (rating tier)
*Regime*: A
*Atoms esperados*: reviews--four-point-eight-threshold-disregard
*Complejidad*: Muy baja

**Q2: Photo count**
> "¿Cuántas fotos debería subir de mi listing de 2 dormitorios?"

*Tipo*: Numeric / specification
*Palancas*: 1 (photo count by bedroom)
*Regime*: A
*Atoms esperados*: listing-optimization--photo-count-by-bedroom-size
*Complejidad*: Muy baja

**Q3: Amenity essentials**
> "¿Cuáles son los 9 amenities básicos que TODOS los guests esperan?"

*Tipo*: Checklist / specification
*Palancas*: 1 (essential amenities)
*Regime*: A
*Atoms esperados*: listing-optimization--essential-amenities-checklist
*Complejidad*: Baja

**Q4: Update frequency**
> "¿Cada cuánto tiempo debería actualizar mi descripción del listing?"

*Tipo*: Interval / optimization
*Palancas*: 1 (reoptimization cadence)
*Regime*: A
*Atoms esperados*: listing-optimization--reoptimize-biannual
*Complejidad*: Baja

**Q5: Direct link workaround**
> "Airbnb no me permite poner links de YouTube en la descripción, ¿cómo hago para que los guests vean mi video?"

*Tipo*: Workaround / tactic
*Palancas*: 1 (mention title, guest searches)
*Regime*: A (grounded)
*Atoms esperados*: listing-optimization--airbnb-does-not-accept-direct-links
*Complejidad*: Baja

---

### Bloque 2: Medio (Regime B) — Preguntas tácticas

**Q6: Orphan night pricing**
> "Tengo una noche huérfana (miércoles) en temporada alta sin reserva. ¿Cómo debería fijar el precio?"

*Tipo*: Tactical / decision-making
*Palancas*: 3-4 (pricing, orphan nights, seasonality, PriceLabs)
*Regime*: B
*Atoms esperados*: pricing--orphan-nights, pricing--seasonality-strategy, tools-tech--simplified-pricing-avoid-trap
*Complejidad*: Media

**Q7: Recovery from negative review**
> "Acabo de recibir una review negativa que bajó mi rating. ¿Qué pasos sigo para recuperarme?"

*Tipo*: Process / recovery
*Palancas*: 3-4 (volume, messaging, response to negative, selection effects)
*Regime*: B
*Atoms esperados*: reviews--more-dilutes-negative, reviews--reciprocity-post-checkout, reviews--emotional-intensity-plus-10
*Complejidad*: Media

**Q8: Cleaning team structure**
> "Estoy empezando con 2 propiedades y quiero contratar limpieza. ¿Cómo estructuro esto?"

*Tipo*: Operational setup
*Palancas*: 4-5 (team structure, turnover time, checklist, communication, cost)
*Regime*: B
*Atoms esperados*: cleaning-ops--team-structure-decisions, hospitality--nine-automated-messages
*Complejidad*: Media-alta

**Q9: Message timing strategy**
> "¿En qué momentos del stay debo enviar mensajes al guest para maximizar que me dejen buena review?"

*Tipo*: Tactical / timing-based
*Palancas*: 4 (pre-arrival, mid-stay, post-checkout, reciprocity)
*Regime*: B
*Atoms esperados*: reviews--four-days-pre-checkin-message, reviews--mid-stay-message, reviews--reciprocity-post-checkout
*Complejidad*: Media

**Q10: Amenities ROI**
> "¿Cuáles son los amenities que me dan más retorno por el dinero invertido?"

*Tipo*: Optimization / resource allocation
*Palancas*: 3-4 (unique amenities, review fuel, specificity, price coherence)
*Regime*: B
*Atoms esperados*: listing-optimization--unique-amenities-review-fuel, listing-optimization--amenities-match-price-point
*Complejidad*: Media-alta

---

### Bloque 3: Difícil (Regime C) — Preguntas estratégicas

**Q11: New listing from zero**
> "Acabo de crear un listing nuevo sin reviews. ¿Cuál es la estrategia COMPLETA para arrancar y conseguir buenos reviews rápido?"

*Tipo*: Strategic / end-to-end
*Palancas*: 6-8 (pricing, photos, amenities, messaging, expectation-setting, gap-nights, recovery loops)
*Regime*: C
*Atoms esperados*: Multiple across pricing, reviews, listing-optimization, hospitality
*Complejidad*: Alta

**Q12: Maximize ranking** (multi-factor)
> "¿Cuál es el plan paso a paso para maximizar mi posición en el algoritmo de búsqueda de Airbnb?"

*Tipo*: Strategic / algorithm optimization
*Palancas*: 7+ (conversion rate, reviews, rating, response time, amenities, title, photos, response rate)
*Regime*: C
*Atoms esperados*: ranking--factors-confirmed, listing-optimization--big-three, reviews--six-attributes
*Complejidad*: Muy alta

**Q13: Investment deal evaluation**
> "Estoy evaluando comprar una propiedad nueva. ¿Cuál es el framework para decidir si es un buen deal o no?"

*Tipo*: Strategic / evaluation framework
*Palancas*: 6-7 (market selection, revenue potential, cap rate, location filters, seasonal variance, regulatory risk)
*Regime*: C
*Atoms esperados*: investing--how-to-evaluate-deals, market-selection--negative-filters, regulations--key-checks
*Complejidad*: Muy alta

**Q14: Negative review removal options**
> "Tengo una review negativa injusta que me está dañando el rating. ¿Cuáles son TODAS mis opciones y cuál funciona?"

*Tipo*: Strategic / options analysis (con contradicciones)
*Palancas*: 5+ (removal process, refund trades, damage claims, call tactics, TOS violations)
*Regime*: C + contradicciones
*Atoms esperados*: reviews--removal-process-broken-2025, reviews--refund-for-review-trade-2026-loophole, reviews--removal-call-playbook
*Complejidad*: Muy alta (hay conflictos documentados)

**Q15: Market saturation pivot**
> "Mi mercado está muy saturado. ¿Debo irme, pivotear, o doble-bajar precios? ¿Cómo lo decido?"

*Tipo*: Strategic / existential business decision
*Palancas*: 7+ (market selection, differentiation, pricing power, profitability math, direct booking, portfolio diversification)
*Regime*: C
*Atoms esperados*: market-selection--filtros, ranking--saturation-signals(?), pricing--race-to-bottom-avoidance(?)
*Complejidad*: Muy alta (requiere síntesis cross-tema)

---

# PARTE 2: METODOLOGÍA DE EVALUACIÓN

## Dimensiones de Evaluación (1-10 para cada una)

### D1: Calidad de español + idioma apropiado (1-10)
- **10**: Español impecable, vocabulario técnico apropiado, 0 anglicismos sin explicar
- **8-9**: Muy bueno, 1-2 términos en inglés explicados bien
- **6-7**: Bueno, español correcto pero algo formal o coloquial según contexto
- **4-5**: Aceptable pero con calidad mejorable (faltas, registro inconsistente)
- **1-3**: Pobre (errores gramaticales, anglicismos sin explicación, confuso)

### D2: Calidad de respuesta — Relevancia y completitud (1-10)
- **10**: Respuesta directa, cita fuentes, cubre todos los ángulos del MOC
- **8-9**: Muy buena, cubre 80%+ de la pregunta, con citas
- **6-7**: Buena, responde la pregunta, pero falta profundidad en algún ángulo
- **4-5**: Aceptable, responde básicamente pero incompleta
- **1-3**: Pobre, evade la pregunta o da información genérica sin fuente

### D3: Legibilidad + Placer de lectura (1-10)
- **10**: Estructura clara (listas, números, bullets), tono conversacional, fácil de seguir
- **8-9**: Muy legible, bien estructurado, texto fluido
- **6-7**: Legible, estructura OK, pero algo denso o monolítico
- **4-5**: Poco legible, párrafos largos, estructura confusa
- **1-3**: Ilegible, puro texto muro, sin estructura

### D4: Tokens input (conteo real)
- Solo conteo, sin nota. Registrar número exacto
- **Peso de coste: 1** (base)
- Rango esperado: Regime A ≈ 3.5k-4k | Regime B ≈ 5-6k | Regime C ≈ 7-10k

### D5: Tokens output (conteo real)
- Solo conteo, sin nota. Registrar número exacto
- **Peso de coste: 6** (6× más caro que input)
- Rango esperado: Regime A ≈ 1-1.5k | Regime B ≈ 1.5-2.5k | Regime C ≈ 2-4k

### D6: Coste total (métrica ponderada PRIMARY)
- **`Total_cost = (tokens_in × 1) + (tokens_out × 6)`**
- Calculado automáticamente
- **Esta es la métrica PRIMARY para optimización y budgets**
- Rango esperado: Regime A ≈ 7.5k-10k | Regime B ≈ 14-18k | Regime C ≈ 19-34k

### D7: Eficiencia (tokens output / tokens input)
- Ratio calculado automáticamente
- Target: <0.3 (menos de 30% de overhead de input)
- Mejor: <0.2
- **Nota**: métrica secundaria para análisis; usar D6 (coste total) como PRIMARY

### D8: Estructura y claridad de instrucciones (1-10)
- **10**: Instrucciones numeradas, claras, accionables, sin ambigüedad
- **8-9**: Muy clara, estructura lógica, fácil de ejecutar
- **6-7**: Claras pero con algún salto lógico
- **4-5**: Confusas, falta orden o detalles
- **1-3**: Incomprensibles, contradictorio o vago

### D8: Score general (1-10)
- Promedio ponderado de D1, D2, D3, D7 (excluyendo tokens)
- Pesos: D1=15%, D2=35%, D3=25%, D7=25%
- `score = 0.15*D1 + 0.35*D2 + 0.25*D3 + 0.25*D7`

---

## Rúbrica de calidad por Regime

| Regime | D1 Spanish | D2 Quality | Tokens out | Coste total | Score target |
|--------|-----------|-----------|-----------|-----------|---|
| A | 9+ | 9+ | ≤1.2k | ≤10.2k | 8.5+ |
| B | 8.5+ | 8+ | 1.2-2.5k | ≤16.5k | 8+ |
| C | 8+ | 7.5+ | 2-4k | ≤28k | 7.5+ |

**Coste total = (tokens_in × 1) + (tokens_out × 6)**

---

# PARTE 3: FORMATO DE RESULTADO

## Tabla de resultados

```
| # | Pregunta | Regime | D1 Spanish | D2 Quality | D3 Readability | D8 Clarity | D9 Score | Tokens In | Tokens Out | Coste Total | Efficiency | Notas |
|----|----------|--------|----------|-----------|----------------|-----------|---------|-----------|-----------|-----------|-----------|-------|
| Q1 | Rating min | A | ? | ? | ? | ? | ? | ? | ? | ? | ? | |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | |
| Q15| Market pivot | C | ? | ? | ? | ? | ? | ? | ? | ? | ? | |
```

**Fórmula Coste Total**: `(tokens_in × 1) + (tokens_out × 6)`

## Resultado final esperado

**Archivo**: `TEST_BATTERY_RESULTS.md`
- Tabla principal (16 filas × 11 columnas)
- Estadísticas por Regime (media, min, max)
- Análisis narrativo (qué salió bien, qué falló, patrones)
- Recomendaciones para optimizaciones

---

# PARTE 4: METODOLOGÍA SIN CACHÉ

## Cómo simular "sesión nueva"

### Opción A: Usar fresh-path query (RECOMENDADO)
En cada pregunta, usar configuración que **NUNCA consulte** `queries/`:
```bash
# Simular: NO abrir MEMORY.md, NO buscar en queries/
# Sólo: index.md → MOC(s) → atoms → fragments
# Esto asegura que el sistema "descubre" la respuesta sin caché
```

### Opción B: Documentación separada
Crear archivo `FRESH_QUERY_PROTOCOL.md` que instruya explícitamente al LLM:
- NO consultar `queries/`
- Empezar siempre en `index.md`
- Seguir protocolo §4.2 de CLAUDE.md (steps 1-11)
- Registrar path: "fresh" vs "cached"

### Opción C: Timestamp isolation
Ejecutar todas las 15 preguntas en sesiones **separadas** (en contextos LLM diferentes) para garantizar cero contaminación.

**Decisión**: Usar **Opción A + B combinadas**: 
- Cada pregunta = contexto limpio
- Instrucción explícita de "fresh-path" en el prompt
- Registrar si hubo cache hit (debería ser 0)

---

# PARTE 5: MATRIZ DE OPTIMIZACIONES (ROI Score)

## ROI Calculation Formula

```
ROI_score = (Impact_value × Frequency) / Effort_cost

Impact_value:
  - Token reduction: 1 token saved ≈ 0.1 points
  - Quality improvement: +1 score point ≈ 10 points
  - Latency improvement: 1s saved ≈ 1 point

Frequency:
  - Per-query (always): ×5
  - Per-batch (rare): ×1

Effort_cost (tokens):
  - Easy: 0.5k tokens implementation
  - Medium: 2-5k tokens
  - Hard: 10-20k tokens
```

## Optimizaciones ordenadas por ROI

| # | Optimización | Effort | Token Impact | Quality Impact | Frequency | ROI Score | Priority |
|----|------------|--------|------------|----------|-----------|-----------|----------|
| 4 | Compact index.md | Medium (1k) | -2.3k/query | +0.5 score | per-query ×5 | **115** | 🔴 P1 |
| 2 | Response Contract | Low (0.5k) | -300-400 tokens | +0.8 score | per-query ×5 | **40** | 🟠 P2a |
| 17 | Lint pre-commit | Low (0.5k) | 0 (prevention) | +0.3 score | per-ingest ×1 | **6** | 🟡 P3a |
| 18 | YAML quoting | Low (0.5k) | 0 (prevention) | +0.2 score | per-ingest ×1 | **4** | 🟡 P3b |
| 1 | Pre-cache queries | Medium (3k) | -4k/hit (if hit) | 0 | when asked ×1 | **13** | 🟠 P2b |
| 3 | Budget escalation | Low (0.5k) | -500-1k | +0.3 score | per-query ×5 | **35** | 🟡 P3c |
| 6 | Query index | Medium (2k) | 0 (lookup speedup) | +0.2 score | per-query ×5 | **5** | 🟡 P4a |
| 8 | Backlinks sources | Medium (1k) | +50-200 (cost) | +0.5 score | per-query ×5 | **20** | 🟠 P2c |
| 12 | Gap detector | Medium (2k) | 0 (prevention) | +0.4 score | per-batch ×1 | **2** | 🔵 P5+ |
| 14 | Dual representation | Medium (1.5k labor) | -200 | +1.0 score | per-query ×5 | **33** | 🟡 P3d |
| 16 | Bidirectional links | Medium (1k) | +100-200 (cost) | +0.7 score | per-query ×5 | **28** | 🟠 P2d |

---

## Fases de optimización (ordenadas por ROI)

### **Fase BASELINE** (sesión 1)
- Ejecutar 15 preguntas, registrar baseline
- No aplicar optimizaciones
- Target: establecer línea base de calidad + tokens

### **Fase P1** (sesión 2)
- ✅ Item #4: Compact index.md (BLOQUEANTE)
- Expected impact: -2.3k tokens/query, revert ceilings
- Re-ejecutar 15 preguntas
- Objetivo: recuperar presupuesto de query

### **Fase P2a** (sesión 3)
- ✅ Item #2: Response Contract (experimental validation)
- Expected impact: -300-400 tokens, +0.8 score
- Re-ejecutar 15 preguntas
- Objetivo: validar tonal improvements

### **Fase P2b** (sesión 4, optional si hay tiempo)
- ✅ Item #1: Pre-cache 10-15 queries principales
- Expected impact: -4k on cache hits (if applicable)
- Nota: Este test usa fresh-path, así que NO habrá hits
- Decision: aplicar solo si vemos que Q11-Q15 se repiten conceptualmente

### **Fase P2c, P2d** (sesión 5-6)
- ✅ Item #8, #16: Backlinks (sources + atoms)
- Expected impact: +0.5-0.7 score (prevents fusion errors), +100-200 token cost
- Trade-off: slight overhead for better graph connectivity

### **Fase P3a-d** (sesión 7, batch)
- ✅ Items #17, #18, #3, #14: Lint + Response refinement
- Expected impact: prevention + schema improvements
- Bundled together (low effort)

---

# PARTE 6: ESTRUCTURA DE RESULTADOS EN REPO

## Archivos a crear/actualizar

### 1. `TEST_BATTERY_RESULTS.md`
**Contenido**:
- Tabla principal (15 preguntas × 8 dimensiones)
- Estadísticas agregadas por Regime
- Gráficos ASCII de tendencias
- Análisis narrativo

**Updated después de**: Baseline + cada fase

### 2. `TEST_BATTERY_LOG.csv`
**Formato**: Máquina-legible para tracking temporal

```csv
phase,date,question_num,regime,d1_spanish,d2_quality,d3_readability,d7_clarity,d8_score,tokens_in,tokens_out,efficiency,cache_hit
BASELINE,2026-04-24,Q1,A,9.0,8.5,8.0,8.0,8.4,3800,950,0.25,0
BASELINE,2026-04-24,Q2,A,9.2,8.8,8.5,8.2,8.7,3900,1100,0.28,0
...
P1,2026-04-25,Q1,A,9.0,8.7,8.2,8.1,8.5,1500,950,0.63,0
```

### 3. `TEST_BATTERY_ANALYSIS.md`
**Contenido**:
- Comparativa ANTES/DESPUÉS por optimización
- Qué mejoró, qué empeoró
- ROI validado vs esperado
- Recomendaciones para siguiente fase

### 4. `FRESH_QUERY_PROTOCOL.md`
**Contenido**:
- Instrucciones explícitas para ejecutar preguntas sin caché
- Template de prompt para cada pregunta
- Cómo registrar tokens reales
- Cómo verificar que fue fresh-path

---

# PARTE 7: CÓMO EJECUTAR CADA SESIÓN

## Checklist por sesión

### Pre-ejecución
- [ ] Leer la pregunta
- [ ] Identificar Regime esperado
- [ ] Preparar contexto LIMPIO (sin caché)
- [ ] Abrir nueva sesión OR protocolizar fresh-path

### Ejecución
- [ ] Hacer pregunta como si fuera usuario nuevo
- [ ] Responder SIGUIENDO §4.2 de CLAUDE.md (steps 1-11)
- [ ] NO usar caché de queries/
- [ ] Registrar tokens_in (load CLAUDE.md + index.md + MOC + atoms)
- [ ] Registrar tokens_out (respuesta completa)
- [ ] Copiar respuesta completa a archivo temporal

### Post-ejecución
- [ ] Evaluar respuesta en las 7 dimensiones (1-10)
- [ ] Llenar fila de tabla
- [ ] Añadir nota cualitativa si hay insight
- [ ] Guardar respuesta completa en `responses/<Q#>_baseline.md` (o `Q#_P1.md` para fase P1)

---

# PARTE 8: TIMELINE ESTIMADO

| Fase | Qué | Sesiones | Horas | Notas |
|------|-----|----------|-------|-------|
| BASELINE | 15 preguntas fresh | 1-2 | 4-6h | Todo en paralelo o secuencial |
| P1 | Compact index.md + re-ejecutar | 2 | 4-5h | Implementación (1h) + batch de preguntas (3-4h) |
| P2a | Response Contract + re-ejecutar | 1-2 | 3-4h | Validación + batch |
| P2b-d | Optional, si ROI justifica | 2-3 | 4-6h | Backlinks + linking |
| P3 batch | Lint + schema + pre-cache | 1-2 | 3-4h | Bundled |
| **TOTAL** | **Línea base + 3-4 ciclos** | **~8-10** | **~20-25h** | Asumiendo 2-3 horas por sesión |

---

# PARTE 9: CÓMO CAMBIAR PLAN SI ES NECESARIO

## Criterios de parada

Si después de **Fase P1** descubrimos:
- [ ] Score general cae (indica regresión) → parar y debuggear
- [ ] Tokens no bajan como esperado → revisar assumption
- [ ] 30%+ de preguntas "fail" (score <6) → replantear approach

## Criterios de éxito

Por cada optimización:
- [ ] Expected impact ≥ 80% de lo predicho
- [ ] Score general sube O tokens bajan sin degradar score
- [ ] Al menos 10/15 preguntas mejoran o se mantienen

---

# PARTE 10: CHECKLIST DE IMPLEMENTACIÓN

### Antes de empezar BASELINE:

- [ ] Crear carpeta `test_battery/` en repo
- [ ] Crear plantilla de respuesta (`response_template.md`)
- [ ] Crear `FRESH_QUERY_PROTOCOL.md` (paso-a-paso)
- [ ] Crear hoja de seguimiento (CSV template)
- [ ] Refrescar conocimiento de §4.2 CLAUDE.md (regime classification)
- [ ] Verificar que vault está en estado conocido (no cambios mid-test)

### Antes de cada FASE:

- [ ] Revisar qué optimización se aplica
- [ ] Crear rama/commit si aplica
- [ ] Implementar optimización (o al menos documentar cambios)
- [ ] Verificar que cambio está activo
- [ ] Ejecutar batch de 15 preguntas
- [ ] Recolectar datos
- [ ] Analizar y documentar

---

# RESUMEN EJECUTIVO

**Este plan garantiza**:
1. ✅ **Reproducibilidad**: Mismas 15 preguntas, fresh-path siempre, sin caché
2. ✅ **Medición rigurosa**: 8 dimensiones por respuesta, ROI calculado
3. ✅ **Iteración controlada**: Cambios aislaods, antes/después claro
4. ✅ **Documentación**: Log completo, CSV para análisis, narrativa de aprendizajes
5. ✅ **Decisiones data-driven**: ROI score ordena prioridades, no intuición

**Próximos pasos**:
1. Aprobar esta planificación
2. Crear archivos/carpetas en repo
3. Ejecutar BASELINE (sesión 1-2)
4. Analizar resultados
5. Decidir qué optimizaciones aplicar en orden

---

**END OF TEST_BATTERY_PLAN**
