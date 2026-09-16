"""Erzeugt ein eigenständiges HTML-Dashboard (keine Server nötig)."""
import html

C = dict(ink="#0E1420", panel="#161E2E", panel2="#1B2438", line="#28324a",
         amber="#E8B23A", teal="#3FB8AF", text="#E6EAF2", dim="#8593AD")
MONO = "ui-monospace,'SF Mono','Cascadia Mono',Menlo,Consolas,monospace"
SANS = "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"


def pct(p):
    return round(p * 100)


def odds(p):
    return f"{1/p:.2f}" if p > 0 else "–"


def _mix(a, b, t):
    return [round(a[i] + (b[i] - a[i]) * t) for i in range(3)]


def heat(p):
    t = max(0.0, min(1.0, (p - 0.32) / 0.5))
    bg = _mix([30, 40, 60], [232, 178, 58], t)
    return f"rgb({bg[0]},{bg[1]},{bg[2]})", (C["ink"] if p > 0.6 else C["text"])


def _cell(p):
    bg, fg = heat(p)
    return (f'<td style="padding:6px 8px;text-align:right;font-family:{MONO};font-size:13px">'
            f'<span style="background:{bg};color:{fg};padding:3px 7px;border-radius:5px;'
            f'display:inline-block;min-width:40px;font-weight:600">{pct(p)}%</span></td>')


def _matrix(pr, h, a):
    mx = max(max(r) for r in pr["matrix"])
    N = 6
    head = "".join(f'<td style="color:{C["dim"]};text-align:center;padding:3px;width:26px">{j}</td>' for j in range(N))
    rows = f'<tr><td></td>{head}</tr>'
    for i in range(N):
        cells = ""
        for j in range(N):
            p = pr["matrix"][i][j]
            t = min(1.0, p / mx) if mx else 0
            rgb = _mix([30, 40, 60], [63, 184, 175], t)
            fg = C["ink"] if t > 0.6 else C["text"]
            cells += (f'<td title="{i}:{j} — {p*100:.1f}%" style="background:rgb({rgb[0]},{rgb[1]},'
                      f'{rgb[2]});text-align:center;padding:3px;color:{fg};border:1px solid {C["ink"]}">{round(p*100)}</td>')
        rows += f'<tr><td style="color:{C["dim"]};padding:3px">{i}</td>{cells}</tr>'
    return (f'<div style="color:{C["dim"]};font-size:11px;margin-bottom:6px;font-family:{MONO}">'
            f'Ergebnis-Matrix · Zeile = {html.escape(h)}, Spalte = {html.escape(a)}</div>'
            f'<table style="border-collapse:collapse;font-family:{MONO};font-size:11px"><tbody>{rows}</tbody></table>')


def _line(label, p):
    return (f'<div style="display:flex;justify-content:space-between;gap:16px;padding:3px 0">'
            f'<span style="color:{C["dim"]}">{html.escape(label)}</span>'
            f'<span style="font-family:{MONO}"><span style="color:{C["text"]};font-weight:600">{pct(p)}%</span>'
            f'<span style="color:{C["teal"]};margin-left:10px">@ {odds(p)}</span></span></div>')


def _detail(pr, f):
    tore = "".join([_line("Über 1.5", pr["over"][1.5]), _line("Über 2.5", pr["over"][2.5]),
                    _line("Über 3.5", pr["over"][3.5]), _line("Unter 2.5", 1 - pr["over"][2.5]),
                    _line("BTTS Ja", pr["btts"]), _line("BTTS Nein", 1 - pr["btts"])])
    ausgang = "".join([_line(f'{f["home"]} (Heim)', pr["home"]), _line("Unentschieden", pr["draw"]),
                       _line(f'{f["away"]} (Ausw.)', pr["away"])])
    tops = "".join(f'<div style="display:flex;justify-content:space-between"><span style="color:{C["dim"]};'
                   f'font-family:{MONO}">{s}</span><span style="font-family:{MONO}">{pct(p)}%</span></div>'
                   for s, p in pr["top"])
    lam = (f'<div style="color:{C["dim"]};font-size:11px;margin-top:8px;font-family:{MONO}">'
           f'erw. Tore (λ): {html.escape(f["home"])} {pr["lh"]:.2f} · {html.escape(f["away"])} {pr["la"]:.2f}</div>')
    hd = lambda s: f'<div style="color:{C["amber"]};font-weight:700;margin-bottom:6px">{s}</div>'
    return (f'<tr class="detail" style="display:none"><td colspan="8" style="background:{C["panel2"]};'
            f'padding:16px;border-top:1px solid {C["line"]}"><div style="display:flex;flex-wrap:wrap;gap:28px">'
            f'<div style="min-width:220px;font-size:13px">{hd("Tore-Märkte")}{tore}</div>'
            f'<div style="min-width:200px;font-size:13px">{hd("Spielausgang")}{ausgang}'
            f'<div style="margin-top:12px">{hd("Wahrsch. Ergebnisse")}{tops}</div></div>'
            f'<div>{_matrix(pr, f["home"], f["away"])}{lam}</div></div></td></tr>')


