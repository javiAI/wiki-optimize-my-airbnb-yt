# Agent Instructions — Test Battery Parallel Execution V2

**CRITICAL**: Clean Session Guarantee  
**Para**: 15 Agentes independientes (sesiones COMPLETAMENTE LIMPIAS)  
**Objetivo**: Generar respuestas a 15 preguntas (protocolo fresh-path + contexto CERO)  
**Importante**: CADA AGENTE es sesión nueva = SIN CACHÉ, SIN CONTEXTO PREVIO, SIN ACCESO A QUERIES

---

# ⚠️ SESIÓN LIMPIA — OBLIGATORIO ABSOLUTO

**TE ESTÁS CONECTANDO A ESTA SESIÓN POR PRIMERA VEZ.**

No tienes memoria de sesiones anteriores. No tienes acceso a conversaciones previas. No tienes caché. Eres como si acabaras de abrir un navegador nuevo en una computadora nueva.

## Restricción ABSOLUTE: Prohibido queries/

**BAJO NINGUNA CIRCUNSTANCIA puedes:**
- Abrir `$VAULT_PATH/queries/`
- Buscar en `queries/`
- Leer archivos previos guardados
- Acceder a síntesis cacheadas
- Reutilizar respuestas anteriores

Si por accidente intentas acceder a `queries/`, **DETENTE INMEDIATAMENTE** y continúa sin esa carpeta.

---

# INSTRUCCIONES PARA CADA AGENTE

## Setup inicial (OBLIGATORIO)

```bash
# 1. Cargar config del vault (SOLO para acceder a ruta)
source /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/scripts/config.sh
export VAULT_PATH=/Users/javierabrilibanez/Dev/obsidian_vaults/optimize-my-airbnb-yt

# 2. Verificar que el vault existe (NO verificar queries/)
test -d "$VAULT_PATH/notes" && echo "✅ Vault accesible" || echo "❌ Error"
```

## Protocolo FRESH-PATH V2 (CONTEXTO CERO)

```
Step 1: Leer pregunta asignada (SOLO la pregunta, nada más)
Step 2: PROHIBIDO ABSOLUTO: NO abrir queries/ — JAMÁS
Step 3: Empezar SOLO en $VAULT_PATH/index.md
Step 4: Identificar Regime (A/B/C) según palancas en la pregunta
Step 5: Abrir MOC(s) correspondiente(s) — SIN LEER QUERIES
Step 6: Seleccionar atoms candidatos (máximo según ceiling del regime)
Step 7: Leer SOLO esos atoms seleccionados, nada más
Step 8: Si necesitas fragment específico de source, usar offset/limit
Step 9: Responder DESDE CERO, citando [[notes/atom-slug]] con locator
Step 10: Guardar respuesta en archivo ASIGNADO ($VAULT_PATH/queries/ PROHIBIDO — usar test_battery/responses/ en su lugar)
Step 11: Registrar metadatos (tokens, atoms consultados)
```

## Template de respuesta (GUARDAR EN test_battery/responses/, NO en vault)

```markdown
# Q[N]: [Título corto de la pregunta]

**Pregunta**: [Copia la pregunta exacta del listado abajo]

**Régimen**: A / B / C  
**Agente**: Agent-Q[N]  
**Fecha**: 2026-04-24  

---

## Respuesta

[TU RESPUESTA COMPLETA — máximo 600-1000 palabras según regime]

[Estructura según preferencia, pero DEBE SER legible para un host real]
[Cita TODOS los atoms con [[notes/slug]] + locator preciso]
[Verificar: ¿un usuario de Airbnb confiaría en esto? ¿tiene evidencia?]

---

## Metadatos

- **Tokens input**: (lineas leídas × 4.5 promedio)
- **Tokens output**: (lineas de respuesta × 4.5 promedio)
- **Atoms consultados**: 
  - [[notes/atom-1]] (locator específico si aplica)
  - [[notes/atom-2]] (locator específico si aplica)
  - ...
- **MOC(s) utilizados**: MOC/tema1, MOC/tema2
- **Régimen estimado**: A / B / C
- **Auto-evaluación**:
  - ¿Todos los claims citados con atom+locator? SÍ / NO
  - ¿Respuesta accionable para un host real? SÍ / NO
  - ¿Cero inventados/alucinaciones? SÍ / NO
```

**⚠️ DÓNDE GUARDAR**:
- **CORRECTO**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q[N].md`
- **INCORRECTO**: vault queries/ (prohibido)
- **INCORRECTO**: cualquier otra ubicación

---

# LAS 15 PREGUNTAS (copia la que corresponde a tu agente)

## Q1 (Agente-Q1)
**Pregunta**: ¿Cuál es el rating mínimo que debo tener para que los guests me encuentren sin problemas en búsqueda de Airbnb?

**Régimen esperado**: A (1 palanca)  
**Archivo de salida**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q1.md`

---

