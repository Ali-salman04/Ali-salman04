# Draws the sticker-board cards (direction B), light and dark, from fetched data and profile.json.
# Every function returns an Svg; build.py renders and writes them. Layout sizes are in px of the SVG
# itself: boards are 880 wide, phone variants 440, app cards 440, video tiles 292.
import os
from datetime import date

from svgkit import Svg, HERE, img_b64, mix, text_width, wrap

THEMES = ("light", "dark")
NBSP = " "


def fmt(n):
    return f"{n:,}"


def short_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b')}"


def long_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b %Y')}"


def fit_size(text, font, size, maxw, floor):
    """The largest size from `size` down to `floor` where the text fits maxw."""
    while size > floor and text_width(text, font, size) > maxw:
        size -= 1
    return size


# ---------------------------------------------------------------- shared pieces
def challenge_view(c):
    """What the hero bar, the whoami line and the alt texts say about the challenge from fetch_challenge(); None
    when there is no challenge to show. Three states: active (a live bar), finished (the most recent completed
    one, with its last logged count) and none (planned challenges are never shown as running).
    With a target the bar is the count over the target; without one it is "day N of D". Day 0 of an active
    challenge shows the count it started from (data.js platform start), never an invented one."""
    if not c or c.get("state") == "none":
        return None
    t, tg, cnt, day, days = c["title"], c.get("target"), c.get("count"), c["day"], c["days"]
    live = c["state"] == "active"
    plat = c.get("platform") or {}
    phrase = t
    if tg and plat.get("name") and plat.get("label") and t == f"Road to {tg['n']:,} on {plat['name']}":
        phrase = f"Road to {tg['n']:,} {plat['label']} on {plat['name']}"
    v = {"live": live, "title": t, "day": day, "days": days}
    if tg and cnt is not None:
        v["count"], v["pct"] = f"{fmt(cnt)} / {fmt(tg['n'])}", cnt / tg["n"]
        if live:
            v["note"] = f"day {day} of {days}, until {short_date(c['end'])}"
            v["alt"] = f"{t}: {fmt(cnt)} of {fmt(tg['n'])}."
            v["now"] = (phrase, f"{fmt(cnt)} after day {day} of {days}" if day else f"{fmt(cnt)} at the start, day 0 of {days}")
        else:
            v["note"] = "finished"
            v["alt"] = f"{t}: finished at {fmt(cnt)}."
            v["now"] = (phrase, f"finished at {fmt(cnt)}")
    elif live:
        v["count"], v["pct"], v["note"] = f"day {day} of {days}", day / days, f"until {short_date(c['end'])}"
        v["alt"] = f"{t}: day {day} of {days}."
        v["now"] = (t, f"day {day} of {days}")
    else:
        v["count"], v["pct"], v["note"] = f"{days} days", 1.0, "finished"
        v["alt"] = f"{t}: finished."
        v["now"] = (t, "finished")
    v["now_word"] = "Now" if live else "Last challenge"
    return v


def today_bar(s, x, y, label, count, pct, note, live=True):
    """The site's Today bar look: a white pill with a live dot, a label, a progress bar and a count.
    A finished challenge gets a still, grey dot."""
    w = 26 + text_width(label, "f700", 18) + 16 + 120 + 14 + text_width(count, "m500", 15) + 14 + text_width(note, "m400", 15) + 22
    s.rect(x + 4, y + 4, w, 44, "line", 99)
    s.rect(x, y, w, 44, "card", 99, "line", 2)
    cls = ' class="pulse"' if live else ""
    s.add(f'<circle cx="{x + 20}" cy="{y + 22}" r="5.5" fill="{s.col("go" if live else "muted")}"{cls}/>')
    cx = x + 36
    cx += s.text(cx, y + 28, label, "f700", 18) + 16
    s.rect(cx, y + 15, 120, 14, "card", 99, "text", 1.5)
    s.rect(cx + 1.5, y + 16.5, max(10, 117 * min(pct, 1)), 11, "go", 99)
    cx += 134
    cx += s.text(cx, y + 28, count, "m500", 15) + 14
    s.text(cx, y + 28, note, "m400", 15, "muted")
    if live:
        s.css.append(PULSE_CSS)
    return w


PULSE_CSS = ("@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}.pulse{animation:pulse 1.6s ease-in-out infinite}"
             "@media (prefers-reduced-motion:reduce){.pulse{animation:none}}")


