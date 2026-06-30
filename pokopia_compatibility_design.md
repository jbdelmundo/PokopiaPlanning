# Pokopia "Who Can Live Together?" — Interactive Page Design Spec

**Goal:** a single standalone HTML page with embedded data. Pick a Pokémon, see its ideal habitat and favorite item categories, then see every other Pokémon ranked by how *compatible* it is to cohabit and how many favorites it *shares* — down to the concrete items that please both.

**Platform priority:** mobile-first (designed for ~6–8 sentences of viewport, thumb reach, single column). Desktop is progressive enhancement.

> **Revised against the repository.** Earlier drafts of this spec assumed a live Serebii scrape with sparse data. The data already lives in this repo — see §0. All counts, edge cases, and the build plan below are now grounded in the actual files.

---

## 0. Data reality check (read before building)

The data this page needs is **already in `reference/`** — no scraping required. The build step is a local *transform*, not a fetch.

| Source file | What it provides | Notes |
|---|---|---|
| `reference/Pokopia.csv` | 305 Pokémon: dex `Number`, `Name`, locations, `Specialty 1/2`, `Ideal Habitat`, `Favorite 1`–`Favorite 6`, per-area habitat availability | One row per Pokémon. This is the spine. |
| `reference/Items By Favorite/<Category>.md` | 43 item-category files, each a `Name \| Description` table | These are the **item lists**. Item names only — there is no item-type column. |
| `reference/Items By Favorite.md` | Master index mapping the 43 categories to their files | Use to confirm the canonical category names/casing. |
| `reference/Specialties.txt` | 31 specialty definitions (tab-separated `Name <tab> Description`) | Source of truth for specialty labels. |
| `reference/Habitats.md` | 209 + 3 event habitat flavor descriptions | Background only — not needed for the compatibility engine. |

Facts verified directly against the files that **change the design**:

1. **Roster is 305, all with a habitat.** Every row has a non-empty `Ideal Habitat`. The selectable roster is **305**, not ~250.
2. **Favorites are essentially complete.** 303 of 305 Pokémon have a full set of 6 favorites. Only **two** lack them: **Ditto** (`None`) and **Tatsugiri Curly Form** (blank). The "no favorites recorded" path is a 2-Pokémon edge case, not a common state.
3. **Favorites are two different kinds.** The six favorite slots mix:
   - **Item categories (43)** — these have item-list files → drive the item modal.
   - **Flavors (5)** — **Dry, Bitter, Sweet, Sour, Spicy** flavors. These are *food* preferences with **no item-list files**. They still count as shared favorites for compatibility, but they have no item modal.
   - Total distinct favorite types = **48** (43 + 5).
4. **Item files have no `item_type`.** Each is just `Name \| Description`. Drop the `item_type` field from the data model (or leave it null). Descriptions exist locally but should be dropped from the embedded payload for size.
5. **Dex numbers collide — key on `name`.** Real collisions in the CSV: `#041`, `#059`, `#060`, `#079`, `#109`, `#145`. Notably **`#079` = Pikachu *and* Peakychu** (Peakychu is a real Pokopia-unique Pokémon). The previously cited `#003` collision does **not** exist. **Key everything on `name`.**
6. **Trade specialty can sit in either slot.** 47 Pokémon have `Trade` as Specialty 1 **or** Specialty 2 — check both columns. The "+50% trade value from a matching favorite item" is a game fact worth surfacing as a badge, but note it is **not** stated in `Specialties.txt`; cite Serebii if you want a tooltip.
7. **Source data needs normalization** (do this in the build step — see §6):
   - Typos: `Noise stuff` → `Noisy stuff`; `Group Activites` → `Group Activities`.
   - Casing drift: `Spicy Flavors`/`Spicy flavors`, `Sweet Flavors`/`Sweet flavors` — case-fold to one canonical form.
   - `None` and blanks → treat as "no favorite recorded" (the 2 Pokémon above).
   - CSV favorites are sentence-case (`Group activities`); the item files are Title Case (`Group Activities`). Map CSV names → canonical category names.

---

## 1. Decisions locked

