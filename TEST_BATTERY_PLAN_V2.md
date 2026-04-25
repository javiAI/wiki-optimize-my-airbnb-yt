---
name: Test Battery Plan V2 — Parallel Agent Execution
description: Batería de 15 preguntas ejecutadas por 15 agentes en paralelo (sesiones limpias), luego evaluación centralizada
date: 2026-04-24
---

# Test Battery Plan V2 — Ejecución con Agentes Paralelos

## Cambios respecto a V1

1. ✅ **Respuestas guardadas visiblemente**: `test_battery/responses/Q<n>.md`
2. ✅ **Agentes paralelos**: 15 agentes simultáneos (no secuencial)
3. ✅ **Sesiones limpias**: Cada agente = contexto nuevo, sin caché
4. ✅ **Evaluación centralizada**: Claude Code evalúa todas después

---

# PARTE 1: LAS 15 PREGUNTAS

## Bloque A: Fácil (Regime A) — Q1 a Q5

| Q# | Pregunta | Palancas | Atoms esperados |
|----|----|----------|---|
| Q1 | ¿Cuál es el rating mínimo para que los guests me encuentren? | 1 | reviews--four-point-eight-threshold |
| Q2 | ¿Cuántas fotos debería subir para 2 dormitorios? | 1 | listing-optimization--photo-count-by-bedroom |
| Q3 | ¿Cuáles son los 9 amenities básicos? | 1 | listing-optimization--essential-amenities-checklist |
| Q4 | ¿Cada cuánto actualizar mi descripción? | 1 | listing-optimization--reoptimize-biannual |
| Q5 | Airbnb no permite links de YouTube, ¿cómo hago? | 1 | listing-optimization--airbnb-does-not-accept-direct-links |

## Bloque B: Medio (Regime B) — Q6 a Q10

| Q# | Pregunta | Palancas | Atoms esperados |
|----|----|----------|---|
| Q6 | ¿Cómo fijar precio en noche huérfana (miércoles) en temporada alta? | 3-4 | pricing--orphan-nights, pricing--seasonality-strategy |
| Q7 | Acabo de recibir review negativa, ¿pasos para recuperarme? | 3-4 | reviews--more-dilutes-negative, reviews--reciprocity |
| Q8 | Contrato limpieza para 2 propiedades, ¿cómo estructuro? | 4-5 | cleaning-ops--(multiple) |
| Q9 | ¿Cuándo enviar mensajes para maximizar buena review? | 4 | reviews--four-days-pre-checkin, reviews--reciprocity-post-checkout |
| Q10 | ¿Cuál amenity me da más ROI por dinero invertido? | 3-4 | listing-optimization--unique-amenities, listing-optimization--amenities-match-price |

## Bloque C: Difícil (Regime C) — Q11 a Q15

| Q# | Pregunta | Palancas | Atoms esperados |
|----|----|----------|---|
| Q11 | Listing nuevo sin reviews, ¿estrategia COMPLETA para arrancar? | 6-8 | Multiple (pricing, reviews, listing, hospitality) |
| Q12 | ¿Plan paso a paso para maximizar posición en algoritmo Airbnb? | 7+ | ranking--factors-confirmed, listing-optimization--big-three |
| Q13 | Evalúo compra nueva propiedad, ¿framework de decisión? | 6-7 | investing--how-to-evaluate-deals, market-selection |
| Q14 | Review negativa injusta, ¿TODAS mis opciones y cuál funciona? | 5+ | reviews--removal-process-broken-2025, reviews--refund-for-review-trade, reviews--removal-call-playbook |
| Q15 | Mercado saturado, ¿irme, pivotar, o bajar precio? ¿Cómo decido? | 7+ | market-selection, ranking, pricing (síntesis) |

---

# PARTE 2: ESTRUCTURA DE RESPUESTAS

## Carpeta: `test_battery/responses/`

Cada pregunta = un archivo visible y legible:

```
responses/
├── Q1.md              # Respuesta completa a Q1
├── Q2.md              # Respuesta completa a Q2
├── ...
└── Q15.md             # Respuesta completa a Q15
```

**Formato de cada archivo**:
```markdown
# Q1: Rating mínimo para encontrarse

**Pregunta**: ¿Cuál es el rating mínimo que debo tener para que los guests me encuentren?

**Agente**: Agent-Q1 (sesión limpia)  
**Fecha**: 2026-04-24  
**Regime**: A

---

## Respuesta

[RESPUESTA COMPLETA AQUÍ]

---

## Metadatos para evaluación

- Tokens input: (calculado por agente)
- Tokens output: (calculado por agente)
- Atoms consultados: (listados por agente)
```

---

# PARTE 3: PROTOCOLO PARA AGENTES

## Instrucciones que recibe CADA agente

Cada agente recibe esto (sin contexto previo, sesión limpia):

