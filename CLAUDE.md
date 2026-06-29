# CLAUDE.md — PokopiaPlanning

## Project Overview

Planning toolkit for building Pokopia cities across five areas. The project covers house group assignments, district layout, architecture, landscaping, and item/habitat reference data for 87 houses across 305 Pokemon.

# Data Sources
Check first if the data needed is already present in the `reference` directory. 

When doing search online, use https://www.serebii.net/pokemonpokopia/ as your primary source.

## Repository Structure

```
PokopiaPlanning/
├── planning/               # Active city-building documents
│   ├── Landscape & Building Plan.md   # Master design guide for all 5 areas
│   ├── Global House Groups v2.md      # Cross-zone Pokemon groupings
│   ├── Wasteland House Groups.md      # Houses 1–19 (Withered Wastelands)
│   ├── Beach House Groups.md          # Houses 20–37 (Bleak Beach)
│   ├── Ridges House Groups.md         # Houses 38–58 (Rocky Ridges)
│   ├── Skylands House Groups.md       # Houses 59–78, 87 (Sparkling Skylands)
│   ├── Pallet House Groups.md         # Houses 79–86 (Palette Town)
│   ├── City Planning.txt              # Working input file for batch analysis
│   └── FloorPlanner_Stackable.xlsx    # Floor plan spreadsheet
├── reference/              # Game data and lookup tables
│   ├── Pokopia.csv                    # Full 305-Pokemon database
│   ├── Item List.txt                  # Complete item catalog
│   ├── Items By Favorite.md           # 43 favorite categories → item lists
│   ├── Items By Favorite/             # Per-category item breakdowns
│   ├── Habitats.md                    # 209 regular + 3 event habitats
│   ├── Locations.md                   # 6 area overviews with available materials
│   └── Specialties.txt                # 31 Pokemon specialty types
├── standalone-pages/       # Deployable web tools (GitHub Pages)
│   ├── compatibility.html             # "Who Can Live Together?" app entry point
│   ├── app.js                         # All UI logic (picker + detail screens)
│   ├── styles.css                     # App styles
│   ├── data.js                        # Generated data bundle (window.POKOPIA_DATA)
│   └── build_data.py                  # Reads Pokopia.csv + Items By Favorite → data.js
└── tools/                  # Scraping utilities
    ├── pokopia scraper.py             # Web scraper for Pokemon data
    ├── pokopia_urls.txt               # Target URLs for scraping
    ├── available pokemon.html         # Cached HTML source
    └── bulbasaur.html                 # Cached HTML example page
```

## Key Game Mechanics

| Mechanic | Rule |
|---|---|
| Comfy Level | Pokemon happiness: Iffy → Average → Nice → Great → Awesome |
| Environment Level | Per-area 1–10 progression; driven by Comfy Levels; unlocks shops/gifts |
| House size | Max 10×10 blocks, at least 3 unique furniture items, up to 4 Pokemon |
| Map height | 127 blocks vertical across all areas |
| Habitat types | Bright, Cool, Dark, Dry, Humid, Warm — never mix habitats in one house |

## Area Summary

| Area | Grid | Houses | Habitats |
|---|---|---|---|
| Withered Wastelands | 240×240 | 1–19 | Bright, Dark, Dry, Humid, Warm |
| Bleak Beach | 272×272 | 20–37 | Bright, Cool*, Dark, Humid, Warm |
| Rocky Ridges | 272×272 | 38–58 | Bright, Cool, Dark, Dry, Humid, Warm |
| Sparkling Skylands | 352×352 | 59–78, 87 | Bright, Cool, Dark, Dry, Humid, Warm |
| Palette Town | 384×384 | 79–86 | Bright, Cool*, Dark, Humid, Warm |

*Cool solos flagged for potential cross-area consolidation (Meowth → House 27, Glaceon → House 41).*

## House Grouping Rules

- **Habitat first** — habitat match determines grouping, flavor preferences are secondary.
- **4 Pokemon max per house.**
- **No house exceeds 10×10 blocks.**
- **Professor Tangrowth is excluded** from all grouping assignments.
- Cross-area moves are allowed when habitat fit is superior (see `Global House Groups v2.md`).