## Q2 (Agente-Q2)
**Pregunta**: ¿Cuántas fotos debería subir de mi listing de 2 dormitorios?

**Régimen esperado**: A (1 palanca)  
**Archivo de salida**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q2.md`

---

## Q3 (Agente-Q3)
**Pregunta**: ¿Cuáles son los 9 amenities básicos que TODOS los guests esperan?

**Régimen esperado**: A (1 palanca)  
**Archivo de salida**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q3.md`

---

## Q4 (Agente-Q4)
**Pregunta**: ¿Cada cuánto tiempo debería actualizar mi descripción del listing?

**Régimen esperado**: A (1 palanca)  
**Archivo de salida**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q4.md`

---

## Q5 (Agente-Q5)
**Pregunta**: Airbnb no me permite poner links de YouTube en la descripción, ¿cómo hago para que los guests vean mi video?

**Régimen esperado**: A (1 palanca)  
**Archivo de salida**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q5.md`

---

## Q6 (Agente-Q6)
**Pregunta**: Tengo una noche huérfana (miércoles) en temporada alta sin reserva. ¿Cómo debería fijar el precio?

**Régimen esperado**: B (3-4 palancas)  
**Archivo de salida**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q6.md`

---

## Q7 (Agente-Q7)
**Pregunta**: Acabo de recibir una review negativa que bajó mi rating. ¿Qué pasos sigo para recuperarme?

**Régimen esperado**: B (3-4 palancas)  
**Archivo de salida**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q7.md`

---

## Q8 (Agente-Q8)
**Pregunta**: Estoy empezando con 2 propiedades y quiero contratar limpieza. ¿Cómo estructuro esto?

**Régimen esperado**: B (4-5 palancas)  
**Archivo de salida**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q8.md`

---

## Q9 (Agente-Q9)
**Pregunta**: ¿En qué momentos del stay debo enviar mensajes al guest para maximizar que me dejen buena review?

**Régimen esperado**: B (4 palancas)  
**Archivo de salida**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q9.md`

---

## Q10 (Agente-Q10)
**Pregunta**: ¿Cuáles son los amenities que me dan más retorno por el dinero invertido?

**Régimen esperado**: B (3-4 palancas)  
**Archivo de salida**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q10.md`

---

## Q11 (Agente-Q11)
**Pregunta**: Acabo de crear un listing nuevo sin reviews. ¿Cuál es la estrategia COMPLETA para arrancar y conseguir buenos reviews rápido?

**Régimen esperado**: C (6-8 palancas)  
**Archivo de salida**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q11.md`

---

## Q12 (Agente-Q12)
**Pregunta**: ¿Cuál es el plan paso a paso para maximizar mi posición en el algoritmo de búsqueda de Airbnb?

**Régimen esperado**: C (7+ palancas)  
**Archivo de salida**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q12.md`

---

## Q13 (Agente-Q13)
**Pregunta**: Estoy evaluando comprar una propiedad nueva. ¿Cuál es el framework para decidir si es un buen deal o no?

**Régimen esperado**: C (6-7 palancas)  
**Archivo de salida**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q13.md`

---

## Q14 (Agente-Q14)
**Pregunta**: Tengo una review negativa injusta que me está dañando el rating. ¿Cuáles son TODAS mis opciones y cuál funciona?

**Régimen esperado**: C (5+ palancas con contradicciones)  
**Archivo de salida**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q14.md`

---

## Q15 (Agente-Q15)
**Pregunta**: Mi mercado está muy saturado. ¿Debo irme, pivotear, o doble-bajar precios? ¿Cómo lo decido?

**Régimen esperado**: C (7+ palancas estratégicas)  
**Archivo de salida**: `/Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/test_battery/responses/Q15.md`

---

# CHECKLIST ANTES DE ENTREGAR

- [ ] Pregunta copiada y entendida
- [ ] Vault path verificado
- [ ] Protocolo FRESH-PATH seguido (sin queries/)
- [ ] Respuesta en ESPAÑOL (sin anglicismos sin explicar)
- [ ] Todos los facts citados con [[notes/...]]
- [ ] Metadatos completados (tokens, atoms)
- [ ] Archivo guardado en ruta correcta (Q#.md)
- [ ] Auto-evaluación completada

---

# NOTAS CRÍTICAS

⚠️ **SESIÓN LIMPIA**: No tienes contexto previo. Esto es por diseño.  
⚠️ **FRESH-PATH OBLIGATORIO**: NO uses queries/. Siempre fresco.  
⚠️ **MÁQUINA LEGIBLE**: El archivo se va a parsear después — respeta el formato.  
⚠️ **ESPAÑOL COMPLETO**: Aunque menciones "Airbnb" o "PriceLabs", explicar o usar en español.  
⚠️ **ACCIONABLE**: La respuesta debe ser útil para un host real.

---

**Gracias por ejecutar tu pregunta asignada. Tus respuestas son datos REALES para el sistema.**
