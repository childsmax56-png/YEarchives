import re, json, csv
from datetime import datetime

HTML_PATH = '/home/user/YEarchives/index.html'
CSV_PATH  = '/home/user/YEarchives/Copy of Suzy Tracker WE LOVE MILO - Recent (3).csv'

with open(HTML_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ── parse RECENT ──────────────────────────────────────────────────────────────
rec_m = re.search(r'(const RECENT\s*=\s*)(\{.*?\})(\s*;\s*\n\s*const RAW)', content, re.DOTALL)
rec   = json.loads(rec_m.group(2))
rec_eras   = rec['eras']
rec_tracks = rec['tracks']

# ── parse RAW ─────────────────────────────────────────────────────────────────
raw_m = re.search(r'(const RAW\s*=\s*)(\{.*?\})(\s*;\s*(?:\n|$))', content, re.DOTALL)
raw   = json.loads(raw_m.group(2))
raw_eras   = raw['eras']
raw_tracks = raw['tracks']

print(f"RECENT: {len(rec_eras)} eras, {len(rec_tracks)} tracks")
print(f"RAW:    {len(raw_eras)} eras, {len(raw_tracks)} tracks")

# ── dedup helper ──────────────────────────────────────────────────────────────
def norm(s):
    s = s.split('\n')[0].lower().strip()
    return re.sub(r'[^\x00-\x7f]', '', s).strip()

rec_existing = {norm(rec_eras[t[0]] + t[1]) for t in rec_tracks}
raw_existing = {norm(raw_eras[t[0]] + t[1]) for t in raw_tracks}

# ── read CSV ──────────────────────────────────────────────────────────────────
def parse_date(s):
    if not s: return None
    s = s.strip()
    for fmt in ['%b %d, %Y', '%B %d, %Y', '%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d']:
        try:
            return datetime.strptime(s, fmt)
        except: pass
    return None

csv_rows = []
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        csv_rows.append(row)

LEAK_KEY  = 'Leak\nDate'
FILE_KEY  = 'File\nDate'

new_csv = []
for row in csv_rows:
    d = parse_date(row.get(LEAK_KEY, ''))
    if d and d.year == 2026 and d.month == 4 and 23 <= d.day <= 28:
        new_csv.append(row)

print(f"\nCSV Apr 23-28 tracks: {len(new_csv)}")

# ── build new RECENT tracks ───────────────────────────────────────────────────
def fmt_date(s):
    d = parse_date(s)
    if not d: return s.strip() if s else ''
    return d.strftime('%m/%d/%Y')

added_rec = 0
added_raw = 0

for row in new_csv:
    era  = row.get('Era', '').strip()
    name = row.get('Name', '').strip()
    notes = row.get('Notes', '').strip()
    tlen  = row.get('Track Length', '').strip()
    fdate = fmt_date(row.get(FILE_KEY, ''))
    ldate = fmt_date(row.get(LEAK_KEY, ''))
    avail = row.get('Available Length', '').strip()
    qual  = row.get('Quality', '').strip()
    links = row.get('Link(s)', '').strip()

    key = norm(era + name)

    # --- RECENT ---
    if era not in rec_eras:
        rec_eras.append(era)
        print(f"  Added era to RECENT: {era}")
    era_idx = rec_eras.index(era)

    if key not in rec_existing:
        rec_tracks.append([era_idx, name, notes, tlen, fdate, ldate, avail, qual, links])
        rec_existing.add(key)
        added_rec += 1

    # --- RAW ---
    if era not in raw_eras:
        raw_eras.append(era)
        print(f"  Added era to RAW: {era}")
    raw_era_idx = raw_eras.index(era)

    if key not in raw_existing:
        # RAW format: [eraIdx, name, len, leakDate, availLen, quality, links, notes]
        raw_tracks.append([raw_era_idx, name, tlen, ldate, avail, qual, links, notes])
        raw_existing.add(key)
        added_raw += 1

print(f"\nAdded to RECENT: {added_rec}")
print(f"Added to RAW:    {added_raw}")

# ── serialise and splice back ─────────────────────────────────────────────────
rec['eras']   = rec_eras
rec['tracks'] = rec_tracks
raw['eras']   = raw_eras
raw['tracks'] = raw_tracks

new_rec_json = json.dumps(rec, ensure_ascii=False, separators=(',', ':'))
new_raw_json = json.dumps(raw, ensure_ascii=False, separators=(',', ':'))

content = (content[:rec_m.start(1)]
           + rec_m.group(1)
           + new_rec_json
           + rec_m.group(3)
           + content[rec_m.end(3):])

# re-find RAW after RECENT replacement
raw_m2 = re.search(r'(const RAW\s*=\s*)(\{.*?\})(\s*;\s*(?:\n|$))', content, re.DOTALL)
content = (content[:raw_m2.start(1)]
           + raw_m2.group(1)
           + new_raw_json
           + raw_m2.group(3)
           + content[raw_m2.end(3):])

with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("\nindex.html updated successfully.")
