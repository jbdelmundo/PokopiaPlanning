"""Scraper for Pokémon Pokopia "favorites" item lists from Serebii.

Reads the favorites index at
``https://www.serebii.net/pokemonpokopia/favorites.shtml`` to discover the 43
favorite categories, then fetches each per-category page
(``/pokemonpokopia/favorites/<slug>.shtml``) and rewrites the reference data:

    reference/Items By Favorite/<Category>.md   (one file per category)
    reference/Items By Favorite.md              (regenerated index)

Each per-category page is a 4-column table: Picture | Name | Description |
Category. We keep Name + Description (the shape ``build_data.py`` consumes).

The display names used for the .md filenames are the *existing* repo names
(Title Case with lowercase connectors, e.g. "Letters and Words"). Serebii uses
sentence case ("Letters and words"); we join the two by URL slug, which is the
display name lowercased with spaces removed (e.g. "lettersandwords"). This keeps
the build pipeline's canonical 43-category contract intact.

Usage (from repo root):
    uv run --with requests --with beautifulsoup4 python tools/pokopia_favorites_scraper.py
    # or, if requests/bs4 are already installed:
    python tools/pokopia_favorites_scraper.py

After running, rebuild the compatibility tool's data bundle:
    python standalone-pages/build_data.py
"""

import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://www.serebii.net"
FAVORITES_INDEX_URL = f"{BASE_URL}/pokemonpokopia/favorites.shtml"

_REPO_ROOT = Path(__file__).parent.parent
ITEMS_DIR = _REPO_ROOT / "reference" / "Items By Favorite"
INDEX_FILE = _REPO_ROOT / "reference" / "Items By Favorite.md"

# Polite delay between HTTP requests (seconds)
REQUEST_DELAY = 0.5

# The pipeline (build_data.py) requires exactly this many categories.
EXPECTED_CATEGORIES = 43


# ---------------------------------------------------------------------------
# HTTP helper — mirrors the pattern from pokopia_item_scraper.py
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
# Display-name <-> slug mapping
# ---------------------------------------------------------------------------


def _slug_from_display(name: str) -> str:
    """Return the URL slug for a category display name.

    The Serebii favorites URLs are the display name lowercased with all spaces
    removed, e.g. "Letters and Words" -> "lettersandwords".

    Parameters
    ----------
    name : str
        Category display name (existing repo casing).

    Returns
    -------
    str
        URL slug.
    """
    return re.sub(r"\s+", "", name.lower())


def read_canonical_categories(index_path: Path) -> list:
    """Parse the existing index .md, return the canonical category display names.

    Mirrors ``build_data.read_canonical_categories`` so the scraper writes files
    under exactly the names the build step later reads back.

    Parameters
    ----------
    index_path : Path
        Path to ``reference/Items By Favorite.md``.

    Returns
    -------
    list of str
        Category display names in index order.
    """
    categories = []
    with open(index_path, encoding="utf-8") as f:
        in_table = False
        for line in f:
            line = line.rstrip("\n")
            if "| Favorite |" in line:
                in_table = True
                continue
            if in_table:
                if line.startswith("|---") or line.startswith("| ---"):
                    continue
                if line.startswith("|"):
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 2 and parts[1]:
                        categories.append(parts[1])
                else:
                    in_table = False
    return categories


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _clean_cell(text: str) -> str:
    """Collapse whitespace and strip a single cell's text."""
    return re.sub(r"\s+", " ", text).strip()


def parse_category_page(soup: BeautifulSoup, category: str) -> list:
    """Extract ``[{"name", "description"}, ...]`` from a category page.

    The relevant table has a header row reading ``Picture | Name | Description |
    Category`` (column 4 is the item *type*, e.g. "Decoration" — not the favorite
    category). We locate that table by its header text, then read each data row's
    Name (col 2) and Description (col 3).

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed per-category page.
    category : str
        Display name (for error messages only).

    Returns
    -------
    list of dict
        Ordered ``{"name": str, "description": str}`` entries.

    Raises
    ------
    RuntimeError
        If the expected table cannot be located — signals a layout change.
    """
    target_table = None
    for table in soup.find_all("table"):
        header = table.find("tr")
        if not header:
            continue
        header_text = " ".join(
            _clean_cell(td.get_text()) for td in header.find_all(["td", "th"])
        ).lower()
        if "name" in header_text and "description" in header_text and "picture" in header_text:
            target_table = table
            break

    if target_table is None:
        raise RuntimeError(
            f"Could not find the item table on the '{category}' page. "
            "The Serebii page layout may have changed."
        )

    items = []
    rows = target_table.find_all("tr")
    for row in rows[1:]:  # skip header
        tds = row.find_all("td", recursive=False)
        if len(tds) < 3:
            continue
        # Column layout: [Picture, Name, Description, Category]
        name = _clean_cell(tds[1].get_text())
        description = _clean_cell(tds[2].get_text())
        if not name:
            continue
        items.append({"name": name, "description": description})

    if not items:
        raise RuntimeError(
            f"Found the table on the '{category}' page but parsed 0 items. "
            "The Serebii page layout may have changed."
        )
    return items


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def _escape_pipes(text: str) -> str:
    """Escape any literal pipe so it doesn't break the markdown table."""
    return text.replace("|", "\\|")


