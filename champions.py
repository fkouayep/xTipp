"""Ligaübergreifendes Modell für die Champions League.

Idee: Die Stärke jedes Teams kommt aus seiner HEIMLIGA (gf/ga relativ zum
Liga-Schnitt) und wird über einen Liga-Stärkefaktor auf eine gemeinsame
europäische Skala gebracht. So werden Teams aus verschiedenen Ligen fair
gegeneinander gerechnet.
"""
import datetime

import analyze
import model

# Relative Ligastärke (1.00 = Ankerliga). Schätzwerte – frei justierbar.
LEAGUE_STRENGTH = {
    "Premier League": 1.15,
    "La Liga": 1.08,
    "Serie A": 1.06,
    "Bundesliga": 1.05,
    "Ligue 1": 1.00,
    "Primeira Liga": 0.92,
    "Eredivisie": 0.90,
}
MU_HOME = 1.45   # europäischer Basiswert Heimtore (CL etwas torärmer als Ligen)
MU_AWAY = 1.25   # europäischer Basiswert Auswärtstore


def build_global_map(domestic_computed):
    """domestic_computed: {liga_name: analyze.compute(...) oder None} -> Team-Map."""
    gmap = {}
    for league, data in domestic_computed.items():
        if not data:
            continue
        ref = data["strengths"]["_ref"]
        for team, s in data["strengths"].items():
            if team == "_ref":
                continue
            gmap[team] = {"a": s["gf"] / ref, "d": s["ga"] / ref,
                          "league": league, "games": s["games"]}
    return gmap


def name_by_id(raw_by_league):
    """{liga: [spiele]} -> {teamId: Anzeigename} (robuste Zuordnung über IDs)."""
    out = {}
    for matches in raw_by_league.values():
        for m in matches or []:
            for side in ("homeTeam", "awayTeam"):
                t = m.get(side) or {}
                if t.get("id") is not None:
                    out[t["id"]] = analyze._team(t)
    return out


def upcoming_fixtures(matches, limit=20):
    """Kommende CL-Spiele als {home, away, home_id, away_id, date, time}."""
    now = datetime.datetime.now(datetime.timezone.utc)
    ups = [m for m in matches if m.get("status") in ("TIMED", "SCHEDULED")]
    out = []
    for m in sorted(ups, key=lambda x: x.get("utcDate", "")):
        try:
            dtm = analyze._dt(m["utcDate"])
        except Exception:
            continue
        if dtm < now - datetime.timedelta(days=1):
            continue
        local = dtm.astimezone()
        out.append({
            "home": analyze._team(m["homeTeam"]), "away": analyze._team(m["awayTeam"]),
            "home_id": (m.get("homeTeam") or {}).get("id"),
            "away_id": (m.get("awayTeam") or {}).get("id"),
            "date": local.strftime("%a %d.%m."), "time": local.strftime("%H:%M"),
        })
        if len(out) >= limit:
            break
    return out


def predict_fixtures(fixtures, gmap, id2name=None, strength=LEAGUE_STRENGTH):
    """Gibt (rows, skipped) zurück. rows: {f, pr} — pr=None wenn nicht abgedeckt."""
    id2name = id2name or {}
    rows, skipped = [], []
    for f in fixtures:
        hn = id2name.get(f.get("home_id"), f["home"])
        an = id2name.get(f.get("away_id"), f["away"])
        h = gmap.get(hn) or gmap.get(f["home"])
        a = gmap.get(an) or gmap.get(f["away"])
        if not h or not a:
            miss = [f["home"]] * (not h) + [f["away"]] * (not a)
            rows.append({"f": f, "pr": None, "note": "Heimliga nicht abgedeckt"})
            skipped.append({"home": f["home"], "away": f["away"], "missing": miss})
            continue
        sx = strength.get(h["league"], 1.0)
        sy = strength.get(a["league"], 1.0)
        lh = MU_HOME * (h["a"] * sx) * (a["d"] / sy)
        la = MU_AWAY * (a["a"] * sy) * (h["d"] / sx)
        rows.append({"f": f, "pr": model.markets(lh, la)})
    return rows, skipped
