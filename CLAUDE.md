# CLAUDE.md — PokopiaPlanning

## Project Overview

Planning toolkit for building Pokopia cities across five areas. The project covers house group assignments, district layout, architecture, landscaping, and item/habitat reference data for 87 houses across 305 Pokemon.

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

## Scraper Usage

```bash
# Run the scraper (requires Python + requests/beautifulsoup4)
python "tools/pokopia scraper.py"
```

Scraper targets are listed in `tools/pokopia_urls.txt`. Cached HTML files (`available pokemon.html`, `bulbasaur.html`) are included as offline references.

## Credits

Pokemon data sourced from [Serebii](https://www.serebii.net/). House groupings and planning structure are original work by the repository author.