```
CONTEXTO DEL PROYECTO:
- Eres un agente especializado en STR/Airbnb
- Tienes acceso a un vault de Obsidian con 248 atoms sobre optimización de listings
- El vault está en: /Users/javierabrilibanez/Dev/obsidian_vaults/optimize-my-airbnb-yt/

TU TAREA:
Responde ESTA PREGUNTA siguiendo protocolo FRESH-PATH (sin caché):

[PREGUNTA ASIGNADA]

PROTOCOLO FRESH-PATH (obligatorio):
1. NO consultar queries/ (archivo cacheado)
2. Empezar en index.md
3. Identificar MOC(s) relevante(s)
4. Leer solo atoms necesarios (4-15 según Regime)
5. Responder citando [[atom]] con locator
6. NO inventar contenido

FORMATO DE RESPUESTA:
```markdown
# [Tu respuesta aquí]

---
## Metadatos
- **Tokens input**: [cuenta lineas de archivo leído × 11.5]
- **Tokens output**: [cuenta lineas de tu respuesta × 11.5]
- **Atoms consultados**: [[notes/atom1]], [[notes/atom2]], ...
- **Regime estimado**: A/B/C
```

DONDE GUARDAR:
Escribe tu respuesta EN ESTE ARCHIVO EXACTO:
/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q[N].md

(reemplaza [N] con tu número: Q1, Q2, ... Q15)

IMPORTANTE:
- Sesión limpia: no tienes contexto anterior
- Fresh-path siempre: no busques queries/
- Respuesta en ESPAÑOL completamente
- Máximo 600-1000 palabras (según Regime)
- Evalúa tu propia respuesta:
  - ¿Español impecable? (sí/no)
  - ¿Citados todos los facts? (sí/no)
  - ¿Respuesta accionable? (sí/no)
```

---

# PARTE 4: EJECUCIÓN PARALELA

## 15 agentes lanzados simultáneamente

```bash
Agent-Q1  → Pregunta Q1 → test_battery/responses/Q1.md
Agent-Q2  → Pregunta Q2 → test_battery/responses/Q2.md
Agent-Q3  → Pregunta Q3 → test_battery/responses/Q3.md
...
Agent-Q15 → Pregunta Q15 → test_battery/responses/Q15.md
```

**Ventaja**: Todas las respuestas en ~5 minutos (paralelo) vs ~30 minutos (secuencial)

**Garantía de sesión limpia**: Cada agente = contexto aislado, sin caché de sesiones anteriores

---

# PARTE 5: EVALUACIÓN CENTRALIZADA (después de que terminen agentes)

**Quién**: Claude Code (yo)  
**Cuándo**: Después de que los 15 agentes terminen  
**Qué**: Leer cada respuesta en `test_battery/responses/Q*.md` y evaluar

## Dimensiones de evaluación (1-10)

- **D1**: Calidad de español
- **D2**: Relevancia y completitud
- **D3**: Legibilidad
- **D4**: Tokens input (conteo)
- **D5**: Tokens output (conteo)
- **D6**: Coste total = (D4×1) + (D5×6)
- **D7**: Efficiency = D5/D4
- **D8**: Claridad de instrucciones
- **D9**: Score general = 0.15×D1 + 0.35×D2 + 0.25×D3 + 0.25×D8

## Output de evaluación

```
test_battery/evaluation/
├── EVALUATION_RESULTS.md    # Tabla 15×9 + análisis
├── REGIME_ANALYSIS.md        # Stats por A/B/C
└── BLOCKER_FOR_PHASE_P1.md   # Decisión requerida
```

---

# PARTE 6: TIMELINE

| Fase | Qué | Quién | Tiempo |
|------|-----|-------|--------|
| 1 | Lanzar 15 agentes paralelos | Claude Code | 1 min |
| 2 | Ejecutar preguntas | 15 agentes | ~5-10 min |
| 3 | Guardar respuestas | 15 agentes | automático |
| 4 | Evaluar 15 respuestas | Claude Code | ~20 min |
| 5 | Generar reporte | Claude Code | ~10 min |
| 6 | Decidir P1 | Usuario | ~5 min |
| **TOTAL** | **BASELINE COMPLETO** | — | **~1 hora** |

---

# PARTE 7: DIFERENCIAS V1 → V2

| Aspecto | V1 | V2 |
|--------|----|----|
| Respuestas generadas por | Claude Code (yo) | 15 agentes paralelos |
| Visibilidad de respuestas | ❌ No guardadas | ✅ Archivos Q*.md visibles |
| Tiempo ejecución | Secuencial (~30 min) | Paralelo (~5-10 min) |
| Realidad de datos | Simulada | Real (agentes reales) |
| Evalúa | Yo (durante generación) | Yo (después, centralizado) |
| Sesión limpia | Auto-garantizado | Garantizado por aislamiento |

---

# PRÓXIMO PASO

1. ✅ Este plan aprobado
2. ⏳ Lanzar 15 agentes en paralelo
3. ⏳ Esperar respuestas
4. ⏳ Evaluar respuestas
5. ⏳ Generar reporte BASELINE
6. ⏳ Bloqueador: decisión P1

**¿Comienzo?**
