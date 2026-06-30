# Pokopia Habitat Compatibility — Implementation Plan

Implementation plan for the standalone **"Who Can Live Together?"** page specified in
[`pokopia_compatibility_design.md`](pokopia_compatibility_design.md). Pick a Pokémon,
see its ideal habitat and favorite item categories, then see every other Pokémon
ranked by habitat compatibility and shared-favorite tiers — down to the concrete
items that please both.

## Context

The design spec is complete and grounded in this repo's data. This document turns it
into a concrete build. All data already lives in `reference/` — the build is a local
**transform**, not a scrape:

- `reference/Pokopia.csv` — 305 Pokémon (the spine).
- `reference/Items By Favorite/<Category>.md` — 43 item-category files (`Name | Description`).
- 5 flavors (Dry, Bitter, Sweet, Sour, Spicy) → 48 distinct favorite types total.

## Confirmed decisions

1. **Structure — separate data file, browser-only (no server).** A real
   `fetch('data.json')` is blocked by browsers on `file://` (CORS), so the data is
   emitted as **`data.js`** assigning a global (`window.POKOPIA_DATA = {…}`) and
   loaded via `<script src>`. A **loading spinner** shows while the app indexes the
   data; sprites get image placeholders while they load.
2. **Sprites — real Pokémon sprites.** The CSV `Number` column is a *Pokopia-internal*
   dex (Abra=#213, Absol=#127), **not** national dex, so sprites are keyed by **name
   slug**, not number. Sprites lazy-load from a public sprite CDN by slug, with an
   `onerror` fallback to a habitat-colored dot + initial monogram (covers Pokopia
   uniques like Peakychu and forms like Tatsugiri Curly Form). This is the only
   runtime network dependency; the compatibility engine is fully local.
3. **Location — `standalone-pages/`** (new directory).

## Verified data facts that shape the build

- **Normalization (confirmed present in the CSV):** typos `Group Activites`→`Group
  Activities`, `Noise stuff`→`Noisy stuff`; flavor casing drift (`Spicy Flavors`/
  `Spicy flavors`, `Sweet Flavors`/`Sweet flavors`, `Sour Flavors`); `None` and
  blanks → favorites-missing (Ditto, Tatsugiri Curly Form).
- CSV favorites are sentence-case (`Group activities`); item files are Title Case
  (`Group Activities`) → map CSV names to the 43 canonical category names.
- **Key everything on `name`** — dex numbers collide (#079 = Pikachu *and* Peakychu).

## Files

```
standalone-pages/
├── build_data.py      # transform reference/ → data.js (committed, reproducible)
├── data.js            # generated: window.POKOPIA_DATA = {...}
├── compatibility.html # standalone page (links css + js + data)
├── styles.css         # mobile-first styles
└── app.js             # picker + engine + tiers + item modal + sprite loader
```

## Data contract (`window.POKOPIA_DATA`)

```js
{
  pokemon: [ { name, dex, habitat, specialties:[], trade_specialty:bool,
              favorites:{ categories:[], flavors:[] }, data_note:null|str } ],
  categories: [ "Blocky Stuff", ... ],      // 43, have item lists
  flavors:    [ "Dry","Bitter","Sweet","Sour","Spicy" ],
  items:      { "<Category>": [ "item name", ... ] }  // 43 keys, names only
}
```

## Engine logic (design §2)

- **Habitat:** opposites Dry↔Humid, Dark↔Bright, Cool↔Warm → **Compatible** (same) /
  **Incompatible** (opposite) / **Neutral** (else).
- **Tiers:** by `|F(S) ∩ F(C)|` over categories+flavors, **6→0**. Tier 6 = "Perfect
  match"; Tier 0 = habitat-compatible, zero overlap. Suppress tiers if `F(S)` empty.
- Within a tier: one block per shared favorite → category chip (tappable → item
  modal) or flavor chip (non-tappable, "food preference" hint) → Pokémon sharing it
  that pass the global habitat filter.
- **Global habitat filter:** sticky 3-state multi-select [Compatible · Neutral ·
  Incompatible], default Compatible only, in-memory only.

## Build steps (`build_data.py`)

1. Parse `Pokopia.csv` → name, dex, ideal_habitat, specialties (Specialty 1/2, drop
   blanks), `trade_specialty = Trade in either`, 6 favorite slots.
2. Normalize favorites (typos, case-fold, sentence→canonical category, split category
   vs the 5-flavor allowlist, `None`/blank → `data_note`).
3. Parse the 43 item files → `items{}` (names only; drop descriptions for size).
4. **Reconcile** every CSV favorite-category against the 43 file names; **fail loudly**
   on any unmapped name (catches future typos).
5. Emit `data.js` as `window.POKOPIA_DATA = <json>;`.
6. Print a validation summary (305 rows, 43 categories, 5 flavors, 2 favorites-missing).

## Implementation (Sonnet subagents, sequential)

1. **Agent A — data build:** write & run `build_data.py`, generate & verify `data.js`.
2. **Agent B — frontend:** build `compatibility.html`, `styles.css`, `app.js` to the
   contract.
3. **Agent C — validation:** spot-check vs CSV, confirm the 6→0 ladder, chip behavior,
   the 2 favorites-missing cases, the habitat filter, and a clean `file://` load.

## Verification

- `python3 standalone-pages/build_data.py` runs clean, prints the 305/43/5/2 summary,
  and fails on an injected unmapped favorite.
- Open `standalone-pages/compatibility.html` via `file://` (and a headless load): no
  console errors; data.js loads; spinner shows then clears.
- Spot checks: Abra (Dark; Strange/Wobbly/Metal/Soft/Watching stuff + Dry flavor)
  tiers correctly; a category chip opens the item modal with real items; a flavor chip
  shows the no-modal hint; Ditto shows the favorites-missing notice; the habitat filter
  changes candidate lists; the sprite fallback renders for a Pokopia-unique (Peakychu).
