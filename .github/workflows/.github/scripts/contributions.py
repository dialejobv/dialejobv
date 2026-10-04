"""Draws assets/contributions.svg from the real GitHub contributions of GH_USER.

Runs inside GitHub Actions (see .github/workflows/contributions.yml).
Uses only the Python standard library.
"""
import json
import os
import sys
import urllib.request

OUT = "assets/contributions.svg"
DAYS = 31
W, C, K, D, N, S, M = "#EAF2F8", "#5CE1E6", "#E8A04C", "#B9772F", "#0E2A47", "#081B30", "#17406A"
SANS = "'Segoe UI','Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""


def fetch(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-graph"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [(d["date"], d["contributionCount"]) for w in weeks for d in w["contributionDays"]]
    return days[-DAYS:]


def frame(inner, label):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 320" width="880" height="320" role="img" aria-label="{label}">
  <title>{label}</title>
  <style>
    .h{{font:700 26px {SANS};fill:{W}}}
    .n{{font:700 26px {MONO};fill:{C}}}
    .ax{{font:17px {MONO};fill:#9DB4C8}}
    .grid{{stroke:{M};stroke-width:1.5}}
    .area{{fill:{C};opacity:0;animation:fade 1s 1.6s forwards}}
    .line{{fill:none;stroke:{C};stroke-width:4;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:100;stroke-dashoffset:100;animation:draw 2s ease-out forwards}}
    .pt{{fill:{N};stroke:{K};stroke-width:3;opacity:0;animation:pop .4s forwards}}
    @keyframes draw{{to{{stroke-dashoffset:0}}}}
    @keyframes fade{{to{{opacity:.18}}}}
    @keyframes pop{{to{{opacity:1}}}}
    @media (prefers-reduced-motion:reduce){{.line{{animation:none;stroke-dashoffset:0}}.area{{animation:none;opacity:.18}}.pt{{animation:none;opacity:1}}}}
  </style>
  <rect width="880" height="320" rx="18" fill="{N}"/>
  <rect x="5" y="5" width="870" height="310" rx="14" fill="none" stroke="{M}" stroke-width="2"/>
{inner}
</svg>
"""


def render(days):
    if not days:
        return frame(
            f'  <text class="h" x="440" y="168" text-anchor="middle">Contribution data is on its way</text>',
            "Contribution graph, waiting for the first update",
        )
    counts = [c for _, c in days]
    total, top = sum(counts), max(max(counts), 1)
    x0, x1, y0, y1 = 70, 840, 250, 90
    step = (x1 - x0) / max(len(days) - 1, 1)
    pts = [(x0 + i * step, y0 - (c / top) * (y0 - y1)) for i, c in enumerate(counts)]
    line = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    area = f"{line}L{x1} {y0}L{x0} {y0}Z"
    parts = [
        f'  <text class="h" x="40" y="52">Contributions, last {len(days)} days</text>',
        f'  <text class="n" x="840" y="52" text-anchor="end">{total} total</text>',
    ]
    for frac in (0, 0.5, 1):
        y = y0 - frac * (y0 - y1)
        parts.append(f'  <path class="grid" d="M{x0} {y:.0f}H{x1}"/>')
        parts.append(f'  <text class="ax" x="{x0 - 12}" y="{y + 6:.0f}" text-anchor="end">{round(top * frac)}</text>')
    for i in range(0, len(days), 5):
        d = days[i][0]
        parts.append(f'  <text class="ax" x="{pts[i][0]:.0f}" y="286" text-anchor="middle">{d[8:10]}/{d[5:7]}</text>')
    parts.append(f'  <path class="area" d="{area}"/>')
    parts.append(f'  <path class="line" pathLength="100" d="{line}"/>')
    for i, (x, y) in enumerate(pts):
        delay = 0.2 + 1.8 * i / max(len(pts) - 1, 1)
        parts.append(f'  <circle class="pt" style="animation-delay:{delay:.2f}s" cx="{x:.1f}" cy="{y:.1f}" r="5"/>')
    return frame("\n".join(parts), f"{total} contributions in the last {len(days)} days")


def main():
    login, token = os.environ.get("GH_USER"), os.environ.get("GITHUB_TOKEN")
    if not login or not token:
        sys.exit("GH_USER and GITHUB_TOKEN are required")
    svg = render(fetch(login, token))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
