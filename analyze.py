"""Aus Spielergebnissen form-gewichtete Team-Stärken berechnen."""
import datetime
from collections import defaultdict

HALFLIFE_DAYS = 60.0   # ältere Spiele zählen weniger (Halbwertszeit)
PSEUDO = 4.0           # Regularisierung: Schrumpfung Richtung Liga-Schnitt


def _dt(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def _team(side):
    return side.get("shortName") or side.get("name") or side.get("tla")


def compute(matches, halflife=HALFLIFE_DAYS, pseudo=PSEUDO):
    """Gibt strengths, Liga-Heim/Auswärts-Schnitte und kommende Spiele zurück."""
    finished = [m for m in matches if m.get("status") == "FINISHED"]
    upcoming = [m for m in matches if m.get("status") in ("TIMED", "SCHEDULED")]
    if not finished:
        return None

    now = datetime.datetime.now(datetime.timezone.utc)
    home_goals, away_goals = [], []
    per = defaultdict(lambda: {"gf": [], "ga": []})

    for m in finished:
        ft = m["score"]["fullTime"]
        gh, ga = ft.get("home"), ft.get("away")
        if gh is None or ga is None:
            continue
        h, a = _team(m["homeTeam"]), _team(m["awayTeam"])
        home_goals.append(gh)
        away_goals.append(ga)
        w = 0.5 ** ((now - _dt(m["utcDate"])).days / halflife)
        per[h]["gf"].append((gh, w)); per[h]["ga"].append((ga, w))
        per[a]["gf"].append((ga, w)); per[a]["ga"].append((gh, w))

    if not home_goals:
        return None

    avg_home = sum(home_goals) / len(home_goals)
    avg_away = sum(away_goals) / len(away_goals)
    league_mean = (sum(home_goals) + sum(away_goals)) / (2 * len(home_goals))

    strengths = {"_ref": league_mean}
    for team, d in per.items():
        sw = sum(w for _, w in d["gf"])
        if sw == 0:
            continue
        wgf = sum(v * w for v, w in d["gf"]) / sw
        wga = sum(v * w for v, w in d["ga"]) / sw
        # Schrumpfung Richtung Liga-Schnitt (stabil bei wenigen Spielen)
        gf = (sw * wgf + pseudo * league_mean) / (sw + pseudo)
        ga = (sw * wga + pseudo * league_mean) / (sw + pseudo)
        strengths[team] = {"gf": round(gf, 3), "ga": round(ga, 3), "games": len(d["gf"])}

    fixtures = []
    for m in sorted(upcoming, key=lambda x: x["utcDate"]):
        try:
            dtm = _dt(m["utcDate"])
        except Exception:
            continue
        if dtm < now - datetime.timedelta(days=1):
            continue  # bereits vergangene, nicht gewertete Spiele überspringen
        h, a = _team(m["homeTeam"]), _team(m["awayTeam"])
        if h not in strengths or a not in strengths:
            continue
        local = dtm.astimezone()
        fixtures.append({
            "home": h, "away": a,
            "date": local.strftime("%a %d.%m."),
            "time": local.strftime("%H:%M"),
        })
        if len(fixtures) >= 20:
            break

    return {"strengths": strengths, "avg_home": avg_home,
            "avg_away": avg_away, "fixtures": fixtures}
