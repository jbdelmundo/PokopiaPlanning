# CLAUDE.md — PokopiaPlanning

## Project Overview

Planning toolkit for building Pokopia cities across five areas. The project covers house group assignments, district layout, architecture, landscaping, and item/habitat reference data for 87 houses across 308 Pokemon.

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
│   ├── Pokopia.csv                    # Full 308-Pokemon database
│   ├── Item List.txt                  # Complete item catalog
│   ├── Items By Favorite.md           # 43 favorite categories → item lists
│   ├── Items By Favorite/             # Per-category item breakdowns
│   ├── Habitats.md                    # 209 regular + 5 event habitats
│   ├── Locations.md                   # 6 area overviews with available materials
│   ├── Specialties.txt                # 31 Pokemon specialty types
│   └── Game Mechanics.md              # Mechanics codex + Litter automation-farm table
├── standalone-pages/       # Deployable web tools (GitHub Pages)
│   ├── index.html                     # Landing page (GitHub Pages entry) → routes to both planners
│   ├── compatibility.html             # "Who Can Live Together?" planner
│   ├── app.js                         # Compatibility UI logic (picker + detail screens)
│   ├── farm-planner.html              # "Automation Farm Planner" planner
│   ├── farm-app.js                    # Farm planner UI logic (material farms + roster)
│   ├── farm-styles.css                # Farm-planner-only styles (loaded after styles.css)
│   ├── styles.css                     # Shared app styles / theme
│   ├── data.js                        # Generated data bundle (window.POKOPIA_DATA)
│   └── build_data.py                  # Reads Pokopia.csv + Items By Favorite + Game Mechanics → data.js
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

## Game Mechanics & Automation Farm

Comfy Levels (Iffy → Awesome) are raised by matching a Pokemon's favorites/flavors with
house furniture in a correct habitat; rising Comfy Levels drive each area's Environment
Level (1–10), which unlocks shops, gifts, and infrastructure (Pokemon Center at Env Lv 3).

**Automation farm** — passive material generation via the **Litter** specialty: a Litter
Pokemon drops a material near its home, a nearby **Gather** Pokemon sweeps drops into the
**Community Box**. Marquee farms: **Iron Ore** via Glimmet/Glimmora (late-game ingot
bottleneck), **Honey** via Combee, and **self-chaining** dual-specialty Pokemon like
Garbodor (Litter+Recycle → iron ore) and Haxorus (Litter+Chop → lumber).

Full mechanics codex + the 33-Pokemon Litter drop table → `reference/Game Mechanics.md`.

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

Deployable browser tools hosted via GitHub Pages (branch `gh-pages`). `index.html` is the
landing page / Pages entry point and routes between the two planners; the
`.github/workflows/pages.yml` workflow stages every page + `data.js` into `_site`. All pages
are pure HTML/JS/CSS that also run by opening the file directly (`file://`) — no web server,
no build step at page-load time.

### Compatibility Tool (`compatibility.html`)

"Who Can Live Together?" — pick a Pokémon, see all compatible housemates ranked by shared favorites.

**Architecture:**
- `data.js` is a generated JS bundle (`window.POKOPIA_DATA`) containing all 308 Pokémon, their habitats, specialties, favorites (43 categories + 5 flavors), and the full item lists per category.
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

Reads `reference/Pokopia.csv`, `reference/Items By Favorite/*.md`, and `reference/Recipes.json`. Joins recipes to items by **case-insensitive name match** (Serebii recipe casing differs from the item-file casing). Validates 308 Pokémon, 43 categories, 5 flavors. Fails loudly on unknown favorite values; warns (does not fail) on items with no recipe.

### Automation Farm Planner (`farm-planner.html`)

"Which Pokémon can I group into a working material farm?" A farm is a 3-role chain: a
**Litter** Pokémon drops a raw material, an optional **Processor** (Burn / Chop / Crush /
Recycle) refines it, and a **Gather** Pokémon sweeps drops into the Community Box.

**Architecture (clones the compatibility tool):** `farm-app.js` builds **material-centric
modules** — one per dropped material — from `POKOPIA_DATA.farm` + the per-Pokémon
`specialties`/`favorites`/`habitat` already in the bundle. Two-screen SPA (farm-card picker →
chain detail), reusing the `el()` helper, sprite/monogram fallback, and habitat-relation +
shared-favorite scoring patterns from `app.js`. `farm-styles.css` adds only farm-specific
classes on top of the shared `styles.css`.

- **Roster** ("already in my town") is an editable set saved in `localStorage`
  (`pokopia_roster`); a mode toggle switches between *All Pokémon* and *Buildable now* (a
  farm is buildable when a Litter **and** a Gatherer are both in the roster — a Processor is
  a bonus).
- **Ranking:** modules score on producing a high-value material (Iron Ore/Ingot),
  self-chaining availability, best shared-favorite overlap (comfy), capacity (number of
  Litter Pokémon for that material), and fewest Pokémon. Role candidates rank by shared
  favorites with the Litter cluster, then habitat compatibility.
- **Self-chaining** is computed from data: a Litter whose 2nd specialty matches its
  material's processing rule (Garbodor→Recycle, Haxorus→Chop, Rampardos&c.→Crush) refines
  its own drop, so no extra Pokémon is needed.

**`farm` data shape** in `POKOPIA_DATA` (emitted by `build_data.py`):

```js
POKOPIA_DATA.farm = {
  litter: [ { pokemon, habitat, material, secondSpecialty /* str|null */, highValue } ],
  processing: [ { input, specialty, output } ]   // e.g. Squishy Clay --Burn--> Brick
}
```

`build_data.py` parses the **33-row Litter table in `reference/Game Mechanics.md` §7b** (via
`read_litter_table()`, fails loudly if a Litter name is missing from the CSV or the row count
drifts from 33). `processing` is a small curated constant (`PROCESSING_RULES`) seeded from
§7c + `reference/Item List.txt`; keep it in sync with those files. Pokémon sprites hotlink
from pokemondb (monogram fallback on miss), same tradeoff as the compatibility tool.

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
