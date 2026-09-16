"""Poisson / Dixon-Coles Tormodell."""
import math

RHO = -0.13   # Dixon-Coles-Korrektur für knappe Ergebnisse
MAXG = 8      # betrachtete Tore je Team (0..8)


def poisson(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def _tau(x, y, lh, la):
    if x == 0 and y == 0:
        return 1 - lh * la * RHO
    if x == 0 and y == 1:
        return 1 + lh * RHO
    if x == 1 and y == 0:
        return 1 + la * RHO
    if x == 1 and y == 1:
        return 1 - RHO
    return 1.0


def score_matrix(lh, la):
    m = [[0.0] * (MAXG + 1) for _ in range(MAXG + 1)]
    tot = 0.0
    for i in range(MAXG + 1):
        for j in range(MAXG + 1):
            p = poisson(i, lh) * poisson(j, la) * _tau(i, j, lh, la)
            m[i][j] = p
            tot += p
    for i in range(MAXG + 1):
        for j in range(MAXG + 1):
            m[i][j] /= tot
    return m


def markets(lh, la):
    """Aus erwarteten Toren (lambda) alle Marktwahrscheinlichkeiten ableiten."""
    m = score_matrix(lh, la)
    ph = pd = pa = btts = 0.0
    over = {1.5: 0.0, 2.5: 0.0, 3.5: 0.0}
    scores = []
    for i in range(MAXG + 1):
        for j in range(MAXG + 1):
            p = m[i][j]
            if i > j:
                ph += p
            elif i == j:
                pd += p
            else:
                pa += p
            if i >= 1 and j >= 1:
                btts += p
            for t in over:
                if i + j > t:
                    over[t] += p
            scores.append((f"{i}:{j}", p))
    scores.sort(key=lambda x: -x[1])
    return {"lh": lh, "la": la, "home": ph, "draw": pd, "away": pa,
            "btts": btts, "over": over, "matrix": m, "top": scores[:5]}


def predict(home, away, strengths, avg_home, avg_away):
    """Liga-internes Modell: beide Teams aus derselben Liga."""
    ref = strengths["_ref"]
    h, a = strengths[home], strengths[away]
    lh = (h["gf"] / ref) * (a["ga"] / ref) * avg_home
    la = (a["gf"] / ref) * (h["ga"] / ref) * avg_away
    return markets(lh, la)


def best_tip(pr):
    c = [
        ("Über 2.5", pr["over"][2.5]), ("Unter 2.5", 1 - pr["over"][2.5]),
        ("BTTS Ja", pr["btts"]), ("BTTS Nein", 1 - pr["btts"]),
        ("Heimsieg", pr["home"]), ("Remis", pr["draw"]), ("Auswärtssieg", pr["away"]),
    ]
    return max(c, key=lambda x: x[1])
