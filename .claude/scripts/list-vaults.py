#!/usr/bin/env python3
"""list-vaults.py — discovery endpoint.

Enumerates `vaults/*/vault.yml` for any frontend that wants to render a
vault picker. The CLI form prints a human table; `--json` emits a list of
`{name, path, description, languages, vault_path, active}`.

Usage:
    python3 .claude/scripts/list-vaults.py
    python3 .claude/scripts/list-vaults.py --json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import list_vaults

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--json", action="store_true", help="Emit JSON instead of a table")
    args = p.parse_args()

    vaults = list_vaults(REPO_ROOT)

    if args.json:
        print(json.dumps(vaults, ensure_ascii=False, indent=2))
        return 0

    if not vaults:
        print("(no vaults found in vaults/)", file=sys.stderr)
        return 0

    for v in vaults:
        marker = "*" if v["active"] else " "
        langs = ",".join(v["languages"]) or "-"
        print(f"{marker} {v['name']:<32} [{langs}]  {v['description']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
