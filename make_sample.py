"""Erzeugt sample_matches.json: {"leagues": {name: fd.org-Spiele}, "cl_fixtures":[...]}."""
import json, math, random, datetime, itertools
random.seed(7)

TRUE = {
 "Premier League":{"Man City":(2.35,.95),"Arsenal":(2.05,.80),"Liverpool":(2.25,1.05),"Chelsea":(1.85,1.15),
       "Tottenham":(1.95,1.35),"Man United":(1.55,1.30),"Newcastle":(1.80,1.20),"Brighton":(1.60,1.30)},
 "La Liga":{"Real Madrid":(2.15,.90),"Barcelona":(2.45,1.05),"Atlético":(1.75,.85),"Athletic":(1.55,1.00),
       "Villarreal":(1.70,1.35),"Real Sociedad":(1.40,1.15),"Betis":(1.45,1.30),"Sevilla":(1.25,1.30)},
 "Bundesliga":{"Bayern":(2.75,1.00),"Leverkusen":(2.20,1.05),"Stuttgart":(1.95,1.40),"RB Leipzig":(1.90,1.15),
        "Dortmund":(2.00,1.35),"Frankfurt":(1.85,1.45),"Freiburg":(1.45,1.45),"Bremen":(1.45,1.60)},
 "Serie A":{"Inter":(2.20,.85),"Napoli":(1.75,.95),"Juventus":(1.55,.90),"Milan":(1.80,1.20),
       "Atalanta":(2.10,1.15),"Roma":(1.65,1.10),"Lazio":(1.55,1.10),"Fiorentina":(1.60,1.25)},
 "Ligue 1":{"Paris SG":(2.55,.85),"Monaco":(1.95,1.20),"Marseille":(1.90,1.20),"Lille":(1.70,1.05),
        "Lyon":(1.65,1.25),"Nice":(1.45,1.05),"Lens":(1.50,1.20),"Rennes":(1.55,1.45)},
 "2. Bundesliga":{"Schalke 04":(1.70,1.20),"Hertha BSC":(1.55,1.25),"F. Düsseldorf":(1.60,1.15),
        "Hannover 96":(1.45,1.20),"Kaiserslautern":(1.50,1.35),"1. FC Nürnberg":(1.40,1.30),
        "Karlsruher SC":(1.35,1.25),"SC Paderborn":(1.55,1.40),"Darmstadt 98":(1.45,1.35),
        "Greuther Fürth":(1.30,1.45)},
}

def pois(l):
    L=math.exp(-l); k=0; p=1.0
    while True:
        k+=1; p*=random.random()
        if p<=L: return k-1

def team_obj(n): return {"name":n,"shortName":n,"tla":n[:3].upper()}

now=datetime.datetime.now(datetime.timezone.utc)
leagues={}
for name,teams in TRUE.items():
    tn=list(teams); ms=[]
    pairs=list(itertools.permutations(tn,2)); random.shuffle(pairs)
    for day,(h,a) in enumerate(pairs[:30]):
        lh=teams[h][0]*teams[a][1]/1.35*1.10
        la=teams[a][0]*teams[h][1]/1.35*0.90
        d=now-datetime.timedelta(days=72-day*2, hours=random.randint(0,6))
        ms.append({"status":"FINISHED","utcDate":d.strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "homeTeam":team_obj(h),"awayTeam":team_obj(a),
                   "score":{"fullTime":{"home":pois(lh),"away":pois(la)}}})
    up=list(itertools.permutations(tn,2)); random.shuffle(up)
    for k,(h,a) in enumerate(up[:4]):
        d=now+datetime.timedelta(days=2+k, hours=random.choice([13,15,17,18]))
        ms.append({"status":"TIMED","utcDate":d.strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "homeTeam":team_obj(h),"awayTeam":team_obj(a),
                   "score":{"fullTime":{"home":None,"away":None}}})
    leagues[name]=ms

# CL-Spielplan: ligaübergreifende Paarungen aus den Beispiel-Ligen,
# plus zwei "fremde" Teams (Ajax/Benfica) zum Zeigen von "keine Prognose".
cl_pairs=[("Man City","Real Madrid"),("Bayern","Inter"),("Paris SG","Arsenal"),
          ("Barcelona","Dortmund"),("Liverpool","Milan"),("Atlético","Leverkusen"),
          ("Napoli","Monaco"),("Ajax","Villarreal"),("Benfica","Marseille")]
cl_fixtures=[]
for k,(h,a) in enumerate(cl_pairs):
    d=now+datetime.timedelta(days=3+k//3, hours=random.choice([18,20,21]))
    cl_fixtures.append({"home":h,"away":a,"home_id":None,"away_id":None,
                        "date":d.astimezone().strftime("%a %d.%m."),
                        "time":d.astimezone().strftime("%H:%M")})

json.dump({"leagues":leagues,"cl_fixtures":cl_fixtures},
          open("sample_matches.json","w",encoding="utf-8"),ensure_ascii=False)
print("sample_matches.json:", sum(len(v) for v in leagues.values()), "Ligaspiele,",
      len(leagues), "Ligen,", len(cl_fixtures), "CL-Spiele")
