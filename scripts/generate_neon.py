#!/usr/bin/env python3
"""Generate the neon terminal profile card (profile-neon.svg).

Runs daily in GitHub Actions: pulls the public contribution calendar and
profile stats for USER, then redraws the SVG. The portrait is a pixel grid
(levels 0-5) generated from a photo and stored below as text.
"""
import datetime as dt
import json
import os
import re
import urllib.request

USER = os.environ.get("GH_USER", "Rakshitha-L-V-04")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.environ.get("OUT_FILE", "profile-neon.svg")

PORTRAIT = """
000000000000000000000054333300000000000000000000000000000000
000000000000000000004333322223334400000000000000000000000000
000000000000000000533333333322223334000000000000000000000000
000000000000000004333333332222222332340000000000000000000000
000000000000000033333232222221111222224000000000000000000000
000000000000000322232222222222222222222300000000000000000000
000000000000003222222112222222222222212230000000000000000000
000000000000032222221122222223333232211224000000000000000000
000000000000412222211222222344433322222223000000000000000000
000000000000222222211222223444443332222222300000000000000000
000000000003122222222233334444444332222212340000000000000000
000000000041222222222333344544444432222211235000000000000000
000000000031221222222333444444444443222211224000000000000000
000000000522211222223334444444544444322111223500000000000000
000000000422211222223334444445444444432111222400000000000000
000000000322211221123344444444444444443211222340000000000000
000000005222111111123344444444443323334311122240000000000000
000000004222111111123444444444332333333311122230000000000000
000000003222111111123433334444333333334421112234000000000000
000000003221111111222222223344332222234431112224000000000000
000000042121111111222233222345432223344442122223500000000000
000000542111111111122222223345444333455543121223400000000000
000005432111111111111112333345544444555543112222450000000000
000005332111111111111223344445544555555553112222350000000000
000054331111111111112333444445544455555544212222335000000000
000043421211111111123454444345555444444444211222333000000000
000533311111111111123455554444554433444444211122233450000050
000433111111111111124455443444443343333344211122233345555555
004323111111111111124444433222333454333444311122223334444444
044332111111111111123444334332234433334444321111223333444444
543333211111111111123333334433233332344444111111123333344444
533333211112221111122233333222344444444443111121123334344444
434343211122221122122233332233444444444332111112112443444444
444443321122211111112333433333333344444331111111212334444444
444443211211111111112233443333333444444431111111112334444555
444332211111111111111222334333444455444311111111112334544555
443221111111111111111222223444444455443211112111112334545455
443112112222111111111122333334444444433211121111111334545455
432222222221111111111112223233344333322211121111112344445555
322232222111111111111111122222233322223211111111111244455555
333222221111111111111111112222222222232211111111111233455555
343322211111111111111112221122222222332221112111122222245555
343222211111111111111112222222222233332221212211222212345555
344222111111111111111112222322233333332222212211122112355555
344212222111111111111112233333333333332211111211111232244555
443122222111111111111111233333333333332221111122212121233555
541232221321111111111111223333333333332222111122221111122345
541233211211111111111111233333333333332322112222211111122234
552122111111111111111112223333333333333321211111111111121133
343321121111111111111111123334444444433321121112121112212233
333233222211122212111111122333444444434311121112122112212234
344333332211112212111111222122234444444211211122212222222333
444443333211112221111121122233332454443211211222222222222344
444444333221111221111112112344444245432222211232222222222334
444444333221111122211111212333445335421122221233222222223444
444444433221111111221111221233445234322212111233332222323345
444444433222211111111111222223333234333112211333333332334445
444444433222221111111111122332233345333212212333333333334555
344444433222221111211122223433234445333322213333333333454555
444444433222221111111222223444334554433322123333333333345555
""".strip().split("\n")

GREEN = ["#0b1a0e", "#0f5323", "#1a9e3a", "#2fe05a", "#8dff7a"]
PIX = [None, "#0f3c19", "#1a7832", "#2fbe50", "#6eff6e", "#beffb4"]


