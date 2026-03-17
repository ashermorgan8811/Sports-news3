"""
Daily Hardwood — Auto-Updater
Runs at 5:29 AM Eastern every day via GitHub Actions.
Retries every API call up to 3 times so scores are always fresh.
"""

import requests, re, xml.etree.ElementTree as ET, time
from datetime import datetime, timezone, timedelta
from html import unescape

# ── TIMEZONE ──────────────────────────────────────────────────────────────────
# Detect whether we're in EDT (UTC-4) or EST (UTC-5)
# GitHub Actions runs in UTC — we figure out Eastern from that
utc_now  = datetime.now(timezone.utc)
# EDT runs Mar 2nd Sunday → Nov 1st Sunday (approximate with month check)
month = utc_now.month
is_edt = 3 <= month <= 11
et_offset = -4 if is_edt else -5
ET_OFF   = timezone(timedelta(hours=et_offset))
now_et   = datetime.now(ET_OFF)
today    = now_et.strftime('%Y-%m-%d')
yesterday = (now_et - timedelta(days=1)).strftime('%Y-%m-%d')
label    = now_et.strftime('%A, %B %-d, %Y')
doy      = int(now_et.strftime('%j'))

print(f"\n{'='*60}")
print(f"Daily Hardwood — {label}")
print(f"UTC: {utc_now.strftime('%H:%M')}  Eastern offset: UTC{et_offset}")
print(f"{'='*60}\n")

# ── RESILIENT GET — retries 3 times ──────────────────────────────────────────
def get(url, params=None, timeout=15, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout,
                             headers={'User-Agent': 'Mozilla/5.0 DailyHardwood/1.0'})
            if r.status_code == 200:
                return r
            print(f"  Attempt {attempt+1}: HTTP {r.status_code} — {url[:50]}")
        except Exception as e:
            print(f"  Attempt {attempt+1}: {e} — {url[:50]}")
        if attempt < retries - 1:
            time.sleep(2)  # wait 2 seconds before retry
    return None

def clean(text):
    text = re.sub(r'<[^>]+>', ' ', text or '')
    text = unescape(text)
    return ' '.join(text.split()).strip()

def js_escape(s):
    return (str(s or '')
            .replace('\\', '\\\\')
            .replace("'", "\\'")
            .replace('\n', ' ')
            .replace('\r', ''))

def short_team(n):
    table = {
        'Oklahoma City Thunder': 'OKC Thunder',
        'Golden State Warriors': 'Warriors',
        'Los Angeles Lakers': 'Lakers',
        'Los Angeles Clippers': 'Clippers',
        'Portland Trail Blazers': 'Trail Blazers',
        'New Orleans Pelicans': 'Pelicans',
        'Memphis Grizzlies': 'Grizzlies',
        'Minnesota Timberwolves': 'T-Wolves',
        'San Antonio Spurs': 'Spurs',
        'Philadelphia 76ers': '76ers',
        'Washington Wizards': 'Wizards',
        'Charlotte Hornets': 'Hornets',
        'Cleveland Cavaliers': 'Cavaliers',
        'Toronto Raptors': 'Raptors',
        'Milwaukee Bucks': 'Bucks',
        'Indiana Pacers': 'Pacers',
        'Detroit Pistons': 'Pistons',
        'New York Knicks': 'Knicks',
        'Brooklyn Nets': 'Nets',
        'Boston Celtics': 'Celtics',
        'Miami Heat': 'Heat',
        'Orlando Magic': 'Magic',
        'Atlanta Hawks': 'Hawks',
        'Chicago Bulls': 'Bulls',
        'Denver Nuggets': 'Nuggets',
        'Utah Jazz': 'Jazz',
        'Sacramento Kings': 'Kings',
        'Phoenix Suns': 'Suns',
        'Houston Rockets': 'Rockets',
        'Dallas Mavericks': 'Mavericks',
    }
    return table.get(n, n)


# ════════════════════════════════════════════════════════════════════════════
#  NBA SCORES — fetch today AND yesterday to always have fresh results
# ════════════════════════════════════════════════════════════════════════════
print("🏀 Fetching NBA scores...")
nba_scores = []

