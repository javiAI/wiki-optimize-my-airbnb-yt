---
name: suggest-questions
description: |-
  Mine the atom corpus to propose questions in two buckets: 5-10 questions
  per topic the vault can answer **right now** (showing what's been gathered)
  AND 5-10 that **reveal gaps** (showing what's missing or contradictory).
  Pure-LLM skill — no synthesis script. Reads `wiki/{lang}/`, MOCs and
  `meta/contradictions.md`.
  Use when the user asks "what should I ask this vault?", "what can the corpus
  answer?", "what's missing?", "where are the gaps?", or runs
  `/suggest-questions`. Also a natural follow-up to `/audit` for prioritising
  the next round of `/ingest`.
allowed-tools: Read, Glob, Grep, Bash(source .claude/scripts/resolve-vault.sh:*), Bash(python3 .claude/scripts/retrieve.py:*)
arguments:
  - name: --topic
    description: "Restrict to a single topic (e.g. `--topic pricing`). Default: top 5 topics by atom count."
  - name: --bucket
    description: "`answerable` | `gap-revealing` | `both` (default `both`)."
  - name: --lang
    description: "Force the response lang. Default: auto-detect → `state/wikiforge.yaml#active_lang` → `enabled[0]`."
---

# /suggest-questions — Question mining from the atom corpus

Inverts the normal `/query` flow: instead of "user asks → vault answers", this skill asks the vault *"given everything you know, what should I be asking?"*

Two output buckets:

1. **Answerable now** — questions the corpus can answer with high confidence (multiple corroborating atoms, clear claims).
2. **Gap-revealing** — questions where the corpus is thin, single-sourced, or self-contradictory; these signal where `/ingest` would add the most value.

## When to use

- A new user exploring a vault: *"what can this thing tell me?"*
- After a big ingest: *"what new questions does this corpus support?"*
- Before `/audit`-driven ingest decisions: surface the questions that would expose gaps.

## Steps

0. **Resolve vault** (mandatory preamble):

   ```bash
   source .claude/scripts/resolve-vault.sh
   ```

   Stop on non-zero exit and ask the user which vault to mine.

1. **Determine LANG** via the same chain as `/query`:
   1. `--lang` flag (explicit, always wins).
   2. Auto-detect from any phrase the user typed (chars + stopwords).
   3. `state/wikiforge.yaml#active_lang` (sticky).
   4. `enabled[0]` from the active vault's `vault.yml`.

2. **Read the topic distribution**. Either:
   - Glob `$VAULT_PATH/wiki/{LANG}/*.md` and tally the `topics:` field across atoms, OR
   - Read each MOC file at `$VAULT_PATH/moc/{LANG}/<topic>.md` (faster — pre-aggregated).

   If `--topic` was passed, restrict to that topic. Otherwise pick the top **5 topics** by atom count.

3. **For each topic**, sample 8–12 atoms (use `retrieve.py` with the topic name as query, or glob + read). Look for:
   - **Specific claims with numbers / thresholds** → high-quality answerable questions ("What's the threshold for X?").
   - **Action verbs** in claims (`set`, `raise`, `respond`, `filter`, etc.) → tactical questions.
   - **Contradictions** declared in `conflicts_with:` → gap-revealing ("Which one applies when Z?").
   - **Frontier vocabulary** (terms appearing only 1–2 times) → boundary questions.
   - **Single-source atoms** (low corroboration) → gap-revealing ("Is there more evidence for X?").

4. **Cross-reference `meta/contradictions.md`**. Open contradictions are gap-revealing gold — phrase them as *"Which side wins when…?"* questions.

5. **Compose the report**:

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

## Constraints

- Max **5 topics** per run.
- Max **8 questions** per bucket per topic (token budget).
- Each *answerable* question MUST cite at least one atom by name.
- Each *gap-revealing* question MUST explain WHY it's a gap (single source, contradiction, low confidence, missing topic adjacency).
- Phrase questions in the **user's voice**, not the wiki's: *"How do I…"*, *"What's the right…"*, *"When should I…"* — not *"What does the corpus say about…"*.
- Write natively in **LANG**, as a bilingual native of LANG would phrase them for a monolingual reader. Proper nouns (brands, products, places, people) and universally-known technical acronyms stay verbatim. The vault's `agents.md` defines what counts as a proper noun in this domain.

## Refuse to invent topics

Only suggest questions about topics that **exist** in `wiki/{LANG}/`. If the user asks about an unknown topic, say so and recommend `/suggest-sources <topic>` instead.

## Why this is a skill, not a script

Question generation is pattern matching over claim semantics — exactly what an LLM is for. A script could surface "atoms with numbers" but couldn't phrase a coherent question that respects user voice and lang purity. The script-side scoring (atom count, contradiction count) is already in `vault-agent.py` for `/audit`; this skill consumes that signal and produces natural-language output.
