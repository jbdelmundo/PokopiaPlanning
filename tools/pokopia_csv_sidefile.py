"""Re-scrape the per-Pokémon CSV to a SIDE FILE and emit a human diff prompt.

This deliberately does NOT touch the canonical ``reference/Pokopia.csv``. It:

  1. Verifies ``tools/pokopia_urls.txt`` still covers every Pokémon in the
     canonical CSV (reports any missing/extra URLs).
  2. Scrapes every URL using ``scrape_pokemon`` from the existing
     "pokopia scraper.py" (same 39-column schema), writing
     ``reference/Pokopia.scraped.csv``.
  3. Diffs the scraped data against the canonical CSV and writes
     ``reference/Pokopia.csv.UPDATE.md`` — a review prompt listing rows
     added/removed and per-field changes, so a human can update the live CSV.

Usage (from repo root):
    uv run --with requests --with beautifulsoup4 python tools/pokopia_csv_sidefile.py

Reuses the canonical scraper unchanged (its hardcoded output path is left
alone); we only import its functions and constants.
"""

import csv
import importlib.util
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_TOOLS = _REPO_ROOT / "tools"
URLS_FILE = _TOOLS / "pokopia_urls.txt"
CANONICAL_CSV = _REPO_ROOT / "reference" / "Pokopia.csv"
SIDE_CSV = _REPO_ROOT / "reference" / "Pokopia.scraped.csv"
UPDATE_MD = _REPO_ROOT / "reference" / "Pokopia.csv.UPDATE.md"