for date_str in [today, yesterday]:
    r = get('https://www.balldontlie.io/api/v1/games',
            params={'dates[]': date_str, 'per_page': 15})
    if not r:
        continue
    for g in r.json().get('data', []):
        away   = short_team(g['visitor_team']['full_name'])
        home   = short_team(g['home_team']['full_name'])
        status = g.get('status', '')
        aS     = g.get('visitor_team_score')
        hS     = g.get('home_team_score')

        if status == 'Final':
            st, live = 'Final', False
        elif any(x in status for x in ['Qtr', 'Half', 'OT', "'"]):
            st, live = status, True
        else:
            try:
                dt = datetime.fromisoformat(g['date'].replace('Z', '+00:00'))
                st = dt.astimezone(ET_OFF).strftime('%-I:%M %p ET')
            except Exception:
                st = 'Tonight'
            live = False
            aS = hS = None

        nba_scores.append({
            'away': away, 'home': home,
            'aS': aS, 'hS': hS,
            'st': st, 'live': live
        })

# Deduplicate (same game from both dates), prefer Final over scheduled
seen = {}
for g in nba_scores:
    key = f"{g['away']}-{g['home']}"
    if key not in seen or g['st'] == 'Final':
        seen[key] = g
nba_scores = list(seen.values())[:8]

print(f"  ✓ {len(nba_scores)} NBA games")
for g in nba_scores:
    score = f"{g['aS']}-{g['hS']}" if g['aS'] is not None else 'scheduled'
    print(f"    {g['away']} @ {g['home']}: {score} ({g['st']})")


# ════════════════════════════════════════════════════════════════════════════
#  EPL SCORES — today and yesterday
# ════════════════════════════════════════════════════════════════════════════
print("\n⚽ Fetching EPL scores...")
epl_scores = []

for date_str in [today, yesterday]:
    r = get('https://www.thesportsdb.com/api/v1/json/3/eventsday.php',
            params={'d': date_str, 'l': 'English%20Premier%20League'})
    if not r:
        continue
    for e in (r.json().get('events') or []):
        home   = e.get('strHomeTeam', '').replace(' FC', '').replace(' AFC', '')
        away   = e.get('strAwayTeam', '').replace(' FC', '').replace(' AFC', '')
        status = e.get('strStatus', '')
        hS_raw = e.get('intHomeScore')
        aS_raw = e.get('intAwayScore')

        if status in ('Match Finished', 'FT'):
            st, live = 'Final', False
            hS = int(hS_raw) if hS_raw is not None else None
            aS = int(aS_raw) if aS_raw is not None else None
        elif status in ('In Progress', 'HT') or "'" in status:
            st, live = status, True
            hS = int(hS_raw) if hS_raw is not None else None
            aS = int(aS_raw) if aS_raw is not None else None
        else:
            st   = (e.get('strTime', '') or 'TBD') + ' ET'
            live = False
            hS = aS = None

        if home and away:
            epl_scores.append({
                'away': away, 'home': home,
                'aS': aS, 'hS': hS,
                'st': st, 'live': live, 'lg': 'EPL'
            })

# Deduplicate
seen_epl = {}
for g in epl_scores:
    key = f"{g['away']}-{g['home']}"
    if key not in seen_epl or g['st'] == 'Final':
        seen_epl[key] = g
epl_scores = list(seen_epl.values())[:8]

print(f"  ✓ {len(epl_scores)} EPL games")
for g in epl_scores:
    score = f"{g['aS']}-{g['hS']}" if g['aS'] is not None else 'scheduled'
    print(f"    {g['away']} @ {g['home']}: {score} ({g['st']})")


# ════════════════════════════════════════════════════════════════════════════
#  REAL HEADLINES — ESPN + BBC Sport + CBS Sports RSS
# ════════════════════════════════════════════════════════════════════════════
print("\n📰 Fetching real headlines...")

