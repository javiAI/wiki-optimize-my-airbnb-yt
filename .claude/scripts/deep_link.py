"""
deep_link.py — Convert source locators to deep-link URLs.

Supported source types:
  youtube: "HH:MM" or "HH:MM:SS" or "HH:MM-HH:MM" → https://youtube.com/watch?v=ID&t=SEC
  pdf:     "p{page}:{para}" → "{base_url}#{page}"
  web:     "h2:{heading}" → "{base_url}#{anchor}"
  file:    "L{start}:{end}" → None (no deep link for local files)

Usage:
    from deep_link import locator_to_url, locator_to_seconds
    url = locator_to_url("abc123", "01:06-01:50", source_type="youtube")
    # → "https://youtube.com/watch?v=abc123&t=66"

    # Backfill all atoms in vault
    python3 .claude/scripts/deep_link.py --backfill
"""

import re
import sys
import argparse
from pathlib import Path
from typing import Optional


def locator_to_seconds(locator: str) -> Optional[int]:
    """
    Convert a timestamp string to seconds.
    Handles: "MM:SS", "HH:MM:SS", "MM:SS-MM:SS" (takes start).
    Returns None if locator is not a timestamp format.
    """
    start = locator.split("-")[0].strip()
    # Match HH:MM:SS or MM:SS
    m = re.match(r'^(\d+):(\d+)(?::(\d+))?$', start)
    if not m:
        return None
    h_or_m, m_or_s, s = m.group(1), m.group(2), m.group(3)
    if s is not None:
        return int(h_or_m) * 3600 + int(m_or_s) * 60 + int(s)
    else:
        return int(h_or_m) * 60 + int(m_or_s)


def locator_to_url(
    source_id: str,
    locator: str,
    source_type: str = "youtube",
    base_url: Optional[str] = None,
) -> Optional[str]:
    """
    Convert source_id + locator → deep-link URL.

    Args:
        source_id: YouTube video ID, PDF filename stem, web URL, etc.
        locator: Timestamp ("01:06-01:50"), page ref ("p3:2"), heading ("h2:intro"), etc.
        source_type: "youtube" | "pdf" | "web" | "file"
        base_url: For pdf/web types, the root URL/path to build the link from.

    Returns:
        Deep-link URL string, or None if not applicable.
    """
    if source_type == "youtube":
        t = locator_to_seconds(locator)
        if t is None:
            return None
        return f"https://youtube.com/watch?v={source_id}&t={t}"

    elif source_type == "pdf":
        # "p3:2" → page 3
        m = re.match(r'^p(\d+)', locator)
        if m and base_url:
            return f"{base_url}#page={m.group(1)}"
        return None

    elif source_type == "web":
        # "h2:some-heading" → #some-heading
        m = re.match(r'^h\d+:(.+)', locator)
        if m and base_url:
            anchor = re.sub(r'[^a-z0-9-]', '-', m.group(1).lower()).strip('-')
            return f"{base_url}#{anchor}"
        return None

    elif source_type == "file":
        return None  # Local files have no deep link

    return None


_SOURCE_BLOCK_RE = re.compile(
    r'(  - source_id: (\S+)\n(?:    \w+: [^\n]+\n)*)',
    re.MULTILINE,
)


def inject_urls_into_frontmatter(frontmatter: str, source_type: str = "youtube") -> tuple[str, list[str]]:
    """For each source block missing a url, compute one from source_id+locator
    and inject it after the locator line. Returns (new_frontmatter, urls_added).
    """
    new_frontmatter = frontmatter
    urls_added: list[str] = []
    for block, source_id in _SOURCE_BLOCK_RE.findall(frontmatter):
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
        urls_added.append(url)
    return new_frontmatter, urls_added


def backfill_atom_urls(vault_path: Path, source_type: str = "youtube", dry_run: bool = False,
                       langs: list = None) -> dict:
    """
    Scan per-lang wiki dirs. For each atom that has sources[].locator but no
    sources[].url, compute and inject the URL.

    `langs`: explicit list of enabled languages — required for v2 layout
    (`{vault}/{lang}/wiki`) since we cannot iterate kinds under each lang
    without knowing the lang set. For v1 (`{vault}/wiki/{lang}`) we fall
    back to scanning the subdirs of `wiki/` if no langs given.

    Returns: {lang: {stem: [urls_added]}} summary dict
    """
    sys.path.insert(0, str(Path(__file__).parent))
    from config import kind_dir  # noqa: E402

    results = {}

    if langs:
        lang_dirs = []
        for l in langs:
            d = kind_dir(vault_path, "wiki", l)
            if d.is_dir():
                lang_dirs.append(d)
    else:
        # v1 fallback: enumerate subdirs of wiki/. v2 needs explicit `langs`.
        wiki_root = vault_path / "wiki"
        if not wiki_root.exists():
            wiki_root = vault_path / "notes"
        lang_dirs = sorted(d for d in wiki_root.iterdir() if d.is_dir()) if wiki_root.exists() else []

    for lang_dir in lang_dirs:
        lang = lang_dir.name
        results[lang] = {}

        for atom_file in sorted(lang_dir.glob("*.md")):
            stem = atom_file.stem
            text = atom_file.read_text()

            # Parse YAML frontmatter
            if not text.startswith("---"):
                continue

            end = text.find("---", 3)
            if end == -1:
                continue

            frontmatter = text[3:end]
            body = text[end + 3:]

            new_frontmatter, urls_added = inject_urls_into_frontmatter(frontmatter, source_type)

            if urls_added:
                results[lang][stem] = urls_added
                if not dry_run:
                    new_text = f"---{new_frontmatter}---{body}"
                    atom_file.write_text(new_text)
                    print(f"  [{lang}] {stem}: added {len(urls_added)} URL(s)")
                else:
                    print(f"  [DRY RUN] [{lang}] {stem}: would add {len(urls_added)} URL(s)")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deep link generator for WikiForge atoms")
    parser.add_argument("--backfill", action="store_true",
                        help="Backfill url fields for all atoms missing them")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without writing")
    parser.add_argument("--vault", default=None,
                        help="Path to vault (default: $VAULT_PATH)")
    parser.add_argument("--source-type", default="youtube",
                        choices=["youtube", "pdf", "web", "file"])
    parser.add_argument("--test", action="store_true",
                        help="Run self-tests")
    args = parser.parse_args()

    if args.test:
        assert locator_to_seconds("01:06") == 66
        assert locator_to_seconds("01:06-01:50") == 66
        assert locator_to_seconds("01:06:30") == 3990
        assert locator_to_url("abc123", "01:06") == "https://youtube.com/watch?v=abc123&t=66"
        assert locator_to_url("abc123", "01:06-01:50") == "https://youtube.com/watch?v=abc123&t=66"
        assert locator_to_url("abc123", "01:06:30") == "https://youtube.com/watch?v=abc123&t=3990"
        assert locator_to_url("file.pdf", "p3:2", "pdf", "http://x.com/file.pdf") == "http://x.com/file.pdf#page=3"
        print("All tests passed.")
        sys.exit(0)

    if args.backfill:
        sys.path.insert(0, str(Path(__file__).parent))
        from config import VaultConfig
        cfg = VaultConfig(args.vault)
        print(f"Backfilling deep links in: {cfg.vault_path}")
        results = backfill_atom_urls(cfg.vault_path, args.source_type, args.dry_run,
                                     langs=cfg.enabled_languages)
        total = sum(len(v) for v in results.values())
        print(f"\nDone. {total} atoms updated across {len(results)} languages.")
    else:
        parser.print_help()
