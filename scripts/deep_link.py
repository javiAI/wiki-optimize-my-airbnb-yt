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
    python3 scripts/deep_link.py --backfill
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


def backfill_atom_urls(vault_path: Path, source_type: str = "youtube", dry_run: bool = False) -> dict:
    """
    Scan all wiki/{lang}/*.md files in vault. For each atom that has
    sources[].locator but no sources[].url, compute and inject the URL.

    Returns: {lang: {stem: [urls_added]}} summary dict
    """
    results = {}

    wiki_dir = vault_path / "wiki"
    if not wiki_dir.exists():
        # Legacy path
        wiki_dir = vault_path / "notes"

    for lang_dir in sorted(wiki_dir.iterdir()):
        if not lang_dir.is_dir():
            continue
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

            # Find sources without url
            urls_added = []
            new_frontmatter = frontmatter

            # Match source blocks: source_id + locator lines
            source_blocks = re.findall(
                r'(  - source_id: (\S+)\n(?:    \w+: [^\n]+\n)*)',
                frontmatter,
                re.MULTILINE
            )

            for block, source_id in source_blocks:
                loc_m = re.search(r'    locator: "?([^"\n]+)"?', block)
                url_m = re.search(r'    url:', block)

                if loc_m and not url_m:
                    locator = loc_m.group(1).strip()
                    url = locator_to_url(source_id, locator, source_type)
                    if url:
                        # Insert url line after locator line
                        new_block = block.replace(
                            f'    locator: "{locator}"\n' if f'"{locator}"' in block
                            else f'    locator: {locator}\n',
                            f'    locator: "{locator}"\n    url: "{url}"\n'
                        )
                        if new_block == block:
                            # Try without quotes
                            new_block = re.sub(
                                r'(    locator: [^\n]+\n)',
                                f'    locator: "{locator}"\n    url: "{url}"\n',
                                block,
                                count=1
                            )
                        new_frontmatter = new_frontmatter.replace(block, new_block)
                        urls_added.append(url)

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
        results = backfill_atom_urls(cfg.vault_path, args.source_type, args.dry_run)
        total = sum(len(v) for v in results.values())
        print(f"\nDone. {total} atoms updated across {len(results)} languages.")
    else:
        parser.print_help()