RSS_FEEDS = {
    'ESPN NBA':    'https://www.espn.com/espn/rss/nba/news',
    'ESPN NFL':    'https://www.espn.com/espn/rss/nfl/news',
    'ESPN Soccer': 'https://www.espn.com/espn/rss/soccer/news',
    'ESPN F1':     'https://www.espn.com/espn/rss/rpm/news',
    'ESPN NCAAB':  'https://www.espn.com/espn/rss/ncb/news',
    'BBC Sport':   'https://feeds.bbci.co.uk/sport/rss.xml',
    'CBS Sports':  'https://www.cbssports.com/rss/headlines/',
}

all_stories = []

for source, url in RSS_FEEDS.items():
    r = get(url)
    if not r:
        print(f"  ✗ {source}: unavailable")
        continue
    try:
        root = ET.fromstring(r.content)
        count = 0
        for item in root.findall('.//item')[:5]:
            title = clean(item.findtext('title', ''))
            desc  = clean(item.findtext('description', ''))
            if not title or len(title) < 15:
                continue
            t = (title + ' ' + desc).lower()
            if any(x in t for x in ['nba','lakers','celtics','warriors','thunder',
                'knicks','bucks','spurs','cavaliers','mavericks','nuggets','76ers',
                'heat','suns','nets','bulls','pacers','pistons','grizzlies','rockets',
                'clippers','hawks','hornets','magic','raptors','wizards','jazz',
                'kings','blazers','pelicans','timberwolves','lebron','curry',
                'giannis','wembanyama','flagg','sga','gilgeous']):
                cat = 'NBA'
            elif any(x in t for x in ['premier league','arsenal','liverpool',
                'chelsea','man united','manchester united','man city','manchester city',
                'tottenham','newcastle','everton','aston villa','brighton','fulham',
                'west ham','wolves','leeds','crystal palace','brentford','burnley',
                'sunderland','bournemouth','nottm','forest']):
                cat = 'EPL'
            elif any(x in t for x in ['formula 1','f1','grand prix','verstappen',
                'hamilton','leclerc','russell','norris','alonso','ferrari',
                'mercedes','red bull','mclaren','williams','haas','race','circuit']):
                cat = 'F1'
            elif any(x in t for x in ['ncaa','march madness','college basketball',
                'duke','kansas','arizona','michigan','florida','uconn','gonzaga',
                'houston','purdue','byu','kentucky','tournament bracket']):
                cat = 'NCAA'
            elif any(x in t for x in ['nfl','quarterback','touchdown','super bowl',
                'mahomes','chiefs','eagles','cowboys','patriots','49ers','ravens',
                'bills','bengals','browns','packers','bears','lions','vikings',
                'rams','chargers','raiders','broncos','seahawks','draft']):
                cat = 'NFL'
            else:
                cat = 'Sports'

            all_stories.append({
                'source': source,
                'cat':    cat,
                'title':  title,
                'desc':   desc[:300] if desc else title,
            })
            count += 1
        print(f"  ✓ {source}: {count} stories")
    except Exception as e:
        print(f"  ✗ {source}: parse error — {e}")

print(f"  Total: {len(all_stories)} stories across all sources")

# Pick top story per category
by_cat = {}
for s in all_stories:
    by_cat.setdefault(s['cat'], []).append(s)

priority      = ['NBA', 'F1', 'EPL', 'NCAA', 'NFL', 'Soccer', 'Sports']
picked_leads  = [by_cat[c][0] for c in priority if by_cat.get(c)][:5]
picked_recaps = []
for c in priority:
    for s in by_cat.get(c, [])[1:3]:
        if len(picked_recaps) < 8:
            picked_recaps.append(s)

print(f"\n  Leads:  {len(picked_leads)}")
for s in picked_leads:
    print(f"    [{s['cat']}] {s['title'][:65]}")
print(f"  Recaps: {len(picked_recaps)}")


