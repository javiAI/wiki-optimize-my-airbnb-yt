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


def _parse_yaml_lines(lines) -> dict:
    """Shared YAML parser: operates on an iterable of lines (file or text.split()).

    Handles: key: value, nested dicts, inline lists [item1, item2], booleans,
    expanded lists (- item).
    Does NOT handle: anchors, aliases, multi-line literals.
    """
    import re
    result: dict = {}
    # Stack tracks the open container at each indent level. For each entry we
    # also remember the (parent, key) the container is bound to, so we can
    # swap a placeholder dict for a list when the next line turns out to be
    # an expanded list item.
    stack = [result]
    parent_refs: list = [None]  # parallel to stack: (parent, key) or None
    indent_stack = [-1]

    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue
        stripped = line.rstrip()
        indent = len(stripped) - len(stripped.lstrip())
        content = stripped.strip()

        # Pop stack to current indent level (applies to both keys and list items)
        while indent <= indent_stack[-1]:
            stack.pop()
            parent_refs.pop()
            indent_stack.pop()

        if content.startswith("- "):
            parent = stack[-1]
            # If parent is an empty dict that was bound by a previous "key:"
            # with no inline value, retroactively convert it to a list.
            if isinstance(parent, dict) and not parent and parent_refs[-1] is not None:
                grand, key = parent_refs[-1]
                new_list: list = []
                grand[key] = new_list
                stack[-1] = new_list
                parent = new_list
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

            parent = stack[-1]
            if not val or val == "|" or val == ">":
                # Container coming on next line — placeholder dict; may be
                # promoted to a list if a "- " line follows.
                new_obj: Any = {}
                if isinstance(parent, dict):
                    parent[key] = new_obj
                stack.append(new_obj)
                parent_refs.append((parent, key) if isinstance(parent, dict) else None)
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


def _parse_simple_yaml(path: Path) -> dict:
    """Parse YAML from file. Uses shared _parse_yaml_lines()."""
    with open(path) as f:
        return _parse_yaml_lines(f)


def _parse_simple_yaml_from_text(text: str) -> dict:
    """Parse YAML from string. Uses shared _parse_yaml_lines().

    This variant parses a string instead of reading from disk, avoiding
    redundant file I/O when text is already in memory.
    """
    return _parse_yaml_lines(text.split('\n'))


def _walk_dotted(obj: Any, key_path: str, missing: Any) -> Any:
    """Resolve a dot-path against nested dicts. Returns `missing` sentinel
    when any segment doesn't exist. Pass a unique sentinel when None is a
    valid stored value."""
    for p in key_path.split("."):
        if not isinstance(obj, dict) or p not in obj:
            return missing
        obj = obj[p]
    return obj


# ── Plugin config (.claude/wikiforge/config.yaml) ───────────────────────────
# Holds: defaults: (seed values for /init-vault — read ONLY at init-time),
# retrieval / regimes / evaluation (library config). NO runtime mutable state.
#
# Runtime mutable state (active_vault, active_lang) lives in a separate
# .claude/state/wikiforge.yaml file so plugin defaults can be committable
# while the per-installation state stays gitignored.


def _config_path(repo_dir: Path) -> Path:
    """Canonical config location."""
    return repo_dir / ".claude" / "wikiforge" / "config.yaml"


def _state_path(repo_dir: Path) -> Path:
    """Canonical state file. Gitignored, mutates per query/ingest."""
    return repo_dir / ".claude" / "state" / "wikiforge.yaml"


def read_config(repo_dir: Path) -> dict:
    """Read .claude/wikiforge/config.yaml verbatim. Empty dict if missing."""
    p = _config_path(repo_dir)
    if not p.exists():
        return {}
    try:
        return _load_yaml(p) or {}
    except Exception:
        return {}


def read_state(repo_dir: Path) -> dict:
    """Read .claude/state/wikiforge.yaml. Returns {} if missing."""
    p = _state_path(repo_dir)
    if not p.exists():
        return {}
    try:
        return _load_yaml(p) or {}
    except Exception:
        return {}


