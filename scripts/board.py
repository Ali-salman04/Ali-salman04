"""GitHub activity board card."""
from __future__ import annotations

from cards import fmt
from svgkit import Svg


def github_board(theme: str, data: dict) -> Svg:
    c, r = data["contrib"], data["repos"]
    s = Svg(1200, 280, theme, "GitHub activity board")
    s.board()
    s.text(48, 48, "02 // GITHUB BOARD", 13, "teal", 700, mono=True)
    s.text(48, 88, "Public activity at a glance", 26, "text", 800)

    items = [
        ("LAST YEAR", fmt(c["last_year"]), "contributions"),
        ("THIS YEAR", fmt(c["this_year"]), "contributions"),
        ("ALL TIME", fmt(c["all_time"]), f"since {c['since_year']}"),
        ("REPOS", str(r["public_repos"]), "public non-fork"),
        ("STARS", str(r["stars"]), "earned"),
        ("STREAK", f'{c["current_streak"]["days"]}d', "current"),
    ]
    for i, (label, value, note) in enumerate(items):
        col, row = i % 3, i // 3
        x, y = 48 + col * 370, 120 + row * 70
        s.card(x, y, 350, 58, "card", 12)
        s.text(x + 18, y + 24, label, 11, "muted", 700, mono=True)
        s.text(x + 18, y + 46, f"{value}  ·  {note}", 16, "mint", 700)
    return s


def board_label(data: dict) -> str:
    c = data["contrib"]
    return f"GitHub board · {fmt(c['last_year'])} contributions last year"