# ════════════════════════════════════════════════════════════════════════════
#  BUILD JS + INJECT INTO index.html
# ════════════════════════════════════════════════════════════════════════════
def score_line(g, include_lg=False):
    aS   = 'null' if g['aS'] is None else str(g['aS'])
    hS   = 'null' if g['hS'] is None else str(g['hS'])
    live = 'true' if g.get('live') else 'false'
    lg   = f",lg:'{g['lg']}'" if include_lg and g.get('lg') else ''
    return (f"  {{away:'{js_escape(g['away'])}',home:'{js_escape(g['home'])}',"
            f"aS:{aS},hS:{hS},st:'{js_escape(g['st'])}',live:{live}{lg}}}")

IMG = {
    'NBA':    'basketball nba arena game action',
    'EPL':    'soccer football stadium crowd match',
    'F1':     'formula 1 racing car track speed',
    'NCAA':   'basketball college arena crowd',
    'NFL':    'american football stadium crowd field',
    'Sports': 'sports arena crowd cheering',
}

def make_lead(s, i):
    t   = js_escape(s['title'])
    d   = js_escape(s['desc'][:280])
    src = js_escape(s['source'])
    q   = IMG.get(s['cat'], 'sports arena crowd')
    return (f"  {{id:'live_{i}',tag:'{s['cat']} \u00b7 Today',date:'{label}',"
            f"query:'{q}',seed:{i + doy},"
            f"headline:'{t}',"
            f"deck:'{js_escape(s['desc'][:140])}...',"
            f"body:['{d}','Source: {src}.'],"
            f"sources:[{{o:'{src}',d:'Live RSS feed'}}]}}")

def make_recap(s, i):
    t   = js_escape(s['title'])
    d   = js_escape(s['desc'][:280])
    src = js_escape(s['source'])
    q   = IMG.get(s['cat'], 'sports game action')
    return (f"  {{id:'recap_{i}',tag:'{s['cat']} \u00b7 Recap',date:'{label}',"
            f"query:'{q}',seed:{i + doy + 50},"
            f"headline:'{t}',teams:'',body:['{d}'],km:'',"
            f"sources:[{{o:'{src}',d:'Live RSS feed'}}]}}")

print("\n💉 Injecting into index.html...")
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# NBA scores
if nba_scores:
    new_js = 'const NBA_SCORES = [\n' + ',\n'.join(score_line(g) for g in nba_scores) + '\n];'
    html = re.sub(r'const NBA_SCORES = \[[\s\S]*?\];', new_js, html)
    print("  ✓ NBA scores")

# EPL scores
if epl_scores:
    new_js = 'const SOC_SCORES = [\n' + ',\n'.join(score_line(g, True) for g in epl_scores) + '\n];'
    html = re.sub(r'const SOC_SCORES = \[[\s\S]*?\];', new_js, html)
    print("  ✓ EPL scores")

# Lead stories
if len(picked_leads) >= 2:
    new_js = 'const ALL_LEADS = [\n' + ',\n'.join(make_lead(s, i) for i, s in enumerate(picked_leads)) + '\n];'
    html = re.sub(r'const ALL_LEADS = \[[\s\S]*?\];', new_js, html)
    print(f"  ✓ {len(picked_leads)} lead stories")

# Recap stories
if len(picked_recaps) >= 2:
    new_js = 'const ALL_RECAPS = [\n' + ',\n'.join(make_recap(s, i) for i, s in enumerate(picked_recaps)) + '\n];'
    html = re.sub(r'const ALL_RECAPS = \[[\s\S]*?\];', new_js, html)
    print(f"  ✓ {len(picked_recaps)} recap stories")

# Update date seed so images rotate
html = re.sub(
    r"const DATE_ISO\s*=\s*(?:new Date\(\)\.toISOString\(\)\.slice\(0,\s*10\)|'[0-9-]+');(?:\s*//.*)?",
    f"const DATE_ISO = '{today}'; // auto-updated {today}",
    html
)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n{'='*60}")
print(f"✅ Done — {label}")
print(f"   NBA: {len(nba_scores)} games | EPL: {len(epl_scores)} games | Headlines: {len(all_stories)}")
print(f"{'='*60}\n")


