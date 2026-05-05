"""
config.py — Read per-vault config from vaults/{name}/vault.yml.

All WikiForge scripts import this instead of hardcoding paths or values.

Usage:
    from config import VaultConfig
    cfg = VaultConfig()                          # auto-finds via $VAULT_NAME or single bundle
    cfg = VaultConfig("optimize-my-airbnb-yt")   # explicit vault name
    cfg = VaultConfig("/abs/path/to/vault.yml")  # explicit config file
    print(cfg.enabled_languages)                 # ['es', 'en']
    print(cfg.get("pipeline.auto_propagate"))    # False (legacy alias: auto_translate)
"""

import os
import sys
from pathlib import Path
from typing import Any, List, Optional


def _load_yaml(path: Path) -> dict:
    """Load YAML without requiring PyYAML — minimal inline parser for simple configs."""
    try:
        import yaml
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # Fallback: basic key: value parser sufficient for vault.yaml structure
        return _parse_simple_yaml(path)


def _load_yaml_from_text(text: str) -> dict:
    """Load YAML from a string (avoids re-reading file when text already loaded)."""
    if not text:
        return {}
    try:
        import yaml
        return yaml.safe_load(text) or {}
    except ImportError:
        # Fallback: basic key: value parser
        return _parse_simple_yaml_from_text(text)


def _parse_simple_yaml(path: Path) -> dict:
    """Minimal YAML parser for simple key: value and nested dicts (no anchors/aliases)."""
    import re
    result = {}
    stack = [result]
    indent_stack = [-1]

    with open(path) as f:
        for line in f:
            if not line.strip() or line.strip().startswith("#"):
                continue
            stripped = line.rstrip()
            indent = len(stripped) - len(stripped.lstrip())
            content = stripped.strip()

            if content.startswith("- "):
                # List item
                parent = stack[-1]
                if isinstance(parent, list):
                    item = content[2:].strip()
                    # Inline dict: {id: x, name: y}
                    m = re.match(r'^\{(.+)\}$', item)
                    if m:
                        d = {}
                        for pair in re.findall(r'(\w+):\s*"?([^",}]+)"?', m.group(1)):
                            d[pair[0]] = pair[1].strip()
                        parent.append(d)
                    else:
                        item = item.strip('"\'')
                        parent.append(item)
            elif ":" in content:
                key, _, val = content.partition(":")
                key = key.strip()
                val = val.strip()

                # Pop stack to current indent level
                while indent <= indent_stack[-1]:
                    stack.pop()
                    indent_stack.pop()

                parent = stack[-1]
                if not val or val == "|" or val == ">":
                    # Nested dict or list coming
                    new_obj: Any = {}
                    if isinstance(parent, dict):
                        parent[key] = new_obj
                    stack.append(new_obj)
                    indent_stack.append(indent)
                elif val.startswith("["):
                    # Inline list
                    items = re.findall(r'[\w-]+', val)
                    if isinstance(parent, dict):
                        parent[key] = items
                elif val.lower() in ("true", "yes"):
                    if isinstance(parent, dict):
                        parent[key] = True
                elif val.lower() in ("false", "no"):
                    if isinstance(parent, dict):
                        parent[key] = False
                else:
                    val = val.strip('"\'')
                    if isinstance(parent, dict):
                        parent[key] = val

    return result


