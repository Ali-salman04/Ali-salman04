# Phone variants for every picture. The README gives each a <source media="(max-width: 600px)">; a phone
# shows the README column at about 330 px. The big boards (hero, GitHub board, whoami) are 440 wide with no
# text under 15 px. The app cards (shown at 49% of the column), the video tiles (32%) and the section labels
# are redrawn with fewer, bigger words: the same viewBox as their desktop card, so the image widths and the
# per-card links stay as they are.
import os

from board import FILLS, ICON_OF, ROT, counters, icon, board_label, sticker
from cards import (PULSE_CSS, TAGS, app_label, app_fact, challenge_view, fit_size, hero_label, long_date, name_line,
                   sticker_link, terminal_height, whoami_label, whoami_lines, _terminal)
from svgkit import HERE, Svg, img_b64, mix, text_width, wrap


def hero_phone(t, data, P):
    tag_lines = wrap(P["tagline"]["value"], "f500", 20, 388)
    chip_y0 = 134 + 27 * len(tag_lines)
    places, cx, cy = [], 26, chip_y0
    for lab, fill in TAGS:
        w = text_width(lab, "f600", 15) + 26
        if cx + w > 414:
            cx, cy = 26, cy + 42
        places.append((cx, cy, lab, fill))
        cx += w + 12
    s = Svg(440, int(cy + 32 + 28), t, hero_label(P, data))
    s.board()
    s.zlogo(26, 26, 76)
    name_line(s, 116, 84, 42)
    sticker_link(s, 316, 16, 100, 34, 17)
    ly = 132
    for line in tag_lines:
        s.text(26, ly, line, "f500", 20, "muted")
        ly += 27
    for px, py, lab, fill in places:
        s.chip(px, py, lab, fill, "f600", 15, 32, 13, 2, 9, 3)
    return s


def whoami_phone(t, data, P):
    L, _ = whoami_lines(data, P, phone=True)
    L += [[("$ ", "pop", "m500")]]
    h = terminal_height(L, 16, 26, 408, 18)
    s = Svg(440, h + 36, t, whoami_label(data, P))
    s.board()
    _terminal(s, 14, 16, 408, h, "ali@lahore: ~", L, 16, 26, 18)
    return s


def github_board_phone(t, data):
    cs = counters(data)
    s = Svg(440, 534, t, board_label(data))
    s.board()
    s.text(26, 54, "On GitHub", "f700", 30)
    s.text(414, 52, "redrawn nightly", "m400", 15, "muted", "end")
    # the big one, full width
    sticker(s, 26, 78, 388, 100, FILLS[0], ROT[0])
    s.text(44, 130, cs[0][0], "f700", 50)
    nw = text_width(cs[0][0], "f700", 50)
    icon(s, ICON_OF[0], 26 + 388 - 14 - 32, 78 + 12, 32)
    for k, line in enumerate(wrap(cs[0][1], "m400", 16, 388 - 44 - nw - 16 - 36)[:3]):
        s.text(44 + nw + 14, 118 + k * 20, line, "m400", 16)
    s.add("</g>")
    y = 198
    for k in range(1, 7):
        col, row = (k - 1) % 2, (k - 1) // 2
        x, yy = 26 + col * 200, y + row * 106
        sticker(s, x, yy, 188, 92, FILLS[k], ROT[k])
        icon(s, ICON_OF[k], x + 188 - 12 - 24, yy + 8, 24)
        s.text(x + 14, yy + 42, cs[k][0], "f700", 34)
        for m, line in enumerate(wrap(cs[k][1], "m400", 15, 188 - 28)[:2]):
            s.text(x + 14, yy + 64 + m * 18, line, "m400", 15)
        s.add("</g>")
    return s


# ---------------------------------------------------------------- app cards, video tiles, labels
def app_phone(t, a, data, P):
    """An app card for a phone: the icon, the name (two lines allowed) and the status pill. Same 440 viewBox
    as the desktop card; the description, chips and fact line are left to the alt text."""
    s = Svg(440, 236, t, app_label(a, app_fact(a, data, P)))
    s.board(stroke=False)
    x, y, w, h = 16, 16, 408, 204
    s.card(x, y, w, h, mix(s.col(a["tint"]), s.col("card"), 0.38))
    row_y, row_h, icon = y + 22, 100, 80
    s.image(x + 22, row_y + (row_h - icon) / 2, icon, icon, img_b64(os.path.join(HERE, a["icon"])), 18)
    nx, avail = x + 22 + icon + 16, w - 22 - icon - 16 - 14
    size = 48
    while size > 44 and max(text_width(l, "f700", size) for l in wrap(a["name"], "f700", size, avail)) > avail:
        size -= 1
    lines = wrap(a["name"], "f700", size, avail)
    lh = size + 4
    base = row_y + (row_h - len(lines) * lh) / 2 + size * 0.82
    for k, line in enumerate(lines):
        s.text(nx, base + k * lh, line, "f700", size)
    status = a.get("status_phone", a["status"])
    psize = fit_size(status, "m500", 32, w - 44 - 28, 24)       # about 11.5 px on a phone, 8.7 px at the 24 floor
    s.chip(x + 22, row_y + row_h + 16, status, "go", "m500", psize, psize + 12, 14, 1.5, 12, 0, "#062b16")
    return s


def video_phone(t, v):
    """A video tile for a phone: the thumbnail and the title at 32 px, two lines at most, cut at a word with an
    ellipsis. Same 292 wide viewBox as the desktop tile; the date stays in the alt text."""
    size, maxw = 32, 264 - 24
    lines = wrap(v["title"], "f600", size, maxw)
    if len(lines) > 2:
        lines = lines[:2]
        while lines[1] and text_width(lines[1] + "...", "f600", size) > maxw:
            lines[1] = lines[1].rsplit(" ", 1)[0] if " " in lines[1] else lines[1][:-1]
        lines[1] += "..."
    for k, line in enumerate(lines):          # one word wider than the line: cut it, never clip it
        while text_width(line, "f600", size) > maxw:
            line = line[:-4] + "..."
        lines[k] = line
    s = Svg(292, 280, t, f"{v['title']}, {long_date(v['date'])}")
    s.board(stroke=False)
    x, y, w, h = 14, 14, 264, 252
    s.card(x, y, w, h, "card", 16)
    s.image(x + 12, y + 12, w - 24, 135, v["thumb"], 10)
    px, py = x + w - 36, y + 122
    s.add(f'<circle cx="{px + 2}" cy="{py + 2}" r="16" fill="{s.col("line")}"/><circle cx="{px}" cy="{py}" r="16" fill="{s.col("pop")}" '
          f'stroke="{s.col("line")}" stroke-width="2"/><path d="M{px - 4} {py - 8} L{px + 8} {py} L{px - 4} {py + 8} Z" fill="{s.col("on-pop")}"/>')
    for k, line in enumerate(lines):
        s.text(x + 12, y + 147 + 14 + 26 + k * 38, line, "f600", size)
    return s


def label_phone(t, title, fill):
    """A section label for a phone: the title at 38 px on its sticker, no chip. 440 wide."""
    s = Svg(440, 80, t, title)
    w = text_width(title, "f700", 38) + 40
    s.add(f'<g transform="rotate(-1.2 {12 + w / 2} 40)">')
    s.rect(16, 16, w, 54, "line", 14)
    s.rect(12, 12, w, 54, fill, 14, "line", 2)
    s.text(32, 52, title, "f700", 38)
    s.add("</g>")
    return s
