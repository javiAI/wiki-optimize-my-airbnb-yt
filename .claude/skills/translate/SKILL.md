---
name: translate
description: Translate one atom from source language to target language. Creates wiki/{target}/{stem}.md with monolingual body.
allowed-tools: Read Write Bash(python3 scripts/atom-qa.py)
---

Translate an atom to a target language.

Usage: `/translate {stem} [from={lang}] [to={lang}]`
Defaults: from=primary_language (en), to=first secondary language (es)

Steps:
1. Read `wiki/{from}/{stem}.md` — extract frontmatter (claim, topics, confidence, sources, conflicts_with, last_verified)
2. Check if `wiki/{to}/{stem}.md` already exists — if yes, confirm overwrite with user
3. Write `wiki/{to}/{stem}.md`:
   - `lang: {to}`
   - `claim:` translated to {to} (native, not literal)
   - Same `topics`, `confidence`, `conflicts_with`, `last_verified`
   - Same `sources` block verbatim (source_id, locator, url, excerpt translated to {to})
   - Body text: write natively in {to} — full paragraph(s) explaining the claim
   - **Zero anglicisms**: apply the substitution table from CLAUDE.md §10.7 before writing
4. Run `python3 scripts/atom-qa.py {stem} --lang {to}` — report any violations
5. The PostToolUse(Write) hook fires automatically (auto-link in moc/{to}/)

Quality rules for Spanish translations:
- Body text must be fluent native Spanish — NOT mechanical translation
- Apply the full anglicism substitution table (§10.7) before writing
- Proper nouns/tech (PriceLabs, Airbnb, WiFi, etc.) stay untranslated