# ════════════════════════════════════════════════════════════════════════════
#  NCAA TOURNAMENT BRACKET — fetch live results from TheSportsDB
# ════════════════════════════════════════════════════════════════════════════
print("\n🏀 Fetching NCAA Tournament results...")
ncaa_results = {}

# Fetch last 7 days of NCAA tournament games
for days_back in range(7):
    check_date = (now_et - timedelta(days=days_back)).strftime('%Y-%m-%d')
    r = get('https://www.thesportsdb.com/api/v1/json/3/eventsday.php',
            params={'d': check_date, 's': 'Basketball'})
    if not r:
        continue
    try:
        events = r.json().get('events') or []
        for e in events:
            league = e.get('strLeague', '')
            if 'NCAA' not in league and 'March Madness' not in league and 'College Basketball' not in league:
                continue
            home = e.get('strHomeTeam', '')
            away = e.get('strAwayTeam', '')
            hS = e.get('intHomeScore')
            aS = e.get('intAwayScore')
            status = e.get('strStatus', '')
            if status in ('Match Finished', 'FT') and hS is not None and aS is not None:
                hS, aS = int(hS), int(aS)
                winner = home if hS > aS else away
                loser  = away if hS > aS else home
                ws = hS if hS > aS else aS
                ls = aS if hS > aS else hS
                key = tuple(sorted([home.lower(), away.lower()]))
                if key not in ncaa_results:
                    ncaa_results[key] = f"{winner} {ws}-{ls}"
                    print(f"  {winner} def. {loser} {ws}-{ls}")
    except Exception as ex:
        pass

print(f"  NCAA results found: {len(ncaa_results)}")

# ── INJECT BRACKET RESULTS INTO HTML ─────────────────────────────────────────
if ncaa_results:
    def update_bracket_result(html_content, t1, t2, result):
        """Find the game row for t1 vs t2 and update the result."""
        # Match patterns like: {s1:1, t1:'Duke', s2:16, t2:'Siena', r:null
        patterns = [
            (f"t1:'{t1}'", f"t2:'{t2}'"),
            (f"t1:'{t2}'", f"t2:'{t1}'"),
        ]
        for p1, p2 in patterns:
            # Find the game object and replace r:null with r:'result'
            pattern = r"(\{[^}]*" + re.escape(p1) + r"[^}]*" + re.escape(p2) + r"[^}]*),r:null"
            replacement = r"\1,r:'" + js_escape(result) + "'"
            new_content = re.sub(pattern, replacement, html_content)
            if new_content != html_content:
                return new_content
            # Try reverse order
            pattern2 = r"(\{[^}]*" + re.escape(p2) + r"[^}]*" + re.escape(p1) + r"[^}]*),r:null"
            new_content = re.sub(pattern2, replacement, html_content)
            if new_content != html_content:
                return new_content
        return html_content

    # Map known team name variations
    TEAM_ALIASES = {
        'north carolina': 'n. carolina',
        'north carolina tar heels': 'n. carolina',
        'michigan wolverines': 'michigan',
        'duke blue devils': 'duke',
        'uconn huskies': 'uconn',
        'michigan state spartans': 'michigan st.',
        'iowa state cyclones': 'iowa state',
        'north dakota state bison': 'n. dakota st.',
        'kennesaw state owls': 'kennesaw st.',
        'saint marys gaels': "saint mary's",
        'saint mary s gaels': "saint mary's",
        'texas a m aggies': 'texas a&m',
        'byu cougars': 'byu',
        'unc wilmington seahawks': 'uncw',
    }

    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    updated = 0
    for (t1_raw, t2_raw), result in ncaa_results.items():
        t1 = TEAM_ALIASES.get(t1_raw, t1_raw.title())
        t2 = TEAM_ALIASES.get(t2_raw, t2_raw.title())
        new_html = update_bracket_result(html, t1, t2, result)
        if new_html != html:
            html = new_html
            updated += 1

    if updated:
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  ✓ Updated {updated} bracket game results in index.html")
    else:
        print("  ℹ No bracket results matched (games may not have started yet)")

print(f"\n{'='*60}\nAll done — {label}\n{'='*60}\n")
