"""Daten von football-data.org holen (kostenloser Tarif)."""
import time
import requests

BASE = "https://api.football-data.org/v4"

# Wettbewerbs-Codes der Top-5-Ligen bei football-data.org
COMPS = {
    "PL": "Premier League",
    "PD": "La Liga",
    "BL1": "Bundesliga",
    "SA": "Serie A",
    "FL1": "Ligue 1",
}


def fetch_matches(code, key):
    """Alle Spiele der aktuellen Saison eines Wettbewerbs (ein Aufruf)."""
    r = requests.get(
        f"{BASE}/competitions/{code}/matches",
        headers={"X-Auth-Token": key},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("matches", [])


def fetch_all(key, comps=COMPS, pause=7.0):
    """Ein Aufruf pro Liga (5 gesamt) mit Pause wegen 10-Anfragen/Minute-Limit."""
    out = {}
    for i, code in enumerate(comps):
        print(f"  … lade {comps[code]} ({code})")
        out[code] = fetch_matches(code, key)
        if i < len(comps) - 1:
            time.sleep(pause)
    return out
