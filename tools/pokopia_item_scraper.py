"""Scraper for Pokémon Pokopia crafting recipes from Serebii.

Reads https://www.serebii.net/pokemonpokopia/crafting.shtml and writes
reference/Recipes.json with the full list of craftable items, their image
slug (from the items/<slug>.png src on the page), and their material
requirements.

Usage (from repo root):
    uv run --with requests --with beautifulsoup4 python tools/pokopia_item_scraper.py
    # or, if requests/bs4 are already installed:
    python tools/pokopia_item_scraper.py
"""

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://www.serebii.net"
CRAFTING_URL = f"{BASE_URL}/pokemonpokopia/crafting.shtml"

_REPO_ROOT = Path(__file__).parent.parent
OUTPUT_FILE = _REPO_ROOT / "reference" / "Recipes.json"

# Polite delay between any additional HTTP requests (seconds)
REQUEST_DELAY = 0.5


# ---------------------------------------------------------------------------
# HTTP helper — mirrors the pattern from pokopia scraper.py
# ---------------------------------------------------------------------------


def get_soup(url: str) -> BeautifulSoup:
    """Fetch *url* and return a :class:`BeautifulSoup` parse tree.

    Parameters
    ----------
    url : str
        Full URL to fetch.

    Returns
    -------
    BeautifulSoup
        Parsed HTML document.

    Raises
    ------
    requests.HTTPError
        If the server returns a non-2xx status code.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _extract_slug_from_src(src: str) -> str:
    """Return the slug portion of an ``items/<slug>.png`` image src.

    Parameters
    ----------
    src : str
        Image ``src`` attribute value, e.g. ``"items/storagebox.png"``.

    Returns
    -------
    str
        The slug string, e.g. ``"storagebox"``.  Empty string if not matched.
    """
    match = re.search(r"items/([^/]+?)\.png", src)
    return match.group(1) if match else ""


def _parse_materials(requirements_td) -> list:
    """Parse the nested material table inside a requirements cell.

    Each material row contains a linked image (ignored) and a text cell of the
    form ``<u>Material Name</u> * <qty>``.

    Parameters
    ----------
    requirements_td : bs4.element.Tag
        The ``<td>`` in column 4 of an item row, which contains a nested
        ``<table>`` with one ``<tr>`` per material.

    Returns
    -------
    list of dict
        Ordered list of ``{"material": str, "qty": int}`` dicts.  Empty list
        if no nested table is found.
    """
    mat_table = requirements_td.find("table")
    if not mat_table:
        return []

    materials = []
    for mr in mat_table.find_all("tr"):
        mr_tds = mr.find_all("td")
        if len(mr_tds) < 2:
            continue

        text_td = mr_tds[1]
        full_text = text_td.get_text(strip=True)

        # Prefer <u> tag for the material name; fall back to <a> text
        name_tag = text_td.find("u")
        if name_tag:
            mat_name = name_tag.get_text(strip=True)
        else:
            a_tag = text_td.find("a")
            mat_name = a_tag.get_text(strip=True) if a_tag else full_text

        qty_match = re.search(r"\*\s*(\d+)", full_text)
        qty = int(qty_match.group(1)) if qty_match else 0

        if mat_name:
            materials.append({"material": mat_name, "qty": qty})

    return materials


# ---------------------------------------------------------------------------
# Main scraping logic
# ---------------------------------------------------------------------------


def scrape_recipes() -> dict:
    """Scrape all craftable items from the Serebii crafting page.

    Returns
    -------
    dict
        Mapping of ``item_name -> {"slug": str, "materials": [...]}`` for
        every item found on the crafting page.

    Raises
    ------
    RuntimeError
        If the expected table structure is not found on the page, indicating
        that the page layout may have changed.
    """
    print(f"Fetching {CRAFTING_URL} ...")
    soup = get_soup(CRAFTING_URL)

    # The crafting page contains many tables.  The main crafting table is the
    # first table that has item image links of the form items/<slug>.shtml.
    # We locate it by searching for the first table with 64px item images.
    all_tables = soup.find_all("table")
    main_table = None
    for t in all_tables:
        if t.find("img", src=re.compile(r"items/.+\.png"), height="64"):
            main_table = t
            break

    if main_table is None:
        raise RuntimeError(
            "Could not find the crafting table on the page. "
            "The Serebii page layout may have changed — please inspect "
            f"{CRAFTING_URL} manually."
        )

    rows = main_table.find_all("tr")
    if len(rows) < 2:
        raise RuntimeError(
            f"Crafting table has only {len(rows)} rows (expected header + data). "
            "The page layout may have changed."
        )

    print(f"  Found crafting table with {len(rows)} rows (including header).")

    recipes = {}
    for row in rows[1:]:  # skip the header row
        # Item rows have exactly 4 top-level <td> cells, and the first cell
        # contains a 64-pixel-tall item image.
        tds = row.find_all("td", recursive=False)
        if len(tds) != 4:
            continue
        img_tag = tds[0].find("img")
        if not img_tag or img_tag.get("height") != "64":
            continue

        # --- Name ---
        name = tds[1].get_text(strip=True)
        if not name:
            print(f"  WARNING: Item row has empty name, skipping.")
            continue

        # --- Slug (read from the image src — authoritative) ---
        slug = _extract_slug_from_src(img_tag.get("src", ""))
        if not slug:
            print(f"  WARNING: Could not extract slug for '{name}' from img src '{img_tag.get('src')}'")

        # --- Materials ---
        materials = _parse_materials(tds[3])

        if name in recipes:
            print(f"  WARNING: Duplicate item name '{name}' encountered — overwriting.")

        recipes[name] = {"slug": slug, "materials": materials}

    return recipes


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the scraper and write results to ``reference/Recipes.json``."""
    recipes = scrape_recipes()

    total = len(recipes)
    with_materials = sum(1 for v in recipes.values() if v["materials"])
    without_materials = total - with_materials

    print(f"\n--- Summary ---")
    print(f"  Total items scraped : {total}")
    print(f"  With >= 1 material  : {with_materials}")
    print(f"  With 0 materials    : {without_materials}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"\nWritten to {OUTPUT_FILE}")

    # Validate: round-trip load
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert len(loaded) == total, "Round-trip JSON load produced different item count!"
    print(f"JSON validated successfully ({len(loaded)} items).")


if __name__ == "__main__":
    main()