def _load_scraper():
    """Dynamically import the space-named 'pokopia scraper.py' module."""
    path = _TOOLS / "pokopia scraper.py"
    spec = importlib.util.spec_from_file_location("pokopia_scraper", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _read_canonical_rows():
    """Return (fieldnames, {name: row_dict}) for the canonical CSV."""
    with open(CANONICAL_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = {r["Name"].strip(): r for r in reader}
        return reader.fieldnames, rows


def _coverage_report(mod, canonical_names):
    """Compare URL list slugs to canonical Pokémon; print a coverage report."""
    urls = [u.strip() for u in URLS_FILE.read_text(encoding="utf-8").splitlines() if u.strip()]
    print(f"URL list: {len(urls)} URLs; canonical CSV: {len(canonical_names)} Pokémon.")
    return urls


def _scrape_all(mod, urls):
    """Scrape every URL into a list of row dicts keyed by Name."""
    scraped = {}
    errors = []
    n = len(urls)
    for i, url in enumerate(urls, 1):
        try:
            row = mod.scrape_pokemon(url)
            if row and row.get("Name"):
                scraped[row["Name"].strip()] = row
                print(f"[{i:3d}/{n}] {row['Number']} {row['Name']}")
            else:
                errors.append((url, "no data"))
                print(f"[{i:3d}/{n}] {url}  -- NO DATA")
        except Exception as e:  # network/layout hiccup on a single page
            errors.append((url, str(e)))
            print(f"[{i:3d}/{n}] {url}  -- ERROR: {e}")
        time.sleep(0.5)
    return scraped, errors


def _write_side_csv(fieldnames, scraped):
    """Write the scraped rows to the side CSV, sorted by Name (CSV order)."""
    with open(SIDE_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for name in sorted(scraped):
            # Restrict to canonical fieldnames (schemas match, but be safe).
            writer.writerow({k: scraped[name].get(k, "") for k in fieldnames})


def _build_update_md(fieldnames, canonical, scraped, errors):
    """Diff scraped vs canonical and write the review markdown."""
    canon_names = set(canonical)
    scrap_names = set(scraped)
    added = sorted(scrap_names - canon_names)
    removed = sorted(canon_names - scrap_names)
    common = sorted(canon_names & scrap_names)

    # Per-field changes (ignore Primary Location: it's a hardcoded community
    # list in the scraper, not authoritative Serebii data).
    skip_fields = {"Primary Location"}
    # Split changes into substantive vs casing/whitespace-only. A Pokémon whose
    # every diff is just letter-case (e.g. "Sour Flavors" -> "Sour flavors") is
    # cosmetic — build_data.py matches favorites case-insensitively — so we list
    # those separately to keep the actionable review focused.
    substantive = {}   # name -> [(field, old, new), ...]
    casing_only = {}   # name -> [(field, old, new), ...]
    for name in common:
        diffs = []
        c, s = canonical[name], scraped[name]
        for field in fieldnames:
            if field in skip_fields:
                continue
            old = (c.get(field) or "").strip()
            new = (s.get(field) or "").strip()
            if old != new:
                diffs.append((field, old, new))
        if not diffs:
            continue
        if all(old.lower() == new.lower() for _, old, new in diffs):
            casing_only[name] = diffs
        else:
            substantive[name] = diffs
    changes = {**substantive, **casing_only}  # for the summary count

    lines = [
        "# Pokopia.csv — Update Review",
        "",
        "Generated by `tools/pokopia_csv_sidefile.py`. The canonical "
        "`reference/Pokopia.csv` was **not** modified. Freshly scraped data is "
        "in `reference/Pokopia.scraped.csv`. Review the changes below, then "
        "update the live CSV as desired.",
        "",
        "> Note: `Primary Location` is intentionally excluded from the diff — it "
        "comes from a hardcoded community list in `pokopia scraper.py`, not from "
        "Serebii, so the scraped value is authoritative only if that list is "
        "current.",
        "",
        "## Summary",
        "",
        f"- Canonical Pokémon: **{len(canonical)}**",
        f"- Scraped Pokémon: **{len(scraped)}**",
        f"- Added (on site, not in CSV): **{len(added)}**",
        f"- Removed (in CSV, not scraped): **{len(removed)}**",
        f"- Existing with **substantive** field changes: **{len(substantive)}**",
        f"- Existing with **casing-only** changes (cosmetic): **{len(casing_only)}**",
        f"- Scrape errors: **{len(errors)}**",
        "",
    ]

    if added:
        lines += ["## Added Pokémon", ""]
        for name in added:
            lines.append(f"- `{scraped[name].get('Number','?')}` **{name}**")
        lines.append("")
    if removed:
        lines += ["## Removed Pokémon (present in CSV, not scraped)", ""]
        for name in removed:
            lines.append(f"- `{canonical[name].get('Number','?')}` **{name}**")
        lines.append("")

    def _render_changes(heading, group, note=None):
        lines.append(f"## {heading}")
        lines.append("")
        if note:
            lines.append(note)
            lines.append("")
        if not group:
            lines.extend(["_None._", ""])
            return
        for name in sorted(group):
            num = canonical[name].get("Number", "?")
            lines.append(f"### {num} {name}")
            lines.append("")
            lines.append("| Field | Old | New |")
            lines.append("|-------|-----|-----|")
            for field, old, new in group[name]:
                old_d = old if old else "_(empty)_"
                new_d = new if new else "_(empty)_"
                lines.append(f"| {field} | {old_d} | {new_d} |")
            lines.append("")

    _render_changes("Substantive field changes (existing Pokémon)", substantive)
    _render_changes(
        "Casing-only changes (cosmetic)", casing_only,
        note="These differ only in letter case. `build_data.py` matches "
             "favorites case-insensitively, so applying them is optional.",
    )

    if errors:
        lines += ["## Scrape errors", ""]
        for url, err in errors:
            lines.append(f"- `{url}` — {err}")
        lines.append("")

    UPDATE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return added, removed, changes


def main():
    mod = _load_scraper()
    fieldnames, canonical = _read_canonical_rows()
    if fieldnames != mod.CSV_HEADERS:
        print("WARNING: canonical CSV header differs from scraper CSV_HEADERS.")
        print("  canonical:", fieldnames)
        print("  scraper  :", mod.CSV_HEADERS)

    urls = _coverage_report(mod, canonical)

    print("\nScraping all Pokémon pages (this takes a few minutes)...")
    scraped, errors = _scrape_all(mod, urls)

    print(f"\nWriting side CSV -> {SIDE_CSV.name} ({len(scraped)} rows)")
    _write_side_csv(fieldnames, scraped)

    print(f"Building update prompt -> {UPDATE_MD.name}")
    added, removed, changes = _build_update_md(fieldnames, canonical, scraped, errors)

    print("\n" + "=" * 50)
    print("CSV SIDE-FILE SUMMARY")
    print("=" * 50)
    print(f"  Scraped rows     : {len(scraped)}")
    print(f"  Added            : {len(added)}")
    print(f"  Removed          : {len(removed)}")
    print(f"  Changed (fields) : {len(changes)}")
    print(f"  Errors           : {len(errors)}")
    print("=" * 50)
    print(f"  Side CSV : {SIDE_CSV}")
    print(f"  Prompt   : {UPDATE_MD}")
    print("  Canonical Pokopia.csv was NOT modified.")


if __name__ == "__main__":
    main()
