---
name: test-vault
description: Run the automated vault-quality test framework. Generates questions from the vault's MOCs, drives them through fresh /query subagents, fans out to N independent evaluators, computes inter-rater statistics, and produces a narrative report per language. Defaults: 15 questions, 5 evaluators, all enabled langs, queries cache OFF. All parameters configurable via CLI flags or vault.yml.tests.
allowed-tools: Read Write Bash(python3 *) Bash(source *)
---

# /test-vault

End-to-end automated quality testing for a WikiForge vault.

Usage:

```
/test-vault [--vault NAME] [--langs es,en] [--count 15] [--mix 5:7:3]
            [--evaluators 5] [--label baseline] [--read-queries]
            [--regenerate | --questions-from SRC] [--phase 1|2|3|4|5|all]
```

All flags are optional. If omitted, defaults come from `vaults/{name}/vault.yml` `tests:` block, and finally from hardcoded defaults (15 questions, 5 evaluators, mix 5:7:3, langs = enabled, read_queries = false).

## Parameter resolution order (CLI > vault.yml > built-in default)

| Param | CLI flag | `vault.yml.tests` key | Built-in |
| --- | --- | --- | --- |
| Vault | `--vault NAME` | — | `active_vault` from `.claude/state/wikiforge.yaml` |
| Languages | `--langs es,en` | `langs: enabled \| active \| [es]` | `enabled` |
| Question count | `--count 15` | `count` | `15` |
| Regime mix | `--mix 5:7:3` | `mix: { A:5, B:7, C:3 }` | `5:7:3` |
| Evaluators | `--evaluators 5` | `evaluators` | `5` |
| Label | `--label baseline-…` | — | `baseline-{today}` |
| Read queries cache | `--read-queries` | `read_queries` | `false` (OFF) |
| Regenerate questions | `--regenerate` | — | `false` |
| Reuse questions from another vault/path | `--questions-from SRC` | — | (none — generate fresh) |
| Phase scope | `--phase {1\|2\|3\|4\|5\|all}` | — | `all` |

CLI wins. `vault.yml.tests` is read but never mutated by the run.

## Five-phase pipeline

Each phase is independently runnable via `--phase N`. With `--phase all` (default) phases 1→5 run in sequence per language, with parallel fan-out within each phase.

### Phase 0 — Resolve

```bash
source .claude/scripts/resolve-vault.sh --vault {name}
```

Exports `VAULT_NAME` and `VAULT_PATH`. If `--vault` is absent, reads `active_vault` from `.claude/state/wikiforge.yaml`.

Determine the lang list:

- `--langs es,en` (CLI) wins.
- Else `vault.yml.tests.langs`: literal `enabled` → all enabled langs of the vault; literal `active` → `active_lang`; explicit list → that list.
- Else default: every enabled lang.

If multiple langs, **phases run in parallel across langs** (one parallel branch per lang). Within a lang, phases are sequential.

### Phase 1 — Generate questions (per lang)

For each lang, in parallel:

```bash
python3 scripts/run-test-suite.py --generate-questions \
    --vault {name} --label {label} --lang {lang} \
    --count {count} --mix {mix} [--regenerate | --questions-from SRC]
```

Three behaviors, in priority order:

1. **`--questions-from SRC`** (cross-vault reuse): the script copies the source YAML into `vaults/{name}/tests/questions.{lang}.yaml` and Phase 1 ends with no subagent launched. `SRC` can be a vault name (resolves to `vaults/{SRC}/tests/questions.{lang}.yaml`) or a path to a YAML file. Use this for **fair vault-to-vault comparisons** — running vault A and vault B against the exact same question set isolates differences in the vault content/methodology, not in the questions. Mutually exclusive with `--regenerate`.
2. **`--regenerate`** or no existing questions: the script writes a question-generator subagent prompt to `vaults/{name}/tests/raw-responses/{label}/run-1/{lang}/prompts/question-generator.md`. **Launch the subagent** with the Agent tool — fresh context, prompt content as input. The subagent reads the vault's index + MOCs and writes `vaults/{name}/tests/questions.{lang}.yaml`.
3. **Existing `questions.{lang}.yaml` and no `--regenerate`**: skip — reuse the same set for label-to-label comparability within the same vault.

### Phase 2 — Answer (per lang × per Q, parallel)

```bash
python3 scripts/run-test-suite.py --prepare \
    --vault {name} --label {label} --lang {lang} [--read-queries]
```

This writes `vaults/{name}/tests/raw-responses/{label}/run-N/{lang}/prompts/Q*.md` (one per question). For 15 questions × 2 langs = 30 prompt files.

**Launch all answering subagents in parallel** — single message with one `Agent` tool_use per Q. Each subagent:

- Has fresh context.
- Reads its prompt at `prompts/Q{N}.md`.
- Executes the equivalent of `/query --vault {name} --lang {lang} "{question}"` exactly as a real user would.
- Writes its result to `Q{N}.json`.

Hard-forbidden reads: `queries/` (unless `--read-queries`), other Q*.json, evaluator/aggregator outputs. The agent prompt template already declares these constraints.

### Phase 3 — Evaluate (per lang × N evaluators, parallel)

