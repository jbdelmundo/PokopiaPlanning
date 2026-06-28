/* =========================================================
   Pokopia "Who Can Live Together?" — app.js
   Vanilla JS, no frameworks, works from file://
   ========================================================= */

(function () {
  'use strict';

  /* ── 1. Constants & state ───────────────────────────────── */

  const HABITATS = ['Bright', 'Cool', 'Dark', 'Dry', 'Humid', 'Warm'];
  const OPPOSITE = { Bright: 'Dark', Dark: 'Bright', Cool: 'Warm', Warm: 'Cool', Dry: 'Humid', Humid: 'Dry' };

  // Global filter state — persists across Pokémon selections (in-memory only)
  const filterState = new Set(['compatible']); // default: Compatible only

  // Currently selected Pokémon
  let selectedPokemon = null;

  // Grouped-by-habitat toggle
  let groupByHabitat = false;

  // Current search query
  let searchQuery = '';

  /* ── 2. Engine functions ────────────────────────────────── */

  /**
   * habitatRelation(a, b) — returns 'compatible' | 'neutral' | 'incompatible'
   * a and b are habitat name strings (e.g. 'Dark', 'Bright').
   */
  function habitatRelation(a, b) {
    if (a === b) return 'compatible';
    if (OPPOSITE[a] === b) return 'incompatible';
    return 'neutral';
  }

  /**
   * allFavorites(pk) — returns a Set of all favorite strings (categories + flavors)
   * for a Pokémon object.
   */
  function allFavorites(pk) {
    const cats = (pk.favorites && pk.favorites.categories) || [];
    const flavs = (pk.favorites && pk.favorites.flavors) || [];
    return new Set([...cats, ...flavs]);
  }

  /**
   * hasFavorites(pk) — true unless data_note is set (Ditto / Tatsugiri Curly Form edge case).
   */
  function hasFavorites(pk) {
    return !pk.data_note && (allFavorites(pk).size > 0);
  }

  /**
   * sharedFavorites(selected, candidate) — returns an Array of favorite strings
   * that appear in both Pokémon's favorite sets.
   */
  function sharedFavorites(selected, candidate) {
    const sSet = allFavorites(selected);
    const cSet = allFavorites(candidate);
    const shared = [];
    for (const fav of sSet) {
      if (cSet.has(fav)) shared.push(fav);
    }
    return shared;
  }

  /**
   * tierFor(selected, candidate) — returns an integer 0–6 (or 0 when no favorites).
   */
  function tierFor(selected, candidate) {
    if (!hasFavorites(selected)) return null; // suppress tiers for missing-favorites Pokémon
    return sharedFavorites(selected, candidate).length;
  }

  /* ── 3. Sprite utilities ────────────────────────────────── */

  /**
   * spriteSlug(name) — converts a Pokémon name to the pokemondb URL slug.
   * Rules:
   *   - lowercase
   *   - strip accents (é → e, etc.)
   *   - remove non-alphanumeric except hyphens
   *   - spaces → hyphens
   *   - trailing/duplicate hyphens cleaned up
   *   - special form overrides (e.g. Tatsugiri Curly Form → tatsugiri-curly)
   */
  function spriteSlug(name) {
    // Special-case overrides for Pokopia-unique or oddly-named forms
    const overrides = {
      'Tatsugiri Curly Form': 'tatsugiri-curly',
      'Peakychu': 'pikachu',            // Pokopia-unique; fallback to base form
      'Mr. Mime': 'mr-mime',
      'Mime Jr.': 'mime-jr',
      "Farfetch'd": 'farfetchd',
      'Flabébé': 'flabebe',
      'Nidoran♀': 'nidoran-f',
      'Nidoran♂': 'nidoran-m',
      'Porygon-Z': 'porygon-z',
      'Ho-oh': 'ho-oh',
      'Type: Null': 'type-null',
      'Jangmo-o': 'jangmo-o',
      'Hakamo-o': 'hakamo-o',
      'Kommo-o': 'kommo-o',
      'Tapu Koko': 'tapu-koko',
      'Tapu Lele': 'tapu-lele',
      'Tapu Bulu': 'tapu-bulu',
      'Tapu Fini': 'tapu-fini',
    };
    if (overrides[name]) return overrides[name];

    let s = name.toLowerCase();
    // Strip diacritics
    s = s.normalize('NFD').replace(/[̀-ͯ]/g, '');
    // Replace ♀/♂ with -f/-m
    s = s.replace('♀', '-f').replace('♂', '-m');
    // Strip apostrophes
    s = s.replace(/[''']/g, '');
    // Remove trailing "form" or "forme" suffix often not in sprite names
    s = s.replace(/\s+form[e]?$/, '');
    // Spaces to hyphens
    s = s.replace(/\s+/g, '-');
    // Remove everything except alphanumeric and hyphens
    s = s.replace(/[^a-z0-9-]/g, '');
    // Clean up multiple or leading/trailing hyphens
    s = s.replace(/-+/g, '-').replace(/^-|-$/g, '');
    return s;
  }

  function spriteUrl(name) {
    return 'https://img.pokemondb.net/sprites/home/normal/' + spriteSlug(name) + '.png';
  }

  /**
   * buildSpriteElement(pk, sizeClass) — returns a .sprite-container div.
   * Shows shimmer while loading; swaps to img on load or monogram on error.
   */
  function buildSpriteElement(pk, sizeClass) {
    sizeClass = sizeClass || 'sprite-small';
    const container = el('div', { class: 'sprite-container ' + sizeClass });

    const shimmer = el('div', { class: 'sprite-shimmer' });
    container.appendChild(shimmer);

    const img = el('img', {
      src: spriteUrl(pk.name),
      alt: pk.name,
      loading: 'lazy',
      class: 'sprite-img loading',
    });

    img.addEventListener('load', function () {
      img.classList.remove('loading');
      img.classList.add('loaded');
      shimmer.remove();
    });

    img.addEventListener('error', function () {
      // Replace with monogram fallback
      shimmer.remove();
      img.remove();
      const fb = el('div', {
        class: 'sprite-fallback sprite-' + pk.habitat,
        'aria-hidden': 'true',
      });
      fb.textContent = pk.name.charAt(0).toUpperCase();
      container.appendChild(fb);
    });

    container.appendChild(img);
    return container;
  }

  /* ── 4. DOM helpers ─────────────────────────────────────── */

  function el(tag, attrs, ...children) {
    const node = document.createElement(tag);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        if (k === 'class') node.className = v;
        else node.setAttribute(k, v);
      }
    }
    for (const child of children) {
      if (child == null) continue;
      if (typeof child === 'string') node.appendChild(document.createTextNode(child));
      else node.appendChild(child);
    }
    return node;
  }

  function habitatBadge(habitat) {
    const b = el('span', { class: 'habitat-badge badge-' + habitat });
    b.textContent = habitat;
    return b;
  }

  /* ── 5. Indexes built from POKOPIA_DATA ─────────────────── */

  let pkByName = {};         // name → pokemon object
  let pkList = [];           // all 305 Pokémon
  let categorySet = new Set(); // canonical category names
  let flavorSet = new Set();   // 'Dry', 'Bitter', etc.

  function buildIndexes() {
    const data = window.POKOPIA_DATA;
    pkList = data.pokemon;
    data.categories.forEach(function (c) { categorySet.add(c); });
    data.flavors.forEach(function (f) { flavorSet.add(f); });
    pkList.forEach(function (pk) { pkByName[pk.name] = pk; });
  }

  /* ── 6. Screen A — Picker ───────────────────────────────── */

  function renderPicker() {
    const list = document.getElementById('pokemon-list');
    const countEl = document.getElementById('result-count');

    let filtered = pkList.filter(function (pk) {
      if (!searchQuery) return true;
      return pk.name.toLowerCase().includes(searchQuery.toLowerCase());
    });

    countEl.textContent = filtered.length + ' of ' + pkList.length + ' Pokémon';

    list.innerHTML = '';

    if (groupByHabitat) {
      // Group by habitat (sorted in canonical order)
      const byHabitat = {};
      filtered.forEach(function (pk) {
        if (!byHabitat[pk.habitat]) byHabitat[pk.habitat] = [];
        byHabitat[pk.habitat].push(pk);
      });

      HABITATS.forEach(function (hab) {
        if (!byHabitat[hab] || byHabitat[hab].length === 0) return;
        const group = byHabitat[hab];

        // Group header (collapsible)
        const header = el('div', { class: 'habitat-group-header', role: 'button', tabindex: '0', 'aria-expanded': 'true', 'aria-controls': 'group-body-' + hab });
        header.appendChild(habitatBadge(hab));
        header.appendChild(document.createTextNode(hab));
        const countSpan = el('span', { class: 'group-count' });
        countSpan.textContent = group.length;
        header.appendChild(countSpan);
        list.appendChild(header);

        const body = el('div', { class: 'habitat-group-body', id: 'group-body-' + hab });
        group.forEach(function (pk) { body.appendChild(buildPokemonRow(pk)); });
        list.appendChild(body);

        // Toggle collapse
        function toggleGroup() {
          const collapsed = body.classList.toggle('collapsed');
          header.setAttribute('aria-expanded', String(!collapsed));
        }
        header.addEventListener('click', toggleGroup);
        header.addEventListener('keydown', function (e) {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleGroup(); }
        });
      });
    } else {
      filtered.forEach(function (pk) { list.appendChild(buildPokemonRow(pk)); });
    }

    if (filtered.length === 0) {
      const empty = el('p', { class: 'favorites-notice' });
      empty.textContent = 'No Pokémon match "' + searchQuery + '".';
      list.appendChild(empty);
    }
  }

  function buildPokemonRow(pk) {
    const row = el('button', {
      class: 'pokemon-row',
      type: 'button',
      'aria-label': pk.name + ', ' + pk.habitat + ' habitat',
      role: 'listitem',
    });
    row.appendChild(buildSpriteElement(pk, 'sprite-small'));
    const nameEl = el('span', { class: 'pokemon-row-name' });
    nameEl.textContent = pk.name;
    row.appendChild(nameEl);
    row.appendChild(habitatBadge(pk.habitat));
    const dexEl = el('span', { class: 'pokemon-row-dex' });
    dexEl.textContent = pk.dex;
    row.appendChild(dexEl);

    row.addEventListener('click', function () { openDetail(pk); });
    return row;
  }

  /* ── 7. Screen B — Detail ───────────────────────────────── */

  function openDetail(pk) {
    selectedPokemon = pk;
    document.getElementById('screen-picker').classList.add('hidden');
    document.getElementById('screen-detail').classList.remove('hidden');
    renderDetail(pk);
    window.scrollTo(0, 0);
  }

  function openPicker() {
    selectedPokemon = null;
    document.getElementById('screen-detail').classList.add('hidden');
    document.getElementById('screen-picker').classList.remove('hidden');
    window.scrollTo(0, 0);
  }

  function renderDetail(pk) {
    // ── Header
    document.getElementById('header-name').textContent = pk.name;
    const headerBadge = document.getElementById('header-habitat-badge');
    headerBadge.className = 'habitat-badge badge-' + pk.habitat;
    headerBadge.textContent = pk.habitat;

    const tradeStar = document.getElementById('header-trade-star');
    if (pk.trade_specialty) tradeStar.classList.remove('hidden');
    else tradeStar.classList.add('hidden');

    // ── About card
    document.getElementById('about-name').textContent = pk.name;

    // Sprite (replace any previous)
    const spriteContainer = document.getElementById('about-sprite-container');
    const parent = spriteContainer.parentElement;
    const newSprite = buildSpriteElement(pk, 'sprite-large');
    newSprite.id = 'about-sprite-container';
    parent.replaceChild(newSprite, spriteContainer);

    // Habitat line
    const opp = OPPOSITE[pk.habitat];
    const neutralOthers = HABITATS.filter(function (h) { return h !== pk.habitat && h !== opp; });
    document.getElementById('habitat-line').textContent =
      'Ideal habitat: ' + pk.habitat + '. ' +
      'Incompatible with ' + opp + '. ' +
      neutralOthers.join(', ') + ' are neutral.';

    // Specialty chips
    const specRow = document.getElementById('specialty-chips');
    specRow.innerHTML = '';
    if (pk.specialties && pk.specialties.length) {
      pk.specialties.forEach(function (spec) {
        const c = el('span', { class: 'chip chip-specialty' });
        c.textContent = spec;
        specRow.appendChild(c);
      });
    } else {
      specRow.textContent = 'None';
    }

    // Favorites chips
    const favRow = document.getElementById('favorite-chips');
    const favNotice = document.getElementById('favorites-notice');
    favRow.innerHTML = '';

    if (!hasFavorites(pk)) {
      favRow.classList.add('hidden');
      favNotice.classList.remove('hidden');
      favNotice.textContent = pk.data_note
        ? 'No favorites recorded for this Pokémon (' + pk.data_note + ').'
        : 'No favorites recorded for this Pokémon.';
    } else {
      favRow.classList.remove('hidden');
      favNotice.classList.add('hidden');
      const cats = (pk.favorites && pk.favorites.categories) || [];
      const flavs = (pk.favorites && pk.favorites.flavors) || [];
      cats.forEach(function (cat) {
        favRow.appendChild(buildCategoryChip(cat, 'chip chip-category'));
      });
      flavs.forEach(function (flav) {
        const wrap = el('div', { class: 'fav-chip-wrap' });
        const c = el('span', { class: 'chip chip-flavor' });
        const icon = el('span', { class: 'chip-icon', 'aria-hidden': 'true' });
        icon.textContent = '🍴';
        c.appendChild(icon);
        c.appendChild(document.createTextNode(flav));
        wrap.appendChild(c);
        const hint = el('span', { class: 'chip-flavor-hint' });
        hint.textContent = 'Food preference — no item list';
        wrap.appendChild(hint);
        favRow.appendChild(wrap);
      });
    }

    // ── Tiers
    renderTiers(pk);
  }

  function buildCategoryChip(cat, classes) {
    const c = el('button', { class: classes, type: 'button', 'aria-label': cat + ' — tap to see items' });
    const icon = el('span', { class: 'chip-icon', 'aria-hidden': 'true' });
    icon.textContent = '📦';
    c.appendChild(icon);
    c.appendChild(document.createTextNode(cat));
    c.addEventListener('click', function () { openItemModal(cat); });
    return c;
  }

  /* ── 8. Tiers rendering ─────────────────────────────────── */

  function renderTiers(pk) {
    const container = document.getElementById('tiers-container');
    container.innerHTML = '';

    if (!hasFavorites(pk)) {
      // Show a simple notice; still show compatible Pokémon in a flat list
      const notice = el('p', { class: 'favorites-notice' });
      notice.textContent = 'Favorites not recorded — showing habitat-compatible Pokémon only.';
      container.appendChild(notice);
      renderNoFavoritesTier(pk, container);
      return;
    }

    // Build per-tier data: tier 6 → 0
    const tiers = buildTierData(pk);

    // Open the highest-ranked non-empty tier by default. Perfect match (6) is
    // usually empty, so falling through to the best populated tier keeps the
    // user from landing on a wall of collapsed accordions.
    let openTier = -1;
    for (let t = 6; t >= 0; t--) {
      if (tiers[t].pokemonSet.size > 0) { openTier = t; break; }
    }

    for (let t = 6; t >= 0; t--) {
      const tierData = tiers[t];
      const block = buildTierBlock(pk, t, tierData, t === openTier);
      container.appendChild(block);
    }
  }

  /**
   * buildTierData(pk) — returns an object keyed by tier number (0–6).
   * Each value is { favorites: [ { name, isCategory, candidates: [pk...] } ], pokemonSet: Set }
   * Candidates are filtered by the current filterState.
   */
  function buildTierData(pk) {
    const data = {};
    for (let t = 0; t <= 6; t++) {
      data[t] = { favorites: [], pokemonSet: new Set() };
    }

    const others = pkList.filter(function (c) { return c.name !== pk.name; });

    others.forEach(function (candidate) {
      const rel = habitatRelation(pk.habitat, candidate.habitat);
      if (!filterState.has(rel)) return; // filtered out

      const shared = sharedFavorites(pk, candidate);
      const t = shared.length;

      // Track candidate in tier's overall pokemonSet
      data[t].pokemonSet.add(candidate.name);

      // For each shared favorite, add candidate to that favorite's sub-list
      shared.forEach(function (fav) {
        let favEntry = data[t].favorites.find(function (f) { return f.name === fav; });
        if (!favEntry) {
          favEntry = {
            name: fav,
            isCategory: categorySet.has(fav),
            isFlavor: flavorSet.has(fav),
            candidates: [],
          };
          data[t].favorites.push(favEntry);
        }
        favEntry.candidates.push(candidate);
      });
    });

    // Handle tier 0 separately: candidates with 0 shared favorites that pass the filter
    // Already captured above via shared.length === 0

    // Sort favorites within each tier by candidate count descending
    for (let t = 0; t <= 6; t++) {
      data[t].favorites.sort(function (a, b) { return b.candidates.length - a.candidates.length; });
    }

    return data;
  }

  function buildTierBlock(pk, tierNum, tierData, shouldOpen) {
    const count = tierData.pokemonSet.size;
    const isEmpty = count === 0;

    let label;
    if (tierNum === 6) label = 'Perfect match (6 shared)';
    else if (tierNum === 0) label = 'None in common';
    else label = tierNum + ' shared';

    const block = el('div', { class: 'tier-block' + (isEmpty ? ' tier-empty' : '') });

    // Accordion header (button for keyboard/a11y)
    const header = el('button', {
      class: 'tier-header',
      type: 'button',
      'aria-expanded': 'false',
    });
    const labelEl = el('span', { class: 'tier-label' });
    labelEl.textContent = label;
    const countEl = el('span', { class: 'tier-count' });
    countEl.textContent = count + ' Pokémon';
    const chevron = el('span', { class: 'tier-chevron', 'aria-hidden': 'true' });
    chevron.textContent = '▼';
    header.appendChild(labelEl);
    header.appendChild(countEl);
    header.appendChild(chevron);
    block.appendChild(header);

    // Tier body
    const body = el('div', { class: 'tier-body' });

    if (!isEmpty) {
      if (tierNum === 0) {
        // Tier 0: list compatible Pokémon with no shared favs
        const listEl = el('div', { class: 'none-tier-list' });
        tierData.pokemonSet.forEach(function (name) {
          const c = pkByName[name];
          listEl.appendChild(buildCandidateChip(c, pk.habitat));
        });
        body.appendChild(listEl);
      } else {
        // Tiers 1–6: one block per shared favorite
        tierData.favorites.forEach(function (fav) {
          const filtered = fav.candidates.filter(function (c) {
            const rel = habitatRelation(pk.habitat, c.habitat);
            return filterState.has(rel);
          });
          if (filtered.length === 0) return;

          const group = el('div', { class: 'fav-group' });
          const chipRow = el('div', { class: 'fav-group-chip-row' });

          if (fav.isCategory) {
            chipRow.appendChild(buildCategoryChip(fav.name, 'chip chip-category'));
          } else {
            // Flavor
            const wrap = el('div', { class: 'fav-chip-wrap' });
            const c = el('span', { class: 'chip chip-flavor' });
            const icon = el('span', { class: 'chip-icon', 'aria-hidden': 'true' });
            icon.textContent = '🍴';
            c.appendChild(icon);
            c.appendChild(document.createTextNode(fav.name));
            wrap.appendChild(c);
            const hint = el('span', { class: 'chip-flavor-hint' });
            hint.textContent = 'Food preference — no item list';
            wrap.appendChild(hint);
            chipRow.appendChild(wrap);
          }
          group.appendChild(chipRow);

          const candList = el('div', { class: 'candidate-list' });
          filtered.forEach(function (candidate) {
            candList.appendChild(buildCandidateChip(candidate, pk.habitat));
          });
          group.appendChild(candList);
          body.appendChild(group);
        });
      }
    }

    block.appendChild(body);

    // Open the highest non-empty tier by default (decided in renderTiers).
    if (shouldOpen && !isEmpty) {
      block.classList.add('open');
      header.setAttribute('aria-expanded', 'true');
    }

    // Accordion toggle
    if (!isEmpty) {
      header.addEventListener('click', function () {
        const isOpen = block.classList.toggle('open');
        header.setAttribute('aria-expanded', String(isOpen));
      });
    }

    return block;
  }

  function renderNoFavoritesTier(pk, container) {
    // Just show compatible Pokémon in a flat list (no tier structure)
    const compatibles = pkList.filter(function (c) {
      if (c.name === pk.name) return false;
      const rel = habitatRelation(pk.habitat, c.habitat);
      return filterState.has(rel);
    });
    if (compatibles.length === 0) return;

    const block = el('div', { class: 'tier-block open' });
    const header = el('button', { class: 'tier-header', type: 'button', 'aria-expanded': 'true' });
    const labelEl = el('span', { class: 'tier-label' });
    labelEl.textContent = 'By habitat only';
    const countEl = el('span', { class: 'tier-count' });
    countEl.textContent = compatibles.length + ' Pokémon';
    const chevron = el('span', { class: 'tier-chevron', 'aria-hidden': 'true' });
    chevron.textContent = '▼';
    header.appendChild(labelEl);
    header.appendChild(countEl);
    header.appendChild(chevron);
    block.appendChild(header);

    const body = el('div', { class: 'tier-body' });
    const listEl = el('div', { class: 'none-tier-list' });
    compatibles.forEach(function (c) {
      listEl.appendChild(buildCandidateChip(c, pk.habitat));
    });
    body.appendChild(listEl);
    block.appendChild(body);

    header.addEventListener('click', function () {
      const isOpen = block.classList.toggle('open');
      header.setAttribute('aria-expanded', String(isOpen));
    });
    container.appendChild(block);
  }

  /**
   * buildCandidateChip(candidate, selectedHabitat) — a small chip with sprite + name.
   * Shows a compat tag if the filter is widened beyond Compatible-only.
   */
  function buildCandidateChip(candidate, selectedHabitat) {
    const rel = habitatRelation(selectedHabitat, candidate.habitat);
    const showTag = filterState.size > 1 || !filterState.has('compatible') || rel !== 'compatible';

    const chip = el('button', {
      class: 'candidate-chip',
      type: 'button',
      'aria-label': candidate.name + ' (' + candidate.habitat + ', ' + rel + ')',
    });
    chip.appendChild(buildSpriteElement(candidate, 'sprite-small'));

    const nameSpan = el('span');
    nameSpan.textContent = candidate.name;
    chip.appendChild(nameSpan);

    if (showTag) {
      const tag = el('span', { class: 'compat-tag compat-' + rel, 'aria-label': rel });
      tag.textContent = rel.charAt(0).toUpperCase() + rel.slice(1, 4); // "Com" / "Neu" / "Inc"
      chip.appendChild(tag);
    }

    chip.addEventListener('click', function () { openDetail(candidate); });
    return chip;
  }

  /* ── 9. Item modal ──────────────────────────────────────── */

  function openItemModal(category) {
    const modal = document.getElementById('item-modal');
    const title = document.getElementById('modal-title');
    const itemList = document.getElementById('modal-item-list');

    title.textContent = category;
    itemList.innerHTML = '';

    const items = (window.POKOPIA_DATA.items && window.POKOPIA_DATA.items[category]) || [];
    if (items.length === 0) {
      const li = el('li');
      li.textContent = 'No items recorded for this category.';
      itemList.appendChild(li);
    } else {
      items.forEach(function (item) {
        const li = el('li');
        li.textContent = item;
        itemList.appendChild(li);
      });
    }

    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');

    // Trap focus: focus the close button
    document.getElementById('modal-close').focus();
  }

  function closeItemModal() {
    const modal = document.getElementById('item-modal');
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
  }

  /* ── 10. Global habitat filter ──────────────────────────── */

  function initFilter() {
    const group = document.getElementById('habitat-filter');
    group.querySelectorAll('.filter-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const key = btn.getAttribute('data-filter');
        if (filterState.has(key)) {
          // Don't allow deselecting if it's the only active filter
          if (filterState.size === 1) return;
          filterState.delete(key);
          btn.classList.remove('active');
          btn.setAttribute('aria-pressed', 'false');
        } else {
          filterState.add(key);
          btn.classList.add('active');
          btn.setAttribute('aria-pressed', 'true');
        }
        // Re-render tiers if a Pokémon is selected
        if (selectedPokemon) renderTiers(selectedPokemon);
      });
    });
  }

  /* ── 11. Event wiring ───────────────────────────────────── */

  function wireEvents() {
    // Back button
    document.getElementById('back-btn').addEventListener('click', openPicker);

    // Search
    document.getElementById('search-input').addEventListener('input', function (e) {
      searchQuery = e.target.value;
      renderPicker();
    });

    // Group-by-habitat toggle
    document.getElementById('group-toggle').addEventListener('click', function () {
      groupByHabitat = !groupByHabitat;
      this.setAttribute('aria-pressed', String(groupByHabitat));
      renderPicker();
    });

    // Modal close
    document.getElementById('modal-close').addEventListener('click', closeItemModal);
    document.getElementById('item-modal').addEventListener('click', function (e) {
      if (e.target === this) closeItemModal();
    });

    // ESC closes modal
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        const modal = document.getElementById('item-modal');
        if (!modal.classList.contains('hidden')) closeItemModal();
      }
    });
  }

  /* ── 12. Init ───────────────────────────────────────────── */

  function init() {
    // Build indexes first (synchronous — data is already in window.POKOPIA_DATA)
    buildIndexes();

    // Wire events
    initFilter();
    wireEvents();

    // Initial render
    renderPicker();

    // Hide loading overlay, reveal app
    const overlay = document.getElementById('loading-overlay');
    const app = document.getElementById('app');

    // Brief timeout to ensure spinner is actually visible before hiding it
    // (satisfies the spec requirement for a real spinner that shows then hides)
    setTimeout(function () {
      overlay.classList.add('hidden');
      app.classList.remove('hidden');
    }, 350);
  }

  // Bootstrap after DOM + data.js are loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
