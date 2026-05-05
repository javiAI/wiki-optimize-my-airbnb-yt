"""
atom-qa.py — Quality gate for WikiForge atoms.

Checks per atom (per language):
  1. Completeness: claim, ≥1 source with url, last_verified
  2. URL format: sources[].url is a valid deep link
  3. Multilingual schema: each source has excerpt_source ∈ {yt_manual, yt_auto,
     llm_fallback, native_atomization}; if propagated_from is present at the
     top level, it points to an enabled language.
  4. Anglicism (non-English langs): prohibited English words in body text
  5. Acronyms: acronyms used without expansion on first occurrence
  6. Conflict: claim overlaps with meta/contradictions.md entries

Lexical data (anglicisms, whitelist, acronyms) lives in `.claude/scripts/qa_lexicon.py`.

Usage:
    python3 .claude/scripts/atom-qa.py pricing--base-price --lang en
    python3 .claude/scripts/atom-qa.py pricing--base-price --lang es
    python3 .claude/scripts/atom-qa.py --all --lang es
    python3 .claude/scripts/atom-qa.py --all          # checks all langs enabled in vault.yaml
    python3 .claude/scripts/atom-qa.py --all --fix    # auto-fix anglicisms, acronyms, missing URLs

Output: meta/qa-reports/{stem}.{lang}.json — written ONLY when violations exist.
        If atom becomes clean, any pre-existing report is deleted.
Exit code: 0 = pass or warnings only, 1 = critical failures found
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from qa_lexicon import ANGLICISM_TABLE, ANGLICISM_WHITELIST, ACRONYM_TABLE


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from atom markdown. Returns (frontmatter_dict, body)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end]
    body = text[end + 3:].strip()

    fm = {}
    current_key = None
    sources_list = []
    in_sources = False
    current_source = {}

    for line in fm_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line.startswith("sources:"):
            in_sources = True
            current_key = "sources"
            continue

        if in_sources:
            if stripped.startswith("- source_id:"):
                if current_source:
                    sources_list.append(current_source)
                current_source = {"source_id": stripped.split(":", 1)[1].strip()}
            elif current_source is not None:
                if ":" in stripped:
                    k, v = stripped.split(":", 1)
                    k, v = k.strip(), v.strip().strip('"')
                    current_source[k] = v
            # Detect end of sources block
            if not line.startswith(" ") and ":" in stripped and not stripped.startswith("-"):
                in_sources = False
                if current_source:
                    sources_list.append(current_source)
                    current_source = {}
                current_key = None
                k, v = stripped.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
            continue

        if ":" in stripped:
            k, v = stripped.split(":", 1)
            k, v = k.strip(), v.strip().strip('"')
            if v.startswith("[") and v.endswith("]"):
                v = [x.strip().strip('"') for x in v[1:-1].split(",") if x.strip()]
            fm[k] = v

    if current_source:
        sources_list.append(current_source)
    if sources_list:
        fm["sources"] = sources_list

    return fm, body


def check_completeness(fm: dict) -> list[dict]:
    violations = []
    if not fm.get("claim"):
        violations.append({"type": "missing_claim", "severity": "critical",
                           "message": "Missing required field: claim"})
    sources = fm.get("sources", [])
    if not sources:
        violations.append({"type": "missing_sources", "severity": "critical",
                           "message": "No sources defined"})
    else:
        for i, src in enumerate(sources):
            if not src.get("url"):
                violations.append({"type": "missing_url", "severity": "warning",
                                   "message": f"Source [{i}] {src.get('source_id', '?')} has no url field",
                                   "auto_fixable": True})
    if not fm.get("last_verified"):
        violations.append({"type": "missing_last_verified", "severity": "warning",
                           "message": "Missing last_verified date"})
    return violations


def check_url_format(fm: dict, source_type: str = "youtube") -> list[dict]:
    violations = []
    sources = fm.get("sources", [])
    youtube_pattern = re.compile(r'^https://youtube\.com/watch\?v=[\w-]+&t=\d+$')
    for i, src in enumerate(sources):
        url = src.get("url", "")
        if not url:
            continue
        if source_type == "youtube" and not youtube_pattern.match(url):
            violations.append({"type": "invalid_url_format", "severity": "warning",
                               "message": f"Source [{i}] URL format invalid: {url}"})
    return violations


VALID_EXCERPT_SOURCES = {"yt_manual", "yt_auto", "llm_fallback", "native_atomization"}


def check_multilingual_schema(fm: dict, enabled_langs: list[str]) -> list[dict]:
    """Validate the per-source `excerpt_source` field and top-level `propagated_from`.

    - Every source MUST declare excerpt_source ∈ VALID_EXCERPT_SOURCES.
    - If the atom has top-level `propagated_from`, it must be a lang in `enabled_langs`.
    - If `propagated_from` is set, every source's `excerpt_source` must be one of
      {yt_manual, yt_auto, llm_fallback} (never native_atomization, since this atom
      is propagated, not canonical).
    """
    violations = []
    enabled_set = set(enabled_langs or [])

    propagated_from = fm.get("propagated_from")
    if propagated_from:
        if enabled_set and propagated_from not in enabled_set:
            violations.append({
                "type": "invalid_propagated_from",
                "severity": "critical",
                "message": f'propagated_from="{propagated_from}" is not in enabled languages {sorted(enabled_set)}',
            })

    for i, src in enumerate(fm.get("sources", [])):
        es = src.get("excerpt_source")
        if not es:
            violations.append({
                "type": "missing_excerpt_source",
                "severity": "warning",
                "message": f"Source [{i}] {src.get('source_id', '?')} missing excerpt_source field "
                           f"(expected one of {sorted(VALID_EXCERPT_SOURCES)})",
            })
            continue
        if es not in VALID_EXCERPT_SOURCES:
            violations.append({
                "type": "invalid_excerpt_source",
                "severity": "warning",
                "message": f'Source [{i}] excerpt_source="{es}" is not a known value '
                           f"(expected one of {sorted(VALID_EXCERPT_SOURCES)})",
            })
            continue
        if propagated_from and es == "native_atomization":
            violations.append({
                "type": "inconsistent_excerpt_source",
                "severity": "warning",
                "message": f'Source [{i}] uses excerpt_source="native_atomization" but the atom '
                           f'is propagated_from="{propagated_from}" (expected yt_manual / yt_auto / llm_fallback)',
            })

    return violations


def check_anglicisms(body: str, lang: str) -> list[dict]:
    """Check body text for prohibited English words. Skipped for English atoms (those ARE in English)."""
    violations = []
    if lang == "en":
        return violations

    body_lower = body.lower()
    whitelist_lower = {w.lower() for w in ANGLICISM_WHITELIST}

    for english, spanish in ANGLICISM_TABLE:
        if english.lower() in whitelist_lower:
            continue
        # Build pattern that also matches common plural/inflected forms
        base = re.escape(english.lower())
        pattern = r'\b' + base + r's?\b'
        m = re.search(pattern, body_lower)
        if m:
            found = m.group(0)
            violations.append({
                "type": "anglicism",
                "severity": "warning",
                "message": f'Found "{found}" — use "{spanish}" instead',
                "word": english,
                "replacement": spanish,
                "auto_fixable": True,
            })

    return violations


def apply_anglicism_fixes(body: str, violations: list[dict]) -> str:
    """Apply auto_fixable anglicism substitutions to body text."""
    result = body
    for v in violations:
        if not v.get("auto_fixable") or v.get("type") != "anglicism":
            continue
        word = v["word"]
        replacement = v["replacement"]
        base = re.escape(word)
        result = re.sub(r'\b' + base + r's?\b', replacement, result, flags=re.IGNORECASE)
    return result


def check_acronyms(body: str) -> list[dict]:
    """
    Check body for acronyms used without their expansion defined inline.
    Applies to all languages — acronyms must be expanded on first use.
    """
    violations = []
    for acronym, expansion in ACRONYM_TABLE:
        # Case-sensitive match: acronyms are uppercase, avoids matching e.g. "adr" inside words
        if not re.search(r'\b' + re.escape(acronym) + r'\b', body):
            continue
        # Skip if expansion already appears anywhere (case-insensitive)
        if expansion.lower() in body.lower():
            continue
        violations.append({
            "type": "acronym_unexpanded",
            "severity": "warning",
            "message": f'Acronym "{acronym}" used without expansion — first occurrence should be followed by "({expansion})"',
            "acronym": acronym,
            "expansion": expansion,
            "auto_fixable": True,
        })
    return violations


def apply_acronym_fixes(body: str, violations: list[dict]) -> str:
    """Insert ' (expansion)' after the FIRST occurrence of each flagged acronym."""
    result = body
    for v in violations:
        if not v.get("auto_fixable") or v.get("type") != "acronym_unexpanded":
            continue
        acronym = v["acronym"]
        expansion = v["expansion"]
        result = re.sub(
            r'\b' + re.escape(acronym) + r'\b',
            f'{acronym} ({expansion})',
            result,
            count=1,
        )
    return result


def _inject_missing_urls(text: str, source_type: str = "youtube") -> tuple[str, int]:
    """For each source in frontmatter without a url, compute one from source_id+locator."""
    from deep_link import locator_to_url

    if not text.startswith("---"):
        return text, 0
    end = text.find("---", 3)
    if end == -1:
        return text, 0

    frontmatter = text[3:end]
    body = text[end + 3:]
    new_frontmatter = frontmatter
    fixes = 0

    source_blocks = re.findall(
        r'(  - source_id: (\S+)\n(?:    \w+: [^\n]+\n)*)',
        frontmatter,
        re.MULTILINE,
    )

    for block, source_id in source_blocks:
        if re.search(r'^    url:', block, re.MULTILINE):
            continue
        loc_m = re.search(r'    locator: "?([^"\n]+?)"?\n', block)
        if not loc_m:
            continue
        locator = loc_m.group(1).strip()
        url = locator_to_url(source_id, locator, source_type)
        if not url:
            continue
        new_block = re.sub(
            r'(    locator: [^\n]+\n)',
            f'    locator: "{locator}"\n    url: "{url}"\n',
            block,
            count=1,
        )
        new_frontmatter = new_frontmatter.replace(block, new_block)
        fixes += 1

    if fixes == 0:
        return text, 0
    return f"---{new_frontmatter}---{body}", fixes


def check_conflicts(stem: str, fm: dict, meta_dir: Path) -> list[dict]:
    violations = []
    contradictions_file = meta_dir / "contradictions.md"
    if not contradictions_file.exists():
        return violations

    content = contradictions_file.read_text()
    if stem in content:
        violations.append({
            "type": "known_conflict",
            "severity": "info",
            "message": f"Atom '{stem}' appears in meta/contradictions.md — verify conflict is documented"
        })
    return violations


def run_qa(
    stem: str,
    lang: str,
    vault_path: Path,
    source_type: str = "youtube",
    write_report: bool = True,
    enabled_langs: Optional[list] = None,
) -> dict:
    """Run all QA checks on a single atom. Returns the QA report dict.

    Side-effect (when write_report=True):
      - Writes meta/qa-reports/{stem}.{lang}.json IF violations exist
      - Deletes any stale report if atom is now clean (skip-write-when-clean)
    """
    wiki_dir = vault_path / "wiki" / lang
    if not wiki_dir.exists():
        wiki_dir = vault_path / "notes"  # Legacy fallback

    atom_file = wiki_dir / f"{stem}.md"
    if not atom_file.exists():
        return {"atom": stem, "lang": lang, "pass": False, "error": f"File not found: {atom_file}"}

    text = atom_file.read_text()
    fm, body = _parse_frontmatter(text)

    violations = []
    violations += check_completeness(fm)
    violations += check_url_format(fm, source_type)
    violations += check_multilingual_schema(fm, enabled_langs or [])
    violations += check_anglicisms(body, lang)
    violations += check_acronyms(body)
    violations += check_conflicts(stem, fm, vault_path / "meta")

    critical = [v for v in violations if v.get("severity") == "critical"]
    warnings = [v for v in violations if v.get("severity") == "warning"]

    report = {
        "atom": stem,
        "lang": lang,
        "timestamp": datetime.now().isoformat(),
        "pass": len(critical) == 0,
        "critical_count": len(critical),
        "warning_count": len(warnings),
        "violations": violations,
        "auto_fixable": [v for v in violations if v.get("auto_fixable")],
    }

    if write_report:
        qa_dir = vault_path / "meta" / "qa-reports"
        report_file = qa_dir / f"{stem}.{lang}.json"
        if violations:
            qa_dir.mkdir(parents=True, exist_ok=True)
            report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        elif report_file.exists():
            report_file.unlink()

    return report


def run_all(lang: str, vault_path: Path, source_type: str = "youtube",
            enabled_langs: Optional[list] = None) -> dict:
    """Run QA on all atoms for a given language."""
    wiki_dir = vault_path / "wiki" / lang
    if not wiki_dir.exists():
        if lang == "en":
            wiki_dir = vault_path / "notes"
        else:
            print(f"  No wiki/{lang}/ directory found — skipping")
            return {}

    results = {}
    atom_files = sorted(wiki_dir.glob("*.md"))
    total = len(atom_files)
    passed = 0
    failed = 0

    for atom_file in atom_files:
        stem = atom_file.stem
        report = run_qa(stem, lang, vault_path, source_type, enabled_langs=enabled_langs)
        results[stem] = report
        if report.get("pass"):
            passed += 1
        else:
            failed += 1
            print(f"  FAIL [{lang}] {stem}: {[v['message'] for v in report['violations'] if v['severity']=='critical']}")

    print(f"  [{lang}] {passed}/{total} passed, {failed} failed")
    return results


def fix_atom(stem: str, lang: str, vault_path: Path, source_type: str = "youtube") -> int:
    """Apply all auto_fixable corrections to an atom file. Returns count of fixes applied."""
    wiki_dir = vault_path / "wiki" / lang
    atom_file = wiki_dir / f"{stem}.md"
    if not atom_file.exists():
        return 0

    text = atom_file.read_text()
    fixes = 0

    # 1. Inject missing URLs in frontmatter
    text, url_fixes = _inject_missing_urls(text, source_type)
    fixes += url_fixes

    # 2. Apply body-level fixes (anglicisms + acronyms), preserving original whitespace
    end = text.find("---", 3)
    if end == -1:
        return fixes
    frontmatter_raw = text[:end + 3]
    body_raw = text[end + 3:]

    # Split body into (leading_ws, content, trailing_ws) so substitutions don't collapse separators
    body_lstripped = body_raw.lstrip()
    leading_ws = body_raw[: len(body_raw) - len(body_lstripped)]
    body_content = body_lstripped.rstrip()
    trailing_ws = body_lstripped[len(body_content):]

    new_content = body_content

    anglicism_violations = check_anglicisms(new_content, lang)
    fixable_anglicisms = [v for v in anglicism_violations if v.get("auto_fixable")]
    if fixable_anglicisms:
        new_content = apply_anglicism_fixes(new_content, fixable_anglicisms)
        fixes += len(fixable_anglicisms)

    acronym_violations = check_acronyms(new_content)
    fixable_acronyms = [v for v in acronym_violations if v.get("auto_fixable")]
    if fixable_acronyms:
        new_content = apply_acronym_fixes(new_content, fixable_acronyms)
        fixes += len(fixable_acronyms)

    if fixes == 0:
        return 0

    atom_file.write_text(frontmatter_raw + leading_ws + new_content + trailing_ws)
    return fixes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WikiForge atom QA")
    parser.add_argument("stem", nargs="?", help="Atom stem (e.g. pricing--base-price)")
    parser.add_argument("--lang", default=None, help="Language code (en, es, ...)")
    parser.add_argument("--all", action="store_true", help="Check all atoms")
    parser.add_argument("--fix", action="store_true", help="Auto-fix violations in place")
    parser.add_argument("--vault", default=None, help="Vault path (default: $VAULT_PATH)")
    parser.add_argument("--dry-run", action="store_true", help="Don't write QA reports")
    parser.add_argument("--source-type", default="youtube")
    args = parser.parse_args()

    from config import VaultConfig
    cfg = VaultConfig(args.vault)

    if args.all:
        enabled = cfg.enabled_languages
        langs = [args.lang] if args.lang else enabled
        all_results = {}
        total_fixes = 0
        for lang in langs:
            print(f"\nChecking {lang}...")
            all_results[lang] = run_all(lang, cfg.vault_path, args.source_type,
                                        enabled_langs=enabled)
            if args.fix:
                wiki_dir = cfg.vault_path / "wiki" / lang
                for atom_file in sorted(wiki_dir.glob("*.md")):
                    n = fix_atom(atom_file.stem, lang, cfg.vault_path, args.source_type)
                    if n:
                        print(f"  [fix] {atom_file.stem} [{lang}]: {n} correction(s)")
                        total_fixes += n
        if args.fix:
            print(f"\nTotal fixes applied: {total_fixes}")
            # Re-run QA after fixes so qa-reports/ reflects clean state
            print("\nRe-running QA after fixes...")
            for lang in langs:
                run_all(lang, cfg.vault_path, args.source_type)

        total_critical = sum(
            r["critical_count"]
            for lang_results in all_results.values()
            for r in lang_results.values()
            if isinstance(r, dict) and "critical_count" in r
        )
        print(f"\n{'='*50}")
        print(f"Total critical failures: {total_critical}")
        sys.exit(1 if total_critical > 0 else 0)

    elif args.stem:
        enabled = cfg.enabled_languages
        lang = args.lang or (enabled[0] if enabled else "en")
        report = run_qa(args.stem, lang, cfg.vault_path, args.source_type,
                        write_report=not args.dry_run, enabled_langs=enabled)
        if args.fix:
            n = fix_atom(args.stem, lang, cfg.vault_path, args.source_type)
            if n:
                print(f"[fix] {n} correction(s) applied to {args.stem}", file=sys.stderr)
                # Re-run QA so report reflects post-fix state
                report = run_qa(args.stem, lang, cfg.vault_path, args.source_type,
                                write_report=not args.dry_run, enabled_langs=enabled)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.exit(0 if report.get("pass") else 1)

    else:
        parser.print_help()
        sys.exit(1)
