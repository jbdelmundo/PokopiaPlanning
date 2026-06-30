# Game Mechanics

A reference codex of Pokémon Pokopia's core systems — Pokémon, habitats, comfy/comfort
levels, food/favorites, and specialties — with a focus on the **automation farm**
(passive material generation via the **Litter** specialty). Each section ends with a
pointer to the authoritative file in this repo.

> **Sourcing note:** Rosters, habitats, specialties, and favorites below are taken
> verbatim from the local `reference/` files (ground truth). The **drop-material column**
> in the Litter table is external game data ([game8](https://game8.co/games/Pokemon-Pokopia/archives/585452),
> [thegameswiki](https://thegameswiki.com/pokopia/wiki/litter-specialty-and-item-drops)) —
> it is not in any local file and not on Serebii's per-Pokémon pages. Drop **rates** as a
> function of comfy/environment level are undocumented (marked TBD).

---

## 1. Pokémon (overview)

- **308 Pokémon** across 5 areas. Each has:
  - up to **2 specialties** (`Specialty 1`, `Specialty 2`),
  - **1 ideal habitat** (one of 6 types),
  - up to **6 favorites** (a mix of item categories and flavors),
  - per-area habitat availability with rarity / time / weather.
- A Pokémon only appears once you build a habitat that suits it (and even then it isn't
  guaranteed — others may show up instead).

**Reference:** `reference/Pokopia.csv` (full column model documented in `CLAUDE.md`).

---

## 2. Habitat

- **6 habitat types:** Bright, Cool, Dark, Dry, Humid, Warm.
- **Never mix habitat types in a single house** — habitat match is the primary grouping
  rule; flavor/favorite preferences are secondary.
- **209 regular + 5 event habitats**, each an atmospheric build (e.g. "Tree-shaded tall
  grass", "Trash collection site") that attracts a set of Pokémon.

**Reference:** `reference/Habitats.md` (catalog), `reference/Locations.md` (which
habitats/materials each of the 5 areas offers).

---

## 3. Comfy Level (comfort)

- Per-Pokémon happiness ladder: **Iffy → Average → Nice → Great → Awesome**.
- Raised by placing furniture that matches the Pokémon's **favorites** (item categories)
  and feeding it the right **flavors**, inside a correctly-matched habitat.
- Higher comfy levels across an area push up that area's **Environment Level** (§4).
- Relevant to farming: a happier Litter Pokémon is generally more productive (exact
  relationship undocumented — TBD).

**Reference:** `reference/Items By Favorite.md` (furniture grouped by favorite to
maximize comfy levels).

---

## 4. Environment Level

- **Per-area 1–10 progression**, driven by the Comfy Levels of the Pokémon living there.
- Unlocks shops, gifts, and infrastructure as it rises — e.g. the **Pokémon Center
  requires Env Lv 3**.
- It is the lever that gates most area infrastructure (see the Infrastructure Checklist
  in `CLAUDE.md`).

---

## 5. Food / Favorites

Each Pokémon's favorites are two kinds:

- **Item categories (43)** — e.g. *Stone Stuff, Garbage, Cute Stuff, Electronics*. These
  map to furniture lists; match them to raise comfy levels.
- **Flavors (5)** — *Dry, Bitter, Sweet, Sour, Spicy*. These are **food** preferences;
  there are no furniture lists for flavors.

**Reference:** `reference/Items By Favorite/` (43 per-category furniture files).

---

## 6. Specialties (all 31)

Condensed from `reference/Specialties.txt`. **Farming-relevant specialties are bold.**

| # | Specialty | What it does |
|---|---|---|
| 1 | Appraise | Show lost relics to Professor Tangrowth to appraise them |
| 2 | Build | Lead building projects |
| 3 | Bulldoze | Lead demolition / rebuilding / relocation |
| 4 | **Burn** | Set fire to flammable objects; turn **Squishy clay → Brick** |
| 5 | **Chop** | Process **small logs → lumber** |
| 6 | Collect | Trade rare things for certain items |
| 7 | **Crush** | Mash materials into different things |
| 8 | DJ | DJ Rotom plays music CDs |
| 9 | Dream Island | Transport you to a Dream Island |
| 10 | Eat | Mosslax; something good may happen if you offer food |
| 11 | Engineer | Tinkmaster; lead huge building projects |
| 12 | Explode | Fired from a cannon, destroying everything on impact |
| 13 | Fly | Fly you to a Pokémon you're searching for |
| 14 | **Gather** | Pick up items on the ground → put them in a **Community Box** |
| 15 | Gather Honey | Give special furniture if you bring honey |
| 16 | **Generate** | Power machines with electricity |
| 17 | **Grow** | Make plants grow faster |
| 18 | Hype | Dances to music, improving the mood |
| 19 | Illuminate | Peakychu; light up the whole town |
| 20 | **Litter** | **Drop useful materials near their homes** ← farm driver |
| 21 | Paint | Smearguru; recolor furniture |
| 22 | Party | Chef Dente; help prepare food for parties |
| 23 | Rarify | Turn Star Pieces into rare Pokémetal |
| 24 | **Recycle** | **Nonburnable garbage → iron ore**; wastepaper → paper |
| 25 | Search | Help find buried items |
| 26 | Storage | Hold on to your items |
| 27 | Teleport | Instantly take you to a Pokémon you're searching for |
| 28 | Trade | Exchange items at a cash register |
| 29 | Transform | Ditto; improve its moves |
| 30 | **Water** | Spray water on nearby fields and plants |
| 31 | Yawn | Tell you how humid it is |

**Reference:** `reference/Specialties.txt`.

---

## 7. Automation Farm (primary focus)

Passive, hands-free material generation. This is the headline use of the **Litter**
specialty.

### 7a. How the chain works

1. **Litter** Pokémon passively **drop a material** on the ground near their home
   (random quantity — often 1, sometimes 2 or 4).
2. A **Gather** Pokémon living nearby periodically sweeps up dropped items and deposits
   them into the **nearest Community Box**.
3. You collect from the Community Box at your leisure.

**Minimal setup:** Litter habitat → **Community Box placed nearby** → Gather habitat
nearby. No player input after that.

> Drop rate/quantity as a function of Comfy Level and Environment Level is not officially
> documented (**TBD**) — but a comfier, higher-environment area is expected to be more
> productive.

### 7b. Litter Pokémon → dropped material

All **33** Litter-specialty Pokémon (ground truth from `reference/Pokopia.csv`), grouped
by what they drop. **Ideal Habitat** comes from the CSV; **2nd Specialty** is their other
specialty (`—` = Litter only); **Material** is sourced externally (see top of file).

| Pokémon | Ideal Habitat | Material Dropped | 2nd Specialty |
|---|---|---|---|
| **Glimmet** | Dark | Iron Ore ⭐ | — |
| **Glimmora** | Dark | Iron Ore ⭐ | — |
| Combee | Bright | Honey | — |
| Blissey | Bright | Stone | Trade |
| Rampardos | Dry | Stone | Crush |
| Bastiodon | Dry | Stone | Crush |
| Tyrantrum | Dry | Stone | Crush |
| Aurorus | Cool | Stone | Crush |
| Bellsprout | Humid | Vine Rope | Grow |
| Weepinbell | Humid | Vine Rope | Grow |
| Snivy | Humid | Vine Rope | Grow |
| Servine | Humid | Vine Rope | Grow |
| Serperior | Humid | Vine Rope | Grow |
| Tangela | Bright | Vine Rope | Grow |
| Tangrowth | Humid | Vine Rope | Grow |
| Venusaur | Bright | Leaf | Grow |
| Vileplume | Humid | Leaf | Grow |
| Mareep | Bright | Fluff | Generate |
| Flaaffy | Bright | Fluff | Generate |
| Swablu | Bright | Fluff | — |
| Altaria | Bright | Fluff | Fly |
| Grimer | Dark | Nonburnable Garbage | — |
| Muk | Dark | Nonburnable Garbage | — |
| Garbodor | Humid | Nonburnable Garbage | Recycle |
| Spinarak | Humid | Twine | — |
| Ariados | Humid | Twine | — |
| Larvesta | Dry | Twine | Burn |
| Volcarona | Dry | Twine | Burn |
| Paldean Wooper | Humid | Squishy Clay | — |
| Clodsire | Humid | Squishy Clay | Bulldoze |
| Trapinch | Dry | Squishy Clay | Bulldoze |
| Haxorus | Dark | Small Log | Chop |
| Cacturne | Dry | Sturdy Stick | Grow |

**Quick lookup by material:**

| Material | Pokémon |
|---|---|
| **Iron Ore** ⭐ | Glimmet, Glimmora |
| **Honey** | Combee |
| **Stone** | Blissey, Rampardos, Bastiodon, Tyrantrum, Aurorus |
| **Vine Rope** | Bellsprout, Weepinbell, Snivy, Servine, Serperior, Tangela, Tangrowth |
| **Leaf** | Venusaur, Vileplume |
| **Fluff** | Mareep, Flaaffy, Swablu, Altaria |
| **Nonburnable Garbage** | Grimer, Muk, Garbodor |
| **Twine** | Spinarak, Ariados, Larvesta, Volcarona |
| **Squishy Clay** | Paldean Wooper, Clodsire, Trapinch |
| **Small Log** | Haxorus |
| **Sturdy Stick** | Cacturne |

### 7c. Chain-processing — dual-specialty Litter Pokémon = self-contained factories

Some Litter Pokémon have a **2nd specialty that processes their own drop**, turning a
raw farm into a refined-material farm without extra Pokémon:

| Pokémon | Chain | Result |
|---|---|---|
| **Garbodor** | Litter + **Recycle** | Nonburnable Garbage → **Iron Ore** / paper |
| **Haxorus** | Litter + **Chop** | Small Log → **Lumber** |
| **Larvesta / Volcarona** | Litter + **Burn** | Squishy Clay → **Brick** |
| **Rampardos / Bastiodon / Tyrantrum / Aurorus** | Litter + **Crush** | Stone → crushed materials |

> **Iron Ore is the late-game bottleneck** (Iron Ingots gate much high-tier crafting).
> Glimmet/Glimmora drop it directly — the single highest-value farm. Garbodor reaches the
> same output via its self-contained Recycle chain.

### 7d. Best farm picks

| Goal | Pick | Notes |
|---|---|---|
| Iron / ingots | **Glimmet / Glimmora** | Direct Iron Ore drop; or **Garbodor** self-chain |
| Honey | **Combee** | Feeds Gather Honey furniture & honey recipes |
| Lumber | **Haxorus** | Litter + Chop self-chain (Small Log → Lumber) |
| Bricks | **Larvesta / Volcarona** | Litter + Burn self-chain (Squishy Clay → Brick) |

### 7e. References / sources

- **In-repo:** `reference/Specialties.txt` (Litter/Gather/Recycle/Chop/Burn/Crush defs),
  `reference/Pokopia.csv` (Litter roster + habitats + 2nd specialty),
  `reference/Locations.md` (where each material occurs naturally),
  `reference/Recipes.json` (what each farmed material crafts into).
- **External (drop mapping):**
  [game8 Litter guide](https://game8.co/games/Pokemon-Pokopia/archives/585452),
  [thegameswiki Litter list](https://thegameswiki.com/pokopia/wiki/litter-specialty-and-item-drops).
  Used for the **Material Dropped** column only — not present in any local file or on
  Serebii's per-Pokémon pages.
