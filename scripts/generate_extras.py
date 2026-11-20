#!/usr/bin/env python3
"""Generate the animated extras for the profile README.

  terminal.svg          - a recruiter-facing shell session that types itself out
  rag-pipeline.svg      - animated diagram of the RAG systems built in Gen-AI
  cards/<repo>.svg      - one live card per public repo (language, stars, last commit)

Runs daily in GitHub Actions next to generate_neon.py. Live data comes from the
GitHub REST API; everything else is drawn with SVG + CSS/SMIL animation.
"""
import datetime as dt
import json
import os
import urllib.request

USER = os.environ.get("GH_USER", "Rakshitha-L-V-04")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
FONT = "'JetBrains Mono','Fira Code',Consolas,'DejaVu Sans Mono',monospace"

NEON, DIM, SOFT, WHITE, BG, PANEL, EDGE = "#39ff14", "#1f7a2e", "#8dff7a", "#d8ffd0", "#030803", "#050d06", "#123f1b"

# Short recruiter-facing pitch per repo (falls back to the GitHub description).
PITCH = {
    "Gen-AI": "RAG, GraphRAG, ReAct agents, DeepEval, LoRA/QLoRA on Mistral 7B, GPT from scratch",
    "streamlit-anomalie-inchemical-process": "Interactive Streamlit dashboard for anomalies in batch distillation sensor data",
    "kalman-filter-noisy-sensor-data": "Kalman filter estimating position and velocity from noisy sensor data, with tests",
}
TITLE = {
    "Gen-AI": "Gen-AI",
    "streamlit-anomalie-inchemical-process": "Chemical Process Anomalies",
    "kalman-filter-noisy-sensor-data": "Kalman Filter",
}
LANG_COLOR = {"Python": "#3572A5", "Jupyter Notebook": "#DA5B0B", "JavaScript": "#f1e05a",
              "TypeScript": "#3178c6", "HTML": "#e34c26", "CSS": "#563d7c"}

DEFS = f"""<defs>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.1" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="2" fill="#000" opacity="0.18"/></pattern>
</defs>
<style>
text{{white-space:pre}}.t{{fill:{NEON}}}.d{{fill:{DIM}}}.m{{fill:{SOFT}}}.w{{fill:{WHITE}}}
.blink{{animation:b 1.1s steps(1) infinite}}@keyframes b{{50%{{opacity:0}}}}
.pulse{{animation:p 2.4s ease-in-out infinite}}@keyframes p{{50%{{opacity:.35}}}}
.dash{{stroke-dasharray:6 8;animation:ds 1.2s linear infinite}}@keyframes ds{{to{{stroke-dashoffset:-28}}}}
.breathe{{animation:br 3s ease-in-out infinite}}@keyframes br{{50%{{stroke-opacity:.35}}}}
</style>"""


def http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-extras", "Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def ago(iso, now):
    if not iso:
        return "unknown"
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    s = int((now - t).total_seconds())
    for unit, n in (("y", 31536000), ("mo", 2592000), ("d", 86400), ("h", 3600), ("m", 60)):
        if s >= n:
            return f"{s // n}{unit} ago"
    return "just now"


def svg_open(w, h):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}" xml:space="preserve">',
            DEFS, f'<rect width="{w}" height="{h}" rx="16" fill="{BG}"/>',
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="16" fill="none" stroke="#0f3d18" stroke-width="2"/>']


def svg_close(o, w, h):
    o.append(f'<rect width="{w}" height="{h}" rx="16" fill="url(#scan)" pointer-events="none"/>')
    o.append("</svg>")
    return "\n".join(o)