def write_state(repo_dir: Path, **updates) -> None:
    """Merge `updates` into the state file. Pass None to delete a key.

    Allowed keys: active_vault, active_lang (others are silently dropped).
    """
    allowed = {"active_vault", "active_lang"}
    dst = _state_path(repo_dir)
    dst.parent.mkdir(parents=True, exist_ok=True)

    current = read_state(repo_dir)
    for k, v in updates.items():
        if k not in allowed:
            continue
        if v is None:
            current.pop(k, None)
        else:
            current[k] = v

    lines = [
        "# WikiForge runtime state — written by init-vault, query routing, set-config.sh.",
        "# Gitignored. Do not edit by hand unless you know what you're doing.",
        "",
    ]
    for k in ("active_vault", "active_lang"):
        v = current.get(k)
        if v is not None and v != "":
            lines.append(f"{k}: {v}")
    dst.write_text("\n".join(lines) + "\n")


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


def list_vaults(repo_dir: Path) -> List[dict]:
    """Enumerate vault bundles. Used by .claude/scripts/list-vaults.py
    and by any frontend wanting to render a vault picker.

    Returns `[{name, path, description, languages, vault_path, active}]`.
    """
    vaults_dir = repo_dir / "vaults"
    if not vaults_dir.exists():
        return []
    active = read_state(repo_dir).get("active_vault")
    out: List[dict] = []
    for d in sorted(vaults_dir.iterdir()):
        cfg = d / "vault.yml"
        if not d.is_dir() or not cfg.exists():
            continue
        try:
            data = _load_yaml(cfg) or {}
        except Exception:
            data = {}
        langs = (data.get("languages") or {}).get("enabled") or []
        out.append({
            "name": data.get("name", d.name),
            "path": str(d),
            "description": data.get("description", ""),
            "languages": langs,
            "vault_path": data.get("vault_path", ""),
            "active": data.get("name", d.name) == active,
        })
    return out


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


def kind_dir(vault_path: Path, kind: str, lang: str) -> Path:
    """Resolve `<vault>/<kind>/<lang>` (v1) or `<vault>/<lang>/<kind>` (v2).

    Filesystem-detected: returns whichever path exists. New vaults default
    to v2 (the write-target). Mirror of `VaultConfig._kind_dir` for callers
    that only have a vault data path.
    """
    v2 = vault_path / lang / kind
    if v2.is_dir():
        return v2
    v1 = vault_path / kind / lang
    if v1.is_dir():
        return v1
    return v2


def wikilink_prefix(vault_path: Path, kind: str, lang: str) -> str:
    """Wikilink path prefix for either layout: `{lang}/{kind}` (v2) or `{kind}/{lang}` (v1)."""
    if (vault_path / lang / kind).is_dir():
        return f"{lang}/{kind}"
    if (vault_path / kind / lang).is_dir():
        return f"{kind}/{lang}"
    return f"{lang}/{kind}"


