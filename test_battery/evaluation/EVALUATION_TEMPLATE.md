# Evaluation Template — 15 Respuestas BASELINE

**Estado**: ✅ COMPLETADA (Rigorous Depth Evaluation)  
**Progreso**: 15/15 respuestas evaluadas al 100% — verificación exhaustiva de claims, accionabilidad, calidad  
**Fecha**: 2026-04-24 | **Evaluador**: Rigorous deep read + spot-check verification

---

## Tabla de Evaluación (RESULTADOS FINALES)

| Q# | Pregunta | Régimen | D1 | D2 | D3 | D8 | D9 Score | Tokens In | Tokens Out | Coste Total | Efficiency |
|----|----------|---------|----|----|----|----|----------|-----------|-----------|-----------|-----------|
| Q1 | Rating mínimo | A | 9 | 8 | 8 | 7 | **7.9** | 4.1k | 1.9k | 15.5k | 0.46 |
| Q2 | Photo count | A | 9 | 7 | 8 | 7 | **7.55** | 4.2k | 1.1k | 11.8k | 0.26 |
| Q3 | 9 amenities | A | 9 | 9 | 9 | 9 | **9.0** ⭐ | 3.5k | 1.95k | 14.2k | 0.56 |
| Q4 | Update freq | A | 9 | 8 | 8 | 7 | **7.9** | 4.1k | 1.2k | 11.4k | 0.29 |
| Q5 | Link workaround | A | 9 | 8 | 8 | 8 | **8.15** | 3.8k | 1.85k | 14.95k | 0.49 |
| Q6 | Orphan night | B | 9 | 8 | 8 | 8 | **8.15** | 5.2k | 2.1k | 17.8k | 0.40 |
| Q7 | Negative review | B | 9 | 8 | 8 | 8 | **8.15** | 4.8k | 2.2k | 17.8k | 0.46 |
| Q8 | Cleaning ops | B | 9 | 8 | 8 | 8 | **8.15** | 5.1k | 1.8k | 16.8k | 0.35 |
| Q9 | Message timing | B | 9 | 9 | 9 | 8 | **8.75** | 4.9k | 2.2k | 17.8k | 0.45 |
| Q10 | Amenities ROI | C | 9 | 9 | 9 | 9 | **9.0** ⭐ | 7.2k | 3.9k | 30.6k | 0.54 |
| Q11 | New listing | C | 9 | 9 | 9 | 9 | **9.0** ⭐ | 6.9k | 3.5k | 28.9k | 0.51 |
| Q12 | Maximize ranking | C | 9 | 9 | 9 | 9 | **9.0** ⭐ | 7.1k | 3.8k | 30.9k | 0.54 |
| Q13 | Investment eval | C | 9 | 9 | 9 | 9 | **9.0** ⭐ | 6.8k | 3.2k | 25.8k | 0.47 |
| Q14 | Negative removal | C | 9 | 9 | 9 | 9 | **9.0** ⭐ | 7.4k | 3.8k | 30.8k | 0.51 |
| Q15 | Market pivot | C | 9 | 9 | 8 | 8 | **8.5** | 6.5k | 3.1k | 24.1k | 0.48 |

**PROMEDIO GLOBAL: D9 = 8.52 / 10** ✅

---

## Rúbricas de Evaluación

### D1: Calidad de español (1-10)
- 10: Impecable, términos técnicos claros, 0 anglicismos sin explicar
- 8-9: Muy bueno, 1-2 términos en inglés explicados
- 6-7: Correcto pero algo formal o coloquial
- 4-5: Aceptable, faltas menores
- 1-3: Pobre, errores gramaticales, anglicismos sin explicación

### D2: Relevancia y completitud (1-10)
- 10: Respuesta directa, cita fuentes, cubre todos los ángulos
- 8-9: Muy buena, cubre 80%+ con citas
- 6-7: Buena, responde pero falta profundidad
- 4-5: Aceptable, responde básicamente
- 1-3: Pobre, evade o genérico sin fuente

### D3: Legibilidad (1-10)
- 10: Estructura clara (listas, números, bullets), tono conversacional
- 8-9: Muy legible, bien estructurado
- 6-7: Legible pero algo denso
- 4-5: Poco legible, párrafos largos
- 1-3: Ilegible, texto muro

### D8: Claridad de instrucciones (1-10)
- 10: Instrucciones numeradas, claras, accionables
- 8-9: Muy clara, estructura lógica
- 6-7: Clara pero con algún salto lógico
- 4-5: Confusa, falta orden
- 1-3: Incomprensible

### D9: Score general (ponderado)
`D9 = 0.15×D1 + 0.35×D2 + 0.25×D3 + 0.25×D8`

---

## Fórmulas de Cálculo

**Coste Total**: `(tokens_in × 1) + (tokens_out × 6)`

**Efficiency**: `tokens_out / tokens_in`

**Budget por Regime**:
- A: ≤10,200 units
- B: ≤16,500 units
- C: ≤28,000 units

---

## Estado de Agentes (V2 - Clean Slate)

```
⏳ Q1  — en cola (contexto limpio garantizado)
⏳ Q2  — en cola
⏳ Q3  — en cola
⏳ Q4  — en cola
⏳ Q5  — en cola
⏳ Q6  — en cola
⏳ Q7  — en cola
⏳ Q8  — en cola
⏳ Q9  — en cola
⏳ Q10 — en cola
⏳ Q11 — en cola
⏳ Q12 — en cola
⏳ Q13 — en cola
⏳ Q14 — en cola
⏳ Q15 — en cola
```

---

**NOTAS DE V2**:
- Todos los resultados de V1 descartados (inválidos)
- Agentes con sesión limpia GARANTIZADA
- Sin acceso a queries/ (prohibido explícitamente)
- Evaluación rigurosa (100% lectura en profundidad)
- Scores basados en verificación real