# --------------------------------------------------------------------------- data
def load_repos():
    repos = http_json(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed")
    out = []
    for r in repos:
        if r.get("fork") or r["name"] == USER:
            continue
        commit = {}
        try:
            c = http_json(f"https://api.github.com/repos/{USER}/{r['name']}/commits?per_page=1")
            if c:
                commit = {"msg": c[0]["commit"]["message"].split("\n")[0], "date": c[0]["commit"]["committer"]["date"]}
        except Exception:
            pass
        out.append({"name": r["name"], "desc": r.get("description") or "", "lang": r.get("language") or "Code",
                    "stars": r.get("stargazers_count", 0), "forks": r.get("forks_count", 0),
                    "pushed": r.get("pushed_at"), "commit": commit})
    return out


# ----------------------------------------------------------------------- terminal
def terminal(repos, now):
    W, H, DUR = 1000, 500, 22.0
    o = svg_open(W, H)
    o.append(f'<rect x="24" y="22" width="{W-48}" height="{H-44}" rx="12" fill="{PANEL}" stroke="{EDGE}"/>')
    o.append(f'<text x="48" y="50" font-size="12" class="d">rakshitha@github: ~/recruiter-mode</text>')
    o.append(f'<text x="{W-48}" y="50" font-size="12" class="d" text-anchor="end">session live <tspan class="t pulse">●</tspan></text>')

    latest = next((r for r in repos if r["commit"]), None)
    git_line = (f'{latest["name"]}: "{latest["commit"]["msg"][:48]}" · {ago(latest["commit"]["date"], now)}'
                if latest else "no public commits yet")

    script = [
        ("cmd", "whoami"),
        ("out", "Rakshitha L V · M.Sc. Computer Science @ RPTU Kaiserslautern-Landau", "w"),
        ("cmd", "cat experience.log"),
        ("out", "[2021-06 → 2025-10]  Application Software Developer · Enverus · Bengaluru", "w"),
        ("out", "[now]                M.Sc. Computer Science · RPTU · Kaiserslautern", "w"),
        ("cmd", "ls ~/stack"),
        ("out", "python/  pytorch/  langchain/  huggingface/  neo4j/  chroma/  streamlit/", "m"),
        ("cmd", "git log -1 --author=rakshitha"),
        ("out", git_line, "w"),
        ("cmd", "./hire_me --role werkstudent"),
        ("ok", "✔ open to Werkstudent / HiWi roles in software, AI/ML and data"),
        ("ok", "✔ English C1 · Deutsch A2 · based in Kaiserslautern"),
        ("ok", "→ linkedin.com/in/rakshithalv"),
    ]
    y, t = 84, 0.4
    lh = 26
    for i, item in enumerate(script):
        kind = item[0]
        if kind == "cmd":
            text = item[1]
            dur = 0.25 + len(text) * 0.045
            w = 30 + len(text) * 9.2
            n = max(4, len(text))
            k0, k1 = t / DUR, (t + dur) / DUR
            vals = ["0"] + [f"{w * j / n:.1f}" for j in range(n + 1)] + [f"{w:.1f}"]
            keys = [0] + [k0 + (k1 - k0) * j / n for j in range(n + 1)] + [1]
            o.append(f'<clipPath id="c{i}"><rect x="66" y="{y-16}" width="{w:.1f}" height="22">'
                     f'<animate attributeName="width" values="{";".join(vals)}" keyTimes="{";".join(f"{k:.4f}" for k in keys)}" '
                     f'dur="{DUR}s" repeatCount="indefinite" calcMode="discrete"/></rect></clipPath>')
            vis = f'<animate attributeName="opacity" values="0;1;1" keyTimes="0;{k0:.4f};1" dur="{DUR}s" repeatCount="indefinite" calcMode="discrete"/>'
            o.append(f'<g opacity="1">{vis}<text x="48" y="{y}" font-size="15"><tspan class="t" font-weight="700">❯</tspan></text>'
                     f'<text x="70" y="{y}" font-size="15" class="t" clip-path="url(#c{i})">{esc(text)}</text></g>')
            t += dur + 0.35
        else:
            text, cls = (item[1], item[2]) if kind == "out" else (item[1], "t")
            k = t / DUR
            o.append(f'<text x="70" y="{y}" font-size="14" class="{cls}" opacity="1">{esc(text)}'
                     f'<animate attributeName="opacity" values="0;1;1" keyTimes="0;{k:.4f};1" dur="{DUR}s" repeatCount="indefinite" calcMode="discrete"/></text>')
            t += 0.45
        y += lh
        if kind != "cmd" and i + 1 < len(script) and script[i + 1][0] == "cmd":
            y += 6
    o.append(f'<text x="48" y="{y + 4}" font-size="15" class="t" font-weight="700">❯ <tspan class="blink">█</tspan></text>')
    return svg_close(o, W, H)


# --------------------------------------------------------------------- RAG pipeline
def rag_pipeline():
    W, H = 1000, 370
    o = svg_open(W, H)
    o.append(f'<rect x="24" y="22" width="{W-48}" height="{H-44}" rx="12" fill="{PANEL}" stroke="{EDGE}"/>')
    o.append(f'<text x="48" y="52" font-size="13" class="d">~/Gen-AI $ ./rag --explain</text>')
    o.append(f'<text x="48" y="80" font-size="20" font-weight="700" class="t" filter="url(#soft)">How I build retrieval-augmented GenAI</text>')
    nodes = [
        ("DOCS", "Docling parsing", 60),
        ("EMBED", "Hugging Face", 245),
        ("RETRIEVE", "Chroma · Neo4j", 430),
        ("LLM", "Groq · Mistral 7B", 615),
        ("ANSWER", "with references", 800),
    ]
    bw, bh, by = 140, 74, 170
    cy = by + bh / 2
    path = f"M{nodes[0][2] + bw},{cy} L{nodes[-1][2]},{cy}"
    o.append(f'<path d="{path}" stroke="{DIM}" stroke-width="2" fill="none"/>')
    o.append(f'<path d="{path}" stroke="{NEON}" stroke-width="2" fill="none" class="dash" opacity=".8"/>')
    for i, (name, sub, x) in enumerate(nodes):
        o.append(f'<rect x="{x}" y="{by}" width="{bw}" height="{bh}" rx="10" fill="#071a0b" stroke="{NEON}" class="breathe" '
                 f'style="animation-delay:{i * 0.4:.1f}s"/>')
        o.append(f'<text x="{x + bw/2}" y="{by + 32}" font-size="17" font-weight="800" class="t" text-anchor="middle" filter="url(#soft)">{name}</text>')
        o.append(f'<text x="{x + bw/2}" y="{by + 54}" font-size="12" class="m" text-anchor="middle">{esc(sub)}</text>')
    # data packets
    for k in range(4):
        o.append(f'<circle r="5" fill="#b6ff9e" filter="url(#glow)"><animateMotion dur="4s" begin="{k}s" repeatCount="indefinite" path="{path}"/>'
                 f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.08;.9;1" dur="4s" begin="{k}s" repeatCount="indefinite"/></circle>')
    # user query into retrieval
    qx = nodes[2][2] + bw / 2
    qpath = f"M{qx},{by - 50} L{qx},{by}"
    o.append(f'<text x="{qx + 10}" y="{by - 36}" font-size="12" class="w">user query</text>')
    o.append(f'<path d="{qpath}" stroke="{NEON}" stroke-width="2" class="dash" fill="none"/>')
    o.append(f'<circle r="4" fill="{WHITE}" filter="url(#glow)"><animateMotion dur="2s" repeatCount="indefinite" path="{qpath}"/></circle>')
    # evaluation loop
    ex1, ex2 = nodes[-1][2] + bw / 2, nodes[3][2] + bw / 2
    epath = f"M{ex1},{by + bh} C{ex1},{by + bh + 60} {ex2},{by + bh + 60} {ex2},{by + bh}"
    o.append(f'<path d="{epath}" stroke="{SOFT}" stroke-width="1.6" fill="none" class="dash" opacity=".7"/>')
    o.append(f'<circle r="4" fill="{SOFT}" filter="url(#glow)"><animateMotion dur="3s" repeatCount="indefinite" path="{epath}"/></circle>')
    o.append(f'<text x="{(ex1 + ex2) / 2}" y="{by + bh + 66}" font-size="12" class="m" text-anchor="middle">DeepEval: faithfulness · relevancy · hallucination</text>')
    o.append(f'<text x="48" y="{H - 34}" font-size="12" class="d">also in repo: ReAct tool-calling agents · LoRA / QLoRA fine-tuning · character-level GPT from scratch</text>')
    return svg_close(o, W, H)


# ------------------------------------------------------------------- project cards
def card(repo, now):
    W, H = 480, 190
    o = svg_open(W, H)
    title = TITLE.get(repo["name"], repo["name"])
    pitch = PITCH.get(repo["name"], repo["desc"]) or "Project repository"
    fresh = repo["pushed"] and (now - dt.datetime.fromisoformat(repo["pushed"].replace("Z", "+00:00"))).days < 14
    o.append(f'<text x="24" y="40" font-size="12" class="d">~/{esc(repo["name"][:40])}</text>')
    if fresh:
        o.append(f'<rect x="{W-86}" y="25" width="62" height="20" rx="4" fill="#0b2a12" stroke="{NEON}"/>'
                 f'<text x="{W-55}" y="39" font-size="11" class="t" text-anchor="middle"><tspan class="pulse">●</tspan> ACTIVE</text>')
    o.append(f'<text x="24" y="74" font-size="22" font-weight="800" class="t" filter="url(#soft)">{esc(title)}</text>')
    # wrap pitch into two lines
    words, lines, cur = pitch.split(), [], ""
    for wd in words:
        if len(cur) + len(wd) + 1 > 50:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    lines.append(cur)
    for i, ln in enumerate(lines[:2]):
        o.append(f'<text x="24" y="{100 + i * 18}" font-size="12.5" class="w">{esc(ln)}</text>')
    lc = LANG_COLOR.get(repo["lang"], NEON)
    o.append(f'<circle cx="30" cy="{H-50}" r="5" fill="{lc}"/><text x="42" y="{H-46}" font-size="12" class="m">{esc(repo["lang"])}</text>')
    o.append(f'<text x="200" y="{H-46}" font-size="12" class="m">★ {repo["stars"]}   ⑂ {repo["forks"]}</text>')
    if repo["commit"]:
        msg = repo["commit"]["msg"][:38]
        o.append(f'<text x="24" y="{H-22}" font-size="11.5" class="d">last commit {ago(repo["commit"]["date"], now)} · '
                 f'<tspan class="m">{esc(msg)}</tspan></text>')
    o.append(f'<rect x="10" y="10" width="{W-20}" height="{H-20}" rx="12" fill="none" stroke="{NEON}" stroke-opacity=".35" class="breathe"/>')
    return svg_close(o, W, H)


def main():
    now = dt.datetime.now(dt.timezone.utc)
    repos = load_repos()
    os.makedirs("cards", exist_ok=True)
    with open("terminal.svg", "w", encoding="utf-8") as f:
        f.write(terminal(repos, now))
    with open("rag-pipeline.svg", "w", encoding="utf-8") as f:
        f.write(rag_pipeline())
    for r in repos:
        with open(f"cards/{r['name']}.svg", "w", encoding="utf-8") as f:
            f.write(card(r, now))
    print(f"wrote terminal.svg, rag-pipeline.svg and {len(repos)} cards")


if __name__ == "__main__":
    main()
