"""
Baut das Tipp-Dashboard: Daten holen -> Stärken berechnen -> Prognosen ->
eigenständige dashboard.html + predictions.json.

Datenquellen:
  - Top-5-Ligen:     football-data.org (API-Key nötig)
  - 2. Bundesliga:   OpenLigaDB (kostenlos, ohne Key)
  - Champions League: football-data.org, ligaübergreifend gerechnet
      (Stärkebasis: Top-5 + Eredivisie + Primeira Liga)

Nutzung:
  export FOOTBALL_DATA_KEY="dein-key"
  python build_dashboard.py               # alles
  python build_dashboard.py --demo        # ohne Key/Netz, Beispieldaten
"""
import os
import sys
import json
import shutil
import datetime

import analyze
import render
import champions
from model import predict
from fetch import fetch_all, COMPS
from fetch_openligadb import fetch_bl2, current_season

# zusätzliche football-data.org-Ligen nur als CL-Stärkebasis (nicht als Tab)
CL_BASE_EXTRA = {"DED": "Eredivisie", "PPL": "Primeira Liga"}
CL_CODE, CL_NAME = "CL", "Champions League"


def build(sources):
    """sources: {Liga-Anzeigename: Spiele im fd.org-Format} -> Liga-interne Prognosen."""
    results, payload = [], {}
    for name, matches in sources.items():
        data = analyze.compute(matches or [])
        if not data:
            print(f"  ! {name}: keine beendeten Spiele – übersprungen")
            continue
        rows, out_fix = [], []
        for f in data["fixtures"]:
            pr = predict(f["home"], f["away"], data["strengths"],
                         data["avg_home"], data["avg_away"])
            rows.append({"f": f, "pr": pr})
            out_fix.append(_fix_out(f, pr))
        results.append({"league": name, "rows": rows})
        payload[name] = out_fix
        print(f"  ✓ {name}: {len(rows)} Spiele prognostiziert")
    return results, payload


def _fix_out(f, pr):
    return {"home": f["home"], "away": f["away"], "date": f["date"], "time": f["time"],
            "p_home": round(pr["home"], 4), "p_draw": round(pr["draw"], 4),
            "p_away": round(pr["away"], 4), "over25": round(pr["over"][2.5], 4),
            "btts": round(pr["btts"], 4), "xg_home": round(pr["lh"], 2),
            "xg_away": round(pr["la"], 2)}


def cl_from(base_computed, fixtures, id2name=None):
    """CL-Zeilen + Rohdaten aus Heimliga-Stärken und CL-Spielplan."""
    gmap = champions.build_global_map(base_computed)
    rows, skipped = champions.predict_fixtures(fixtures, gmap, id2name)
    out = [_fix_out(r["f"], r["pr"]) for r in rows if r["pr"]]
    n_ok = sum(1 for r in rows if r["pr"])
    print(f"  ✓ {CL_NAME}: {n_ok} Spiele prognostiziert"
          + (f", {len(skipped)} ohne Prognose (Heimliga nicht abgedeckt)" if skipped else ""))
    for s in skipped:
        print(f"      – {s['home']} vs {s['away']}: {', '.join(s['missing'])}")
    return rows, out, skipped


def gather_live():
    sources_display, cl_rows, cl_out, cl_skipped = {}, None, [], []
    key = os.environ.get("FOOTBALL_DATA_KEY")

    if key:
        codes = {**COMPS, **CL_BASE_EXTRA, CL_CODE: CL_NAME}
        print(f"Hole {len(codes)} Wettbewerbe (football-data.org, ~1 min wegen Ratenlimit)…")
        raw = fetch_all(key, comps=codes)
        for code, name in COMPS.items():
            sources_display[name] = raw.get(code, [])
        # CL-Stärkebasis: Top-5 + Eredivisie + Primeira
        base_codes = {**COMPS, **CL_BASE_EXTRA}
        base = {name: analyze.compute(raw.get(code, [])) for code, name in base_codes.items()}
        id2name = champions.name_by_id({name: raw.get(code, []) for code, name in base_codes.items()})
        fixtures = champions.upcoming_fixtures(raw.get(CL_CODE, []))
        cl_rows, cl_out, cl_skipped = cl_from(base, fixtures, id2name)
    else:
        print("Hinweis: kein FOOTBALL_DATA_KEY – Top-5 und Champions League werden übersprungen.")
        print("         (Die 2. Bundesliga braucht keinen Key.)")

    season = current_season()
    print(f"Hole 2. Bundesliga (OpenLigaDB, Saison {season}/{season + 1})…")
    try:
        sources_display["2. Bundesliga"] = fetch_bl2(season)
    except Exception as e:
        print(f"  ! 2. Bundesliga konnte nicht geladen werden: {e}")

    return sources_display, cl_rows, cl_out, cl_skipped


def gather_demo():
    with open("sample_matches.json", encoding="utf-8") as fh:
        data = json.load(fh)
    sources_display = data["leagues"]
    base = {name: analyze.compute(m) for name, m in sources_display.items()
            if name in champions.LEAGUE_STRENGTH}
    cl_rows, cl_out, cl_skipped = cl_from(base, data.get("cl_fixtures", []))
    return sources_display, cl_rows, cl_out, cl_skipped


def main():
    if "--demo" in sys.argv:
        print("Demo-Modus: lade sample_matches.json")
        sources_display, cl_rows, cl_out, cl_skipped = gather_demo()
    else:
        sources_display, cl_rows, cl_out, cl_skipped = gather_live()

    results, payload = build(sources_display)
    if cl_rows:
        results.append({"league": CL_NAME, "rows": cl_rows})
        payload[CL_NAME] = cl_out
    if not results:
        sys.exit("Keine Prognosen erzeugt (keine Daten).")

    stamp = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    html_out = render.render_html(results, stamp)
    meta = {"generated": stamp, "leagues": payload}
    if cl_skipped:
        meta["champions_ohne_prognose"] = cl_skipped
    meta_json = json.dumps(meta, ensure_ascii=False, indent=2)

    # 1) lokal: eigenständige Datei zum Doppelklicken
    with open("dashboard.html", "w", encoding="utf-8") as fh:
        fh.write(html_out)
    with open("predictions.json", "w", encoding="utf-8") as fh:
        fh.write(meta_json)

    # 2) PWA: fertiger site/-Ordner für GitHub Pages
    write_site(html_out, meta_json)

    print("\nFertig:")
    print("  dashboard.html      → lokal im Browser öffnen")
    print("  predictions.json    → Rohdaten")
    print("  site/               → fertige PWA (GitHub Pages / lokal per Webserver)")


def write_site(html_out, meta_json):
    """Baut den site/-Ordner: index.html + PWA-Assets aus web/."""
    site = "site"
    if os.path.isdir(site):
        shutil.rmtree(site)
    if os.path.isdir("web"):
        shutil.copytree("web", site)
    else:
        os.makedirs(site, exist_ok=True)
    with open(os.path.join(site, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html_out)
    with open(os.path.join(site, "predictions.json"), "w", encoding="utf-8") as fh:
        fh.write(meta_json)


if __name__ == "__main__":
    main()