def http_get(url, accept="text/html"):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-neon", "Accept": accept})
    if TOKEN and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def contributions():
    html = http_get(f"https://github.com/users/{USER}/contributions")
    days = {}
    for m in re.finditer(r'<td[^>]*class="ContributionCalendar-day"[^>]*>', html):
        tag = m.group(0)
        date = re.search(r'data-date="([\d-]+)"', tag)
        level = re.search(r'data-level="(\d)"', tag)
        cid = re.search(r'id="([^"]+)"', tag)
        if date and level:
            days[date.group(1)] = {"level": int(level.group(1)), "id": cid.group(1) if cid else "", "count": 0}
    counts = {}
    for m in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        n = re.match(r"\s*(\d+) contribution", m.group(2))
        counts[m.group(1)] = int(n.group(1)) if n else 0
    for d in days.values():
        d["count"] = counts.get(d["id"], 0)
    total = re.search(r"([\d,]+)\s+contributions?\s+in the last year", html)
    total = int(total.group(1).replace(",", "")) if total else sum(d["count"] for d in days.values())
    return dict(sorted(days.items())), total


def streaks(days):
    dates = sorted(days)
    longest = run = 0
    for d in dates:
        run = run + 1 if days[d]["count"] > 0 or days[d]["level"] > 0 else 0
        longest = max(longest, run)
    current = 0
    for i, d in enumerate(reversed(dates)):
        active = days[d]["count"] > 0 or days[d]["level"] > 0
        if active:
            current += 1
        elif i == 0:
            continue  # today may not have activity yet
        else:
            break
    return current, longest


def profile_stats():
    try:
        u = json.loads(http_get(f"https://api.github.com/users/{USER}", "application/vnd.github+json"))
        return u.get("public_repos", 0), u.get("followers", 0)
    except Exception:
        return None, None


def typed(o, cid, x, y, w, h, t0, t1, dur=14):
    """Clip rect that 'types' text in between t0..t1 seconds, looping every dur seconds."""
    k0, k1 = t0 / dur, t1 / dur
    o.append(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}">'
             f'<animate attributeName="width" values="0;0;{w};{w}" keyTimes="0;{k0:.3f};{k1:.3f};1" '
             f'dur="{dur}s" repeatCount="indefinite" calcMode="discrete"/></rect></clipPath>')
    return f'clip-path="url(#{cid})"'


