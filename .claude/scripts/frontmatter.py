"""
frontmatter.py — Shared YAML frontmatter parser for WikiForge atoms.

Provides a single, well-tested parser for atom frontmatter used across
retrieve.py, atom-qa.py, propagate_atom.py, etc.

Usage:
    from frontmatter import parse_frontmatter
    fm, body = parse_frontmatter(atom_text)
    # fm: dict with all frontmatter keys, sources list, etc.
    # body: markdown body after '---' fence

Compiled regexes are also exported for callers that only need a single field
without paying the cost of the full parser (e.g. type/claim sniffing).
"""

import re
from typing import Optional

# Splits an atom file into (fm_text, body_text). Use .match() — anchored at start.
ATOM_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)

# Single-field sniffers. Faster than parse_frontmatter when only one key is needed.
CLAIM_RE = re.compile(r"^claim:\s*(.+?)$", re.MULTILINE)
TYPE_RE = re.compile(r"^type:\s*(\w+)", re.MULTILINE)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from an atom markdown file.

    Returns:
        (frontmatter_dict, body_text)

    The frontmatter dict includes:
    - Top-level keys: claim, topics, lang, confidence, last_verified, url, etc.
    - sources: list of dicts, each with source_id, locator, excerpt, excerpt_source, etc.
    """
    if not text.startswith("---"):
        return {}, text

    end = text.find("---", 3)
    if end == -1:
        return {}, text

    fm_text = text[3:end]
    body = text[end + 3:].strip()

    fm = {}
    sources_list = []
    current_source: Optional[dict] = None
    in_sources = False

    for raw_line in fm_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        # Skip blank lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        # Detect end of sources block: a top-level key (no leading spaces) that isn't a list item
        if in_sources and line and not line[0].isspace() and not stripped.startswith("-"):
            if current_source is not None:
                sources_list.append(current_source)
                current_source = None
            in_sources = False

        # Check if this line starts the sources block
        if stripped.startswith("sources:"):
            in_sources = True
            continue

        # Parse source block entries
        if in_sources:
            if stripped.startswith("- source_id:"):
                # Start of new source
                if current_source is not None:
                    sources_list.append(current_source)
                current_source = {"source_id": stripped.split(":", 1)[1].strip().strip('"')}
            elif current_source is not None and ":" in stripped:
                # Key-value pair within current source
                k, v = stripped.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"')
                current_source[k] = v
            continue

        # Parse top-level key-value pairs
        if ":" in stripped:
            k, v = stripped.split(":", 1)
            k = k.strip()
            v = v.strip()

            # Handle inline lists: [item1, item2]
            if v.startswith("[") and v.endswith("]"):
                v = [x.strip().strip('"') for x in v[1:-1].split(",") if x.strip()]
            else:
                v = v.strip('"')

            fm[k] = v

    # Flush final source if in_sources ended at EOF
    if current_source is not None:
        sources_list.append(current_source)

    if sources_list:
        fm["sources"] = sources_list

    return fm, body
