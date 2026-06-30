"""Scraper for Pokémon Pokopia reference data from Serebii.

Refreshes three reference files from their Serebii source pages:

    habitats     habitats.shtml   -> reference/Habitats.md
    specialties  specialty.shtml  -> reference/Specialties.txt
    items        items.shtml      -> reference/Item List.txt

Each source page uses Serebii's ``class="dextable"`` layout. We locate the data
table(s) by their header row text (robust to surrounding-markup changes) and
fail loudly if the expected structure is missing, rather than writing empty or
partial data.

Usage (from repo root):
    uv run --with requests --with beautifulsoup4 python tools/pokopia_reference_scraper.py [SECTION ...]

    # SECTION is one or more of: habitats specialties items  (default: all)
    uv run ... python tools/pokopia_reference_scraper.py habitats
    uv run ... python tools/pokopia_reference_scraper.py            # all three

Sister scrapers: pokopia_favorites_scraper.py (favorites item lists),
pokopia_item_scraper.py (crafting recipes -> Recipes.json), and
"pokopia scraper.py" (per-Pokémon CSV).
"""

import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://www.serebii.net"
HABITATS_URL = f"{BASE_URL}/pokemonpokopia/habitats.shtml"
SPECIALTY_URL = f"{BASE_URL}/pokemonpokopia/specialty.shtml"
ITEMS_URL = f"{BASE_URL}/pokemonpokopia/items.shtml"

_REPO_ROOT = Path(__file__).parent.parent
HABITATS_FILE = _REPO_ROOT / "reference" / "Habitats.md"
SPECIALTIES_FILE = _REPO_ROOT / "reference" / "Specialties.txt"
ITEM_LIST_FILE = _REPO_ROOT / "reference" / "Item List.txt"

REQUEST_DELAY = 0.5  # polite delay between HTTP requests (seconds)


# ---------------------------------------------------------------------------
# HTTP / text helpers — mirror the sister scrapers
# ---------------------------------------------------------------------------


def get_soup(url: str) -> BeautifulSoup:
    """Fetch *url* and return a parsed :class:`BeautifulSoup` tree."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


# Serebii serves these pages as ISO-8859-1 (matching their Content-Type), and
# almost every accented character is genuine Latin-1, so requests decodes them
# correctly. A handful of cells, however, contain UTF-8 bytes embedded in the
# Latin-1 stream (a data-entry inconsistency on Serebii's side), which decode to
# mojibake like "PokÃ©mon". We repair those specific double-encoding artifacts
# after decoding rather than forcing a single encoding (which would corrupt the
# 150+ correctly-Latin-1 characters to fix the one bad one).
_MOJIBAKE_FIXES = {
    "Ã©": "é", "Ã¨": "è", "Ã¡": "á", "Ã³": "ó", "Ã­": "í",
    "Ã±": "ñ", "Ã¼": "ü", "Ã¶": "ö", "Ã¤": "ä", "Â": "",
}


def _fix_mojibake(text: str) -> str:
    """Repair UTF-8-as-Latin-1 double-encoding artifacts (e.g. 'Ã©' -> 'é')."""
    for bad, good in _MOJIBAKE_FIXES.items():
        if bad in text:
            text = text.replace(bad, good)
    return text


def _clean(text: str) -> str:
    """Collapse all whitespace runs to single spaces, repair mojibake, strip."""
    return _fix_mojibake(re.sub(r"\s+", " ", text).strip())


def _header_text(table: Tag) -> str:
    """Return the lowercased, space-joined text of a table's first row."""
    header = table.find("tr")
    if not header:
        return ""
    return " ".join(_clean(td.get_text()) for td in header.find_all(["td", "th"])).lower()


