"""
migrate-atoms.py — One-time migration: notes/ → wiki/{lang}/

For each .md in notes/:
  1. Adds `lang: {lang}` to frontmatter
  2. Computes sources[].url from source_id + locator (YouTube deep links)
  3. Writes to wiki/{lang}/{stem}.md

Usage:
    python3 scripts/migrate-atoms.py --lang es               # move notes/ → wiki/es/
    python3 scripts/migrate-atoms.py --lang es --dry-run     # preview only
    python3 scripts/migrate-atoms.py --lang es --source-dir custom/path
    python3 scripts/migrate-atoms.py --verify                # check wiki/{lang}/ after migration

Exit code: 0 = success, 1 = errors found
"""

import argparse
import re
import sys
from pathlib import Path

LOCATOR_RE = re.compile(r'locator:\s*"?([^"\n]+)"?')
SOURCE_ID_RE = re.compile(r'source_id:\s*(\S+)')
URL_FIELD_RE = re.compile(r'url:\s*\S+')
LANG_FIELD_RE = re.compile(r'^lang:\s*\S+', re.MULTILINE)


def locator_to_seconds(locator: str):
    start = locator.split("-")[0].strip()
    m = re.match(r'^(\d+):(\d+)(?::(\d+))?$', start)
    if not m:
        return None
    h_or_m, m_or_s, s = m.group(1), m.group(2), m.group(3)
    if s is not None:
        return int(h_or_m) * 3600 + int(m_or_s) * 60 + int(s)
    return int(h_or_m) * 60 + int(m_or_s)


def compute_url(source_id: str, locator: str, source_type: str = "youtube"):
    if source_type == "youtube":
        t = locator_to_seconds(locator)
        if t is None:
            return None
        return f"https://youtube.com/watch?v={source_id}&t={t}"
    return None


def inject_urls(frontmatter: str, source_type: str) -> tuple[str, int]:
    """Add url field after each locator line if url not already present."""
    lines = frontmatter.split("\n")
    new_lines = []
    urls_added = 0
    current_source_id = None
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Track current source block's source_id (may appear as "- source_id: X" or "source_id: X")
        sid_match = re.search(r'source_id:\s*(\S+)', stripped)
        if sid_match:
            current_source_id = sid_match.group(1).strip()

        # If this is a locator line, check if next line has url
        if stripped.startswith("locator:"):
            new_lines.append(line)
            # Check if url already exists in next few lines
            has_url = any(
                lines[j].strip().startswith("url:")
                for j in range(i+1, min(i+4, len(lines)))
                if lines[j].strip() and not lines[j].strip().startswith("-")
            )
            if not has_url and current_source_id:
                # Extract locator value
                loc_m = re.match(r'\s*locator:\s*"?([^"\n]+)"?', line)
                if loc_m:
                    locator = loc_m.group(1).strip()
                    url = compute_url(current_source_id, locator, source_type)
                    if url:
                        # Preserve indentation of locator line
                        indent = len(line) - len(line.lstrip())
                        new_lines.append(" " * indent + f'url: "{url}"')
                        urls_added += 1
            i += 1
            continue

        new_lines.append(line)
        i += 1

    return "\n".join(new_lines), urls_added


def add_lang_field(frontmatter: str, lang: str) -> str:
    """Add lang: {lang} as first field if not already present."""
    if LANG_FIELD_RE.search(frontmatter):
        return frontmatter  # Already has lang field
    # Insert after opening newline
    return f"\nlang: {lang}" + frontmatter


