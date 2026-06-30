#!/usr/bin/env python3
"""
build_data.py — Pokopia "Who Can Live Together?" data builder.

Reads reference/Pokopia.csv and reference/Items By Favorite/*.md,
produces standalone-pages/data.js with window.POKOPIA_DATA = <json>.

Standard library only. No network.
"""

import csv
import json
import os
import sys
import unicodedata

# ---------------------------------------------------------------------------
# Paths (relative to repo root, i.e. where this script is invoked from)
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(REPO_ROOT, "reference", "Pokopia.csv")
ITEMS_INDEX_PATH = os.path.join(REPO_ROOT, "reference", "Items By Favorite.md")
ITEMS_DIR = os.path.join(REPO_ROOT, "reference", "Items By Favorite")
RECIPES_PATH = os.path.join(REPO_ROOT, "reference", "Recipes.json")
GAME_MECHANICS_PATH = os.path.join(REPO_ROOT, "reference", "Game Mechanics.md")
OUTPUT_PATH = os.path.join(REPO_ROOT, "standalone-pages", "data.js")

# ---------------------------------------------------------------------------
# Flavor constants
# ---------------------------------------------------------------------------
FLAVORS_CANONICAL = ["Dry", "Bitter", "Sweet", "Sour", "Spicy"]
# Map lowercase leading word -> canonical flavor
FLAVOR_LOOKUP = {f.lower(): f for f in FLAVORS_CANONICAL}

# ---------------------------------------------------------------------------
# Typo corrections (applied before any lookup)
# ---------------------------------------------------------------------------
TYPO_FIXES = {
    "group activites": "group activities",
    "noise stuff": "noisy stuff",
}


def is_flavor(value_lower):
    """Return canonical flavor name if value_lower starts with a flavor word, else None."""
    # Match e.g. "dry flavors", "sweet flavors", "spicy flavors"
    parts = value_lower.split()
    if parts and parts[0] in FLAVOR_LOOKUP:
        return FLAVOR_LOOKUP[parts[0]]
    return None


# ---------------------------------------------------------------------------
# Step 1: Read canonical category list from Items By Favorite.md
# ---------------------------------------------------------------------------
def read_canonical_categories(index_path):
    """Parse the master index md file, return list of canonical category names."""
    categories = []
    with open(index_path, encoding="utf-8") as f:
        in_table = False
        for line in f:
            line = line.rstrip("\n")
            # Detect table start: line contains '| Favorite | File |'
            if "| Favorite |" in line:
                in_table = True
                continue
            if in_table:
                # Skip separator row
                if line.startswith("|---") or line.startswith("| ---"):
                    continue
                # Table row
                if line.startswith("|"):
                    parts = [p.strip() for p in line.split("|")]
                    # parts[0] is empty (before first |), parts[1] is Favorite
                    if len(parts) >= 2 and parts[1]:
                        categories.append(parts[1])
                else:
                    # End of table
                    in_table = False
    return categories


# ---------------------------------------------------------------------------
# Step 2: Read items from each category .md file
# ---------------------------------------------------------------------------
def read_category_items(items_dir, canonical_categories):
    """Return dict: canonical_name -> [{"name": str, "description": str}, ...]"""
    items = {}
    for cat in canonical_categories:
        md_path = os.path.join(items_dir, f"{cat}.md")
        if not os.path.isfile(md_path):
            raise FileNotFoundError(f"Missing item file: {md_path}")
        cat_items = []
        with open(md_path, encoding="utf-8") as f:
            in_table = False
            past_separator = False
            for line in f:
                line = line.rstrip("\n")
                if "| Name |" in line:
                    in_table = True
                    continue
                if in_table:
                    if line.startswith("|---") or line.startswith("| ---"):
                        past_separator = True
                        continue
                    if past_separator and line.startswith("|"):
                        parts = [p.strip() for p in line.split("|")]
                        # parts[1] = item name, parts[2] = description (if present)
                        if len(parts) >= 2 and parts[1]:
                            name = parts[1]
                            description = parts[2] if len(parts) >= 3 and parts[2] else ""
                            cat_items.append({"name": name, "description": description})
                    elif past_separator:
                        break
        items[cat] = cat_items
    return items