def _split_on_br(cell: Tag) -> list:
    """Split a cell's contents into lines, breaking on ``<br>`` tags.

    Text between consecutive ``<br>`` elements (including the text of any inline
    tags such as ``<a>``) is joined and cleaned into one line. Empty lines are
    dropped. Used for the multi-line Locations column on the items page.
    """
    lines = []
    cur = ""
    for node in cell.children:
        if isinstance(node, Tag) and node.name == "br":
            if _clean(cur):
                lines.append(_clean(cur))
            cur = ""
        else:
            cur += node.get_text() if isinstance(node, Tag) else str(node)
    if _clean(cur):
        lines.append(_clean(cur))
    return lines


def _find_dextables(soup: BeautifulSoup) -> list:
    """Return every ``<table class="dextable">`` on the page."""
    return [t for t in soup.find_all("table") if t.get("class") == ["dextable"]]


# ---------------------------------------------------------------------------
# habitats.shtml -> Habitats.md
# ---------------------------------------------------------------------------

# Preserved verbatim from the existing file so the refresh is a pure data update.
_HABITATS_INTRO = (
    "In Pokemon Pokopia, in order to get Pokemon to appear in your area, you "
    "need to build a habitat for them. Each Pokemon comes from specific "
    "habitats but it isn't always a guaranteed chance as others may appear."
)


def scrape_habitats() -> None:
    """Rewrite ``reference/Habitats.md`` from the habitats page.

    The page is one ``dextable`` (No. | Picture | Name | Description) holding the
    regular habitats #001..#209, then a single-cell ``Habitats (Event)`` divider
    row, then the event habitats (#001.. on the page, written as E001.. here to
    match the existing file). Numbers are zero-padded to 3 digits.
    """
    soup = get_soup(HABITATS_URL)
    tables = [t for t in _find_dextables(soup)
              if "name" in _header_text(t) and "description" in _header_text(t)]
    if not tables:
        raise RuntimeError(
            "Could not find the habitats table — Serebii layout may have changed."
        )
    table = tables[0]

    regular, event = [], []
    in_event = False
    for tr in table.find_all("tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) == 1:
            # Section divider, e.g. "Habitats (Event)".
            if "event" in _clean(tds[0].get_text()).lower():
                in_event = True
            continue
        if len(tds) < 4:
            continue  # header row or stray markup
        num = _clean(tds[0].get_text())
        name = _clean(tds[2].get_text())
        desc = _clean(tds[3].get_text())
        if num.lower() == "no." or not name:
            continue
        digits = re.sub(r"\D", "", num)  # strip leading '#'
        if not digits:
            continue
        (event if in_event else regular).append((int(digits), name, desc))

    if not regular:
        raise RuntimeError("Parsed 0 regular habitats — aborting before write.")

    lines = ["# Habitats", "", _HABITATS_INTRO, "", "| # | Name | Description |",
             "|---|------|-------------|"]
    for n, name, desc in regular:
        lines.append(f"| {n:03d} | {name} | {desc} |")
    lines += ["", "## Event Habitats", "", "| # | Name | Description |",
              "|---|------|-------------|"]
    for n, name, desc in event:
        lines.append(f"| E{n:03d} | {name} | {desc} |")

    HABITATS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Habitats: {len(regular)} regular + {len(event)} event "
          f"-> {HABITATS_FILE.name}")


# ---------------------------------------------------------------------------
# specialty.shtml -> Specialties.txt
# ---------------------------------------------------------------------------


def scrape_specialties() -> None:
    """Rewrite ``reference/Specialties.txt`` (tab-separated Name<TAB>Description)."""
    soup = get_soup(SPECIALTY_URL)
    tables = [t for t in _find_dextables(soup)
              if "name" in _header_text(t) and "description" in _header_text(t)]
    if not tables:
        raise RuntimeError(
            "Could not find the specialty table — Serebii layout may have changed."
        )
    table = tables[0]

    rows = []
    for tr in table.find_all("tr")[1:]:  # skip header
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 3:
            continue
        name = _clean(tds[1].get_text())
        desc = _clean(tds[2].get_text())
        if name:
            rows.append((name, desc))

    if not rows:
        raise RuntimeError("Parsed 0 specialties — aborting before write.")

    body = "\n".join(f"{name}\t{desc}" for name, desc in rows) + "\n"
    SPECIALTIES_FILE.write_text(body, encoding="utf-8")
    print(f"  Specialties: {len(rows)} -> {SPECIALTIES_FILE.name}")


