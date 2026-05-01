#!/usr/bin/env python3
"""
Injects the Eras tab into index.html:
- Parses YZY Archives homepage - Eras.csv
- Embeds ERAS_DATA constant
- Adds tab button, panel, CSS, and JS
"""

import csv, json, re

HTML  = '/home/user/YEarchives/index.html'
CSV   = '/home/user/YEarchives/YZY Archives homepage - Eras.csv'

# ── Parse CSV ─────────────────────────────────────────────────────────────────

rows = []
with open(CSV, newline='', encoding='utf-8') as f:
    all_rows = list(csv.reader(f))

headers = all_rows[1]
eras_data = []
for row in all_rows[2:]:
    if len(row) < 5:
        continue
    d = dict(zip(headers, row))
    name = d.get('Era Name', '').split('\n')[0].strip().strip('"')
    if not name:
        continue
    eras_data.append({
        'name':  name,
        'desc':  d.get('Era Description', '').strip(),
        'img':   d.get('Image Link', '').strip(),
        'range': d.get('Era Range', '').replace('\n', ' ').strip().strip('"'),
    })

print(f"Parsed {len(eras_data)} eras from CSV")

# ── Load index.html ───────────────────────────────────────────────────────────

with open(HTML, 'r', encoding='utf-8') as f:
    html = f.read()

# ── 1. Embed ERAS_DATA constant (before closing </script> of main block) ──────

eras_json = json.dumps(eras_data, ensure_ascii=False, separators=(',', ':'))
eras_const = f'const ERAS_DATA = {eras_json};\n'

# Insert after the RAW constant
raw_end = re.search(r'const RAW\s*=\s*\{.*?\};\s*\n', html, re.DOTALL)
if not raw_end:
    raise RuntimeError("Could not find RAW constant end")

insert_pos = raw_end.end()
# Check if already injected
if 'const ERAS_DATA' not in html:
    html = html[:insert_pos] + eras_const + html[insert_pos:]
    print("Inserted ERAS_DATA constant")
else:
    # Replace existing
    html = re.sub(r'const ERAS_DATA\s*=\s*\[.*?\];\s*\n', eras_const, html, flags=re.DOTALL)
    print("Replaced existing ERAS_DATA constant")

# ── 2. Add Eras tab button ────────────────────────────────────────────────────

OLD_TABS = '    <button class="tab-btn" data-tab="covers">Album Covers</button>\n  </div>'
NEW_TABS = '    <button class="tab-btn" data-tab="covers">Album Covers</button>\n    <button class="tab-btn" data-tab="eras">Eras</button>\n  </div>'

if 'data-tab="eras"' not in html:
    html = html.replace(OLD_TABS, NEW_TABS)
    print("Added Eras tab button")

# ── 3. Add panel HTML (after panel-covers) ────────────────────────────────────

PANEL_COVERS_END = '''  <div id="panel-covers" style="display:none">
    <div id="cov-grid" class="covers-grid"></div>
    <div class="empty" id="cov-empty" style="display:none"><span>🔍</span>No covers match your search.</div>
    <div class="pagination" id="cov-pagination"></div>
  </div>'''

PANEL_ERAS = '''  <div id="panel-covers" style="display:none">
    <div id="cov-grid" class="covers-grid"></div>
    <div class="empty" id="cov-empty" style="display:none"><span>🔍</span>No covers match your search.</div>
    <div class="pagination" id="cov-pagination"></div>
  </div>

  <div id="panel-eras" style="display:none">
    <div id="eras-grid" class="eras-grid"></div>
  </div>

  <!-- ERA MODAL -->
  <div class="modal-overlay" id="era-modal-overlay" style="display:none">
    <div class="modal era-modal" id="era-modal">
      <button class="modal-close" id="era-modal-close">✕</button>
      <div class="era-modal-header">
        <img id="era-modal-img" class="era-modal-cover" src="" alt="" loading="lazy">
        <div class="era-modal-meta">
          <div class="era-modal-name" id="era-modal-name"></div>
          <div class="era-modal-range" id="era-modal-range"></div>
          <div class="era-modal-desc" id="era-modal-desc"></div>
        </div>
      </div>
      <div class="era-modal-tracks-header">
        <span id="era-modal-track-count"></span>
        <input type="text" id="era-modal-search" placeholder="Search tracks…" autocomplete="off">
      </div>
      <div id="era-modal-track-list" class="era-modal-track-list"></div>
    </div>
  </div>'''

if 'panel-eras' not in html:
    html = html.replace(PANEL_COVERS_END, PANEL_ERAS)
    print("Added panel-eras HTML and era modal")

# ── 4. Add CSS ────────────────────────────────────────────────────────────────

