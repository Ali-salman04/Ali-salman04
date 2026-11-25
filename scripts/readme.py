# README.md from template — numbers in alt text stay current.
from datetime import date
from html import escape

from board import board_label
from cards import app_fact, app_label, fmt, hero_label, whoami_label
from graphs import graph_titles, last_days, title_of, total_of

PHONE = ("hero", "github", "whoami")


def line_title(data, today):
    return title_of(total_of(last_days(data, today)), "in the last 30 days")


def picture(name, width, alt, phone=False):
    a = f"assets/{name}"
    srcs = []
    if phone:
        srcs.append(
            f'<source media="(prefers-color-scheme: dark) and (max-width: 600px)" srcset="{a}-phone-dark.svg">'
        )
        srcs.append(f'<source media="(max-width: 600px)" srcset="{a}-phone-light.svg">')
    srcs.append(f'<source media="(prefers-color-scheme: dark)" srcset="{a}-dark.svg">')
    attr = f'height="{width[1:]}"' if width.startswith("h") else f'width="{width}"'
    return (
        f'<picture>{"".join(srcs)}'
        f'<img src="{a}-light.svg" {attr} alt="{escape(alt, quote=True)}"></picture>'
    )


def link(url, inner):
    return f'<a href="{url}">{inner}</a>'


def render(data, P):
    L = P["links"]
    out = [
        link(L["github"]["url"], picture("hero", "100%", hero_label(P, data), "hero" in PHONE)),
        "",
    ]
    badges = []
    for key, name in (("github", "gh"), ("linkedin", "li"), ("email", "email")):
        alt = f"{L[key]['label']} {L[key]['handle']}".strip()
        badges.append(link(L[key]["url"], picture(f"badge-{name}", "h44", alt)))
    out += ['<p align="center">', *badges, "</p>", ""]
    out += [picture("github", "100%", board_label(data), "github" in PHONE), ""]
    for key, summary, total, title in graph_titles(data, date.fromisoformat(data["today"])):
        pic = picture(f"graph-{key}", "100%", title, True)
        if summary is None:
            out += [pic, ""]
        else:
            unit = "contribution" if total == 1 else "contributions"
            out += [
                f"<details><summary>{summary}: {fmt(total)} {unit}</summary>",
                "",
                pic,
                "",
                "</details>",
                "",
            ]
    out += [
        picture("line-30d", "100%", line_title(data, date.fromisoformat(data["today"])), True),
        "",
    ]
    out += [picture("whoami", "100%", whoami_label(data, P), "whoami" in PHONE), ""]
    out += [picture("label-ship", "100%", "What I ship", True), ""]
    apps = []
    for a in P["apps"]:
        alt = app_label(a, app_fact(a, data, P))
        apps.append(link(a["url"], picture(f"app-{a['id']}", "49%", alt, True)))
    out += ['<p align="center">', *apps, "</p>", ""]
    more = " · ".join(link(m["url"], m["name"]) for m in P.get("more", []))
    if more:
        out += [f'<p align="center"><sub>More ships: {more}</sub></p>', ""]
    out += [
        '<p align="center"><sub>Drawn in the Hafiz Ali Salman teal design system · '
        "numbers redrawn by a GitHub Action · "
        f'{link(L["linkedin"]["url"], "LinkedIn")} · '
        f'{link(L["github"]["url"], "GitHub")}</sub></p>',
        "",
    ]
    return "\n".join(out)