def _parse_simple_yaml_from_text(text: str) -> dict:
    """Minimal YAML parser for simple key: value and nested dicts (no anchors/aliases).

    This variant parses a string instead of reading from disk, avoiding redundant
    file I/O when text is already in memory.
    """
    import re
    result = {}
    stack = [result]
    indent_stack = [-1]

    for line in text.split('\n'):
        if not line.strip() or line.strip().startswith("#"):
            continue
        stripped = line.rstrip()
        indent = len(stripped) - len(stripped.lstrip())
        content = stripped.strip()

        if content.startswith("- "):
            parent = stack[-1]
            if isinstance(parent, list):
                item = content[2:].strip()
                m = re.match(r'^\{(.+)\}$', item)
                if m:
                    d = {}
                    for pair in re.findall(r'(\w+):\s*"?([^",}]+)"?', m.group(1)):
                        d[pair[0]] = pair[1].strip()
                    parent.append(d)
                else:
                    item = item.strip('"\'')
                    parent.append(item)
        elif ":" in content:
            key, _, val = content.partition(":")
            key = key.strip()
            val = val.strip()

            while indent <= indent_stack[-1]:
                stack.pop()
                indent_stack.pop()

            parent = stack[-1]
            if not val or val == "|" or val == ">":
                new_obj: Any = {}
                if isinstance(parent, dict):
                    parent[key] = new_obj
                stack.append(new_obj)
                indent_stack.append(indent)
            elif val.startswith("["):
                items = re.findall(r'[\w-]+', val)
                if isinstance(parent, dict):
                    parent[key] = items
            elif val.lower() in ("true", "yes"):
                if isinstance(parent, dict):
                    parent[key] = True
            elif val.lower() in ("false", "no"):
                if isinstance(parent, dict):
                    parent[key] = False
            else:
                val = val.strip('"\'')
                if isinstance(parent, dict):
                    parent[key] = val

    return result


# ── Repo config (.claude/config/config.yaml) ────────────────────────────────
# config.yaml is the unified configuration file holding:
# - current selection (active_vault, active_lang)
# - retrieval backend choice and parameters

def _config_path(repo_dir: Path) -> Path:
    return repo_dir / ".claude" / "config" / "config.yaml"


def read_config(repo_dir: Path) -> dict:
    """Read config.yaml. Returns empty dict if not found or invalid.

    This is the canonical config file. Legacy state.yaml and active-vault
    are no longer read (were deprecated in favor of unified config.yaml).
    """
    p = _config_path(repo_dir)
    if p.exists():
        try:
            return _load_yaml(p) or {}
        except Exception:
            return {}
    return {}


def write_config(repo_dir: Path, **updates) -> None:
    """Merge `updates` into config.yaml. Pass None to delete a key.

    Merges updates into current config while preserving the entire file structure.
    Uses hand-written YAML only for top-level keys; preserves sections like
    `retrieval:` and all their nested content exactly as-is.

    Allowed keys: active_vault, active_lang (others are silently dropped).
    """
    p = _config_path(repo_dir)
    p.parent.mkdir(parents=True, exist_ok=True)

    # Read current file as raw text (to preserve formatting and comments)
    current_text = p.read_text() if p.exists() else ""

    # Parse config from same text (avoids second file read)
    current = _load_yaml_from_text(current_text)

    # Merge updates
    for k, v in updates.items():
        if v is None:
            current.pop(k, None)
        else:
            current[k] = v

    # Rebuild: preserve comments + structure for retrieval section,
    # but update top-level state keys (active_vault, active_lang)
    lines = [
        "# WikiForge unified configuration",
        "# Holds: vault selection, language, retrieval backend choice, and backend-specific settings",
        "# Written by init-vault.sh, ingest hooks, and query routing",
        "",
    ]

    # Write updated top-level fields
    for k in ["active_vault", "active_lang"]:
        v = current.get(k)
        if v is not None and v != "":
            lines.append(f"{k}: {v}")

    # Preserve retrieval section from current file if it exists,
    # otherwise write it from parsed config
    if "retrieval:" in current_text:
        # Extract and preserve the original retrieval block
        lines.append("")
        lines.append("# === RETRIEVAL BACKEND ===")
        lines.append("#")
        lines.append("# Currently implemented: BM25, LLM (as primary backend or fallback)")
        lines.append("# The fields below are READ and USED by .claude/scripts/retrieve.py")
        lines.append("#")
        lines.append("retrieval:")

        # Extract retrieval subsection from original text
        in_retrieval = False
        for line in current_text.split("\n"):
            if line.startswith("retrieval:"):
                in_retrieval = True
                continue
            elif in_retrieval:
                # Stop at next top-level key (no indent)
                if line and not line[0].isspace() and line.strip():
                    break
                # Preserve the line as-is (comments, values, indentation, and blank lines)
                lines.append(line)

    p.write_text("\n".join(lines) + "\n")