## Design Pillars (from Landscape & Building Plan)

1. Water access in every area — ponds, rivers, fountains, or ocean.
2. Urban districts — each area gets a Pokecenter, shops, plaza, and fighting court.
3. No slum blocks — houses spaced with gardens, parks, and sightlines.
4. Habitat zones never cross lines inside a single area.

## Infrastructure Checklist (Per Area)

- [ ] Pokemon Center (requires Env Lv 3)
- [ ] Generator (Windmill / Waterwheel / Furnace)
- [ ] Workbench
- [ ] Community Box
- [ ] Cooking station (cutting board + frying pan + bread oven)
- [ ] Smelting furnace
- [ ] Streetlights along main paths
- [ ] Signs / signposts at key intersections
- [ ] Sprinkler system for farms

## Lighting Reference

| Area | Primary | Accent |
|---|---|---|
| Withered Wastelands | Mushroom streetlight, mushroom lamp | Glowing mushrooms, slender candles |
| Bleak Beach | Harbor streetlight, shell lamp | Lanterns, string lights |
| Rocky Ridges | Town streetlight, wall torch | Eerie candles, crystal clusters, glowing stone |
| Sparkling Skylands | Double streetlight, chic streetlight | Neon flooring, cube lights, spotlight |
| Palette Town | Garden light, plain lamp | String lights, surface lights |

## Standalone Pages

Deployable browser tools hosted via GitHub Pages (branch `gh-pages`).

### Compatibility Tool (`compatibility.html`)

"Who Can Live Together?" — pick a Pokémon, see all compatible housemates ranked by shared favorites.

**Architecture:**
- `data.js` is a generated JS bundle (`window.POKOPIA_DATA`) containing all 305 Pokémon, their habitats, specialties, favorites (43 categories + 5 flavors), and the full item lists per category.
- `app.js` handles all UI: two-screen SPA (picker list → detail view), habitat filter, search, compatibility scoring, and item modal.
- No build toolchain — pure HTML/JS/CSS, no dependencies.

**Item data shape:** each entry in `POKOPIA_DATA.items[<category>]` is an object, not a bare string:

```js
{ name, description, recipe, slug }
// recipe: [{ material, qty }, ...]  OR  null when the item isn't craftable
// slug:   Serebii image slug (lowercase, accents stripped, non-alphanumerics removed)
```

The item modal renders these as a table (sprite · name · description · recipe). Item **sprites are hotlinked** from `https://www.serebii.net/pokemonpokopia/items/<slug>.png` — same external-dependency tradeoff as the Pokémon sprites (which hotlink from pokemondb); a missing image falls back to a monogram tile. Recipe materials show as `Material ×N` chips; non-craftable items show an em dash.

**Rebuild `data.js` after changing CSV, item files, or recipes:**

```bash
# Run from repo root
python standalone-pages/build_data.py
```

Reads `reference/Pokopia.csv`, `reference/Items By Favorite/*.md`, and `reference/Recipes.json`. Joins recipes to items by **case-insensitive name match** (Serebii recipe casing differs from the item-file casing). Validates 305 Pokémon, 43 categories, 5 flavors. Fails loudly on unknown favorite values; warns (does not fail) on items with no recipe.

## Scraper Usage

```bash
# Pokémon database scraper (requires Python + requests/beautifulsoup4)
python "tools/pokopia scraper.py"

# Item recipe + image-slug scraper → reference/Recipes.json
python tools/pokopia_item_scraper.py
```

`pokopia scraper.py` targets are listed in `tools/pokopia_urls.txt`; cached HTML files (`available pokemon.html`, `bulbasaur.html`) are included as offline references.

`pokopia_item_scraper.py` reads Serebii's crafting page and writes `reference/Recipes.json` (item name → `{ slug, materials }`). Re-run it, then `build_data.py`, to refresh recipes/sprites in the compatibility tool.

## Credits

Pokemon data sourced from [Serebii](https://www.serebii.net/). House groupings and planning structure are original work by the repository author.