def write_category_md(path: Path, category: str, items: list) -> None:
    """Write one ``Items By Favorite/<Category>.md`` file.

    Format matches the existing files exactly so ``build_data.read_category_items``
    parses it unchanged::

        # <Category>

        | Name | Description |
        |------|-------------|
        | <name> | <description> |
    """
    lines = [f"# {category}", "", "| Name | Description |", "|------|-------------|"]
    for item in items:
        name = _escape_pipes(item["name"])
        desc = _escape_pipes(item["description"])
        lines.append(f"| {name} | {desc} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_index_md(path: Path, categories: list) -> None:
    """Regenerate the ``Items By Favorite.md`` master index."""
    lines = [
        "# Items by Favorite",
        "",
        "Furniture and decoration items grouped by Pokémon favorite type. "
        "Use these when furnishing houses to maximize Comfy Levels.",
        "",
        "| Favorite | File |",
        "|----------|------|",
    ]
    for cat in categories:
        # URL-encode spaces in the link target to match the existing index.
        link_target = f"Items%20By%20Favorite/{cat.replace(' ', '%20')}.md"
        lines.append(f"| {cat} | [{cat}]({link_target}) |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Main scraping logic
# ---------------------------------------------------------------------------


def main() -> None:
    """Scrape every favorite category and rewrite the reference .md files."""
    print(f"Reading canonical categories from {INDEX_FILE.name} ...")
    categories = read_canonical_categories(INDEX_FILE)
    print(f"  Found {len(categories)} canonical categories.")
    if len(categories) != EXPECTED_CATEGORIES:
        raise RuntimeError(
            f"Expected {EXPECTED_CATEGORIES} categories in the index, "
            f"got {len(categories)}. Aborting before any writes."
        )

    # Cross-check the index against the live favorites page so we notice if
    # Serebii has added/removed/renamed a category.
    print(f"Fetching favorites index {FAVORITES_INDEX_URL} ...")
    index_soup = get_soup(FAVORITES_INDEX_URL)
    live_slugs = set()
    for a in index_soup.find_all("a", href=re.compile(r"/pokemonpokopia/favorites/[^/]+\.shtml")):
        m = re.search(r"/favorites/([^/]+)\.shtml", a["href"])
        if m:
            live_slugs.add(m.group(1).lower())

    repo_slugs = {_slug_from_display(c): c for c in categories}
    missing_on_site = sorted(s for s in repo_slugs if s not in live_slugs)
    new_on_site = sorted(live_slugs - set(repo_slugs))
    if missing_on_site:
        print(f"  WARNING: repo categories not found on site: "
              f"{[repo_slugs[s] for s in missing_on_site]}")
    if new_on_site:
        print(f"  WARNING: new categories on site not in repo (not scraped): {new_on_site}")
    if not missing_on_site and not new_on_site:
        print(f"  Index cross-check OK — all {len(categories)} categories present on site.")

    ITEMS_DIR.mkdir(parents=True, exist_ok=True)

    total_items = 0
    per_category_counts = {}
    for i, category in enumerate(categories, 1):
        slug = _slug_from_display(category)
        url = f"{BASE_URL}/pokemonpokopia/favorites/{slug}.shtml"
        print(f"[{i:2d}/{len(categories)}] {category:<20} <- {slug}.shtml", end="", flush=True)
        soup = get_soup(url)
        items = parse_category_page(soup, category)
        out_path = ITEMS_DIR / f"{category}.md"
        write_category_md(out_path, category, items)
        per_category_counts[category] = len(items)
        total_items += len(items)
        print(f"  ... {len(items)} items")
        time.sleep(REQUEST_DELAY)

    print("Regenerating index ...")
    write_index_md(INDEX_FILE, categories)

    print()
    print("=" * 50)
    print("SCRAPE SUMMARY")
    print("=" * 50)
    print(f"  Categories scraped : {len(categories)}")
    print(f"  Total items written: {total_items}")
    print(f"  Files written      : {len(categories)} category files + 1 index")
    print("=" * 50)
    print("Next step: python standalone-pages/build_data.py")


if __name__ == "__main__":
    main()