# ---------------------------------------------------------------------------
# Step 3: Load recipes from Recipes.json (case-insensitive keyed lookup)
# ---------------------------------------------------------------------------
def load_recipes(path):
    """
    Read Recipes.json and return a case-insensitive lookup dict.

    Parameters
    ----------
    path : str
        Absolute path to Recipes.json.

    Returns
    -------
    dict
        Maps item_name.lower().strip() -> {"slug": str, "materials": [...]}
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Recipes.json not found at {path}. This file is required."
        )
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    # Build case-insensitive lookup
    lookup = {}
    for key, entry in raw.items():
        lookup[key.lower().strip()] = entry
    return lookup


# ---------------------------------------------------------------------------
# Step 3b: Automation-farm data
# ---------------------------------------------------------------------------
# Materials whose farm is worth boosting in the planner (late-game bottlenecks).
HIGH_VALUE_MATERIALS = {"Iron Ore", "Iron Ingot"}

# Processing rules: a Pokémon whose specialty == `specialty` turns `input` into
# `output`. Curated constant — the transformation rules are partly externally
# sourced (see the note atop reference/Game Mechanics.md) and documented in
# §7c + reference/Item List.txt. Keep small and in sync with those files.
PROCESSING_RULES = [
    {"input": "Squishy Clay", "specialty": "Burn", "output": "Brick"},
    {"input": "Small Log", "specialty": "Chop", "output": "Lumber"},
    {"input": "Nonburnable Garbage", "specialty": "Recycle", "output": "Iron Ore"},
    {"input": "Wastepaper", "specialty": "Recycle", "output": "Paper"},
    {"input": "Stone", "specialty": "Crush", "output": "Crushed materials"},
    {"input": "Iron Ore", "specialty": "Burn", "output": "Iron Ingot"},
    {"input": "Copper Ore", "specialty": "Burn", "output": "Copper Ingot"},
    {"input": "Gold Ore", "specialty": "Burn", "output": "Gold Ingot"},
]


def _clean_cell(text):
    """Strip markdown bold/markers and decorative symbols from a table cell."""
    text = text.replace("**", "").replace("⭐", "")
    return text.strip()


def read_litter_table(game_mechanics_path):
    """
    Parse §7b of Game Mechanics.md — the Litter Pokémon → dropped-material table.

    Columns: Pokémon | Ideal Habitat | Material Dropped | 2nd Specialty.
    Returns a list of dicts:
        {"pokemon", "habitat", "material", "secondSpecialty" (str|None), "highValue" (bool)}

    The "Quick lookup by material" table that follows shares the same `| ... |`
    shape, so we stop at the first row whose 2nd-specialty cell is missing
    (that table only has two columns) or when the table block ends.
    """
    if not os.path.isfile(game_mechanics_path):
        raise FileNotFoundError(f"Game Mechanics file not found at {game_mechanics_path}")

    litter = []
    with open(game_mechanics_path, encoding="utf-8") as f:
        in_table = False
        past_separator = False
        for line in f:
            line = line.rstrip("\n")
            # The §7b table header is the only one with both these column labels.
            if "| Pokémon |" in line and "Material Dropped" in line:
                in_table = True
                past_separator = False
                continue
            if not in_table:
                continue
            if line.startswith("|---") or line.startswith("| ---"):
                past_separator = True
                continue
            if past_separator and line.startswith("|"):
                parts = [p.strip() for p in line.split("|")]
                # parts[0] empty, parts[1..4] = name, habitat, material, 2nd specialty
                if len(parts) < 5:
                    break  # different table shape → end of §7b
                name = _clean_cell(parts[1])
                habitat = _clean_cell(parts[2])
                material = _clean_cell(parts[3])
                second = _clean_cell(parts[4])
                if not name:
                    continue
                second_specialty = None if second in ("", "—", "-") else second
                litter.append(
                    {
                        "pokemon": name,
                        "habitat": habitat,
                        "material": material,
                        "secondSpecialty": second_specialty,
                        "highValue": material in HIGH_VALUE_MATERIALS,
                    }
                )
            elif past_separator:
                break  # blank line / prose → table finished
    return litter


# ---------------------------------------------------------------------------
# Step 4: Slug helper for items without a recipe
# ---------------------------------------------------------------------------
def item_slug(name):
    """
    Derive an image slug from an item name.

    Lowercases the name, strips Unicode accents, then removes every character
    that is not a-z or 0-9 (no hyphens, no spaces).

    Parameters
    ----------
    name : str
        Item display name (e.g. "Cutting board").

    Returns
    -------
    str
        URL-safe slug (e.g. "cuttingboard").
    """
    # Normalize to NFD to decompose accented characters, then drop combining marks
    nfd = unicodedata.normalize("NFD", name.lower())
    ascii_approx = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    # Keep only a-z and 0-9
    return "".join(c for c in ascii_approx if c.isalnum() and (c.isdigit() or c.isascii()))


# ---------------------------------------------------------------------------
# Step 5: Process CSV
# ---------------------------------------------------------------------------
def process_csv(csv_path, canonical_categories):
    """Return list of pokemon dicts."""
    # Build case-insensitive lookup: lowercase(category) -> canonical
    cat_lookup = {c.lower(): c for c in canonical_categories}

    pokemon_list = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["Name"].strip()
            dex = row["Number"].strip()
            habitat = row["Ideal Habitat"].strip()
            spec1 = row["Specialty 1"].strip()
            spec2 = row["Specialty 2"].strip()

            specialties = [s for s in [spec1, spec2] if s]
            trade_specialty = any("trade" in s.lower() for s in specialties)

            fav_categories = []
            fav_flavors = []
            data_note = None

            for i in range(1, 7):
                raw = row.get(f"Favorite {i}", "").strip()
                if not raw or raw.lower() == "none":
                    continue

                # Apply typo fixes (lowercase key)
                fixed = TYPO_FIXES.get(raw.lower(), raw)

                # Check if it's a flavor
                flavor = is_flavor(fixed.lower())
                if flavor:
                    if flavor not in fav_flavors:
                        fav_flavors.append(flavor)
                    continue

                # Check if it's a known category
                canonical = cat_lookup.get(fixed.lower())
                if canonical is None:
                    # Fail loudly — unknown value
                    raise ValueError(
                        f"Unknown favorite value {raw!r} (after typo fix: {fixed!r}) "
                        f"for Pokémon {name!r}. Not a flavor and not in the 43 categories."
                    )
                if canonical not in fav_categories:
                    fav_categories.append(canonical)

            if not fav_categories and not fav_flavors:
                data_note = "no favorites recorded"

            pokemon_list.append(
                {
                    "name": name,
                    "dex": dex,
                    "habitat": habitat,
                    "specialties": specialties,
                    "trade_specialty": trade_specialty,
                    "favorites": {
                        "categories": fav_categories,
                        "flavors": fav_flavors,
                    },
                    "data_note": data_note,
                }
            )

    return pokemon_list


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Reading canonical categories from index...")
    canonical_categories = read_canonical_categories(ITEMS_INDEX_PATH)
    print(f"  Found {len(canonical_categories)} categories.")
    if len(canonical_categories) != 43:
        raise ValueError(f"Expected 43 categories, got {len(canonical_categories)}")

    print("Reading item lists from .md files...")
    items = read_category_items(ITEMS_DIR, canonical_categories)

    print("Loading recipes from Recipes.json...")
    recipe_lookup = load_recipes(RECIPES_PATH)
    print(f"  Loaded {len(recipe_lookup)} recipe entries.")

    print("Processing Pokémon CSV...")
    pokemon_list = process_csv(CSV_PATH, canonical_categories)

    print("Reading Litter drop table from Game Mechanics.md...")
    litter = read_litter_table(GAME_MECHANICS_PATH)
    print(f"  Found {len(litter)} Litter Pokémon.")
    # Cross-check every litter Pokémon exists in the CSV roster (fail loudly on drift).
    csv_names = {p["name"] for p in pokemon_list}
    missing_litter = [l["pokemon"] for l in litter if l["pokemon"] not in csv_names]
    if missing_litter:
        raise ValueError(
            f"Litter Pokémon not found in Pokopia.csv: {missing_litter}. "
            "The §7b table in Game Mechanics.md is out of sync with the roster."
        )

    # Build output structure — transform items into rich objects
    categories_sorted = sorted(canonical_categories)

    # Enrich each item with recipe data and slug
    n_with_recipe = 0
    n_without_recipe = 0
    items_enriched = {}
    for cat in categories_sorted:
        enriched_list = []
        for item in items[cat]:
            name = item["name"]
            description = item["description"]
            key = name.lower().strip()
            if key in recipe_lookup:
                recipe_entry = recipe_lookup[key]
                recipe = recipe_entry["materials"]
                slug = recipe_entry["slug"]
                n_with_recipe += 1
            else:
                recipe = None
                slug = item_slug(name)
                n_without_recipe += 1
            enriched_list.append(
                {
                    "name": name,
                    "description": description,
                    "recipe": recipe,
                    "slug": slug,
                }
            )
        items_enriched[cat] = enriched_list

    data = {
        "pokemon": pokemon_list,
        "categories": categories_sorted,
        "flavors": FLAVORS_CANONICAL,
        "items": items_enriched,
        "farm": {
            "litter": litter,
            "processing": PROCESSING_RULES,
        },
    }

    print("Writing data.js...")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("window.POKOPIA_DATA = ")
        f.write(json_str)
        f.write(";\n")

    # ---------------------------------------------------------------------------
    # Validation summary
    # ---------------------------------------------------------------------------
    n_pokemon = len(pokemon_list)
    n_categories = len(categories_sorted)
    n_flavors = len(FLAVORS_CANONICAL)
    no_fav_pokemon = [p for p in pokemon_list if p["data_note"] == "no favorites recorded"]
    total_items = sum(len(v) for v in items_enriched.values())

    print()
    print("=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    print(f"  Pokémon count      : {n_pokemon}  (expect 308)")
    print(f"  Category count     : {n_categories}  (expect 43)")
    print(f"  Flavor count       : {n_flavors}  (expect 5)")
    print(f"  No-favorites count : {len(no_fav_pokemon)}  (expect 1)")
    for p in no_fav_pokemon:
        print(f"    - {p['name']} ({p['dex']})")
    print(f"  Total distinct items across all categories: {total_items}")
    print(f"  Items with recipe  : {n_with_recipe}")
    print(f"  Items without recipe (recipe=null, slug derived): {n_without_recipe}")
    if n_without_recipe > 0:
        print(f"  NOTE: {n_without_recipe} items have no recipe entry — this is normal.")
    print(f"  Litter Pokémon     : {len(litter)}  (expect 33)")
    print(f"  Processing rules   : {len(PROCESSING_RULES)}")
    print("=" * 50)

    # ---------------------------------------------------------------------------
    # Assertions
    # ---------------------------------------------------------------------------
    assert n_pokemon == 308, f"FAIL: expected 308 pokemon, got {n_pokemon}"
    assert n_categories == 43, f"FAIL: expected 43 categories, got {n_categories}"
    assert n_flavors == 5, f"FAIL: expected 5 flavors, got {n_flavors}"
    assert len(litter) == 33, f"FAIL: expected 33 Litter Pokémon, got {len(litter)}"

    expected_no_fav = {"Ditto"}
    actual_no_fav = {p["name"] for p in no_fav_pokemon}
    if actual_no_fav != expected_no_fav:
        print(
            f"WARNING: Expected no-favorites Pokémon to be {expected_no_fav}, "
            f"got {actual_no_fav}"
        )
    else:
        print("  Assertion passed: only Ditto has no favorites.")

    print()
    print("Build complete. Output written to:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