def sticker_link(s, x, y, w, h, size, rot=5):
    cx, cy = x + w / 2, y + h / 2
    s.add(f'<g transform="rotate({rot} {cx} {cy})">')
    s.rect(x + 4, y + 4, w, h, "line", 10)
    s.rect(x, y, w, h, "pop", 10, "line", 2)
    s.text(cx, cy + size * 0.36, "GitHub", "f700", size, "on-pop", "middle")
    s.add("</g>")


TAGS = [("SaaS", "lx"), ("Healthcare", "rd"), ("Integrations", "bd"), ("Full stack", "li")]


def name_line(s, x, base, size):
    """'Hi, I'm Ali' with the name on a teal highlight."""
    w1 = text_width("Hi, I'm ", "f700", size)
    wz = text_width("Ali", "f700", size)
    s.rect(x + w1 - size * 0.14, base - size * 0.93, wz + size * 0.28, size * 1.2, "yt", size * 0.2)
    s.text(x, base, "Hi, I'm Ali", "f700", size)


def hero_label(P, data):
    return f"Hi, I'm Ali. {P['tagline']['value']}"


# ---------------------------------------------------------------- hero
def hero(t, data, P):
    s = Svg(880, 244, t, hero_label(P, data))
    s.board()
    s.zlogo(40, 42, 104)
    x0 = 172
    name_line(s, x0, 106, 58)
    tag = P["tagline"]["value"]
    s.text(x0, 150, tag, "f500", fit_size(tag, "f500", 21, 880 - x0 - 150, 16), "muted")
    cx = x0
    for label, fill in TAGS:
        cx += s.chip(cx, 170, label, fill, "f600", 15, 32, 13, 2, 9, 3) + 14
    sticker_link(s, 724, 34, 126, 44, 20)
    return s


# ---------------------------------------------------------------- badges
def badge(t, label, handle, fill, icon=None):
    w = 26 + (30 if icon else 0) + text_width(label, "f600", 17) + (10 + text_width(handle, "m400", 15) if handle else 0) + 10
    s = Svg(int(w) + 8, 46, t, f"{label} {handle}".strip())
    s.rect(4, 7, w - 4, 36, "line", 10)
    s.rect(1, 3, w - 4, 36, fill, 10, "line", 2)
    x = 15
    if icon == "play":
        s.rect(x, 12, 24, 18, "card", 5, "line", 1.5)
        s.add(f'<path d="M{x + 9} 16 L{x + 17} 21 L{x + 9} 26 Z" fill="{s.col("text")}"/>')
        x += 32
    x += s.text(x, 27, label, "f600", 17) + 10
    if handle:
        s.text(x, 26, handle, "m400", 15)
    return s


# ---------------------------------------------------------------- whoami terminal
def terminal_rows(lines, size, maxw):
    """Wraps terminal lines to maxw. A one-run line wraps plainly; a [prefix, text] line (the arrows)
    wraps with a hanging indent, so continuation rows line up under the text."""
    rows = []
    for line in lines:
        plain = "".join(t for t, _, _ in line) if line else ""
        if line is None or text_width(plain, "m400", size) <= maxw:
            rows.append(line)
        elif len(line) == 1:
            rows += [[(part, line[0][1], line[0][2])] for part in wrap(plain, "m400", size, maxw)]
        elif len(line) == 2:
            (p, pf, pfont), (t, tf, tfont) = line
            parts = wrap(t, "m400", size, maxw - text_width(p, "m400", size))
            rows.append([(p, pf, pfont), (parts[0], tf, tfont)])
            rows += [[(" " * len(p), tf, None), (part, tf, tfont)] for part in parts[1:]]
        else:
            rows.append(line)
    return rows


def terminal_height(lines, size, lh, w, pad=24):
    rows = terminal_rows(lines, size, w - pad * 2)
    return int(38 + pad + size * 0.7 + sum(lh * 0.45 if r is None else lh for r in rows) - lh * 0.2 + pad)


