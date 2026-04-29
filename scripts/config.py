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
    """Reads vault config and provides typed accessors.

    Resolution order (first match wins):
      1. explicit vault_path arg → directory containing vault.yaml
      2. explicit vault_path arg → name matching configs/{name}.yaml in repo
      3. $VAULT_NAME env var     → configs/{VAULT_NAME}.yaml in repo
      4. $VAULT_PATH env var     → vault directory containing vault.yaml (legacy)
      5. configs/*.yaml          → auto-select if exactly one file exists
    """

    def __init__(self, vault_path: Optional[str] = None):
        repo_dir = Path(__file__).parent.parent
        configs_dir = repo_dir / "configs"

        config_file: Optional[Path] = None

        # Resolve config file from argument
        if vault_path is not None:
            p = Path(vault_path).expanduser()
            if p.is_dir() and (p / "vault.yaml").exists():
                # Passed a vault directory directly (legacy)
                config_file = p / "vault.yaml"
            elif (configs_dir / f"{vault_path}.yaml").exists():
                # Passed a vault name
                config_file = configs_dir / f"{vault_path}.yaml"
            elif p.is_file() and p.suffix in (".yaml", ".yml"):
                config_file = p

        # VAULT_NAME env var → configs/{name}.yaml
        if config_file is None:
            vault_name = os.environ.get("VAULT_NAME")
            if vault_name:
                candidate = configs_dir / f"{vault_name}.yaml"
                if candidate.exists():
                    config_file = candidate

        # VAULT_PATH env var → vault dir (legacy)
        if config_file is None:
            vault_env = os.environ.get("VAULT_PATH")
            if vault_env:
                p = Path(vault_env).expanduser()
                if (p / "vault.yaml").exists():
                    config_file = p / "vault.yaml"

        # Auto-select if exactly one config exists
        if config_file is None and configs_dir.exists():
            yamls = list(configs_dir.glob("*.yaml"))
            if len(yamls) == 1:
                config_file = yamls[0]

        # config.sh fallback (legacy)
        if config_file is None:
            config_sh = Path(__file__).parent / "config.sh"
            if config_sh.exists():
                for line in config_sh.read_text().splitlines():
                    if "VAULT_PATH=" in line and not line.strip().startswith("#"):
                        vp = line.split("=", 1)[1].strip().strip('"\'')
                        vp = vp.replace("$HOME", str(Path.home()))
                        p = Path(vp).expanduser()
                        if (p / "vault.yaml").exists():
                            config_file = p / "vault.yaml"
                        break

        if config_file is None:
            print(
                "ERROR: no vault config found.\n"
                "  Set $VAULT_NAME (e.g. export VAULT_NAME=my-vault) and create configs/my-vault.yaml,\n"
                "  or pass the vault name/path as an argument.",
                file=sys.stderr,
            )
            sys.exit(1)

        if not config_file.exists():
            print(f"ERROR: vault config not found at {config_file}", file=sys.stderr)
            sys.exit(1)

        self._data = _load_yaml(config_file)
        self._config_file = config_file

        # vault_path: prefer explicit field in config, then infer from config location
        vp = self._data.get("vault_path")
        if vp:
            self.vault_path = Path(vp).expanduser().resolve()
        elif config_file.parent.name == "configs":
            # Config lives in repo/configs/ — vault_path must be declared in YAML
            print(
                f"ERROR: vault_path not declared in {config_file}.\n"
                "  Add: vault_path: ~/Dev/obsidian_vaults/{vault-name}",
                file=sys.stderr,
            )
            sys.exit(1)
        else:
            # Legacy: config lives inside the vault directory
            self.vault_path = config_file.parent.resolve()

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
