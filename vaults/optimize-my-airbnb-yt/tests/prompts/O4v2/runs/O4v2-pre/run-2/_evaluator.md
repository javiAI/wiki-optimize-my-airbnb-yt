Eres un evaluador externo. Tu tarea es evaluar 15 respuestas a preguntas de hosts de Airbnb/Booking, generadas por un agente que opera sobre una bóveda LLM.

ESTAS RESPUESTAS PRUEBAN UNA OPTIMIZACIÓN ESPECÍFICA: O4v2 (smart contradiction resolver + auto-curation + temporal narrator). La rúbrica es CUSTOM, distinta de la rúbrica estándar de 5 dimensiones.

REGLAS DE LECTURA:
1. SOLO puedes LEER de:
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4v2-pre/run-2/Q*.json (las 15 respuestas a evaluar)
   - /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/prompts/O4v2/questions.yaml (battery con expected_atoms / expected_resolution / expected_temporal_narrative por pregunta)
   - /Users/javierabrilibanez/Dev/obsidian_vaults/optimize-my-airbnb-yt/meta/contradictions.md (referencia de conflictos documentados)
   - /Users/javierabrilibanez/Dev/obsidian_vaults/optimize-my-airbnb-yt/notes/*.md (verificación de atoms citados)
   - /Users/javierabrilibanez/Dev/obsidian_vaults/optimize-my-airbnb-yt/MOC/*.md (verificación de topics)
2. PROHIBIDO leer otros prompts o respuestas fuera de la ruta indicada en regla 1.
3. NO uses contexto de sesiones anteriores.

REGLAS DE ESCRITURA:
4. Escribes UN único archivo JSON en EXACTAMENTE esta ruta:
   /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4v2-pre/run-2/evaluation.json

RÚBRICA CUSTOM (6 dimensiones, escala 1-10):

| Dim | Peso | Qué mide |
|---|---|---|
| **conflict_detection** | 20% | ¿El agente detecta los conflictos que SÍ existen (true positives) y NO inventa los que no existen (true negatives)? |
| **resolution_clarity** | 25% | ¿El criterio de resolución aplicado es correcto + el rationale es coherente con la jerarquía (temporal_supersession → contextual_scope → confidence_tier → authority_tier → specificity_tier)? |
| **temporal_narrative** | 20% | Cuando hay componente temporal: ¿narra la evolución ("Antes X, desde Y se hace Z, hoy Z")? Cuando NO hay temporal: penalizar si fuerza la narrativa. |
| **context_awareness** | 15% | ¿Reconoce que dos atoms pueden ser compatibles por scope distinto en lugar de tratar todo conflicto como direct contradiction? |
| **proposed_contradiction_quality** | 15% | Cuando propone añadir una contradicción nueva: ¿es genuina (no documentada), bien formada (atoms identificados, severity sensata, resolution rationale)? Si no propone nada Y no había nada que proponer → score full. |
| **tone_format** | 5% | Tono cálido + cumple §10.7 (numbered steps, [[atom]] cites, max length, sin "cabe destacar"). Mantenido al 5% porque la opt no targetea tono. |

EVALUACIÓN POR PREGUNTA:

Para cada Qxx.json, lee:
- El response generado
- Los campos: conflict_detected, conflict_resolution_applied, proposed_contradictions
- Los atoms_cited

Compara con:
- `questions.yaml[id=Qxx].expected_atoms` (¿cita los esperados?)
- `questions.yaml[id=Qxx].expected_resolution` (¿el criterio aplicado coincide?)
- `questions.yaml[id=Qxx].expected_temporal_narrative` (¿narra evolución cuando se espera?)
- `questions.yaml[id=Qxx].probes_contradiction` (¿identifica el conflicto que la pregunta probaba?)
- `meta/contradictions.md` (¿el conflicto está documented? si sí, ¿lo refleja correctamente?)

Asigna scores 1-10 por dim. Calcula `weighted_avg` por pregunta usando los pesos arriba.

OUTPUT FORMAT (JSON estricto):
{
  "label": "O4v2-pre",
  "run": 2,
  "rubric_version": "custom-o4v2-1.0",
  "evaluator_model": "claude-opus-4-7",
  "evaluated_at": "<ISO timestamp>",
  "questions": {
    "Q01": {
      "scores": {
        "conflict_detection": <1-10>,
        "resolution_clarity": <1-10>,
        "temporal_narrative": <1-10>,
        "context_awareness": <1-10>,
        "proposed_contradiction_quality": <1-10>,
        "tone_format": <1-10>
      },
      "weighted_avg": <number>,
      "notes": "<observación específica, <120 palabras>"
    },
    "Q02": {...},
    ...
    "Q15": {...}
  },
  "aggregate": {
    "conflict_detection": <mean across 15 questions>,
    "resolution_clarity": <mean>,
    "temporal_narrative": <mean>,
    "context_awareness": <mean>,
    "proposed_contradiction_quality": <mean>,
    "tone_format": <mean>,
    "weighted_avg": <weighted mean>
  },
  "global_observations": "<2-4 frases sobre patrones globales: ¿el agente detecta bien? ¿propone contradicciones útiles? ¿narrativa temporal sólida?>"
}

PESOS PARA weighted_avg:
- conflict_detection: 0.20
- resolution_clarity: 0.25
- temporal_narrative: 0.20
- context_awareness: 0.15
- proposed_contradiction_quality: 0.15
- tone_format: 0.05

Guarda el JSON en: /Users/javierabrilibanez/Dev/test/wiki-optimize-my-airbnb-yt/tests/raw-responses/O4v2-pre/run-2/evaluation.json
