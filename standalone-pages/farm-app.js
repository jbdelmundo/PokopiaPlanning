/* =========================================================
   Pokopia "Automation Farm Planner" — farm-app.js
   Vanilla JS, no frameworks, works from file://
   Reuses the patterns of app.js (el helper, sprites, habitat
   relations, shared-favorite scoring) for a material-centric
   farm builder: Litter → Process → Gather.
   ========================================================= */

(function () {
  'use strict';

  /* ── 1. Constants & state ───────────────────────────────── */

  const HABITATS = ['Bright', 'Cool', 'Dark', 'Dry', 'Humid', 'Warm'];
  const OPPOSITE = { Bright: 'Dark', Dark: 'Bright', Cool: 'Warm', Warm: 'Cool', Dry: 'Humid', Humid: 'Dry' };
  const REL_ORDER = { compatible: 0, neutral: 1, incompatible: 2 };
  const HIGH_VALUE = new Set(['Iron Ore', 'Iron Ingot']);
  const ROSTER_KEY = 'pokopia_roster';
  const MAX_CANDIDATES = 10; // cap per role list before "+N more"

  let pkByName = {};        // name → pokemon record
  let modules = [];         // material-centric farm modules (built once)
  let rosterSet = new Set();
  let mode = 'all';         // 'all' | 'buildable'
  let searchQuery = '';
  let selectedModule = null;
  let rosterSearch = '';

  /* ── 2. Engine helpers (shared with app.js patterns) ────── */

  function habitatRelation(a, b) {
    if (a === b) return 'compatible';
    if (OPPOSITE[a] === b) return 'incompatible';
    return 'neutral';
  }

  function allFavorites(pk) {
    const cats = (pk && pk.favorites && pk.favorites.categories) || [];
    const flavs = (pk && pk.favorites && pk.favorites.flavors) || [];
    return new Set([...cats, ...flavs]);
  }

  function sharedFavorites(a, b) {
    if (!a || !b) return [];
    const aSet = allFavorites(a);
    const bSet = allFavorites(b);
    const shared = [];
    aSet.forEach(function (f) { if (bSet.has(f)) shared.push(f); });
    return shared;
  }

  function hasSpecialty(pk, spec) {
    return pk && pk.specialties && pk.specialties.indexOf(spec) !== -1;
  }

  /* ── 3. DOM + sprite helpers ────────────────────────────── */

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

  function spriteSlug(name) {
    const overrides = {
      'Tatsugiri Curly Form': 'tatsugiri-curly',
      'Peakychu': 'pikachu',
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
    s = s.normalize('NFD').replace(/[̀-ͯ]/g, '');
    s = s.replace('♀', '-f').replace('♂', '-m');
    s = s.replace(/['’`]/g, '');
    s = s.replace(/\s+form[e]?$/, '');
    s = s.replace(/\s+/g, '-');
    s = s.replace(/[^a-z0-9-]/g, '');
    s = s.replace(/-+/g, '-').replace(/^-|-$/g, '');
    return s;
  }

  function spriteUrl(name) {
    return 'https://img.pokemondb.net/sprites/home/normal/' + spriteSlug(name) + '.png';
  }

  function buildSpriteElement(pk, sizeClass) {
    sizeClass = sizeClass || 'sprite-small';
    const container = el('div', { class: 'sprite-container ' + sizeClass });
    const shimmer = el('div', { class: 'sprite-shimmer' });
    container.appendChild(shimmer);
    const img = el('img', { src: spriteUrl(pk.name), alt: pk.name, loading: 'lazy', class: 'sprite-img loading' });
    img.addEventListener('load', function () {
      img.classList.remove('loading'); img.classList.add('loaded'); shimmer.remove();
    });
    img.addEventListener('error', function () {
      shimmer.remove(); img.remove();
      const fb = el('div', { class: 'sprite-fallback sprite-' + pk.habitat, 'aria-hidden': 'true' });
      fb.textContent = pk.name.charAt(0).toUpperCase();
      container.appendChild(fb);
    });
    container.appendChild(img);
    return container;
  }

  function habitatBadge(habitat) {
    const b = el('span', { class: 'habitat-badge badge-' + habitat });
    b.textContent = habitat;
    return b;
  }

  function compatTag(rel) {
    const tag = el('span', { class: 'compat-tag compat-' + rel, 'aria-label': rel });
    tag.textContent = rel.charAt(0).toUpperCase() + rel.slice(1, 4);
    return tag;
  }

  /* ── 4. Roster (localStorage) ───────────────────────────── */

  function loadRoster() {
    try {
      const raw = localStorage.getItem(ROSTER_KEY);
      if (raw) JSON.parse(raw).forEach(function (n) { rosterSet.add(n); });
    } catch (e) { /* ignore corrupt/blocked storage */ }
  }

  function saveRoster() {
    try { localStorage.setItem(ROSTER_KEY, JSON.stringify([...rosterSet])); }
    catch (e) { /* storage may be unavailable (private mode) */ }
  }

  function inRoster(name) { return rosterSet.has(name); }

  function toggleRoster(name) {
    if (rosterSet.has(name)) rosterSet.delete(name);
    else rosterSet.add(name);
    saveRoster();
    updateRosterCount();
  }

  function updateRosterCount() {
    const badge = document.getElementById('roster-count');
    if (badge) badge.textContent = rosterSet.size;
  }

  /* ── 5. Build farm modules (one per dropped material) ───── */

  function ruleForMaterial(material) {
    const rules = (window.POKOPIA_DATA.farm && window.POKOPIA_DATA.farm.processing) || [];
    return rules.find(function (r) { return r.input === material; }) || null;
  }

  function buildModules() {
    const data = window.POKOPIA_DATA;
    data.pokemon.forEach(function (pk) { pkByName[pk.name] = pk; });

    const litterEntries = (data.farm && data.farm.litter) || [];

    // Pre-compute role candidate pools from the full roster.
    const gatherPool = data.pokemon.filter(function (pk) { return hasSpecialty(pk, 'Gather'); });

    // Group litter entries by material.
    const byMaterial = {};
    litterEntries.forEach(function (entry) {
      if (!byMaterial[entry.material]) byMaterial[entry.material] = [];
      byMaterial[entry.material].push(entry);
    });

    modules = Object.keys(byMaterial).map(function (material) {
      const rule = ruleForMaterial(material);
      const output = rule ? rule.output : material;

      const litters = byMaterial[material].map(function (entry) {
        const pk = pkByName[entry.pokemon] || { name: entry.pokemon, habitat: entry.habitat, specialties: [], favorites: {} };
        const selfChain = !!(rule && entry.secondSpecialty && entry.secondSpecialty === rule.specialty);
        return { entry: entry, pk: pk, selfChain: selfChain };
      });

      const litterPks = litters.map(function (l) { return l.pk; });
      const selfChainAvailable = litters.some(function (l) { return l.selfChain; });

      // Dominant litter habitat (most common) — used for compat tags on candidates.
      const habCount = {};
      litters.forEach(function (l) { habCount[l.pk.habitat] = (habCount[l.pk.habitat] || 0) + 1; });
      let dominantHabitat = litters[0].pk.habitat;
      let best = 0;
      Object.keys(habCount).forEach(function (h) { if (habCount[h] > best) { best = habCount[h]; dominantHabitat = h; } });

      const processorPool = rule
        ? data.pokemon.filter(function (pk) { return hasSpecialty(pk, rule.specialty); })
        : [];

      const gatherCandidates = rankCandidates(gatherPool, litterPks, dominantHabitat);
      const processorCandidates = rankCandidates(processorPool, litterPks, dominantHabitat);

      const producesHighValue = HIGH_VALUE.has(material) || HIGH_VALUE.has(output);
      const minPokemon = (!rule || selfChainAvailable) ? 2 : 3;

      // Best comfy overlap achievable in this cluster (litter ↔ gatherer/processor).
      let bestOverlap = 0;
      gatherCandidates.concat(processorCandidates).forEach(function (c) {
        if (c.overlap.length > bestOverlap) bestOverlap = c.overlap.length;
      });

      let score = 0;
      if (producesHighValue) score += 100;
      if (selfChainAvailable) score += 40;
      score += bestOverlap * 5;
      score += litters.length;          // capacity (scaling potential)
      score += (3 - minPokemon) * 10;   // fewest Pokémon

      return {
        material: material,
        rule: rule,
        output: output,
        litters: litters,
        litterPks: litterPks,
        selfChainAvailable: selfChainAvailable,
        dominantHabitat: dominantHabitat,
        processorCandidates: processorCandidates,
        gatherCandidates: gatherCandidates,
        producesHighValue: producesHighValue,
        minPokemon: minPokemon,
        capacity: litters.length,
        bestOverlap: bestOverlap,
        score: score,
      };
    });

    modules.sort(function (a, b) {
      if (b.score !== a.score) return b.score - a.score;
      return a.material.localeCompare(b.material);
    });
  }

  /**
   * rankCandidates — returns [{ pk, overlap:[fav...], rel }] sorted by comfy
   * overlap (desc), then habitat relation to the litter cluster, then name.
   */
  function rankCandidates(pool, litterPks, dominantHabitat) {
    const litterNames = new Set(litterPks.map(function (p) { return p.name; }));
    return pool
      .filter(function (pk) { return !litterNames.has(pk.name); }) // a litter can't gather its own drop here
      .map(function (pk) {
        const set = new Set();
        litterPks.forEach(function (lp) { sharedFavorites(lp, pk).forEach(function (f) { set.add(f); }); });
        return { pk: pk, overlap: [...set], rel: habitatRelation(dominantHabitat, pk.habitat) };
      })
      .sort(function (a, b) {
        if (b.overlap.length !== a.overlap.length) return b.overlap.length - a.overlap.length;
        if (REL_ORDER[a.rel] !== REL_ORDER[b.rel]) return REL_ORDER[a.rel] - REL_ORDER[b.rel];
        return a.pk.name.localeCompare(b.pk.name);
      });
  }

  /* ── 6. Buildability vs roster ──────────────────────────── */

  function litterInRoster(module) { return module.litters.some(function (l) { return inRoster(l.pk.name); }); }
  function gatherInRoster(module) { return module.gatherCandidates.some(function (c) { return inRoster(c.pk.name); }); }
  function processorInRoster(module) { return module.processorCandidates.some(function (c) { return inRoster(c.pk.name); }); }

  // A valid setup = a Litter + a Gather in the roster (processor is a bonus).
  function isBuildable(module) { return litterInRoster(module) && gatherInRoster(module); }

  /* ── 7. Screen A — Farm picker ──────────────────────────── */

  function moduleMatchesSearch(module) {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    if (module.material.toLowerCase().includes(q)) return true;
    if (module.output.toLowerCase().includes(q)) return true;
    return module.litters.some(function (l) { return l.pk.name.toLowerCase().includes(q); });
  }

  function renderPicker() {
    const list = document.getElementById('farm-list');
    const countEl = document.getElementById('result-count');
    list.innerHTML = '';

    let visible = modules.filter(moduleMatchesSearch);
    if (mode === 'buildable') visible = visible.filter(isBuildable);

    countEl.textContent = visible.length + ' of ' + modules.length + ' material farms' +
      (mode === 'buildable' ? ' buildable now' : '');

    if (visible.length === 0) {
      const empty = el('p', { class: 'favorites-notice farm-empty' });
      empty.textContent = mode === 'buildable'
        ? 'No farms are fully buildable from your current roster yet. Add Pokémon via “Edit roster”, or switch to “All Pokémon”.'
        : 'No material farms match “' + searchQuery + '”.';
      list.appendChild(empty);
      return;
    }

    visible.forEach(function (module) { list.appendChild(buildFarmCard(module)); });
  }

  function buildFarmCard(module) {
    const card = el('button', { class: 'farm-card', type: 'button',
      'aria-label': module.material + ' farm' });

    // Sprites of up to 3 litter Pokémon
    const sprites = el('div', { class: 'farm-card-sprites' });
    module.litters.slice(0, 3).forEach(function (l) { sprites.appendChild(buildSpriteElement(l.pk, 'sprite-small')); });
    card.appendChild(sprites);

    const body = el('div', { class: 'farm-card-body' });

    // Title: material → output
    const title = el('div', { class: 'farm-card-title' });
    title.appendChild(el('span', { class: 'farm-material' }, module.material));
    if (module.rule) {
      title.appendChild(el('span', { class: 'farm-arrow', 'aria-hidden': 'true' }, ' → '));
      title.appendChild(el('span', { class: 'farm-output' }, module.output));
    }
    body.appendChild(title);

    // Badges
    const badges = el('div', { class: 'farm-badge-row' });
    if (module.producesHighValue) badges.appendChild(farmBadge('⭐ High-value', 'badge-highvalue'));
    if (module.selfChainAvailable) badges.appendChild(farmBadge('♻ Self-chaining', 'badge-selfchain'));
    badges.appendChild(farmBadge('Capacity ×' + module.capacity, 'badge-capacity'));
    badges.appendChild(farmBadge(module.minPokemon + ' Pokémon', 'badge-count'));
    body.appendChild(badges);

    // Role summary line
    const roleParts = ['Litter ×' + module.capacity];
    if (module.rule) roleParts.push(module.selfChainAvailable ? 'Process (self or ' + module.rule.specialty + ')' : 'Process (' + module.rule.specialty + ')');
    roleParts.push('Gather');
    const roleLine = el('div', { class: 'farm-card-roles' });
    roleLine.textContent = roleParts.join('  ·  ');
    body.appendChild(roleLine);

    // Roster status
    const status = el('div', { class: 'farm-card-status' });
    if (isBuildable(module)) {
      status.appendChild(farmBadge('✓ Buildable now', 'badge-buildable'));
      if (module.rule && !module.selfChainAvailable && !processorInRoster(module)) {
        status.appendChild(farmBadge('refine: need ' + module.rule.specialty, 'badge-need'));
      }
    } else {
      const missing = [];
      if (!litterInRoster(module)) missing.push('a Litter');
      if (!gatherInRoster(module)) missing.push('a Gatherer');
      status.appendChild(farmBadge('Need ' + missing.join(' + ') + ' in town', 'badge-need'));
    }
    body.appendChild(status);

    card.appendChild(body);
    card.appendChild(el('span', { class: 'farm-card-arrow', 'aria-hidden': 'true' }, '›'));
    card.addEventListener('click', function () { openDetail(module); });
    return card;
  }

  function farmBadge(text, cls) {
    const b = el('span', { class: 'farm-badge ' + cls });
    b.textContent = text;
    return b;
  }

  /* ── 8. Screen B — Farm detail ──────────────────────────── */

  function openDetail(module) {
    selectedModule = module;
    document.getElementById('screen-picker').classList.add('hidden');
    document.getElementById('screen-detail').classList.remove('hidden');
    renderDetail(module);
    window.scrollTo(0, 0);
  }

  function openPicker() {
    selectedModule = null;
    document.getElementById('screen-detail').classList.add('hidden');
    document.getElementById('screen-picker').classList.remove('hidden');
    renderPicker();
    window.scrollTo(0, 0);
  }

  function renderDetail(module) {
    document.getElementById('header-material').textContent =
      module.rule ? module.material + ' → ' + module.output : module.material + ' farm';

    const badges = document.getElementById('header-badges');
    badges.innerHTML = '';
    if (module.producesHighValue) badges.appendChild(farmBadge('⭐ High-value', 'badge-highvalue'));
    if (module.selfChainAvailable) badges.appendChild(farmBadge('♻ Self-chaining', 'badge-selfchain'));
    badges.appendChild(farmBadge('Capacity ×' + module.capacity, 'badge-capacity'));
    badges.appendChild(farmBadge('Min ' + module.minPokemon + ' Pokémon', 'badge-count'));

    const container = document.getElementById('chain-container');
    container.innerHTML = '';

    let step = 1;

    // ── Step 1: Litter
    const litterSection = roleSection(
      step++ + ' · Litter',
      'Drops ' + module.material + ' near home. Stack several to scale production — each lives in its own Prefab habitat, so they can cluster around one collector.'
    );
    module.litters.forEach(function (l) {
      const extras = [];
      if (l.selfChain && module.rule) {
        extras.push(el('span', { class: 'role-note role-note-selfchain' },
          'Self-chains: ' + module.rule.specialty + ' → ' + module.output));
      }
      litterSection.body.appendChild(buildRoleRow(l.pk, module, [], extras));
    });
    container.appendChild(litterSection.section);

    // ── Step 2: Process (only if a rule exists)
    if (module.rule) {
      const proc = roleSection(
        step++ + ' · Process',
        module.rule.specialty + ' turns ' + module.material + ' into ' + module.output + '.'
      );
      if (module.selfChainAvailable) {
        const selfNames = module.litters.filter(function (l) { return l.selfChain; })
          .map(function (l) { return l.pk.name; });
        const note = el('p', { class: 'role-section-hint role-section-hint-good' });
        note.textContent = 'No extra Pokémon needed if you use ' + selfNames.join(' / ') +
          ' — they process their own drop. Otherwise add a dedicated ' + module.rule.specialty + ' Pokémon:';
        proc.body.appendChild(note);
      } else {
        const note = el('p', { class: 'role-section-hint' });
        note.textContent = 'Add a ' + module.rule.specialty + ' Pokémon nearby:';
        proc.body.appendChild(note);
      }
      appendCandidateList(proc.body, module.processorCandidates, module);
      container.appendChild(proc.section);
    }

    // ── Step 3 (or 2): Gather
    const gather = roleSection(
      step++ + ' · Gather',
      'Sweeps the drops into the Community Box. One Gatherer can serve several Litter farms.'
    );
    appendCandidateList(gather.body, module.gatherCandidates, module);
    container.appendChild(gather.section);

    renderNotes(module);
  }

  function roleSection(title, subtitle) {
    const section = el('section', { class: 'card role-section', 'aria-label': title });
    section.appendChild(el('h2', { class: 'role-section-title' }, title));
    if (subtitle) section.appendChild(el('p', { class: 'role-section-sub' }, subtitle));
    const body = el('div', { class: 'role-section-body' });
    section.appendChild(body);
    return { section: section, body: body };
  }

  function appendCandidateList(body, candidates, module) {
    let list = candidates;
    if (mode === 'buildable') list = list.filter(function (c) { return inRoster(c.pk.name); });

    if (list.length === 0) {
      const empty = el('p', { class: 'role-section-hint role-empty' });
      empty.textContent = mode === 'buildable'
        ? 'None in your roster yet — switch to “All Pokémon” to see options.'
        : 'No Pokémon available for this role.';
      body.appendChild(empty);
      return;
    }

    const shown = list.slice(0, MAX_CANDIDATES);
    shown.forEach(function (c) { body.appendChild(buildRoleRow(c.pk, module, c.overlap, [], c.rel)); });

    if (list.length > shown.length) {
      const more = el('p', { class: 'role-more' });
      more.textContent = '+' + (list.length - shown.length) + ' more with this specialty';
      body.appendChild(more);
    }
  }

  /**
   * buildRoleRow — a Pokémon row inside a role section.
   *   pk       : pokemon record
   *   module   : the active module (for habitat relation context)
   *   overlap  : array of shared-favorite names to show as chips
   *   extras   : extra inline nodes (e.g. self-chain note)
   *   rel      : optional precomputed habitat relation tag to show
   */
  function buildRoleRow(pk, module, overlap, extras, rel) {
    const row = el('div', { class: 'role-row' });

    row.appendChild(buildSpriteElement(pk, 'sprite-small'));

    const info = el('div', { class: 'role-row-info' });
    const topLine = el('div', { class: 'role-row-top' });
    topLine.appendChild(el('span', { class: 'role-row-name' }, pk.name));
    topLine.appendChild(habitatBadge(pk.habitat));
    if (rel) topLine.appendChild(compatTag(rel));
    info.appendChild(topLine);

    (extras || []).forEach(function (node) { info.appendChild(node); });

    if (overlap && overlap.length) {
      const chips = el('div', { class: 'role-overlap' });
      const label = el('span', { class: 'role-overlap-label' }, 'Shares: ');
      chips.appendChild(label);
      overlap.slice(0, 4).forEach(function (fav) {
        chips.appendChild(el('span', { class: 'overlap-chip' }, fav));
      });
      if (overlap.length > 4) chips.appendChild(el('span', { class: 'overlap-more' }, '+' + (overlap.length - 4)));
      info.appendChild(chips);
    }
    row.appendChild(info);

    // In-town checkbox
    const label = el('label', { class: 'roster-check' });
    const cb = el('input', { type: 'checkbox', 'aria-label': pk.name + ' is in my town' });
    cb.checked = inRoster(pk.name);
    cb.addEventListener('change', function () {
      toggleRoster(pk.name);
      // Re-render detail so buildable tags/filters stay in sync.
      renderDetail(module);
    });
    label.appendChild(cb);
    label.appendChild(el('span', { class: 'roster-check-text' }, 'In town'));
    row.appendChild(label);

    return row;
  }

  function renderNotes(module) {
    const notes = document.getElementById('farm-notes');
    notes.innerHTML = '';
    notes.appendChild(el('h2', { class: 'role-section-title' }, 'Planning notes'));

    const comfy = el('p', { class: 'farm-note-line' });
    comfy.textContent = 'Habitat between a Litter Pokémon and its gatherer/processor is a soft, comfy concern — ' +
      'the Litter lives in its own Prefab, so an “Incompatible” tag just means they can’t share a single house, ' +
      'not that the farm fails. Shared favorites raise Comfy Level, which lifts the area’s Environment Level.';
    notes.appendChild(comfy);

    // Shared infrastructure
    const shared = el('p', { class: 'farm-note-line' });
    if (module.rule) {
      const sameSpec = modules.filter(function (m) {
        return m !== module && m.rule && m.rule.specialty === module.rule.specialty;
      }).map(function (m) { return m.material; });
      shared.textContent = 'Shared infrastructure: one Gatherer can collect for any farm. ' +
        'A ' + module.rule.specialty + ' processor also serves ' +
        (sameSpec.length ? sameSpec.join(', ') + '.' : 'no other listed material.');
    } else {
      shared.textContent = 'Shared infrastructure: one Gatherer can collect for any farm, so this raw-material ' +
        'farm can share a collector with neighbouring farms.';
    }
    notes.appendChild(shared);
  }

  /* ── 9. Roster editor modal ─────────────────────────────── */

  function openRosterModal() {
    const modal = document.getElementById('roster-modal');
    rosterSearch = '';
    document.getElementById('roster-search').value = '';
    renderRosterList();
    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');
    document.getElementById('roster-modal-close').focus();
  }

  function closeRosterModal() {
    const modal = document.getElementById('roster-modal');
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
    // Reflect roster changes on whichever screen is showing.
    if (selectedModule) renderDetail(selectedModule);
    else renderPicker();
  }

  function renderRosterList() {
    const listEl = document.getElementById('roster-list');
    const countEl = document.getElementById('roster-modal-count');
    listEl.innerHTML = '';

    const all = window.POKOPIA_DATA.pokemon;
    const filtered = all.filter(function (pk) {
      return !rosterSearch || pk.name.toLowerCase().includes(rosterSearch.toLowerCase());
    });
    countEl.textContent = rosterSet.size + ' in town · ' + filtered.length + ' shown';

    filtered.forEach(function (pk) {
      const row = el('label', { class: 'roster-row', role: 'listitem' });
      const cb = el('input', { type: 'checkbox', 'aria-label': pk.name });
      cb.checked = inRoster(pk.name);
      cb.addEventListener('change', function () {
        toggleRoster(pk.name);
        document.getElementById('roster-modal-count').textContent =
          rosterSet.size + ' in town · ' + filtered.length + ' shown';
      });
      row.appendChild(cb);
      row.appendChild(buildSpriteElement(pk, 'sprite-small'));
      const name = el('span', { class: 'roster-row-name' }, pk.name);
      row.appendChild(name);
      row.appendChild(habitatBadge(pk.habitat));
      listEl.appendChild(row);
    });
  }

  /* ── 10. Event wiring & init ────────────────────────────── */

  function wireEvents() {
    document.getElementById('back-btn').addEventListener('click', openPicker);

    document.getElementById('search-input').addEventListener('input', function (e) {
      searchQuery = e.target.value;
      renderPicker();
    });

    document.getElementById('mode-toggle').querySelectorAll('.mode-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        mode = btn.getAttribute('data-mode');
        document.getElementById('mode-toggle').querySelectorAll('.mode-btn').forEach(function (b) {
          const active = b === btn;
          b.classList.toggle('active', active);
          b.setAttribute('aria-pressed', String(active));
        });
        if (selectedModule) renderDetail(selectedModule);
        else renderPicker();
      });
    });

    document.getElementById('roster-btn').addEventListener('click', openRosterModal);
    document.getElementById('roster-modal-close').addEventListener('click', closeRosterModal);
    document.getElementById('roster-modal').addEventListener('click', function (e) {
      if (e.target === this) closeRosterModal();
    });
    document.getElementById('roster-search').addEventListener('input', function (e) {
      rosterSearch = e.target.value;
      renderRosterList();
    });
    document.getElementById('roster-clear').addEventListener('click', function () {
      rosterSet.clear();
      saveRoster();
      updateRosterCount();
      renderRosterList();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        const modal = document.getElementById('roster-modal');
        if (!modal.classList.contains('hidden')) closeRosterModal();
      }
    });
  }

  function init() {
    if (!window.POKOPIA_DATA || !window.POKOPIA_DATA.farm) {
      document.getElementById('loading-overlay').innerHTML =
        '<p class="loading-text">Farm data missing — rebuild data.js with build_data.py.</p>';
      return;
    }
    loadRoster();
    buildModules();
    updateRosterCount();
    wireEvents();
    renderPicker();

    const overlay = document.getElementById('loading-overlay');
    const app = document.getElementById('app');
    setTimeout(function () {
      overlay.classList.add('hidden');
      app.classList.remove('hidden');
    }, 350);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