```bash
python3 scripts/run-test-suite.py --prepare-evaluator \
    --vault {name} --label {label} --lang {lang} \
    --evaluators {N} [--read-queries]
```

Writes `evaluator-E1.md` … `evaluator-E{N}.md` to the run's `prompts/` dir. The N prompts are identical except for `{evaluator_id}`.

**Launch all N evaluator subagents in parallel.** Each evaluator reads CLAUDE.md §10.7, RESPONSE_TEMPLATES.md, contradictions.md, the 15 Q*.json responses, and the cited atoms in `{lang}/wiki/`. Each writes its scores to `evaluation-E{i}.json`.

Hard-forbidden reads: other `evaluation-E*.json`, the aggregator's prompt or output, the answering agents' prompts, `queries/` (unless `--read-queries`).

### Phase 4 — Statistics (script only — no LLM)

```bash
python3 scripts/run-test-suite.py --consolidate \
    --vault {name} --label {label} --lang {lang} --append-history
```

Reads all `evaluation-E*.json`, computes per-Q per-dim mean and std across the N evaluators, weighted average using rubric weights, flags Qs with std > `max_dim_disagreement` threshold (default 1.5). Writes:

- `vaults/{name}/tests/raw-responses/{label}/run-N/{lang}/stats.json` — full per-Q breakdown.
- `vaults/{name}/tests/results/{label}.{lang}.json` — flat consolidated result.
- One line appended to `vaults/{name}/tests/history.md`.

### Phase 5 — Narrative report (1 aggregator agent per lang)

```bash
python3 scripts/run-test-suite.py --prepare-aggregator \
    --vault {name} --label {label} --lang {lang}
```

Writes `prompts/aggregator.md`. **Launch one aggregator subagent.** It reads stats.json + the N evaluator JSONs and writes `vaults/{name}/tests/reports/{label}.{lang}.md` — executive summary, per-dim findings, inter-rater disagreement section, action items.

Aggregators do NOT re-evaluate. They synthesise.

## Orchestration recipe (the orchestrator that runs this skill)

For each lang in resolved-langs (parallel across langs):

1. Phase 1 — call script, launch question-generator subagent (single Agent tool_use), wait for `questions.{lang}.yaml` to exist on disk.
2. Phase 2 — call script, launch all 15 answering subagents in **one message with 15 Agent tool_use blocks**. Wait for all to complete.
3. Phase 3 — call script, launch all N evaluator subagents in **one message with N Agent tool_use blocks**. Wait for all to complete.
4. Phase 4 — call script (`--consolidate --append-history`). No subagent. Writes `tokens.json` with input/output token estimates for answers + evaluators (aggregator output not yet present at this point).
5. Phase 5 — call script, launch the aggregator subagent (single Agent tool_use). Wait for the report.
6. Post-Phase 5 — call script (`--update-tokens --label {label} --lang {lang}`) so `tokens.json` includes the aggregator's output tokens too. No subagent.

If `--phase` is set to a single number, run only that phase (and assume the prior phases produced their artifacts).

## Example invocations

Default baseline run:

```
/test-vault
```

(Resolves to: active vault, all enabled langs, 15 questions per lang, 5 evaluators, label `baseline-{today}`.)

Spanish-only ablation with smaller question set:

```
/test-vault --langs es --count 10 --mix 4:4:2 --label small-es
```

Re-run an existing label without regenerating questions (label-to-label comparison):

```
/test-vault --label baseline-2 --langs en
```

Inspect what `--read-queries` does to scores (cache-on ablation):

```
/test-vault --label cache-on --langs en --read-queries
```

Compare two vaults against the **same** question set (fair A/B):

```
# 1. Generate questions in the reference vault (or reuse what's already there)
/test-vault --vault oma-test-2 --label baseline

# 2. Run the second vault using vault-A's questions
/test-vault --vault oma-test-3 --label baseline --questions-from oma-test-2
```

`--questions-from` accepts a vault name or a YAML path (e.g. `--questions-from /tmp/shared-questions.es.yaml`). It copies the source set into the target vault and skips the generator subagent. Mutually exclusive with `--regenerate`.

## Verification after a run

- `ls vaults/{name}/tests/questions.{lang}.yaml` — Phase 1 wrote the question set.
- `ls vaults/{name}/tests/raw-responses/{label}/run-N/{lang}/Q*.json | wc -l` — should match `--count`.
- `ls vaults/{name}/tests/raw-responses/{label}/run-N/{lang}/evaluation-E*.json | wc -l` — should match `--evaluators`.
- `cat vaults/{name}/tests/results/{label}.{lang}.json | jq '.weighted_avg'` — top-line score.
- Open `vaults/{name}/tests/reports/{label}.{lang}.md` — narrative report.

## Hard isolation invariants

These hold for every run, regardless of flags:

1. Answering agents and evaluators NEVER read `queries/` unless `--read-queries` is explicitly set.
2. Evaluators NEVER see each other's outputs.
3. Aggregator does not re-evaluate — only synthesises what the N evaluators said.
4. No subagent writes to `{vault_path}` (vault is read-only). All outputs land under `vaults/{name}/tests/`.
5. Each subagent has fresh context; no session memory leaks across Qs or evaluators.
