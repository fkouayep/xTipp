"""2. Bundesliga von OpenLigaDB holen (kostenlos, ohne API-Key)."""
import datetime
import requests

BASE = "https://api.openligadb.de"


def current_season():
    """Saison-Startjahr: ab Juli das laufende Jahr, sonst Vorjahr."""
    t = datetime.date.today()
    return t.year if t.month >= 7 else t.year - 1


def _name(team):
    return ((team or {}).get("shortName") or "").strip() or (team or {}).get("teamName") or ""


def _final(match):
    """Endergebnis aus matchResults ziehen (resultTypeID 2 = Endergebnis)."""
    res = match.get("matchResults") or []
    end = [r for r in res if r.get("resultTypeID") == 2]
    if not end and res:
        end = [max(res, key=lambda r: r.get("resultOrderID", 0))]
    if not end:
        return None, None
    r = end[0]
    return r.get("pointsTeam1"), r.get("pointsTeam2")


def to_fdorg(matches):
    """OpenLigaDB -> football-data.org-ähnliches Format (für analyze.compute)."""
    out = []
    for m in matches:
        finished = bool(m.get("matchIsFinished"))
        gh, ga = _final(m) if finished else (None, None)
        utc = m.get("matchDateTimeUTC")
        if not utc:
            dt = m.get("matchDateTime") or ""
            utc = dt + ("Z" if dt and "Z" not in dt else "")
        out.append({
            "status": "FINISHED" if (finished and gh is not None) else "TIMED",
            "utcDate": utc,
            "homeTeam": {"name": _name(m.get("team1")), "shortName": _name(m.get("team1"))},
            "awayTeam": {"name": _name(m.get("team2")), "shortName": _name(m.get("team2"))},
            "score": {"fullTime": {"home": gh, "away": ga}},
        })
    return out


def fetch_bl2(season=None):
    season = season or current_season()
    r = requests.get(f"{BASE}/getmatchdata/bl2/{season}", timeout=30)
    r.raise_for_status()
    return to_fdorg(r.json())