1. **Data source:** transform the existing `reference/` files into embedded JSON. No runtime network calls. (Build step #1.)
2. **Selectable roster:** **all 305** Pokémon are selectable. The 2 without favorites still appear (habitat works; favorites show "none recorded").
3. **Favorite tiering:** **numbered tiers by shared-favorite count** (resolved — see §2b). The old "All / Some / None" three-band model is dropped.

---

## 2. Core logic (the engine behind the screens)

### 2a. Habitat compatibility — 6 habitats, 3 opposing pairs

Opposites: **Dry ↔ Humid · Dark ↔ Bright · Cool ↔ Warm**

| Relationship | Rule | Label | Suggested color |
|---|---|---|---|
| Same habitat | `a == b` | **Compatible** | green |
| Opposite pair | `(a,b)` in the 3 pairs above | **Incompatible** | red |
| Anything else | not same, not opposite | **Neutral** | amber/grey |

Total and unambiguous: every habitat has exactly one opposite, so the remaining four are always Neutral (e.g. Bright vs Cool/Dry/Humid/Warm = Neutral; Bright vs Dark = Incompatible).

Habitat distribution in the data (for sanity / tier sizing): Bright 93 · Humid 74 · Dark 60 · Warm 49 · Dry 20 · Cool 9.

### 2b. Favorites overlap → numbered tiers

For selected Pokémon `S` with favorite set `F(S)` (categories **and** flavors), and any candidate `C`:
`shared = F(S) ∩ F(C)`

**Tiering is by `|shared|`, highest first.** Because 303/305 Pokémon carry exactly 6 favorites, the ladder is effectively fixed and stable — it does not collapse per-Pokémon the way a subset model would:

| Tier | Condition | Label | Meaning |
|---|---|---|---|
| **Tier 6** | `\|shared\| = 6` | **Perfect match** | Identical favorite set. (With both sets size 6, "shares all" = "identical".) |
| **Tier 5** | `\|shared\| = 5` | **5 shared** | |
| **Tier 4** | `\|shared\| = 4` | **4 shared** | |
| **Tier 3** | `\|shared\| = 3` | **3 shared** | |
| **Tier 2** | `\|shared\| = 2` | **2 shared** | |
| **Tier 1** | `\|shared\| = 1` | **1 shared** | |
| **Tier 0** | `\|shared\| = 0` | **None** | Habitat-compatible, zero favorite overlap — still cohabitable by biome. |

General rule (for the rare Pokémon with fewer than 6 favorites, e.g. a future partial entry): tiers run from `|F(S)|` down to `1`, then `0`. Tier `|F(S)|` is always the "identical/contains-all" top band. Empty tiers render as a thin "0" stub (§5) so the ladder stays legible.

**Edge case:** if `F(S)` is empty (Ditto, Tatsugiri Curly Form), suppress the favorites tiers and show a notice; habitat compatibility still works.

> Why numbered, not a subset "All" band: in this dataset almost every Pokémon has exactly 6 favorites, so a subset test (`F(S) ⊆ F(C)`) reduces to *identical set* — a single, often-empty bucket. Numbered tiers give a smooth, populated ladder (6→0) that actually distinguishes candidates.

### 2c. What appears inside a tier

Within each tier, the unit is the **shared favorite**, not the raw Pokémon. For each favorite in `shared`:
- show the **favorite chip**:
  - **item category** → tappable (opens item modal, §2d);
  - **flavor** → styled distinctly (e.g. a small fork/spoon icon) and **not** tappable, with a one-line "food preference — no item list" hint;
- under it, list the Pokémon that **share that favorite** *and* pass the **global habitat filter** (§3).

> Reconciliation: the habitat filter defaults to *Compatible only* (= same habitat). When widened to include Neutral/Incompatible, each listed Pokémon carries a small habitat-compatibility tag so the same/neutral/incompatible distinction stays visible.

### 2d. Item modal

Tapping an **item-category** chip opens a modal listing the **actual items** in that category (`item_name`). Rationale: any item in a shared category pleases *both* Pokémon, so these are the concrete gift/decoration picks. Items come straight from the matching `reference/Items By Favorite/<Category>.md` file. **Flavor chips have no modal** (no item data exists for flavors in the repo).

---

## 3. Global habitat filter

- A persistent, app-wide setting (not per-Pokémon): a 3-state toggle group **[ Compatible · Neutral · Incompatible ]**.
- **Default: Compatible only.**
- Multi-select (any combination). Drives which candidates appear in every tier on the PokémonHabitat page.
- Lives in a sticky header bar so it's reachable with one thumb while scrolling long tiers.
- State persists across Pokémon selections within the session (in-memory only — no localStorage in this environment).

---

## 4. Data model (embedded JSON)

```
pokemon[]    { name, dex, habitat, specialties[], trade_specialty:bool,
               favorites: { categories[], flavors[] } }      # 305 rows
categories[] { name }                                        # 43 item categories (have item lists)
flavors[]    { name }                                        # 5 (Dry, Bitter, Sweet, Sour, Spicy)
items[]      { name, categories[] }                          # union of the 43 files; no item_type in source
```

Derived at runtime (cheap, in JS): habitat compatibility for any pair; `F(S) ∩ F(C)` over categories+flavors; per-favorite Pokémon index. No build-time precompute needed at this scale.

Provenance: keep a `data_note` per Pokémon for the 2 favorites-missing cases and any name reconciled during the build.

---

## 5. Screen-by-screen (mobile-first)

### Screen A — Pokémon Picker (entry)
- Top: search box (type-ahead on name) + result count (305).
- List: single column, each row = sprite-dot + name + a small habitat badge (color-coded).
- Optional collapsible "group by habitat" section headers so users can browse by biome.
- Tap a row → Screen B.

### Screen B — PokémonHabitat page (the heart)
Layout, top to bottom:

1. **Sticky header**
   - Back · selected Pokémon name · habitat badge · Trade-specialty star (if Trade in either specialty slot).
   - The global habitat filter toggle group (§3).

2. **"About this Pokémon" card**
   - Ideal habitat (with its opposite/neutral relationships explained in one line).
   - Specialties (chips).
   - Its favorite chips — item categories tappable (→ item modal), flavors styled distinctly and non-tappable.
   - If no favorites recorded (Ditto, Tatsugiri Curly Form): inline notice.

3. **Tiers** (accordion sections, highest first: **Perfect match (6) → 5 → 4 → 3 → 2 → 1 → None (0)**)
   - Each tier header shows: tier label + count of matching Pokémon (after filter).
   - Inside a tier: one block **per shared favorite** →
     - favorite chip (item category → item modal; flavor → hint, no modal)
     - chips/rows of Pokémon sharing that favorite + passing the filter, each with a habitat-compat tag when the filter is widened.
   - The **None** tier lists habitat-compatible Pokémon with zero favorite overlap.
   - Empty tiers collapse to a thin "0" stub rather than disappearing (keeps the 6→0 ladder legible).

4. **Item modal** (overlay, §2d)
   - Title = category name. Scrollable list of item names. Close affordance large enough for thumb.

### Mobile interaction notes
- Accordions default: **Perfect match (6)** open, rest collapsed (avoids a wall of content).
- Chips are ≥40px tall tap targets; horizontal chip rows scroll, never wrap into tiny targets.
- Color is never the only signal — habitat/compat and category/flavor states also carry text/icon (accessibility, colorblind-safe).
- Everything embedded → works offline once loaded; no network calls at runtime.

---

## 6. Build plan (when you greenlight code)

1. **Parse `reference/Pokopia.csv`** → one Pokémon record each: `name`, `dex`, `ideal_habitat`, `specialties[]` (cols Specialty 1/2, drop blanks), `trade_specialty = (Trade in either)`, and the 6 favorite slots.
2. **Normalize favorites** (per §0.7): fix typos, case-fold, map CSV sentence-case names to canonical category names, split each favorite into **category** vs **flavor** (the 5 flavor names are a fixed allowlist). Drop `None`/blanks → favorites-missing flag.
3. **Parse the 43 `reference/Items By Favorite/<Category>.md` tables** → `items[]` (name only; drop descriptions for payload size) and the category→items / item→categories indexes.
4. **Reconcile** every CSV favorite-category name against the 43 file names; fail the build loudly on any unmapped name (catches new typos).
5. **Emit** the embedded JSON (single file) + build the standalone HTML/CSS/JS (vanilla, mobile-first CSS — no framework needed at this size).
6. **Validate**: spot-check a few Pokémon against the CSV; confirm the 6→0 tier ladder, the flavor-vs-category chip behavior, the 2 favorites-missing Pokémon, and the habitat filter end to end.

---

## 7. Resolved decisions

- **Tiering (was the open question):** **numbered tiers by shared count (6→0)**, not a three-band All/Some/None model. Grounded in the data — nearly every Pokémon has exactly 6 favorites, so numbered bands populate cleanly and a subset "All" band would mostly be empty. See §2b.
- **Flavors vs categories:** both count toward the shared-favorite tier; only item categories open the item modal. See §2c–2d.
- **Roster & completeness:** 305 selectable; only Ditto and Tatsugiri Curly Form lack favorites. See §0.
