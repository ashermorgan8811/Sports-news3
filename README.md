# 📰 The Daily Hardwood

Daily sports newspaper — NBA, EPL, F1, NCAA, NFL.
**Set it up once. It updates itself every morning at 5:30 AM forever.**

---

## What updates automatically every day

| What | How |
|------|-----|
| 🏀 NBA scores | Live from balldontlie.io API |
| ⚽ EPL scores | Live from TheSportsDB API |
| 📰 Lead stories | Scraped from ESPN RSS feed |
| 📰 Recaps & secondary stories | Scraped from BBC Sport + CBS Sports RSS |
| 🖼 Photos | Fresh Unsplash images (seed changes daily) |
| 🔀 Quotes, stats, takes, reactions | Rotate from built-in pool daily |

---

## One-time setup (~5 minutes)

### Step 1 — Create a free GitHub account
→ **github.com** → Sign up (free)

### Step 2 — Create a new repository
1. Click **+** top-right → **New repository**
2. Name: `daily-hardwood`  
3. Visibility: **Public**
4. Click **Create repository**

### Step 3 — Upload ALL files from this zip
Upload these files keeping the exact folder structure:
```
index.html
manifest.json
icon-192.png
icon-512.png
update_scores.py
.github/
  workflows/
    daily-update.yml
```

**To upload the .github folder:**
1. In your repo click **Add file** → **Upload files**
2. Drag ALL files at once — GitHub creates the folders automatically
3. Click **Commit changes**

### Step 4 — Enable GitHub Pages
1. Go to your repo → **Settings** tab
2. Left sidebar → **Pages**
3. Source: **Deploy from a branch**
4. Branch: **main** · Folder: **/ (root)**
5. Click **Save**
6. Wait 2 minutes → your site is live at:
   **`https://YOUR-USERNAME.github.io/daily-hardwood`**

### Step 5 — Enable Actions (important!)
1. Go to **Actions** tab in your repo
2. If you see "Workflows aren't running" → click **I understand, enable them**
3. Click **Daily Hardwood Update** → **Run workflow** → **Run workflow** (green button)
4. This does the first update immediately — confirm it works

### Step 6 — Add to iPhone Home Screen
1. Open **Safari** (must be Safari, not Chrome)
2. Go to `https://YOUR-USERNAME.github.io/daily-hardwood`
3. Tap the **Share** button (square with arrow pointing up)
4. Scroll down → tap **Add to Home Screen**
5. Name it: **The Daily Hardwood**
6. Tap **Add**

The newspaper icon (orange with white lines) appears on your home screen.
Tap it every morning to open your fresh edition.

---

## How the daily update works

```
5:30 AM every day
      ↓
GitHub Actions wakes up (free, no server needed)
      ↓
Runs update_scores.py
      ↓
┌─────────────────────────────────────────────┐
│ Fetches NBA scores from balldontlie.io       │
│ Fetches EPL scores from TheSportsDB         │
│ Scrapes ESPN RSS → real NBA/NFL/NCAA/F1 headlines │
│ Scrapes BBC Sport RSS → real soccer headlines│
│ Scrapes CBS Sports RSS → more stories        │
└─────────────────────────────────────────────┘
      ↓
Injects all of it into index.html
      ↓
Commits + pushes the updated file
      ↓
GitHub Pages serves the new version (within seconds)
      ↓
You open the app → fresh paper with today's real news
```

---

## Troubleshooting

**Actions not running automatically?**
- Go to Actions tab → the workflow might need to be enabled
- Also try: Settings → Actions → General → Allow all actions

**Want to trigger an update right now?**
Actions tab → Daily Hardwood Update → Run workflow

**Stories look like old ones?**
RSS feeds occasionally go down. The page still shows the built-in story pool as fallback.

**Home screen icon isn't showing?**
Make sure you used Safari (not Chrome) to add it. Delete and re-add from Safari.