# ---------------------------------------------------------------------------
# items.shtml -> Item List.txt
# ---------------------------------------------------------------------------

# Preserved verbatim from the existing file (title + intro + anchor lines).
_ITEMS_HEADER_LINES = [
    "Items",
    "",
    "Like most Pokémon games, Pokémon Pokopia has a myriad of items including "
    "Materials and cosmetic items you can use to decaorate the islands and "
    "houses throughout the game. This page is to list all the items and will "
    "add their locations over time as we figure exact locations out.",
    "Anchors \tMaterials \tFood \tFurniture \tMisc. \tOutdoor",
    "Utilities \tNature \tBuildings \tBlocks \tKits",
    "Key Items \tOther \tLost Relics (L) \tLost Relics (S) \tFossils",
]


def _section_name_for(table: Tag) -> str:
    """Return the 'List of <Section>' text preceding *table*, or ''."""
    node = table.find_previous(string=re.compile(r"List of "))
    return _clean(str(node)) if node else ""


def scrape_items() -> None:
    """Rewrite ``reference/Item List.txt`` preserving its raw tab-separated layout.

    The page has 15 ``dextable`` tables (Picture | Name | Description | Tag |
    Locations), each preceded by a ``List of <Section>`` heading. We keep the
    existing file's 4-column shape — Name<TAB>Name <TAB>Description<TAB>Locations
    — dropping the page's newer "Tag" column, with each additional location on
    its own continuation line (matching the current file exactly).
    """
    soup = get_soup(ITEMS_URL)
    dextables = _find_dextables(soup)
    if len(dextables) < 10:
        raise RuntimeError(
            f"Expected ~15 item tables, found {len(dextables)} — "
            "Serebii layout may have changed."
        )

    out = list(_ITEMS_HEADER_LINES)
    total_items = 0
    for table in dextables:
        section = _section_name_for(table)
        if not section:
            raise RuntimeError(
                "An item table has no preceding 'List of ...' heading — "
                "Serebii layout may have changed."
            )
        if "name" not in _header_text(table) or "description" not in _header_text(table):
            raise RuntimeError(f"Unexpected header on '{section}' table.")

        out += ["", section, "", "Picture \tName \tDescription \tLocations"]

        for tr in table.find_all("tr")[1:]:  # skip header
            tds = tr.find_all("td", recursive=False)
            if len(tds) < 5:
                continue  # need Picture, Name, Description, Tag, Locations
            name = _clean(tds[1].get_text())
            desc = _clean(tds[2].get_text())
            locations = _split_on_br(tds[-1])
            if not name:
                continue
            first_loc = locations[0] if locations else ""
            # Row mirrors the existing format: col0 repeats the name (was the
            # image alt/name), then trailing space after Name, then Description,
            # then the first location. Extra locations follow on bare lines.
            out.append(f"{name}\t{name} \t{desc}\t{first_loc}")
            out.extend(locations[1:])
            total_items += 1

    ITEM_LIST_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"  Items: {total_items} across {len(dextables)} sections "
          f"-> {ITEM_LIST_FILE.name}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

_SECTIONS = {
    "habitats": scrape_habitats,
    "specialties": scrape_specialties,
    "items": scrape_items,
}


def main(argv: list) -> None:
    """Run the requested sections (default: all three)."""
    requested = argv or list(_SECTIONS)
    unknown = [s for s in requested if s not in _SECTIONS]
    if unknown:
        raise SystemExit(
            f"Unknown section(s): {unknown}. Valid: {list(_SECTIONS)}"
        )

    print("Scraping reference data from Serebii...")
    for i, section in enumerate(requested):
        _SECTIONS[section]()
        if i < len(requested) - 1:
            time.sleep(REQUEST_DELAY)
    print("Done.")


if __name__ == "__main__":
    main(sys.argv[1:])