def resolve_query_language(
    repo_dir: Path,
    enabled: List[str],
    explicit: Optional[str] = None,
    query_text: Optional[str] = None,
) -> str:
    """Decide which lang to retrieve in. Order: explicit → auto-detect →
    state.active_lang → enabled[0].
    """
    if explicit:
        return explicit
    if query_text:
        detected = detect_language(query_text, enabled)
        if detected:
            return detected
    cand = read_state(repo_dir).get("active_lang")
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
      5. .claude/state/wikiforge.yaml → last operated vault (active_vault)
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
                    if config_file is None and vaults_dir.exists():
                        # Path is a data dir without vault.yml. Scan bundles for
                        # one whose vault_path: field resolves to this dir.
                        target = p.resolve()
                        for d in vaults_dir.iterdir():
                            cand = d / "vault.yml"
                            if not cand.exists():
                                continue
                            try:
                                vp = _load_yaml(cand).get("vault_path", "")
                            except Exception:
                                continue
                            if vp and Path(vp).expanduser().resolve() == target:
                                config_file = cand
                                bundle_dir = d
                                break

                # Explicit --vault must resolve. Falling through to env / state /
                # auto-select would mask user error: a typo in --vault would
                # silently pick whatever active_vault happens to be.
                if config_file is None:
                    print(
                        f"ERROR: --vault {vault_path!r} did not resolve to any vault.\n"
                        "  Tried: bundle name (vaults/{name}/vault.yml), "
                        "config-file path, data-dir-with-vault.yml, "
                        "and reverse lookup against vaults/*/vault.yml:vault_path.",
                        file=sys.stderr,
                    )
                    if vaults_dir.exists():
                        avail = [d.name for d in vaults_dir.iterdir() if d.is_dir() and (d / "vault.yml").exists()]
                        if avail:
                            print("  Available vaults: " + ", ".join(sorted(avail)), file=sys.stderr)
                    sys.exit(1)

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

        # state/wikiforge.yaml.active_vault → last operated vault.
        if config_file is None:
            active = read_state(repo_dir).get("active_vault", "")
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
        """Dot-path accessor against vault.yml.

        vault.yml is the sole source of truth for per-vault config.
        If a key is missing, returns `default` (or None if not given).
        Use `require()` instead when the field must exist.
        """
        sentinel = object()
        val = _walk_dotted(self._data, key_path, sentinel)
        if val is not sentinel:
            return val
        return default

    def require(self, key_path: str) -> Any:
        """Like `get()` but raises with a hint when the field is missing.

        Use for fields that must be in vault.yml — keeps the failure mode
        loud instead of silently treating absence as "False" or empty.
        """
        sentinel = object()
        val = _walk_dotted(self._data, key_path, sentinel)
        if val is sentinel:
            template = self._repo_dir / ".claude" / "templates" / "vault.yml.template"
            print(
                f"ERROR: required field '{key_path}' missing from {self._config_file}.\n"
                f"  See {template} for the canonical schema.",
                file=sys.stderr,
            )
            sys.exit(1)
        return val

    @property
    def layout(self) -> str:
        """Vault directory layout: 'v1' = `{kind}/{lang}/`, 'v2' = `{lang}/{kind}/`.

        Detected from the filesystem. v2 wins when both shapes exist (migration
        target). Pure-empty vaults default to v2 — that's the layout new files
        should be written in.
        """
        for lang in self.enabled_languages:
            if (self.vault_path / lang / "wiki").is_dir():
                return "v2"
            if (self.vault_path / "wiki" / lang).is_dir():
                return "v1"
        return "v2"

    def _kind_dir(self, kind: str, lang: str) -> Path:
        """Resolve a per-kind, per-lang dir for either layout.

        Returns the existing dir when one is on disk; otherwise the v2 path
        (the write-target for new files).
        """
        v2 = self.vault_path / lang / kind
        if v2.is_dir():
            return v2
        v1 = self.vault_path / kind / lang
        if v1.is_dir():
            return v1
        return v2

    def wikilink_prefix(self, kind: str, lang: str) -> str:
        """Path prefix used inside wikilinks: `wiki/{lang}` (v1) or `{lang}/wiki` (v2)."""
        if self.layout == "v2":
            return f"{lang}/{kind}"
        return f"{kind}/{lang}"

    def wiki_dir(self, lang: str) -> Path:
        return self._kind_dir("wiki", lang)

    def moc_dir(self, lang: str) -> Path:
        return self._kind_dir("moc", lang)

    def index_file(self, lang: str) -> Path:
        return self._kind_dir("index", lang) / "index.md"

    def queries_dir(self, lang: str) -> Path:
        return self._kind_dir("queries", lang)

    def raw_dir(self, lang: str) -> Path:
        """Per-lang raw transcripts directory."""
        return self._kind_dir("raw", lang)

    def meta_dir(self) -> Path:
        return self.vault_path / "meta"

    def state_dir(self) -> Path:
        """Per-vault state dir under the bundle: vaults/{name}/state/.

        Falls back to vault_path/.state/ for legacy vaults without a bundle.
        """
        if self._bundle_dir is not None:
            return self._bundle_dir / "state"
        return self.vault_path / ".state"

    def cache_dir(self) -> Path:
        """Where transient caches live (retrieval index, etc.)."""
        return self.state_dir() / "cache"

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