ERA_CSS = '''
  /* ── ERAS TAB ── */
  .eras-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1.25rem;
    padding: 1.5rem;
  }
  .era-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    cursor: pointer;
    transition: transform .15s, box-shadow .15s;
    display: flex;
    flex-direction: column;
  }
  .era-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0,0,0,.5);
    border-color: var(--gold);
  }
  .era-card-img-wrap {
    position: relative;
    aspect-ratio: 1 / 1;
    background: #111;
    overflow: hidden;
  }
  .era-card-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    transition: transform .2s;
  }
  .era-card:hover .era-card-img { transform: scale(1.04); }
  .era-card-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,.55);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity .15s;
    font-size: .85rem;
    font-weight: 600;
    letter-spacing: .06em;
    color: #fff;
    text-transform: uppercase;
  }
  .era-card:hover .era-card-overlay { opacity: 1; }
  .era-card-no-img {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3rem;
    color: var(--text-dim);
  }
  .era-card-info {
    padding: .7rem .85rem .85rem;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: .2rem;
  }
  .era-card-name {
    font-size: .88rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.3;
  }
  .era-card-count {
    font-size: .75rem;
    color: var(--gold);
    font-weight: 600;
  }
  /* ERA MODAL */
  .era-modal {
    max-width: 860px;
    width: 95vw;
    max-height: 88vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    padding: 0;
  }
  .era-modal-header {
    display: flex;
    gap: 1.2rem;
    padding: 1.4rem 1.4rem 1rem;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }
  .era-modal-cover {
    width: 120px;
    height: 120px;
    object-fit: cover;
    border-radius: 8px;
    flex-shrink: 0;
    background: #111;
  }
  .era-modal-meta { flex: 1; min-width: 0; }
  .era-modal-name {
    font-size: 1.3rem;
    font-weight: 800;
    color: var(--gold);
    margin-bottom: .25rem;
  }
  .era-modal-range {
    font-size: .78rem;
    color: var(--text-mid);
    margin-bottom: .5rem;
  }
  .era-modal-desc {
    font-size: .8rem;
    color: var(--text-dim);
    line-height: 1.5;
    max-height: 5rem;
    overflow-y: auto;
  }
  .era-modal-tracks-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: .75rem 1.4rem;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
    gap: 1rem;
  }
  #era-modal-track-count {
    font-size: .8rem;
    color: var(--text-mid);
    white-space: nowrap;
  }
  #era-modal-search {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    padding: .3rem .6rem;
    font-size: .8rem;
    width: 200px;
  }
  .era-modal-track-list {
    overflow-y: auto;
    flex: 1;
    padding: .5rem 0;
  }
  .era-track-row {
    display: grid;
    grid-template-columns: 1fr auto auto auto;
    gap: .5rem;
    align-items: center;
    padding: .45rem 1.4rem;
    border-bottom: 1px solid rgba(255,255,255,.04);
    font-size: .8rem;
  }
  .era-track-row:hover { background: rgba(255,255,255,.03); }
  .era-track-name {
    color: var(--text);
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .era-track-date { color: var(--text-dim); font-size: .75rem; white-space: nowrap; }
  .era-track-len  { color: var(--text-dim); font-size: .75rem; white-space: nowrap; }
  @media (max-width: 600px) {
    .eras-grid { grid-template-columns: repeat(auto-fill, minmax(140px,1fr)); gap: .75rem; padding: .75rem; }
    .era-modal-header { flex-direction: column; }
    .era-modal-cover { width: 80px; height: 80px; }
    .era-track-row { grid-template-columns: 1fr auto; }
    .era-track-date, .era-track-len { display: none; }
  }'''

# Insert before closing </style>
if '.eras-grid' not in html:
    html = html.replace('</style>', ERA_CSS + '\n</style>', 1)
    print("Added Eras CSS")

# ── 5. Add JS (before closing </script>) ─────────────────────────────────────