def render_html(results, generated_at):
    from model import best_tip
    tabs = "".join(
        f'<button class="lg" data-lg="{html.escape(name)}" onclick="filt(this)" '
        f'style="background:transparent;color:{C["dim"]};border:1px solid {C["line"]};'
        f'border-radius:20px;padding:4px 12px;font-size:12px;cursor:pointer">{html.escape(name)}</button>'
        for name in ["Alle"] + [r["league"] for r in results])

    body = ""
    for res in results:
        for row in res["rows"]:
            f, pr = row["f"], row["pr"]
            if pr is None:
                note = row.get("note", "keine Prognose")
                body += (
                    f'<tr class="game" data-lg="{html.escape(res["league"])}" '
                    f'style="border-top:1px solid {C["line"]};opacity:.6">'
                    f'<td style="padding:8px 10px;color:{C["dim"]};font-size:12px;font-family:{MONO};white-space:nowrap">{f["date"]} {f["time"]}</td>'
                    f'<td style="padding:8px 10px;font-size:13px;white-space:nowrap"><span style="font-weight:600">{html.escape(f["home"])}</span>'
                    f'<span style="color:{C["dim"]};margin:0 6px">–</span><span style="font-weight:600">{html.escape(f["away"])}</span>'
                    f'<div style="color:{C["dim"]};font-size:10px;font-family:{MONO}">{html.escape(res["league"])}</div></td>'
                    f'<td colspan="6" style="padding:8px 10px;color:{C["dim"]};font-size:12px;font-style:italic">— {html.escape(note)}</td></tr>')
                continue
            tip = best_tip(pr)
            body += (
                f'<tr class="game" data-lg="{html.escape(res["league"])}" onclick="tog(this)" '
                f'style="cursor:pointer;border-top:1px solid {C["line"]}">'
                f'<td style="padding:8px 10px;color:{C["dim"]};font-size:12px;font-family:{MONO};white-space:nowrap">{f["date"]} {f["time"]}</td>'
                f'<td style="padding:8px 10px;font-size:13px;white-space:nowrap"><span style="font-weight:600">{html.escape(f["home"])}</span>'
                f'<span style="color:{C["dim"]};margin:0 6px">–</span><span style="font-weight:600">{html.escape(f["away"])}</span>'
                f'<div style="color:{C["dim"]};font-size:10px;font-family:{MONO}">{html.escape(res["league"])}</div></td>'
                f'{_cell(pr["home"])}{_cell(pr["draw"])}{_cell(pr["away"])}{_cell(pr["over"][2.5])}{_cell(pr["btts"])}'
                f'<td style="padding:8px 10px;white-space:nowrap"><span style="color:{C["teal"]};font-weight:700;font-size:13px">{tip[0]}</span>'
                f'<span style="color:{C["dim"]};font-family:{MONO};font-size:12px;margin-left:8px">{pct(tip[1])}% · @{odds(tip[1])}</span></td></tr>')
            body += _detail(pr, f)

    th = ("Anstoß", "Begegnung", "1", "X", "2", "Ü 2.5", "BTTS", "Tipp")
    heads = "".join(
        f'<th style="text-align:{"left" if i < 2 or i == 7 else "right"};padding:8px 10px;font-weight:600">{t}</th>'
        for i, t in enumerate(th))

    return f"""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Mein Tipp-Dashboard</title>
<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="{C['ink']}">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="Tipp">
<link rel="apple-touch-icon" href="icons/icon-180.png">
<style>
@media (max-width:640px){{
  h1{{font-size:21px!important}}
  table{{min-width:560px!important}}
  th,td{{padding:6px 6px!important;font-size:12px!important}}
}}
</style>
</head>
<body style="margin:0;background:{C['ink']};color:{C['text']};font-family:{SANS}">
<div style="max-width:980px;margin:0 auto;padding:22px 18px">
  <div style="display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:10px">
    <h1 style="font-size:26px;font-weight:800;letter-spacing:-.5px;margin:0">Mein Tipp-Dashboard</h1>
    <span style="color:{C['dim']};font-size:12px;font-family:{MONO}">Poisson · Dixon-Coles · Top-5 · 2. BL · CL</span>
  </div>
  <p style="color:{C['dim']};font-size:13px;margin:6px 0 0;max-width:640px">
    football-data.org &amp; OpenLigaDB · form-gewichtete Stärken · CL ligaübergreifend · Stand: {generated_at}. Zeile anklicken für Details.</p>
  <div style="display:flex;gap:6px;flex-wrap:wrap;margin:16px 0 12px">{tabs}</div>
  <div style="overflow-x:auto;border:1px solid {C['line']};border-radius:10px">
    <table style="width:100%;border-collapse:collapse;min-width:720px">
      <thead><tr style="background:{C['panel']};color:{C['dim']};font-size:11px">{heads}</tr></thead>
      <tbody id="tb">{body}</tbody>
    </table>
  </div>
  <div style="display:flex;gap:18px;margin-top:12px;flex-wrap:wrap;color:{C['dim']};font-size:11px">
    <span>1 / X / 2 = Heim / Remis / Auswärts</span><span>Ü 2.5 = über 2,5 Tore</span>
    <span>BTTS = beide treffen</span><span style="color:{C['teal']}">@ = faire Quote (1 / Wahrscheinlichkeit)</span>
  </div>
</div>
<script>
function tog(r){{var d=r.nextElementSibling;if(d&&d.classList.contains('detail'))d.style.display=d.style.display==='none'?'':'none';}}
function filt(b){{var lg=b.dataset.lg;document.querySelectorAll('.lg').forEach(function(x){{x.style.background='transparent';x.style.color='{C['dim']}';x.style.borderColor='{C['line']}';}});
b.style.background='{C['panel2']}';b.style.color='{C['text']}';b.style.borderColor='{C['teal']}';
document.querySelectorAll('.game').forEach(function(g){{var show=(lg==='Alle'||g.dataset.lg===lg);g.style.display=show?'':'none';var d=g.nextElementSibling;if(d&&d.classList.contains('detail'))d.style.display='none';}});}}
if('serviceWorker' in navigator && location.protocol.indexOf('http')===0){{
  window.addEventListener('load',function(){{navigator.serviceWorker.register('sw.js').catch(function(){{}});}});
}}
</script></body></html>"""
