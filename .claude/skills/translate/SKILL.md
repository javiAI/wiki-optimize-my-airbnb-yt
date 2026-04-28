---
name: translate
description: Translate one atom from source language to target language. Writes wiki/{target}/{stem}.md as a native-language rewrite, not a literal translation.
allowed-tools: Read Write Bash(python3 scripts/atom-qa.py)
---

# /translate — Native-Language Atom Creation

Usage: `/translate {stem} [from={lang}] [to={lang}]`

Defaults: `from` = source.original_language from vault.yaml, `to` = first secondary language

## Steps

1. Read `wiki/{from}/{stem}.md` — extract frontmatter (claim, topics, confidence, sources, conflicts_with, last_verified)
2. If `wiki/{to}/{stem}.md` already exists → confirm overwrite with user before proceeding
3. Write `wiki/{to}/{stem}.md`:
   - `lang: {to}`
   - `claim:` — rewrite the claim natively in {to}. Not a word-for-word translation; express the same fact as a fluent native speaker would say it
   - Same `topics`, `confidence`, `conflicts_with`, `last_verified`
   - Same `sources` block (source_id, locator, url unchanged — language-neutral), `excerpt` rewritten naturally in {to}
   - `source_lang: {from}` — document where it came from
   - Body: write from scratch as a bilingual expert explaining this concept to a native {to} speaker. Do NOT translate the original body — write what a fluent expert would write
4. Pre-write checklist:
   - Zero anglicisms (apply substitution table from vault's CLAUDE.md or agents.md)
   - Proper nouns/tech (PriceLabs, Airbnb, WiFi, etc.) stay untranslated
   - Body opens with the claim restated in {to}, then supporting detail
   - No filler phrases ("Como podemos observar", "Es importante destacar")
5. Run `python3 scripts/atom-qa.py {stem} --lang {to} --vault "$VAULT_PATH"` — report any violations
6. The PostToolUse(Write) hook fires automatically: auto-link + qa in moc/{to}/

## Quality standard

Imagine a bilingual consultant who is completely fluent in both languages.
They do not open a dictionary — they explain the concept naturally in the target language,
using the vocabulary and register of a native professional.
The EN excerpt says "Start 30% below market" → the ES body says
"Arranca un 30% por debajo del mercado" — same meaning, native voice, no calques.
