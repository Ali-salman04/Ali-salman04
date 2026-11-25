"""Hero, whoami, badges, and project cards."""
from __future__ import annotations

from svgkit import Svg

THEMES = ("dark", "light")


def fmt(n: int) -> str:
    return f"{n:,}"


def hero(theme: str, data: dict, P: dict) -> Svg:
    s = Svg(1200, 320, theme, "Hafiz Ali Salman — Full Stack Engineer")
    s.board()
    s.text(48, 58, "SYSTEM.ONLINE // HAFIZ-ALI-SALMAN", 13, "teal", 700, mono=True)
    s.text(1152, 58, P["location"]["value"].upper(), 12, "muted", 600, "end", mono=True)
    s.text(48, 120, "HI THERE, I'M", 16, "muted", 600, mono=True)
    s.text(48, 178, "Hafiz Ali Salman", 48, "text", 900)
    s.rect(48, 200, 420, 38, "panel", 10, "teal", 1.5)
    s.circle(68, 219, 5, "teal")
    s.text(84, 225, "Full Stack Engineer", 15, "mint", 600, mono=True)
    s.text(48, 270, P["tagline"]["value"][:92], 15, "muted", 500)
    # right avatar ring
    s.card(820, 70, 320, 200, "card", 18)
    s.circle(980, 145, 48, "teal")
    s.circle(980, 145, 40, "panel")
    s.text(980, 155, "HAS", 28, "mint", 900, "middle")
    s.text(980, 210, "HAFIZ ALI SALMAN", 14, "text", 800, "middle")
    s.text(980, 232, P["role"]["value"][:36], 11, "teal", 600, "middle", mono=True)
    return s


def whoami(theme: str, data: dict, P: dict) -> Svg:
    c, r = data["contrib"], data["repos"]
    s = Svg(1200, 360, theme, "About Hafiz Ali Salman")
    s.board()
    s.text(48, 48, "01 // WHOAMI", 13, "teal", 700, mono=True)
    s.text(48, 88, "Engineering Snapshot", 28, "text", 800)

    metrics = [
        ("CONTRIBUTIONS (1Y)", fmt(c["last_year"]), "teal"),
        ("PUBLIC REPOS", str(r["public_repos"]), "mint"),
        ("STARS", str(r["stars"]), "cyan"),
        ("STREAK", f'{c["current_streak"]["days"]}d', "go"),
    ]
    for i, (label, value, fill) in enumerate(metrics):
        x = 48 + i * 280
        s.card(x, 120, 260, 110, "card", 14)
        s.text(x + 24, 155, label, 11, "muted", 700, mono=True)
        s.text(x + 24, 200, value, 32, fill, 900)

    s.card(48, 250, 1104, 80, "panel", 14)
    edu = P["education"]
    s.text(72, 285, f'{edu["degree"]} · {edu["school"]}', 16, "text", 700)
    s.text(72, 312, f'{edu["years"]} · {" · ".join(P["now"])}', 13, "muted", 500)
    return s


def badge(theme: str, label: str, handle: str, tint: str = "teal") -> Svg:
    s = Svg(220, 44, theme, f"{label} {handle}".strip())
    s.rect(0, 0, 220, 44, "card", 12, "line", 1.5)
    s.circle(24, 22, 10, tint)
    s.text(44, 20, label, 11, "muted", 700, mono=True)
    s.text(44, 36, handle or label, 13, "text", 700)
    return s


def app_card(theme: str, app: dict) -> Svg:
    s = Svg(580, 200, theme, app["name"])
    s.board(dots=False)
    s.rect(0, 0, 580, 200, "bg", 18, "line", 1.5)
    s.card(16, 16, 548, 168, "card", 14)
    tint = app.get("tint", "teal")
    s.rect(36, 36, 48, 48, tint, 12)
    s.text(60, 66, app["name"][:1].upper(), 20, "bg" if theme == "dark" else "text", 900, "middle")
    s.text(100, 52, app["name"], 20, "text", 800)
    s.text(100, 74, app["status"].upper(), 11, tint, 700, mono=True)
    # wrap line roughly
    line = app["line"]
    s.text(36, 120, line[:62], 14, "muted", 500)
    if len(line) > 62:
        s.text(36, 142, line[62:120], 14, "muted", 500)
    x = 36
    for chip in app.get("chips", [])[:4]:
        x += s.chip(x, 158, chip) + 8
    return s


def label_bar(theme: str, title: str, subtitle: str) -> Svg:
    s = Svg(1200, 72, theme, title)
    s.board(dots=False)
    s.rect(0, 0, 1200, 72, "bg", 16, "line", 1.5)
    s.text(40, 32, title, 22, "text", 800)
    s.text(40, 56, subtitle, 13, "teal", 600, mono=True)
    return s


def hero_label(P: dict, data: dict) -> str:
    return f"Hafiz Ali Salman — {P['tagline']['value']}"


def whoami_label(data: dict, P: dict) -> str:
    c = data["contrib"]
    return f"About · {fmt(c['last_year'])} contributions in the last year"