def _terminal(s, x, y, w, h, title, lines, size, lh, pad=24):
    s.rect(x + 4, y + 4, w, h, "line", 14)
    s.rect(x, y, w, h, "screen", 14, "line", 2)
    s.add(f'<line x1="{x}" y1="{y + 38}" x2="{x + w}" y2="{y + 38}" stroke="{s.col("line")}" stroke-width="2"/>')
    for i, c in enumerate(("pop", "rd", "go")):
        s.add(f'<circle cx="{x + 22 + i * 20}" cy="{y + 19}" r="6" fill="{s.col(c)}" stroke="{s.col("line")}" stroke-width="1.5"/>')
    s.text(x + w / 2, y + 25, title, "m400", 15, "on-screen-muted", "middle")
    ly = y + 38 + pad + size * 0.7
    maxw = w - pad * 2
    for line in terminal_rows(lines, size, maxw):
        if line is None:
            ly += lh * 0.45
            continue
        s.tspans(x + pad, ly, line, "m400", size)
        ly += lh
    cx = x + pad + text_width("$ ", "m500", size)
    s.rect(cx, ly - lh - size * 0.8, size * 0.55, size * 1.05, "on-screen", 1, extra='class="cur"')
    s.css.append("@keyframes blink{50%{opacity:0}}.cur{animation:blink 1.1s steps(1) infinite}"
                 "@media (prefers-reduced-motion:reduce){.cur{animation:none}}")


WHOAMI_LINE = "I build SaaS, marketplaces, and healthcare RCM integrations."


def whoami_lines(data, P, phone=False):
    v = challenge_view(data.get("challenge") or {"state": "none"})
    now = list(P.get("now") or [])
    role = P.get("role", {}).get("value", "Full Stack Engineer")
    who = ([[("ali", "on-screen", "m500"), (f"  ·  {role}", "on-screen-muted", None)],
            [(P["location"]["value"], "on-screen-muted", None)]] if phone else
           [[("ali", "on-screen", "m500"), (f"  ·  {role}  ·  {P['location']['value']}", "on-screen-muted", None)]])
    L = [
        [("$ ", "pop", "m500"), ("whoami", "on-screen", "m500")],
        *who,
        [(WHOAMI_LINE, "on-screen-muted", None)],
        None,
        [("$ ", "pop", "m500"), ("cat now.txt", "on-screen", "m500")],
    ]
    if v:
        L.append([("→ ", "go", None), (f"{v['now'][0]}: {v['now'][1]}", "on-screen-muted", None)])
    L += [[("→ ", "go", None), (n, "on-screen-muted", None)] for n in now]
    return L, now


def whoami_label(data, P):
    v = challenge_view(data.get("challenge") or {"state": "none"})
    _, now = whoami_lines(data, P)
    lead = f"{v['now_word']}: {v['now'][0]}, {v['now'][1]}. " if v else "Now: "
    return f"whoami: ali, {P.get('role', {}).get('value', 'engineer')}, {P['location']['value']}. {WHOAMI_LINE} " + lead + ". ".join(now) + "."


def whoami(t, data, P):
    L, _ = whoami_lines(data, P)
    L += [[("$ ", "pop", "m500")]]
    h = terminal_height(L, 18, 29, 826)
    s = Svg(880, h + 44, t, whoami_label(data, P))
    s.board()
    _terminal(s, 24, 22, 826, h, "ali@lahore: ~", L, 18, 29)
    return s


# ---------------------------------------------------------------- section labels
def label(t, title, chip, fill, chip_fill):
    s = Svg(880, 66, t, title)
    w = text_width(title, "f700", 28) + 36
    s.add(f'<g transform="rotate(-1.2 {12 + w / 2} 33)">')
    s.rect(16, 14, w, 44, "line", 12)
    s.rect(12, 10, w, 44, fill, 12, "line", 2)
    s.text(30, 42, title, "f700", 28)
    s.add("</g>")
    if chip:
        s.chip(w + 36, 20, chip, chip_fill, "m500", 15, 30, 11)
    return s


# ---------------------------------------------------------------- app cards
def arrow(s, x, y, size=30):
    """Pop square button with an up-right arrow, the one loud colour on a card."""
    s.rect(x + 2, y + 2, size, size, "line", 8)
    s.rect(x, y, size, size, "pop", 8, "line", 2)
    c = s.col("on-pop")
    m = size * 0.3
    e = size - m
    s.add(f'<path d="M{x + m:.1f} {y + e:.1f} L{x + e:.1f} {y + m:.1f} M{x + m + 2:.1f} {y + m:.1f} H{x + e:.1f} V{y + e - 2:.1f}" '
          f'stroke="{c}" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')


