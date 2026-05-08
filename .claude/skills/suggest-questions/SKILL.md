---
name: suggest-questions
description: Mine the atom corpus to propose 5-10 questions per topic that the vault could answer right now (showing what's been gathered) AND 5-10 that reveal gaps (showing what's missing). Useful for users wondering "what should I ask this vault?" or for prioritizing /ingest. Pure-LLM skill — no script. Reads from {lang}/wiki/ and meta/contradictions.md.
allowed-tools: Bash(python3 .claude/scripts/resolve-vault.sh .claude/scripts/retrieve.py) Read Glob Grep
---

# /suggest-questions

Inverts the normal `/query` flow: instead of "user asks → vault answers", this skill asks the vault "given everything you know, what should I be asking?"

Two output buckets:

1. **Answerable now** — questions the corpus can answer with high confidence
2. **Gap-revealing** — questions where the corpus is thin or contradicts itself, signaling where `/ingest` would add value

## When to use

- New users exploring a vault: "what can this thing tell me?"
- After a big ingest: "what new questions does this corpus support?"
- Before `/audit`-driven ingest decisions: surface the questions that would expose gaps

## Usage

```
/suggest-questions                       # Top topics, both buckets, default lang
/suggest-questions --topic pricing       # Focus on one topic
/suggest-questions --bucket answerable   # Only answerable, skip gap-revealing
/suggest-questions --lang es             # Force lang (else state/wikiforge.yaml active_lang)
```

## Steps

0. **Resolve vault**:

   ```bash
   source .claude/scripts/resolve-vault.sh
   ```

   Stop on non-zero exit.

1. **Determine LANG** via the same chain as `/query` (auto-detect from any phrase the user typed → `state/wikiforge.yaml` `active_lang` → `enabled[0]`).

2. **Read the topic distribution**. Either:
   - Glob `wiki/{LANG}/*.md` and tally `topics:` field across atoms, OR
   - Read each MOC file at `moc/{LANG}/<topic>.md` (faster — pre-aggregated)

   If `--topic` was passed, restrict to that topic. Otherwise pick the top 5 topics by atom count.

3. **For each topic**, sample 8-12 atoms (use `retrieve.py` with the topic name as query, or just glob and read). Look for:
   - **Specific claims with numbers/thresholds** → high-quality answerable questions ("What's the threshold for X?")
   - **Verbs of action** in claims ("set", "raise", "respond", "filter") → tactical questions
   - **Contradictions** declared in `conflicts_with:` → gap-revealing ("Should I do X or Y when Z?")
   - **Frontier vocabulary** (terms appearing only 1-2 times) → boundary questions ("What about <rare-term>?")
   - **Single-source atoms** (low corroboration) → gap-revealing ("Is there more evidence for X?")

4. **Cross-reference `meta/contradictions.md`**. Open contradictions are gap-revealing gold — phrase them as "Which side wins when…?" questions.

5. **Compose the report**. Format:

   ```markdown
   # Question suggestions — <vault-name> [<lang>]

   ## `<topic>` (N atoms)

   ### Answerable now (the corpus can give you a confident answer)
   1. "<question>" — see [[wiki/<lang>/<topic>--<slug>]]
   2. "<question>" — see [[wiki/<lang>/<topic>--<slug>]]
   ...

   ### Gap-revealing (the corpus is thin / contradictory here)
   1. "<question>" — only 1 source ([[<atom>]]), more would help
   2. "<question>" — atoms [[A]] and [[B]] disagree (no documented resolution)
   ...
   ```

6. **Constraints**:
   - Max 5 topics per run
   - Max 8 questions per bucket per topic (token budget)
   - Each "answerable" question must cite at least one atom by name
   - Each "gap-revealing" question must explain WHY it's a gap (single source, contradiction, low confidence, missing topic adjacency)
   - Phrase questions in the user's voice, not the wiki's: "How do I…", "What's the right…", "When should I…" — not "What does the corpus say about…"
   - Use the **target language**: ES questions in Spanish, EN in English. Phrase natively in the target lang — no English borrowings in non-English questions (brand and standardised tech terms exempt: PriceLabs, Airbnb, PMS, API, etc.).

7. **Refuse to invent topics**. Only suggest questions about topics that exist in `wiki/{LANG}/`. If the user asks about an unknown topic, say so and recommend `/suggest-sources <topic>` instead.

## Why this is a skill, not a script

Question generation is pattern matching over claim semantics — exactly what an LLM is for. A script could surface "atoms with numbers" but couldn't phrase a coherent question that respects user voice and lang purity. The script-side scoring (atom count, contradiction count) is already in `vault-agent.py` for `/audit`; this skill consumes that signal and produces natural-language output.