# ── Language auto-detection ──────────────────────────────────────────────────
# Lightweight heuristic, no extra deps. Sufficient for en/es disambiguation
# (the only langs we ship today). For more langs, swap in `langdetect` later
# without changing the call site.

_LANG_MARKERS: dict = {
    "es": {
        "chars": set("ñáéíóúü¿¡"),
        "stopwords": {
            "que", "de", "la", "el", "los", "las", "y", "a", "en", "un", "una",
            "es", "se", "por", "para", "con", "como", "cómo", "cuál", "cuáles",
            "qué", "cuánto", "cuántos", "cuánta", "cuántas", "dónde", "cuándo",
            "del", "al", "lo", "mi", "tu", "su", "este", "esta", "estos",
            "estas", "muy", "más", "pero", "si", "sí", "no", "ya", "porque",
        },
    },
    "en": {
        "chars": set(),
        "stopwords": {
            "the", "is", "are", "was", "were", "a", "an", "to", "of", "in",
            "on", "for", "with", "by", "as", "at", "from", "how", "what",
            "which", "when", "where", "why", "who", "should", "do", "does",
            "did", "can", "could", "would", "will", "and", "or", "but", "if",
            "this", "that", "these", "those", "my", "your", "i", "you",
        },
    },
}


def detect_language(text: str, enabled: List[str]) -> Optional[str]:
    """Return the most likely lang from `enabled`, or None if undecidable.

    Score = lang-specific chars (×2) + stopword hits (×1). Tie or zero → None
    (caller falls back to config.active_lang or enabled[0]).
    """
    if not text or not enabled:
        return None
    lower = text.lower()
    words = set(w.strip(".,;:!?¿¡()[]\"'`") for w in lower.split())
    scores: dict = {}
    for lang in enabled:
        marker = _LANG_MARKERS.get(lang)
        if not marker:
            continue
        char_hits = sum(1 for c in lower if c in marker["chars"])
        stop_hits = len(words & marker["stopwords"])
        scores[lang] = char_hits * 2 + stop_hits
    if not scores:
        return None
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return None
    # Reject ties
    sorted_scores = sorted(scores.values(), reverse=True)
    if len(sorted_scores) > 1 and sorted_scores[0] == sorted_scores[1]:
        return None
    return best


def resolve_query_language(
    repo_dir: Path,
    enabled: List[str],
    explicit: Optional[str] = None,
    query_text: Optional[str] = None,
) -> str:
    """Decide which lang to retrieve in. Order: explicit → auto-detect →
    config.active_lang → enabled[0].
    """
    if explicit:
        return explicit
    if query_text:
        detected = detect_language(query_text, enabled)
        if detected:
            return detected
    config = read_config(repo_dir)
    cand = config.get("active_lang")
    if cand and cand in enabled:
        return cand
    return enabled[0]


