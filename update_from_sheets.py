#!/usr/bin/env python3
"""
Fetches the latest data from the YE Archive Google Sheet and injects
new tracks into index.html (both RECENT and RAW/Unreleased sections).

Usage:
    python3 update_from_sheets.py

It deduplicates by era+name so running it multiple times is safe.
"""

import re, json, csv, io, sys, subprocess
from datetime import datetime, timezone
from urllib.request import urlopen
from urllib.error import URLError

SPREADSHEET_ID = "12nGHPPh5dVTfLuBLVQYzC3QgPxKfvp-jgCoNccvEasM"
SHEET_GID      = "1385926980"
CSV_URL        = (
    f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    f"/export?format=csv&gid={SHEET_GID}"
)
HTML_PATH = "index.html"

# ── helpers ────────────────────────────────────────────────────────────────────

def parse_date(s):
    if not s:
        return None
    s = s.strip()
    for fmt in ['%b %d, %Y', '%B %d, %Y', '%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d']:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None

def fmt_date(s):
    d = parse_date(s)
    if not d:
        return s.strip() if s else ''
    return d.strftime('%m/%d/%Y')

def norm(s):
    """Normalise era+name for deduplication."""
    s = s.split('\n')[0].lower().strip()
    return re.sub(r'[^\x00-\x7f]', '', s).strip()

# ── fetch CSV from Google Sheets ───────────────────────────────────────────────

print("Fetching sheet from Google Sheets …")
try:
    with urlopen(CSV_URL, timeout=30) as resp:
        raw_csv = resp.read().decode('utf-8')
except URLError as e:
    print(f"ERROR: Could not fetch sheet: {e}")
    sys.exit(1)

rows = list(csv.DictReader(io.StringIO(raw_csv)))
print(f"  {len(rows)} rows fetched")

LEAK_KEY = 'Leak\nDate'
FILE_KEY = 'File\nDate'

# ── find newest tracks already in index.html to determine cutoff ───────────────

with open(HTML_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

rec_m = re.search(r'(const RECENT\s*=\s*)(\{.*?\})(\s*;\s*\n\s*const RAW)', content, re.DOTALL)
raw_m = re.search(r'(const RAW\s*=\s*)(\{.*?\})(\s*;\s*(?:\n|$))', content, re.DOTALL)

rec = json.loads(rec_m.group(2))
raw = json.loads(raw_m.group(2))

rec_eras   = rec['eras']
rec_tracks = rec['tracks']
raw_eras   = raw['eras']
raw_tracks = raw['tracks']

print(f"Current RECENT: {len(rec_eras)} eras, {len(rec_tracks)} tracks")
print(f"Current RAW:    {len(raw_eras)} eras, {len(raw_tracks)} tracks")

rec_existing = {norm(rec_eras[t[0]] + t[1]) for t in rec_tracks}
raw_existing = {norm(raw_eras[t[0]] + t[1]) for t in raw_tracks}

# Find the most recent leak date already in the tracker
dated = [parse_date(t[5]) for t in rec_tracks if parse_date(t[5])]
if dated:
    latest_in_tracker = max(dated)
    print(f"Latest date in tracker: {latest_in_tracker.strftime('%Y-%m-%d')}")
else:
    latest_in_tracker = None
    print("No dated tracks found in tracker")

# ── collect new rows from sheet ────────────────────────────────────────────────

new_rows = []
for row in rows:
    d = parse_date(row.get(LEAK_KEY, ''))
    if d is None:
        continue
    # Only consider tracks newer than what's already in the tracker
    if latest_in_tracker and d <= latest_in_tracker:
        continue
    new_rows.append((d, row))

new_rows.sort(key=lambda x: x[0], reverse=True)
print(f"\nNew tracks to add: {len(new_rows)}")
for d, row in new_rows:
    print(f"  {d.strftime('%Y-%m-%d')} | {row.get('Era','')[:25]} | {row.get('Name','').split(chr(10))[0][:40]}")

if not new_rows:
    print("\nNothing new to add. Tracker is up to date.")
    sys.exit(0)

# ── inject into RECENT and RAW ─────────────────────────────────────────────────

added_rec = 0
added_raw = 0

for d, row in new_rows:
    era   = row.get('Era',   '').strip()
    name  = row.get('Name',  '').strip()
    notes = row.get('Notes', '').strip()
    tlen  = row.get('Track Length', '').strip()
    fdate = fmt_date(row.get(FILE_KEY,  ''))
    ldate = fmt_date(row.get(LEAK_KEY, ''))
    avail = row.get('Available Length', '').strip()
    qual  = row.get('Quality', '').strip()
    links = row.get('Link(s)', '').strip()

    key = norm(era + name)

    # RECENT
    if era not in rec_eras:
        rec_eras.append(era)
    era_idx = rec_eras.index(era)
    if key not in rec_existing:
        rec_tracks.append([era_idx, name, notes, tlen, fdate, ldate, avail, qual, links])
        rec_existing.add(key)
        added_rec += 1

    # RAW  [eraIdx, name, len, leakDate, availLen, quality, links, notes]
    if era not in raw_eras:
        raw_eras.append(era)
    raw_era_idx = raw_eras.index(era)
    if key not in raw_existing:
        raw_tracks.append([raw_era_idx, name, tlen, ldate, avail, qual, links, notes])
        raw_existing.add(key)
        added_raw += 1

print(f"\nAdded to RECENT: {added_rec}")
print(f"Added to RAW:    {added_raw}")

if added_rec == 0 and added_raw == 0:
    print("All tracks were already present. Nothing to write.")
    sys.exit(0)

# ── write back ─────────────────────────────────────────────────────────────────

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

raw_m2 = re.search(r'(const RAW\s*=\s*)(\{.*?\})(\s*;\s*(?:\n|$))', content, re.DOTALL)
content = (content[:raw_m2.start(1)]
           + raw_m2.group(1)
           + new_raw_json
           + raw_m2.group(3)
           + content[raw_m2.end(3):])

with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nindex.html updated.")

# ── git commit & push ──────────────────────────────────────────────────────────

today = datetime.now(timezone.utc).strftime('%b %d, %Y')
msg = f"Add new tracks from Google Sheet ({today})\n\n{added_rec} tracks added to Recent, {added_raw} to Unreleased."

subprocess.run(['git', 'add', 'index.html'], check=True)
result = subprocess.run(['git', 'commit', '-m', msg])
if result.returncode != 0:
    print("Nothing to commit or commit failed — skipping push.")
    sys.exit(0)
subprocess.run(['git', 'push', 'origin', 'main'], check=True)
print("Pushed to main.")
