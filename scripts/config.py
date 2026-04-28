"""
config.py — Read vault.yaml configuration.
All WikiForge scripts import this instead of hardcoding paths or values.

Usage:
    from config import VaultConfig
    cfg = VaultConfig()                          # auto-finds vault from $VAULT_PATH
    cfg = VaultConfig("/path/to/vault")          # explicit vault path
    print(cfg.languages)                         # ['en', 'es']
    print(cfg.topics)                            # [{'id': 'pricing', 'name': '...'}]
    print(cfg.get("pipeline.auto_translate"))    # True
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


class VaultConfig:
    """Reads vault.yaml and provides typed accessors."""

    def __init__(self, vault_path: Optional[str] = None):
        if vault_path is None:
            vault_path = os.environ.get("VAULT_PATH")
        if vault_path is None:
            # Try reading from config.sh
            config_sh = Path(__file__).parent / "config.sh"
            if config_sh.exists():
                for line in config_sh.read_text().splitlines():
                    if "VAULT_PATH=" in line:
                        vault_path = line.split("=", 1)[1].strip().strip('"\'')
                        vault_path = vault_path.replace("$HOME", str(Path.home()))
                        break
        if vault_path is None:
            print("ERROR: VAULT_PATH not set. Set $VAULT_PATH or pass vault_path argument.", file=sys.stderr)
            sys.exit(1)

        self.vault_path = Path(vault_path).expanduser().resolve()
        config_file = self.vault_path / "vault.yaml"
        if not config_file.exists():
            print(f"ERROR: vault.yaml not found at {config_file}", file=sys.stderr)
            sys.exit(1)

        self._data = _load_yaml(config_file)

    @property
    def name(self) -> str:
        return self._data.get("name", "unknown")

    @property
    def languages(self) -> List[str]:
        lang = self._data.get("languages", {})
        return lang.get("enabled", ["en"])

    @property
    def primary_language(self) -> str:
        return self._data.get("languages", {}).get("primary", "en")

    @property
    def secondary_languages(self) -> List[str]:
        return self._data.get("languages", {}).get("secondary", [])

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

    def raw_dir(self) -> Path:
        return self.vault_path / "raw"

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

    try:
        cfg = VaultConfig(_args.vault)
    except SystemExit as e:
        print(f"ERROR: config load failed", file=sys.stderr)
        sys.exit(1)

    summary = {
        "name": cfg.name,
        "primary_language": cfg.primary_language,
        "languages": cfg.languages,
        "topics": cfg.topic_ids,
        "source_type": cfg.source_type,
        "auto_translate": cfg.get("pipeline.auto_translate"),
        "vault_path": str(cfg.vault_path),
    }

    if _args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif _args.validate:
        print(f"[OK] vault.yaml valid — {cfg.name} ({', '.join(cfg.languages)})")
    else:
        for k, v in summary.items():
            print(f"{k}: {v}")
