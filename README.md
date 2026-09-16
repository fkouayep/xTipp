# Mein Tipp-Automat

Holt automatisch aktuelle Ergebnisse, berechnet form-gewichtete Team-Stärken
und erzeugt ein Wett-Dashboard mit Wahrscheinlichkeiten für **Über/Unter,
BTTS und 1X2** (Poisson-/Dixon-Coles-Modell).

Läuft **lokal** als eigenständige `dashboard.html` – oder als **installierbare
iPhone-App (PWA)**, die sich per GitHub Actions täglich selbst neu rechnet.

## Wettbewerbe & Datenquellen

| Wettbewerb | Quelle | API-Key |
|-----------|--------|---------|
| Premier League, La Liga, Bundesliga, Serie A, Ligue 1 | football-data.org | ja (kostenlos) |
| Champions League (ligaübergreifend) | football-data.org | ja (kostenlos) |
| 2. Bundesliga | OpenLigaDB | nein |

Eredivisie und Primeira Liga werden zusätzlich als Stärkebasis für die CL geladen.

---

## A) Lokal nutzen (Windows/Mac/Linux)

1. Key holen: https://www.football-data.org/client/register
2. `pip install -r requirements.txt`
3. Key setzen und bauen:
   - Windows (PowerShell): `$env:FOOTBALL_DATA_KEY="dein-key"` dann `python build_dashboard.py`
   - Mac/Linux: `export FOOTBALL_DATA_KEY="dein-key"` dann `python build_dashboard.py`
4. `dashboard.html` per Doppelklick öffnen.

Ohne Key testen: `python build_dashboard.py --demo`.

Jeder Lauf erzeugt zusätzlich den Ordner **`site/`** – das ist die fertige PWA.

---

## B) Als iPhone-App (PWA über GitHub Pages)

Ziel: eine Seite mit eigenem Icon auf dem Homescreen, die sich jeden Morgen
von allein aktualisiert – ohne Mac, ohne App Store, kostenlos.

### Einmalig einrichten

1. **Repository anlegen** (GitHub-Konto nötig) und alle Projektdateien hochladen.
   → **Wichtig:** Auf dem kostenlosen Plan muss das Repo **öffentlich** sein,
   sonst veröffentlicht GitHub Pages nicht. Das ist unkritisch: Dein Key steht
   nie im Code (siehe Schritt 2). Ein privates Repo bräuchte GitHub Pro (~4 $/Monat).

2. **API-Key als Secret hinterlegen** (nicht in den Code!):
   Repo → **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `FOOTBALL_DATA_KEY`
   - Wert: dein football-data.org-Key

3. **Pages aktivieren:**
   Repo → **Settings → Pages → Build and deployment → Source: „GitHub Actions"**.

4. **Workflow läuft automatisch** – täglich 05:00 UTC (~07:00 DE), bei jedem
   Push und manuell über **Actions → „Dashboard bauen & veröffentlichen" → Run workflow**.
   Nach dem ersten erfolgreichen Lauf steht die Adresse unter **Settings → Pages**
   (Form: `https://<dein-name>.github.io/<repo>/`).

### Aufs iPhone holen

5. Die Pages-URL in **Safari** öffnen → **Teilen-Symbol** → **„Zum Home-Bildschirm"**.
   Fertig: eigenes Icon, Vollbild, und beim Öffnen werden (online) die frischen
   Prognosen geladen; offline zeigt sie den letzten Stand.

### PWA lokal testen (optional)

Der Service-Worker braucht http(s), kein `file://`. Zum Probieren:
```
cd site
python -m http.server 8000
```
Dann `http://localhost:8000` im Browser öffnen.

---

## Dateien

| Datei | Zweck |
|-------|-------|
| `build_dashboard.py` | Startpunkt: Daten holen, rechnen, `dashboard.html` + `site/` schreiben |
| `fetch.py` / `fetch_openligadb.py` | Datenclients (football-data.org / OpenLigaDB) |
| `analyze.py` | form-gewichtete Stärken + Schrumpfung |
| `model.py` | Poisson-/Dixon-Coles-Modell |
| `champions.py` | ligaübergreifendes CL-Modell (Liga-Stärkefaktoren) |
| `render.py` | erzeugt das HTML (inkl. PWA-Tags) |
| `web/` | PWA-Assets: `manifest.webmanifest`, `sw.js`, `icons/` |
| `.github/workflows/build.yml` | tägliches Neurechnen + Deploy zu GitHub Pages |
| `generate_icons.py` | erzeugt die Icons neu (optional, braucht Pillow) |
| `make_sample.py` | Demo-Daten |

## Stellschrauben

- `analyze.py`: `HALFLIFE_DAYS` (60), `PSEUDO` (4)
- `model.py`: `RHO` (−0.13)
- `champions.py`: `LEAGUE_STRENGTH`, `MU_HOME`/`MU_AWAY`
- `.github/workflows/build.yml`: `cron` für die Uhrzeit des täglichen Laufs

## Hinweise

- **Key-Sicherheit:** Der Key gehört in GitHub-Secrets, niemals in den Code
  (`.gitignore` hält lokale Ausgaben ohnehin aus dem Repo).
- Die veröffentlichte Pages-Seite ist öffentlich erreichbar – bei einem privaten
  Tipp-Dashboard unkritisch, aber gut zu wissen.
- Push-Benachrichtigungen für iPhone-PWAs sind ab iOS 16.4 möglich, hier aber
  noch nicht eingebaut – kann später ergänzt werden.
- Faire Quote = `1 / Wahrscheinlichkeit`. Ein Modell bleibt ein Modell – keine
  Gewinngarantie. Glücksspiel kann süchtig machen; Hilfe unter www.bzga.de.
