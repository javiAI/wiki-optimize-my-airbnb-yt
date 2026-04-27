Eres un EVALUADOR EXTERNO. NO eres uno de los 20 agentes de testing.
Tu tarea: evaluar las 20 respuestas generadas por agentes para el label "O4" (run 1),
aplicando una rúbrica de 5 dimensiones.

REGLAS ABSOLUTAS:
1. SOLO LEER de:
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/CLAUDE.md (para entender el response contract §10.7)
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q1.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q2.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q3.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q4.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q5.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q6.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q7.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q8.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q9.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q10.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q11.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q12.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q13.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q14.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q15.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q16.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q17.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q18.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q19.json
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/Q20.json
2. SOLO ESCRIBIR en EXACTAMENTE esta ruta:
   /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/evaluation.json
3. PROHIBIDO escribir en cualquier otro lugar (especialmente PROHIBIDO en la bóveda).
4. PROHIBIDO leer otros prompts/evaluaciones/comparisons.
5. NO uses contexto de sesiones anteriores.

RÚBRICA (cada dimensión 0-10 entero):

1. completeness (peso 25%) — ¿La respuesta cubre la pregunta? ¿Faltan caveats relevantes?
   - 10: cobertura completa, caveats relevantes presentes
   - 7-9: cobertura buena, falta algún detalle menor
   - 4-6: cobertura parcial, faltan elementos importantes
   - 0-3: respuesta incompleta o tangencial

2. accuracy (peso 25%) — ¿Hechos correctos? ¿Citas válidas (las atoms/sources mencionadas existen y dicen lo que se cita)?
   - 10: todo correcto, citas válidas y bien usadas
   - 7-9: mayormente correcto, errores menores
   - 4-6: errores notables o citas dudosas
   - 0-3: errores graves o invenciones
   Nota: si no puedes verificar una cita (no abras los atoms), evalúa por consistencia interna y plausibilidad.

3. spanish_purity (peso 15%) — Español puro. Solo inglés permitido para:
   - Nombres propios: PriceLabs, Airbnb, Booking, Vrbo, AllTheRooms, AirDNA, Wheelhouse, Beyond, Hostfully, Hospitable, Guesty, OwnerRez, NoiseAware, Minut, Google, YouTube
   - Tech estandarizada: WiFi, PMS, API, URL, OS, JSON, YAML, SEO
   - Features Airbnb: Superhost, Aircover, Instant Book, Stays, Co-Host
   PENALIZAR (deberían estar en español):
   - "host" → anfitrión
   - "guest" → huésped
   - "review/reviews" → reseña/reseñas
   - "amenity/amenities" → comodidad/comodidades
   - "rating" → calificación
   - "booking" como sustantivo → reserva
   - "listing" → anuncio (matiz: aceptable si se usa como término técnico de Airbnb explícitamente)
   - "check-in/check-out" → entrada/salida (matiz: aceptable si es término operativo conocido)
   Escala:
   - 10: español puro, whitelist respetada
   - 7-9: ≤2 anglicismos evitables
   - 4-6: 3-5 anglicismos evitables
   - 0-3: 6+ anglicismos o spanglish constante

4. tone (peso 15%) — Humano, profesional, con calidez. Consultor que se preocupa por el host.
   PREMIAR: directo, empático, segunda persona consistente (tú o usted), substantivo, calidez sutil.
   PENALIZAR: robótico, "cabe destacar", "es importante mencionar", "en este sentido", filler, corporate-speak, frío, demasiado casual/slangy, condescendiente.
   - 10: humano + profesional + cálido en equilibrio
   - 7-9: mayormente bien, algún tropiezo menor
   - 4-6: robótico, frío, o demasiado formal
   - 0-3: tono inadecuado

5. format_compliance (peso 20%) — Sigue §10.7 response contract:
   - Steps numerados ejecutables (para tactical)
   - Una cita [[atom]] por step
   - ≤600 palabras (tactical) o ≤1000 (strategic)
   - Sin intro innecesaria
   - Sin filler adjectives ni summaries finales
   - Números siempre con source_id
   - 10: compliance total
   - 7-9: compliance bueno, alguna desviación menor
   - 4-6: compliance parcial
   - 0-3: no sigue el contract

OUTPUT FORMAT (JSON exacto):
{
  "label": "O4",
  "run": 1,
  "rubric_version": "1.0",
  "evaluator_notes": "<2-3 líneas con observaciones globales del batch>",
  "evaluations": {
    "Q1": {
      "completeness": <0-10>,
      "accuracy": <0-10>,
      "spanish_purity": <0-10>,
      "tone": <0-10>,
      "format_compliance": <0-10>,
      "notes": "<1-2 líneas con lo más destacable>",
      "violations": ["<issue 1>", "<issue 2>"]
    },
    "Q2": {...},
    ... (Q1 hasta Q20)
  }
}

PROCEDIMIENTO:
1. Lee /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/CLAUDE.md (sección §10.7) para internalizar el response contract.
2. Lee los 20 archivos de respuestas listados arriba.
3. Evalúa cada respuesta contra la rúbrica.
4. Escribe el JSON completo (20 evaluaciones) en: /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4/run-1/evaluation.json

Procede ahora.