def typed_smooth(o, cid, x, y, w, h, t0, t1, dur=14, steps=None):
    k0, k1 = t0 / dur, t1 / dur
    n = steps or 24
    vals = ["0"] + [f"{w * i / n:.1f}" for i in range(n + 1)] + [f"{w}"]
    keys = [0] + [k0 + (k1 - k0) * i / n for i in range(n + 1)] + [1]
    o.append(f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}">'
             f'<animate attributeName="width" values="{";".join(vals)}" keyTimes="{";".join(f"{k:.4f}" for k in keys)}" '
             f'dur="{dur}s" repeatCount="indefinite" calcMode="discrete"/></rect></clipPath>')
    return f'clip-path="url(#{cid})"'


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(days, total, repos, followers, now):
    W, H = 1000, 720
    o = []
    a = o.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
      f'font-family="\'JetBrains Mono\',\'Fira Code\',Consolas,\'DejaVu Sans Mono\',monospace">')
    a("""<defs>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="2" fill="#000" opacity="0.18"/></pattern>
<linearGradient id="roll" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#39ff14" stop-opacity="0"/><stop offset=".5" stop-color="#39ff14" stop-opacity=".06"/><stop offset="1" stop-color="#39ff14" stop-opacity="0"/></linearGradient>
<radialGradient id="vig" cx="50%" cy="45%" r="75%"><stop offset="60%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#000" stop-opacity="0.55"/></radialGradient>
</defs>
<style>
.t{fill:#39ff14}.d{fill:#1f7a2e}.m{fill:#8dff7a}.w{fill:#d8ffd0}
.blink{animation:b 1.1s steps(1) infinite}@keyframes b{50%{opacity:0}}
.pulse{animation:p 3s ease-in-out infinite}@keyframes p{50%{opacity:.55}}
.boot{animation:f .9s ease-out both}@keyframes f{from{opacity:0}to{opacity:1}}
.wave{opacity:0;animation:wv 5s linear infinite}@keyframes wv{0%{opacity:0}4%{opacity:.55}14%{opacity:0}100%{opacity:0}}
.fl{animation:fl 2.4s steps(2) infinite}@keyframes fl{0%,70%{opacity:1}75%{opacity:.15}80%{opacity:1}90%{opacity:.4}}
.gl{animation:gl 7s steps(1) infinite}@keyframes gl{0%,93%,100%{transform:translate(0,0)}94%{transform:translate(3px,0)}96%{transform:translate(-2px,0)}98%{transform:translate(1px,0)}}
</style>""")
    a(f'<rect width="{W}" height="{H}" rx="18" fill="#030803"/>')
    a(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="none" stroke="#0f3d18" stroke-width="2"/>')

    # ---- panel 1: contribution heatmap ----
    a('<rect x="24" y="22" width="952" height="250" rx="12" fill="#050d06" stroke="#123f1b"/>')
    a('<g font-size="13">')
    a('<circle cx="46" cy="42" r="5" fill="#ff5f56"/><circle cx="64" cy="42" r="5" fill="#ffbd2e"/><circle cx="82" cy="42" r="5" fill="#27c93f"/>')
    a(f'<text x="104" y="46" class="d">~/{esc(USER)} $ ./contributions --last-year</text>')
    a(f'<text x="952" y="46" class="d" text-anchor="end">synced {now:%Y-%m-%d %H:%M} UTC</text>')
    a('</g>')
    clip = typed_smooth(o, "ty-head", 44, 60, 520, 34, 0.2, 1.8, steps=30)
    a(f'<text x="48" y="84" font-size="22" font-weight="700" class="t" filter="url(#soft)" {clip}>{total:,} contributions in the last year</text>')

    dates = list(days)
    if dates:
        start = dt.date.fromisoformat(dates[0])
        start -= dt.timedelta(days=(start.weekday() + 1) % 7)
    else:
        start = now.date() - dt.timedelta(days=364)
    cell, gap, x0, y0 = 13, 4, 48, 118
    months = {}
    for ds, info in days.items():
        d = dt.date.fromisoformat(ds)
        col = (d - start).days // 7
        row = (d.weekday() + 1) % 7
        x, y = x0 + col * (cell + gap), y0 + row * (cell + gap)
        lv = info["level"]
        f = ' filter="url(#glow)"' if lv >= 3 else ""
        title = f'{info["count"]} on {ds}'
        a(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{GREEN[lv]}"{f}><title>{title}</title></rect>')
        if d.day <= 7 and row == 0:
            months[col] = d.strftime("%b")
    ncols = max(((dt.date.fromisoformat(ds) - start).days // 7 for ds in days), default=52) + 1
    for col in range(ncols):
        x = x0 + col * (cell + gap) - 1
        a(f'<rect class="wave" x="{x}" y="{y0 - 1}" width="{cell + 2}" height="{7 * (cell + gap) - gap + 2}" rx="3" '
          f'fill="#39ff14" style="animation-delay:{col * 0.06:.2f}s" filter="url(#glow)"/>')
    for col, name in months.items():
        a(f'<text x="{x0 + col * (cell + gap)}" y="{y0 - 10}" font-size="11" class="d">{name}</text>')
    cur, best = streaks(days)
    ly = y0 + 7 * (cell + gap) + 18
    a(f'<text x="48" y="{ly}" font-size="12" class="d">&gt; github activity heatmap // contribution stream <tspan class="t pulse">online</tspan></text>')
    lx = 952 - 5 * (cell + 3) - 40
    a(f'<text x="{lx - 8}" y="{ly}" font-size="11" class="d" text-anchor="end">less</text>')
    for i, c in enumerate(GREEN):
        a(f'<rect x="{lx + i * (cell + 3)}" y="{ly - 11}" width="{cell}" height="{cell}" rx="2.5" fill="{c}"/>')
    a(f'<text x="952" y="{ly}" font-size="11" class="d" text-anchor="end">more</text>')

    # ---- panel 2: profile ----
    a('<rect x="24" y="290" width="952" height="400" rx="12" fill="#050d06" stroke="#123f1b"/>')
    a('<g class="boot">')
    a('<text x="48" y="326" font-size="12" class="d">&gt; PROFILE BOOT SEQUENCE ............................. [ OK ]</text>')
    c1 = typed_smooth(o, "ty-n1", 40, 340, 300, 56, 1.8, 3.0, steps=9)
    c2 = typed_smooth(o, "ty-n2", 40, 398, 380, 30, 3.0, 4.2, steps=22)
    a(f'<g class="gl"><text x="48" y="384" font-size="44" font-weight="800" class="t" filter="url(#glow)" letter-spacing="2" {c1}>RAKSHITHA</text></g>')
    a(f'<text x="48" y="420" font-size="22" font-weight="700" class="m" letter-spacing="1.5" {c2}>LAKSHMIKANTH VANISHREE</text>')
    tags = ["GenAI", "RAG", "AI Agents", "Python", "LLMs"]
    tx = 48
    for tg in tags:
        w = 16 + len(tg) * 8.6
        a(f'<rect x="{tx}" y="438" width="{w:.0f}" height="24" rx="4" fill="#0b2a12" stroke="#2fe05a"/>')
        a(f'<text x="{tx + w/2:.0f}" y="455" font-size="13" class="t" text-anchor="middle">{tg}</text>')
        tx += w + 10
    lines = [
        ("role", "M.Sc. Computer Science @ RPTU Kaiserslautern-Landau"),
        ("exp ", "4+ yrs Application Software Developer @ Enverus"),
        ("now ", "RAG, GraphRAG, agentic workflows, LLM evaluation"),
        ("lang", "English (C1) · Deutsch (A2)"),
        ("seek", "Werkstudent / HiWi · software, AI/ML, data"),
    ]
    for i, (k, v) in enumerate(lines):
        y = 494 + i * 24
        cl = typed_smooth(o, f"ty-l{i}", 44, y - 16, 560, 22, 4.6 + i * 1.0, 5.4 + i * 1.0, steps=20)
        a(f'<text x="48" y="{y}" font-size="14" {cl}><tspan class="d">$ {k.strip()}</tspan><tspan x="112" class="d">→</tspan><tspan x="134" class="w">{esc(v)}</tspan></text>')
    stats = [("repos", repos), ("followers", followers), ("streak", f"{cur}d"), ("best", f"{best}d")]
    sx = 48
    for k, v in stats:
        if v is None:
            continue
        a(f'<text x="{sx}" y="636" font-size="13"><tspan class="d">{k}:</tspan> <tspan class="t" font-weight="700">{v}</tspan></text>')
        sx += 30 + (len(k) + len(str(v))) * 8.4
    a(f'<text x="48" y="666" font-size="13" class="d">~/rakshitha $ <tspan class="t">contact --linkedin --github</tspan><tspan class="t blink" dx="6">█</tspan></text>')
    a('</g>')

    # portrait
    px, py, ps = 676, 318, 4.4
    n = len(PORTRAIT)
    a(f'<rect x="{px - 12}" y="{py - 12}" width="{n * ps + 24:.0f}" height="{n * ps + 24:.0f}" rx="10" fill="#020602" stroke="#2fe05a" stroke-opacity=".6"/>')
    ph = n * ps
    a(f'<clipPath id="pt-reveal"><rect x="{px}" y="{py}" width="{n * ps:.1f}" height="{ph:.1f}">'
      f'<animate attributeName="height" values="0;{ph:.1f};{ph:.1f}" keyTimes="0;0.25;1" dur="14s" repeatCount="indefinite"/></rect></clipPath>')
    a('<g filter="url(#soft)" clip-path="url(#pt-reveal)">')
    for y, row in enumerate(PORTRAIT):
        x = 0
        while x < len(row):
            ch = row[x]
            if ch == "0":
                x += 1
                continue
            run = 1
            while x + run < len(row) and row[x + run] == ch:
                run += 1
            fl = ""
            if ch in "45" and (x * 7 + y * 13) % 23 == 0:
                fl = f' class="fl" style="animation-delay:{((x * 31 + y * 17) % 24) / 10:.1f}s"'
            a(f'<rect x="{px + x * ps:.1f}" y="{py + y * ps:.1f}" width="{run * ps - 0.6:.1f}" height="{ps - 0.6:.1f}" fill="{PIX[int(ch)]}"{fl}/>')
            x += run
    a('</g>')
    a(f'<rect x="{px - 4}" y="{py}" width="{n * ps + 8:.1f}" height="3" fill="#b6ff9e" opacity=".75" filter="url(#glow)">'
      f'<animate attributeName="y" values="{py};{py + ph:.1f};{py}" dur="4s" repeatCount="indefinite"/>'
      f'<animate attributeName="opacity" values=".8;.35;.8" dur="4s" repeatCount="indefinite"/></rect>')
    a(f'<text x="{px + n * ps / 2:.0f}" y="{py + n * ps + 30:.0f}" font-size="11" class="d" text-anchor="middle">portrait.svg // rendered from code</text>')

    a(f'<rect width="{W}" height="{H}" rx="18" fill="url(#scan)" pointer-events="none"/>')
    a(f'<rect x="0" y="0" width="{W}" height="70" fill="url(#roll)" pointer-events="none">'
      f'<animate attributeName="y" values="-70;{H}" dur="6s" repeatCount="indefinite"/></rect>')
    a(f'<rect width="{W}" height="{H}" rx="18" fill="url(#vig)" pointer-events="none"/>')
    a("</svg>")
    return "\n".join(o)


def main():
    days, total = contributions()
    repos, followers = profile_stats()
    svg = build(days, total, repos, followers, dt.datetime.now(dt.timezone.utc))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT}: {total} contributions, {len(days)} days")


if __name__ == "__main__":
    main()
