"""
atom-qa.py — Quality gate for WikiForge atoms.

Checks per atom (per language):
  1. Completeness: claim, ≥1 source with url, last_verified
  2. URL format: sources[].url is a valid deep link
  3. Anglicism (secondary langs only): prohibited English words in body text
  4. Conflict: claim overlaps with meta/contradictions.md entries

Usage:
    python3 scripts/atom-qa.py pricing--base-price --lang en
    python3 scripts/atom-qa.py pricing--base-price --lang es
    python3 scripts/atom-qa.py --all --lang es
    python3 scripts/atom-qa.py --all          # checks all langs enabled in vault.yaml

Output: meta/qa-reports/{stem}.{lang}.json
Exit code: 0 = pass or warnings only, 1 = critical failures found
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


ANGLICISM_TABLE = [
    ("host", "anfitrión"),
    ("hosts", "anfitriones"),
    ("guest", "huésped"),
    ("guests", "huéspedes"),
    ("review", "reseña"),
    ("reviews", "reseñas"),
    ("rating", "calificación"),
    ("amenity", "comodidad"),
    ("amenities", "comodidades"),
    ("booking", "reserva"),
    ("bookings", "reservas"),
    ("listing", "anuncio"),
    ("listings", "anuncios"),
    ("check-in", "entrada"),
    ("check-out", "salida"),
    ("weekend", "fin de semana"),
    ("last-minute", "último momento"),
    ("min-stay", "estancia mínima"),
    ("base price", "precio base"),
    ("funnel", "embudo"),
    ("ranking", "posicionamiento"),
    ("occupancy", "ocupación"),
    ("revenue", "ingresos"),
    ("cleaner", "personal de limpieza"),
    ("cleaners", "personal de limpieza"),
    ("turnover", "rotación"),
    ("pet-friendly", "admite mascotas"),
    ("hot tub", "jacuzzi"),
    ("smart-lock", "cerradura inteligente"),
    ("workspace", "zona de trabajo"),
    ("king bed", "cama king"),
    ("sweet spot", "punto óptimo"),
    ("follow-up", "seguimiento"),
    ("repeat guest", "huésped recurrente"),
    ("social proof", "prueba social"),
    ("take rate", "comisión"),
    ("fee", "tarifa"),
    ("tier", "nivel"),
]

ANGLICISM_WHITELIST = {
    "PriceLabs", "Wheelhouse", "Beyond", "Hostfully", "Hospitable", "Guesty",
    "OwnerRez", "Airbnb", "Booking", "Vrbo", "AllTheRooms", "AirDNA",
    "NoiseAware", "Minut", "Google", "YouTube", "Superhost", "Aircover",
    "Instant Book", "Stays", "Co-Host", "WiFi", "PMS", "API", "URL", "OS",
    "JSON", "YAML", "SEO", "ADR", "BLT", "FPG", "TOS", "GMB", "StayFi",
    "IntelliHost", "check-in",  # operational term allowed in context
}


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from atom markdown. Returns (frontmatter_dict, body)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end]
    body = text[end + 3:].strip()

    fm = {}
    current_key = None
    sources_list = []
    in_sources = False
    current_source = {}

    for line in fm_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line.startswith("sources:"):
            in_sources = True
            current_key = "sources"
            continue

        if in_sources:
            if stripped.startswith("- source_id:"):
                if current_source:
                    sources_list.append(current_source)
                current_source = {"source_id": stripped.split(":", 1)[1].strip()}
            elif current_source is not None:
                if ":" in stripped:
                    k, v = stripped.split(":", 1)
                    k, v = k.strip(), v.strip().strip('"')
                    current_source[k] = v
            # Detect end of sources block
            if not line.startswith(" ") and ":" in stripped and not stripped.startswith("-"):
                in_sources = False
                if current_source:
                    sources_list.append(current_source)
                    current_source = {}
                current_key = None
                k, v = stripped.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
            continue

        if ":" in stripped:
            k, v = stripped.split(":", 1)
            k, v = k.strip(), v.strip().strip('"')
            if v.startswith("[") and v.endswith("]"):
                v = [x.strip().strip('"') for x in v[1:-1].split(",") if x.strip()]
            fm[k] = v

    if current_source:
        sources_list.append(current_source)
    if sources_list:
        fm["sources"] = sources_list

    return fm, body


def check_completeness(fm: dict) -> list[dict]:
    violations = []
    if not fm.get("claim"):
        violations.append({"type": "missing_claim", "severity": "critical",
                           "message": "Missing required field: claim"})
    sources = fm.get("sources", [])
    if not sources:
        violations.append({"type": "missing_sources", "severity": "critical",
                           "message": "No sources defined"})
    else:
        for i, src in enumerate(sources):
            if not src.get("url"):
                violations.append({"type": "missing_url", "severity": "warning",
                                   "message": f"Source [{i}] {src.get('source_id', '?')} has no url field",
                                   "auto_fixable": True})
    if not fm.get("last_verified"):
        violations.append({"type": "missing_last_verified", "severity": "warning",
                           "message": "Missing last_verified date"})
    return violations


def check_url_format(fm: dict, source_type: str = "youtube") -> list[dict]:
    violations = []
    sources = fm.get("sources", [])
    youtube_pattern = re.compile(r'^https://youtube\.com/watch\?v=[\w-]+&t=\d+$')
    for i, src in enumerate(sources):
        url = src.get("url", "")
        if not url:
            continue
        if source_type == "youtube" and not youtube_pattern.match(url):
            violations.append({"type": "invalid_url_format", "severity": "warning",
                               "message": f"Source [{i}] URL format invalid: {url}"})
    return violations


def check_anglicisms(body: str, lang: str) -> list[dict]:
    """Check body text for prohibited English words (secondary languages only)."""
    violations = []
    if lang == "en":
        return violations  # Primary language — no anglicism check

    body_lower = body.lower()
    for english, spanish in ANGLICISM_TABLE:
        # Skip if it's in the whitelist (case-sensitive check)
        if any(english.lower() == w.lower() for w in ANGLICISM_WHITELIST):
            continue
        # Word-boundary match
        pattern = r'\b' + re.escape(english.lower()) + r'\b'
        if re.search(pattern, body_lower):
            violations.append({
                "type": "anglicism",
                "severity": "warning",
                "message": f'Found "{english}" — use "{spanish}" instead',
                "auto_fixable": False
            })

    return violations


def check_conflicts(stem: str, fm: dict, meta_dir: Path) -> list[dict]:
    violations = []
    contradictions_file = meta_dir / "contradictions.md"
    if not contradictions_file.exists():
        return violations

    content = contradictions_file.read_text()
    # Check if this atom is mentioned in contradictions (simple name match)
    if stem in content:
        violations.append({
            "type": "known_conflict",
            "severity": "info",
            "message": f"Atom '{stem}' appears in meta/contradictions.md — verify conflict is documented"
        })
    return violations


def run_qa(
    stem: str,
    lang: str,
    vault_path: Path,
    source_type: str = "youtube",
    write_report: bool = True,
) -> dict:
    """Run all QA checks on a single atom. Returns the QA report dict."""
    sys.path.insert(0, str(Path(__file__).parent))

    wiki_dir = vault_path / "wiki" / lang
    if not wiki_dir.exists():
        wiki_dir = vault_path / "notes"  # Legacy fallback

    atom_file = wiki_dir / f"{stem}.md"
    if not atom_file.exists():
        return {"atom": stem, "lang": lang, "pass": False, "error": f"File not found: {atom_file}"}

    text = atom_file.read_text()
    fm, body = _parse_frontmatter(text)

    violations = []
    violations += check_completeness(fm)
    violations += check_url_format(fm, source_type)
    violations += check_anglicisms(body, lang)
    violations += check_conflicts(stem, fm, vault_path / "meta")

    critical = [v for v in violations if v.get("severity") == "critical"]
    warnings = [v for v in violations if v.get("severity") == "warning"]
    infos = [v for v in violations if v.get("severity") == "info"]

    report = {
        "atom": stem,
        "lang": lang,
        "timestamp": datetime.now().isoformat(),
        "pass": len(critical) == 0,
        "critical_count": len(critical),
        "warning_count": len(warnings),
        "violations": violations,
        "auto_fixable": [v for v in violations if v.get("auto_fixable")]
    }

    if write_report:
        qa_dir = vault_path / "meta" / "qa-reports"
        qa_dir.mkdir(parents=True, exist_ok=True)
        report_file = qa_dir / f"{stem}.{lang}.json"
        report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    return report


def run_all(lang: str, vault_path: Path, source_type: str = "youtube") -> dict:
    """Run QA on all atoms for a given language."""
    wiki_dir = vault_path / "wiki" / lang
    if not wiki_dir.exists():
        if lang == "en":
            wiki_dir = vault_path / "notes"
        else:
            print(f"  No wiki/{lang}/ directory found — skipping")
            return {}

    results = {}
    atom_files = sorted(wiki_dir.glob("*.md"))
    total = len(atom_files)
    passed = 0
    failed = 0

    for atom_file in atom_files:
        stem = atom_file.stem
        report = run_qa(stem, lang, vault_path, source_type)
        results[stem] = report
        if report.get("pass"):
            passed += 1
        else:
            failed += 1
            print(f"  FAIL [{lang}] {stem}: {[v['message'] for v in report['violations'] if v['severity']=='critical']}")

    print(f"  [{lang}] {passed}/{total} passed, {failed} failed")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WikiForge atom QA")
    parser.add_argument("stem", nargs="?", help="Atom stem (e.g. pricing--base-price)")
    parser.add_argument("--lang", default=None, help="Language code (en, es, ...)")
    parser.add_argument("--all", action="store_true", help="Check all atoms")
    parser.add_argument("--vault", default=None, help="Vault path (default: $VAULT_PATH)")
    parser.add_argument("--dry-run", action="store_true", help="Don't write QA reports")
    parser.add_argument("--source-type", default="youtube")
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).parent))
    from config import VaultConfig
    cfg = VaultConfig(args.vault)

    if args.all:
        langs = [args.lang] if args.lang else cfg.languages
        all_results = {}
        for lang in langs:
            print(f"\nChecking {lang}...")
            all_results[lang] = run_all(lang, cfg.vault_path, args.source_type)

        total_critical = sum(
            r["critical_count"]
            for lang_results in all_results.values()
            for r in lang_results.values()
            if isinstance(r, dict) and "critical_count" in r
        )
        print(f"\n{'='*50}")
        print(f"Total critical failures: {total_critical}")
        sys.exit(1 if total_critical > 0 else 0)

    elif args.stem:
        lang = args.lang or cfg.primary_language
        report = run_qa(args.stem, lang, cfg.vault_path, args.source_type,
                        write_report=not args.dry_run)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.exit(0 if report.get("pass") else 1)

    else:
        parser.print_help()
        sys.exit(1)