ERA_JS = r"""
// ── ERAS TAB ─────────────────────────────────────────────────────────────────
(function() {
  const RAW_ERAS   = RAW.eras;
  const RAW_TRACKS = RAW.tracks;  // [eraIdx, name, len, leakDate, availLen, quality, links, notes]

  // Availability pill colours reuse
  const AVAIL_CLASS = {
    'Full':'pill-full','Partial':'pill-partial','Snippet':'pill-snippet',
    'Beat Only':'pill-beat','Confirmed':'pill-na',
  };

  function countForEra(eraName) {
    const idx = RAW_ERAS.indexOf(eraName);
    if (idx === -1) return 0;
    return RAW_TRACKS.filter(t => t[0] === idx).length;
  }

  function tracksForEra(eraName) {
    const idx = RAW_ERAS.indexOf(eraName);
    if (idx === -1) return [];
    return RAW_TRACKS.filter(t => t[0] === idx);
  }

  // Render era cards grid
  function renderErasGrid() {
    const grid = document.getElementById('eras-grid');
    grid.innerHTML = ERAS_DATA.map((era, i) => {
      const count = countForEra(era.name);
      const imgHtml = era.img
        ? `<img class="era-card-img" src="${era.img.replace(/"/g,'')}" alt="${era.name.replace(/"/g,'&quot;')}" loading="lazy">`
        : `<div class="era-card-no-img">🎵</div>`;
      return `<div class="era-card" data-era-i="${i}">
        <div class="era-card-img-wrap">
          ${imgHtml}
          <div class="era-card-overlay">View Songs</div>
        </div>
        <div class="era-card-info">
          <div class="era-card-name">${era.name.replace(/</g,'&lt;')}</div>
          <div class="era-card-count">${count > 0 ? count + ' unreleased track' + (count !== 1 ? 's' : '') : 'No tracks'}</div>
        </div>
      </div>`;
    }).join('');

    grid.querySelectorAll('.era-card').forEach(card => {
      card.addEventListener('click', () => openEraModal(+card.dataset.eraI));
    });
  }

  // Open modal for era index i
  function openEraModal(i) {
    const era = ERAS_DATA[i];
    document.getElementById('era-modal-img').src    = era.img ? era.img.replace(/"/g,'') : '';
    document.getElementById('era-modal-img').style.display = era.img ? '' : 'none';
    document.getElementById('era-modal-name').textContent  = era.name;
    document.getElementById('era-modal-range').textContent = era.range;
    document.getElementById('era-modal-desc').textContent  = era.desc;
    document.getElementById('era-modal-search').value = '';

    renderEraTrackList(era.name, '');
    document.getElementById('era-modal-overlay').style.display = '';
    document.body.style.overflow = 'hidden';
  }

  function renderEraTrackList(eraName, filter) {
    let tracks = tracksForEra(eraName);
    const fl = filter.toLowerCase();
    if (fl) tracks = tracks.filter(t => t[1].toLowerCase().includes(fl));

    document.getElementById('era-modal-track-count').textContent =
      tracks.length + ' track' + (tracks.length !== 1 ? 's' : '');

    const list = document.getElementById('era-modal-track-list');
    if (tracks.length === 0) {
      list.innerHTML = '<div style="padding:2rem;text-align:center;color:var(--text-dim)">No tracks found.</div>';
      return;
    }
    list.innerHTML = tracks.map(t => {
      const name    = (t[1]||'').split('\n')[0];
      const len     = t[2] || '';
      const ldate   = t[3] || '';
      const avail   = t[4] || '';
      const qual    = t[5] || '';
      const cls     = AVAIL_CLASS[avail] || '';
      const qualBadge = qual ? `<span class="badge" style="font-size:.7rem;padding:.1rem .35rem">${qual}</span>` : '';
      const availBadge = avail ? `<span class="pill ${cls}" style="font-size:.7rem;padding:.1rem .35rem;cursor:default">${avail}</span>` : '';
      return `<div class="era-track-row">
        <div class="era-track-name" title="${name.replace(/"/g,'&quot;')}">${name.replace(/</g,'&lt;')}</div>
        <div>${availBadge}</div>
        <div class="era-track-len">${len}</div>
        <div class="era-track-date">${ldate}</div>
      </div>`;
    }).join('');
  }

  function closeEraModal() {
    document.getElementById('era-modal-overlay').style.display = 'none';
    document.body.style.overflow = '';
  }

  document.getElementById('era-modal-close').addEventListener('click', closeEraModal);
  document.getElementById('era-modal-overlay').addEventListener('click', e => {
    if (e.target === document.getElementById('era-modal-overlay')) closeEraModal();
  });
  document.getElementById('era-modal-search').addEventListener('input', e => {
    const eraName = document.getElementById('era-modal-name').textContent;
    renderEraTrackList(eraName, e.target.value);
  });

  // Hook into tab switching
  const origTabClick = null;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    if (btn.dataset.tab === 'eras') {
      btn.addEventListener('click', () => {
        // hide all panels/filters
        ['panel-unreleased','panel-released','panel-recent','panel-album-copies','panel-covers','panel-eras']
          .forEach(id => { const el = document.getElementById(id); if(el) el.style.display = 'none'; });
        ['unreleased-filters','released-filters','recent-filters','ac-filters','covers-filters']
          .forEach(id => { const el = document.getElementById(id); if(el) el.style.display = 'none'; });
        document.getElementById('panel-eras').style.display = '';
        if (!document.getElementById('eras-grid').children.length) renderErasGrid();
      });
    }
  });

  // Keyboard close
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeEraModal();
  });
})();
"""

# Insert before </script> at end
if 'ERAS TAB' not in html:
    # Find the last </script>
    last_script = html.rfind('</script>')
    html = html[:last_script] + ERA_JS + '\n</script>' + html[last_script+9:]
    print("Added Eras JS")

# ── Write back ────────────────────────────────────────────────────────────────

with open(HTML, 'w', encoding='utf-8') as f:
    f.write(html)

print("\nDone — index.html updated.")
