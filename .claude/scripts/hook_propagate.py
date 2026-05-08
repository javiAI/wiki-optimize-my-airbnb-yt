"""
hook_propagate.py — single-call helper for on-file-write.sh.

Replaces 4 separate `python3 -c` invocations (auto_refine, auto_propagate,
atomization_lang, enabled_languages) with one process that reads VaultConfig
once and prints all four values. The shell parses with `read` line-by-line.

Usage:
    FILE=/path/to/atom.md LANG=es python3 .claude/scripts/hook_propagate.py

Output (4 lines, in order):
    auto_refine={true|false}
    auto_propagate={true|false}
    atomization_lang={lang}
    enabled={space-separated langs}
"""

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import VaultConfig


def _atomization_lang(cfg: VaultConfig, atom_file: str, fallback_lang: str) -> str:
    """Resolve atomization_lang by looking up the source video's native_lang."""
    atom = Path(atom_file)
    if not atom.exists():
        return fallback_lang
    text = atom.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^\s*-\s*source_id:\s*(\S+)", text, re.MULTILINE)
    if not m:
        return fallback_lang
    sid = m.group(1)
    for lang in cfg.enabled_languages:
        raw_dir = cfg.raw_dir(lang)
        if not raw_dir.is_dir():
            continue
        for raw in raw_dir.glob("*.md"):
            rt = raw.read_text(encoding="utf-8", errors="replace")
            if re.search(rf"^video_id:\s*{re.escape(sid)}\s*$", rt, re.MULTILINE):
                n = re.search(r"^native_lang:\s*(\S+)", rt, re.MULTILINE)
                if n:
                    return cfg.atomization_lang_for(n.group(1).strip())
    return fallback_lang


def main():
    atom_file = os.environ.get("FILE", "")
    lang = os.environ.get("LANG", "")

    cfg = VaultConfig()

    auto_refine = bool(cfg.get("pipeline.auto_refine", False))
    auto_propagate = cfg.get("pipeline.auto_propagate")
    if auto_propagate is None:
        auto_propagate = cfg.get("pipeline.auto_translate", False)
    auto_propagate = bool(auto_propagate)

    if auto_propagate and atom_file:
        atomization_lang = _atomization_lang(cfg, atom_file, lang)
    else:
        atomization_lang = lang

    enabled = " ".join(cfg.enabled_languages)

    print(f"auto_refine={'true' if auto_refine else 'false'}")
    print(f"auto_propagate={'true' if auto_propagate else 'false'}")
    print(f"atomization_lang={atomization_lang}")
    print(f"enabled={enabled}")


if __name__ == "__main__":
    main()