def app_fact(a, data, P):
    """The mono fact line of an app card, in parts; a part that cannot be filled with a real value is left out."""
    repo = data["repos"]["repos"].get(a.get("repo", ""), {})
    mv = data.get("appstore") or {"martva_rating": 0, "martva_count": 0}
    parts = []
    for key in a.get("fact") or []:
        if key == "tag" and repo.get("tag"):
            parts.append(repo["tag"])
        elif key == "downloads" and repo.get("downloads") is not None and a.get("repo"):
            parts.append(f"{fmt(repo['downloads'])} downloads")
        elif key == "stars" and repo.get("stars"):
            parts.append(f"{fmt(repo['stars'])} stars")
        elif key == "language" and repo.get("language"):
            parts.append(repo["language"])
        elif key == "martva_downloads" and P.get("martva_downloads"):
            parts.append(f"{P['martva_downloads']['value']} downloads")
        elif key == "rating":
            if mv.get("martva_count", 0) > 0:
                parts.append(f"{mv['martva_rating']:.1f} from {mv['martva_count']} ratings")
        elif key not in ("tag", "downloads", "stars", "language", "rating", "martva_downloads"):
            parts.append(key)
    return parts


def app_label(a, parts):
    return f"{a['name']}: {a['line']} {a['status'].capitalize()}, {', '.join(parts)}."


def app(t, a, data, P):
    parts = app_fact(a, data, P)
    s = Svg(440, 304, t, app_label(a, parts))
    s.board(stroke=False)
    x, y, w, h = 16, 16, 408, 274
    s.card(x, y, w, h, mix(s.col(a["tint"]), s.col("card"), 0.38))
    s.image(x + 20, y + 24, 72, 72, img_b64(os.path.join(HERE, a["icon"])), 16)
    nx = x + 108
    size = fit_size(a["name"], "f700", 28, w - 108 - 20, 26)
    s.text(nx, y + 66, a["name"], "f700", size)
    s.chip(nx, y + 76, a["status"], "go", "m500", 13, 24, 10, 1.5, 12, 0, "#062b16")
    arrow(s, x + w - 46, y + 14, 28)
    lines = wrap(a["line"], "f500", 19, w - 40)
    if len(lines) > 2:
        raise ValueError(f"{a['name']}: description needs {len(lines)} lines, shorten it")
    ly = y + 134
    for line in lines:
        s.text(x + 20, ly, line, "f500", 19)
        ly += 26
    cx = x + 20
    for lab, fill in a["chips"]:
        cx += s.chip(cx, y + 186, lab, fill, "m500", 13, 26, 9) + 8
    text = "  ·  ".join(parts)
    while len(parts) > 1 and text_width(text, "m400", 15) > w - 40:
        parts = parts[:-1]
        text = "  ·  ".join(parts)
    s.text(x + 20, y + 246, text, "m400", 15, "muted")
    return s


# ---------------------------------------------------------------- video tiles
def video(t, v):
    s = Svg(292, 296, t, f"{v['title']}, {long_date(v['date'])}")
    s.board(stroke=False)
    x, y, w, h = 14, 14, 264, 268
    s.card(x, y, w, h, "card", 16)
    s.image(x + 12, y + 12, w - 24, 135, v["thumb"], 10)
    px, py = x + w - 36, y + 122
    s.add(f'<circle cx="{px + 2}" cy="{py + 2}" r="16" fill="{s.col("line")}"/><circle cx="{px}" cy="{py}" r="16" fill="{s.col("pop")}" '
          f'stroke="{s.col("line")}" stroke-width="2"/><path d="M{px - 4} {py - 8} L{px + 8} {py} L{px - 4} {py + 8} Z" fill="{s.col("on-pop")}"/>')
    lines = wrap(v["title"], "f600", 18, w - 24)
    if len(lines) > 2:
        lines = lines[:2]
        while text_width(lines[1] + "...", "f600", 18) > w - 24:
            lines[1] = lines[1].rsplit(" ", 1)[0]
        lines[1] += "..."
    ly = y + 176
    for line in lines:
        s.text(x + 12, ly, line, "f600", 18)
        ly += 23
    s.text(x + 12, y + h - 16, f"{long_date(v['date'])}  ·  YouTube", "m400", 13, "muted")
    return s