def migrate_atom(src_path: Path, dest_path: Path, lang: str, source_type: str, dry_run: bool) -> dict:
    text = src_path.read_text(errors="replace")

    if not text.startswith("---"):
        return {"stem": src_path.stem, "status": "skip", "reason": "no frontmatter"}

    end = text.find("---", 3)
    if end == -1:
        return {"stem": src_path.stem, "status": "skip", "reason": "unclosed frontmatter"}

    frontmatter = text[3:end]
    body = text[end + 3:]

    # 1. Add lang field
    frontmatter = add_lang_field(frontmatter, lang)

    # 2. Inject url fields
    frontmatter, urls_added = inject_urls(frontmatter, source_type)

    new_text = f"---{frontmatter}---{body}"

    if dry_run:
        print(f"  [DRY-RUN] {src_path.stem} → wiki/{lang}/{dest_path.name} (+{urls_added} URLs)")
        return {"stem": src_path.stem, "status": "dry-run", "urls_added": urls_added}

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(new_text)
    return {"stem": src_path.stem, "status": "ok", "urls_added": urls_added}


def verify_migration(vault_path: Path, lang: str) -> dict:
    """Check wiki/{lang}/ atoms for lang field and url presence."""
    wiki_dir = vault_path / "wiki" / lang
    if not wiki_dir.exists():
        return {"error": f"wiki/{lang}/ not found"}

    total = missing_lang = missing_url = 0
    for p in sorted(wiki_dir.glob("*.md")):
        total += 1
        text = p.read_text(errors="replace")
        if not LANG_FIELD_RE.search(text):
            missing_lang += 1
            print(f"  MISSING lang field: {p.stem}")
        if "locator:" in text and "url:" not in text:
            missing_url += 1
            print(f"  MISSING url field: {p.stem}")

    print(f"\n[{lang}] {total} atoms: {missing_lang} missing lang, {missing_url} missing url")
    return {"total": total, "missing_lang": missing_lang, "missing_url": missing_url}


def main():
    p = argparse.ArgumentParser(description="Migrate notes/ atoms to wiki/{lang}/")
    p.add_argument("--lang", default=None, help="Target language code (e.g. es, en)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--vault", default=None, help="Vault path")
    p.add_argument("--source-dir", default=None, help="Override source directory (default: notes/)")
    p.add_argument("--source-type", default="youtube", help="Source type for URL computation")
    p.add_argument("--verify", action="store_true", help="Verify wiki/{lang}/ after migration")
    args = p.parse_args()

    sys.path.insert(0, str(Path(__file__).parent))
    from config import VaultConfig
    cfg = VaultConfig(args.vault)
    vault_path = cfg.vault_path

    lang = args.lang or cfg.primary_language

    if args.verify:
        verify_migration(vault_path, lang)
        sys.exit(0)

    # Determine source directory
    if args.source_dir:
        source_dir = Path(args.source_dir)
    else:
        source_dir = vault_path / "notes"
        if not source_dir.exists():
            source_dir = vault_path / "wiki" / lang

    if not source_dir.exists():
        print(f"ERROR: source directory not found: {source_dir}", file=sys.stderr)
        sys.exit(1)

    dest_dir = vault_path / "wiki" / lang
    atom_files = sorted(source_dir.glob("*.md"))
    total = len(atom_files)

    print(f"Migrating {total} atoms: {source_dir} → wiki/{lang}/")
    if args.dry_run:
        print("(DRY RUN — no files written)\n")

    ok = skip = errors = total_urls = 0
    for atom_file in atom_files:
        dest = dest_dir / atom_file.name
        result = migrate_atom(atom_file, dest, lang, args.source_type, args.dry_run)
        if result["status"] == "ok":
            ok += 1
            total_urls += result.get("urls_added", 0)
        elif result["status"] == "dry-run":
            ok += 1
            total_urls += result.get("urls_added", 0)
        elif result["status"] == "skip":
            skip += 1
            print(f"  SKIP {atom_file.stem}: {result.get('reason','')}")
        else:
            errors += 1

    print(f"\nDone: {ok} migrated, {skip} skipped, {errors} errors")
    print(f"URLs added: {total_urls}")
    if not args.dry_run and ok > 0:
        print(f"\nNext steps:")
        print(f"  python3 scripts/migrate-atoms.py --verify --lang {lang}")
        print(f"  python3 scripts/atom-qa.py --all --lang {lang}")

    sys.exit(1 if errors > 0 else 0)


if __name__ == "__main__":
    main()