class VaultConfig:
    """Reads per-vault config from vaults/{name}/vault.yml.

    Resolution order (first match wins):
      1. explicit arg → vaults/{arg}/vault.yml
      2. explicit arg → absolute path to a .yml/.yaml file
      3. explicit arg → directory containing vault.yml or vault.yaml
      4. $VAULT_NAME env  → vaults/{name}/vault.yml
      5. .claude/config/config.yaml → last operated vault (active_vault)
      6. vaults/*/vault.yml → auto-select if exactly one bundle exists
      7. 2+ bundles, no signal → loud error, refuse to guess
      8. $VAULT_PATH env  → directory with vault.yaml (legacy fallback)
    """

    def __init__(self, vault_path: Optional[str] = None):
        # __file__ is at .claude/scripts/config.py — repo root is two levels up
        repo_dir = Path(__file__).parent.parent.parent
        self._repo_dir = repo_dir
        vaults_dir = repo_dir / "vaults"

        # Reject empty string up front. Without this, `Path("")` becomes `Path(".")`
        # and the dir-scan branch below could silently latch onto whatever vault.yml
        # happens to live in the current working directory.
        if isinstance(vault_path, str) and vault_path.strip() == "":
            print(
                "ERROR: --vault was passed an empty string.\n"
                "  Either omit --vault (uses $VAULT_NAME or active-vault), "
                "or pass a vault name / path.",
                file=sys.stderr,
            )
            sys.exit(2)

        config_file: Optional[Path] = None
        bundle_dir: Optional[Path] = None

        if vault_path is not None:
            # Try as vault name first
            candidate = vaults_dir / vault_path / "vault.yml"
            if candidate.exists():
                config_file = candidate
                bundle_dir = candidate.parent
            else:
                p = Path(vault_path).expanduser()
                if p.is_file() and p.suffix in (".yml", ".yaml"):
                    config_file = p
                    if p.parent.parent.name == "vaults":
                        bundle_dir = p.parent
                elif p.is_dir():
                    for fname in ("vault.yml", "vault.yaml"):
                        cand = p / fname
                        if cand.exists():
                            config_file = cand
                            if p.parent.name == "vaults":
                                bundle_dir = p
                            break

        # $VAULT_NAME env var
        if config_file is None:
            vault_name = os.environ.get("VAULT_NAME")
            if vault_name:
                candidate = vaults_dir / vault_name / "vault.yml"
                if candidate.exists():
                    config_file = candidate
                    bundle_dir = candidate.parent
                else:
                    # VAULT_NAME pointed at a missing bundle — loud, no fallback.
                    print(
                        f"ERROR: VAULT_NAME={vault_name} but vaults/{vault_name}/vault.yml does not exist.",
                        file=sys.stderr,
                    )
                    if vaults_dir.exists():
                        avail = [d.name for d in vaults_dir.iterdir() if d.is_dir() and (d / "vault.yml").exists()]
                        if avail:
                            print("Available vaults: " + ", ".join(sorted(avail)), file=sys.stderr)
                    sys.exit(1)

        # config.yaml.active_vault (or legacy files) → last operated vault.
        if config_file is None:
            active = read_config(repo_dir).get("active_vault", "")
            if active:
                cand = vaults_dir / active / "vault.yml"
                if cand.exists():
                    config_file = cand
                    bundle_dir = cand.parent

        # Auto-select bundle. Single → silent. Multiple → loud refusal.
        if config_file is None and vaults_dir.exists():
            bundles = [d for d in vaults_dir.iterdir() if d.is_dir() and (d / "vault.yml").exists()]
            if len(bundles) == 1:
                config_file = bundles[0] / "vault.yml"
                bundle_dir = bundles[0]
            elif len(bundles) > 1:
                names = sorted(d.name for d in bundles)
                print(
                    f"ERROR: vault is ambiguous — {len(bundles)} bundles exist and none is selected.\n"
                    f"  Available: {', '.join(names)}\n"
                    "  Pick one with:  export VAULT_NAME=<name>\n"
                    "  Or set the active default:  bash .claude/scripts/set-config.sh active_vault <name>",
                    file=sys.stderr,
                )
                sys.exit(1)

        # Legacy $VAULT_PATH env var
        if config_file is None:
            vault_env = os.environ.get("VAULT_PATH")
            if vault_env:
                p = Path(vault_env).expanduser()
                if (p / "vault.yaml").exists():
                    config_file = p / "vault.yaml"

        if config_file is None:
            print(
                "ERROR: no vault config found.\n"
                "  Create vaults/{name}/vault.yml, then set $VAULT_NAME or pass the name as an argument.",
                file=sys.stderr,
            )
            sys.exit(1)

        if not config_file.exists():
            print(f"ERROR: vault config not found at {config_file}", file=sys.stderr)
            sys.exit(1)

        self._data = _load_yaml(config_file)
        self._config_file = config_file
        self._bundle_dir = bundle_dir  # vaults/{name}/, or None for legacy

        vp = self._data.get("vault_path")
        if vp:
            self.vault_path = Path(vp).expanduser().resolve()
        elif bundle_dir is not None:
            print(
                f"ERROR: vault_path not declared in {config_file}.\n"
                "  Add: vault_path: ~/Dev/obsidian_vaults/{vault-name}",
                file=sys.stderr,
            )
            sys.exit(1)
        else:
            self.vault_path = config_file.parent.resolve()

    @property
    def name(self) -> str:
        return self._data.get("name", "unknown")

    @property
    def languages(self) -> List[str]:
        """All wiki languages enabled for this vault. No primary/secondary distinction.

        Source of truth: `languages.enabled` in vault.yml (required, no fallback).
        Atomization language is decided per-source via `atomization_lang_for()`.
        """
        lang = self._data.get("languages", {})
        enabled = lang.get("enabled")
        return enabled if enabled else []

    @property
    def enabled_languages(self) -> List[str]:
        """Alias for `languages`. Preferred over `languages` in new code."""
        return self.languages

    def atomization_lang_for(self, native_lang: Optional[str]) -> str:
        """Decide which language a video gets atomized in.

        Rule: if native_lang ∈ enabled, atomize in native_lang (preserves creator
        voice in claim+body). Otherwise atomize in enabled[0] — the LLM does a
        single combined translate-and-atomize pass from the native transcript.
        """
        enabled = self.enabled_languages
        if not enabled:
            return native_lang or "en"
        if native_lang and native_lang in enabled:
            return native_lang
        return enabled[0]

    @property
    def topics(self) -> List[dict]:
        return self._data.get("topics", [])

    @property
    def topic_ids(self) -> List[str]:
        return [t["id"] if isinstance(t, dict) else t for t in self.topics]

    @property
    def source_type(self) -> str:
        return self._data.get("source", {}).get("type", "youtube")

    def get(self, key_path: str, default=None) -> Any:
        """Dot-path accessor: cfg.get('pipeline.auto_translate')"""
        parts = key_path.split(".")
        obj = self._data
        for p in parts:
            if not isinstance(obj, dict):
                return default
            obj = obj.get(p, default)
        return obj

    def wiki_dir(self, lang: str) -> Path:
        return self.vault_path / "wiki" / lang

    def moc_dir(self, lang: str) -> Path:
        return self.vault_path / "moc" / lang

    def index_file(self, lang: str) -> Path:
        return self.vault_path / "index" / lang / "index.md"

    def queries_dir(self, lang: str) -> Path:
        return self.vault_path / "queries" / lang

    def raw_dir(self, lang: Optional[str] = None) -> Path:
        """Raw transcripts directory.

        Multilingual layout: raw/{lang}/{video}.md (one file per video per
        available subtitle language). Pass `lang` to get the lang-specific
        subdir; omit for the parent `raw/`.
        """
        base = self.vault_path / "raw"
        if lang is None:
            return base
        return base / lang

    def meta_dir(self) -> Path:
        return self.vault_path / "meta"

    def source_dir(self) -> Path:
        """Legacy path (sources/ → raw/ migration compatibility)."""
        raw = self.vault_path / "raw"
        if raw.exists():
            return raw
        return self.vault_path / "sources"


if __name__ == "__main__":
    import json
    import argparse as _ap

    _p = _ap.ArgumentParser(description="Validate and display vault config")
    _p.add_argument("--vault", default=None)
    _p.add_argument("--validate", action="store_true", help="Validate only (exit 0=ok, 1=error)")
    _p.add_argument("--json", action="store_true", help="Output as JSON")
    _args = _p.parse_args()

    cfg = VaultConfig(_args.vault)

    summary = {
        "name": cfg.name,
        "enabled_languages": cfg.enabled_languages,
        "topics": cfg.topic_ids,
        "source_type": cfg.source_type,
        "auto_propagate": cfg.get("pipeline.auto_propagate", cfg.get("pipeline.auto_translate")),
        "vault_path": str(cfg.vault_path),
    }

    if _args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif _args.validate:
        print(f"[OK] vault.yml valid — {cfg.name} ({', '.join(cfg.enabled_languages)})")
    else:
        for k, v in summary.items():
            print(f"{k}: {v}")
