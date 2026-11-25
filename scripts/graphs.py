"""Contribution heatmap graphs (last 12 months + calendar years)."""
from __future__ import annotations

from datetime import date, timedelta

from svgkit import Svg

LEVEL_FILLS = {
    "dark": ["#122430", "#0E4A52", "#0E7490", "#14B8A6", "#00C2CB"],
    "light": ["#ECFEFF", "#99F6E4", "#5EEAD4", "#14B8A6", "#0E7490"],
}


def _level(count: int, max_c: int) -> int:
    if count <= 0:
        return 0
    if max_c <= 1:
        return 4
    t = count / max_c
    if t < 0.25:
        return 1
    if t < 0.5:
        return 2
    if t < 0.75:
        return 3
    return 4


def last_days(data: dict, today: date, n: int = 365):
    days = data["contrib"]["days"]
    out = []
    for i in range(n - 1, -1, -1):
        d = today - timedelta(days=i)
        iso = d.isoformat()
        out.append((iso, days.get(iso, 0)))
    return out


def total_of(pairs) -> int:
    return sum(c for _, c in pairs)


def title_of(total: int, suffix: str) -> str:
    unit = "contribution" if total == 1 else "contributions"
    return f"{total:,} {unit} {suffix}"


def make_heatmap(theme: str, title: str, pairs: list, label: str) -> Svg:
    fills = LEVEL_FILLS[theme]
    max_c = max((c for _, c in pairs), default=1) or 1
    # layout: ~53 weeks x 7 days
    cell, gap = 12, 3
    left, top = 48, 72
    weeks = (len(pairs) + 6) // 7
    w = left + weeks * (cell + gap) + 48
    h = 220
    s = Svg(max(w, 900), h, theme, label)
    s.board()
    s.text(48, 40, title, 18, "text", 800)
    # pad to week start (Monday-ish): use first date weekday
    if not pairs:
        return s
    first = date.fromisoformat(pairs[0][0])
    pad = first.weekday()  # Mon=0
    cells = [(None, 0)] * pad + pairs
    for i, (d, c) in enumerate(cells):
        week, day = divmod(i, 7)
        x = left + week * (cell + gap)
        y = top + day * (cell + gap)
        lvl = 0 if d is None else _level(c, max_c)
        s.rect(x, y, cell, cell, fills[lvl], 2)
    # legend
    s.text(48, h - 24, "Less", 11, "muted", 500, mono=True)
    for i, fill in enumerate(fills):
        s.rect(90 + i * 16, h - 36, 12, 12, fill, 2)
    s.text(90 + 5 * 16 + 8, h - 24, "More", 11, "muted", 500, mono=True)
    return s


def graph_12m(theme: str, data: dict, today: date) -> Svg:
    pairs = last_days(data, today, 365)
    total = total_of(pairs)
    return make_heatmap(
        theme,
        f"Last 12 months · {total:,} contributions",
        pairs,
        f"Last 12 months: {total:,} contributions",
    )


def graph_year(theme: str, data: dict, year: int) -> Svg | None:
    days = data["contrib"]["days"]
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    today = date.fromisoformat(data["today"])
    if start > today:
        return None
    pairs = []
    d = start
    while d <= end and d <= today:
        iso = d.isoformat()
        pairs.append((iso, days.get(iso, 0)))
        d += timedelta(days=1)
    total = data["contrib"]["years"].get(str(year), total_of(pairs))
    return make_heatmap(
        theme,
        f"{year} · {total:,} contributions",
        pairs,
        f"{year}: {total:,} contributions",
    )


def graph_titles(data: dict, today: date):
    """Yield (key, summary_md_or_None, total, title) for README."""
    pairs = last_days(data, today, 365)
    t12 = total_of(pairs)
    yield ("12m", "Last 12 months", t12, title_of(t12, "in the last 12 months"))
    years = sorted(data["contrib"]["years"].keys(), reverse=True)
    for y in years:
        total = data["contrib"]["years"][y]
        yield (y, str(y), total, title_of(total, f"in {y}"))


def make_graphs(theme: str, data: dict, today: date) -> dict:
    out = {}
    out[f"graph-12m-{theme}.svg"] = graph_12m(theme, data, today)
    for y in sorted(data["contrib"]["years"].keys()):
        g = graph_year(theme, data, int(y))
        if g:
            out[f"graph-{y}-{theme}.svg"] = g
    return out
