# The contribution graphs, each its own image with its total on top: the last 6 months (26 weeks, a count
# printed in every cell), the last 12 months and every calendar year since the account
# was made (each in a <details> in the README). Drawn like GitHub's graph (weeks as columns, Sunday on top)
# in design-system colours. Every total is the sum of the cells drawn, never a number read from elsewhere.
# Desktop is 880 wide. The phone variants are 440 wide: the 6-month graph turns on its side (a week per row,
# seven big cells across) so every count is big enough to read; the 12-month and year graphs are cut into
# four stacked rows of 14 columns (about three months each), with a count in every cell (10.5 to 12 in a
# 440 box, about 8.5 to 10 px on a 390 px phone).
from datetime import date, timedelta
from math import ceil

from cards import fmt
from svgkit import TOK, Svg, mix, text_width


def sunday_of(d):
    return d - timedelta(days=(d.weekday() + 1) % 7)


def range_of(kind, today, first_day=None):
    """(start, end, heading words) for "6m", "12m" or a year such as "2025"."""
    if kind == "6m":
        return sunday_of(today) - timedelta(weeks=25), today, "in the last 6 months"
    if kind == "12m":
        return first_day, today, "in the last 12 months"
    y = int(kind)
    return date(y, 1, 1), min(date(y, 12, 31), today), f"in {y}"


def cells_of(days, start, end):
    """[(date, count)] for every day from start to end, zero when nothing was recorded."""
    out, d = [], start
    while d <= end:
        out.append((d, days.get(d.isoformat(), 0)))
        d += timedelta(days=1)
    return out


def total_of(cells):
    return sum(c for _, c in cells)


def title_of(total, words):
    return f"{fmt(total)} contribution{'' if total == 1 else 's'} {words}"


def level_of(count, top):
    if count <= 0 or top <= 0:
        return 0
    return min(4, max(1, ceil(4 * count / top)))


def level_colors(s):
    return [mix(s.col("muted"), s.col("card"), 0.14), s.col("li"), mix(s.col("go"), s.col("li"), 0.5), s.col("go"),
            mix(s.col("go"), s.col("line"), 0.7)]


def _lum(hexc):
    c = [int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# the two inks a printed count can take, both from tokens.json: the dark ink and the white card colour
INKS = (TOK["color"]["light"]["line"], TOK["color"]["light"]["card"])


def ink_on(fill):
    return max(INKS, key=lambda c: _contrast(c, fill))


def count_text(count, maxw, size):
    """(text, size) for a day's count that fits `maxw`: shrink a long number a little, then use 1.2k."""
    txt = f"{count / 1000:.1f}k" if count >= 1000 else str(count)
    while text_width(txt, "m500", size) > maxw and size > 7:
        size -= 0.5
    return txt, size


class Dim:
    """Sizes of one layout. px/py: the pitch of a column and a row; cw/ch: the cell; rows: stacked blocks;
    num: the font size of the count inside a cell (0 prints none); side: weeks run down the page."""
    def __init__(self, W, cx, card_w, px, py, cw, ch, rx, label, head, rows=1, num=0, side=False):
        self.W, self.cx, self.card_w = W, cx, card_w
        self.px, self.py, self.cw, self.ch, self.rx = px, py, cw, ch, rx
        self.label, self.head, self.rows, self.num, self.side = label, head, rows, num, side


DESKTOP_WIDE = Dim(880, 28, 824, 30.5, 32, 28, 28, 6, 16, 24, num=13)     # 26 columns, a count in every cell
DESKTOP_YEAR = Dim(880, 32, 816, 29, 29, 26, 26, 5, 15, 22, rows=2, num=12)   # two half-year rows of 27 columns
PHONE_WIDE = Dim(440, 26, 388, 44, 42, 40, 36, 8, 16, 30, num=19, side=True)
PHONE_YEAR = Dim(440, 26, 388, 25.2, 25.2, 23, 23, 4, 15, 30, rows=4, num=12)   # four rows of 14 columns
SIDE_LABELS = 46          # width of the month column of a sideways graph
GAP = 14                  # between stacked blocks


def ncols_of(cells, start):
    return (cells[-1][0] - sunday_of(start)).days // 7 + 1


def block_h(dim, ncols):
    if dim.side:
        return dim.label + 8 + ncols * dim.py
    return dim.label + 8 + 7 * dim.py


def draw_cells(s, dim, x, y, cells, start):
    """The cells in `dim.rows` stacked blocks, each with month labels, and the counts. Returns (bottom y, colours)."""
    top = max(c for _, c in cells) if cells else 0
    lv = level_colors(s)
    base = sunday_of(start)
    ncols = ncols_of(cells, start)
    per = ceil(ncols / dim.rows)
    by = y
    for r in range(dim.rows):
        c0 = r * per
        n = min(ncols, c0 + per) - c0
        gx = x + 16 + (SIDE_LABELS if dim.side else 0)
        gy = by + dim.label + 8
        if dim.side:
            for k, letter in enumerate("SMTWTFS"):
                s.text(gx + k * dim.px + dim.cw / 2, by + dim.label - 2, letter, "m400", dim.label, "muted", "middle")
        last_end, prev_month = -99, None
        for col in range(c0, c0 + n):
            mid = min(max(base + timedelta(days=7 * col + 3), start), cells[-1][0])
            if mid.month == prev_month:
                continue
            if dim.side:
                ly = gy + (col - c0) * dim.py + dim.ch / 2 + dim.label * 0.35
                if ly > last_end + 20:
                    s.text(x + 16, ly, mid.strftime("%b"), "m400", dim.label, "muted")
                    last_end, prev_month = ly, mid.month
            else:
                lx = gx + (col - c0) * dim.px
                if lx > last_end + 6:
                    s.text(lx, by + dim.label, mid.strftime("%b"), "m400", dim.label, "muted")
                    last_end, prev_month = lx + text_width("Mar", "m400", dim.label), mid.month
        shown = []
        for d, cnt in cells:
            col, row = (d - base).days // 7, (d.weekday() + 1) % 7
            if not c0 <= col < c0 + n:
                continue
            cx = gx + (row if dim.side else col - c0) * dim.px
            cy = gy + ((col - c0) if dim.side else row) * dim.py
            fill = lv[level_of(cnt, top)]
            shown.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{dim.cw}" height="{dim.ch}" rx="{dim.rx}" fill="{fill}"/>')
        s.add("".join(shown))
        if dim.num:                                      # every day prints its count, a quiet 0 on an empty one
            for d, cnt in cells:
                col, row = (d - base).days // 7, (d.weekday() + 1) % 7
                if not c0 <= col < c0 + n:
                    continue
                cx = gx + (row if dim.side else col - c0) * dim.px
                cy = gy + ((col - c0) if dim.side else row) * dim.py
                txt, size = count_text(cnt, dim.cw - 4, dim.num)
                fill = lv[level_of(cnt, top)]
                ink = mix(s.col("muted"), fill, 0.6) if cnt == 0 else ink_on(fill)
                s.text(cx + dim.cw / 2, cy + dim.ch / 2 + size * 0.35, txt, "m400" if cnt == 0 else "m500", size,
                       ink, "middle", extra=f'data-count="{cnt}"')
        by += block_h(dim, per if dim.side else ncols_of(cells, start)) + GAP
    return by - GAP, lv


def graph_image(t, dim, days, start, end, words, note="contributions per day"):
    cells = cells_of(days, start, end)
    total = total_of(cells)
    title = title_of(total, words)
    phone = dim.W == 440
    head_h = dim.head + (24 if phone else 0)          # on a phone the words go on a second line
    per = ceil(ncols_of(cells, start) / dim.rows)
    bh = block_h(dim, per if dim.side else per)
    inner = 16 + head_h + 14 + dim.rows * bh + (dim.rows - 1) * GAP + 12 + 24 + 14
    s = Svg(dim.W, int(inner + 2 * 28), t, title)
    s.board()
    x, y = dim.cx, 28
    s.rect(x + 4, y + 4, dim.card_w, inner, "line", 16)
    s.rect(x, y, dim.card_w, inner, "card", 16, "line", 2)
    nw = s.text(x + 16, y + 16 + dim.head, fmt(total), "f700", dim.head)
    words_text = title[len(fmt(total)) + 1:]
    if phone:
        s.text(x + 16, y + 16 + dim.head + 24, words_text, "m400", 16)
    else:
        s.text(x + 16 + nw + 8, y + 16 + dim.head, words_text, "m400", dim.label + 1)
    bottom, lv = draw_cells(s, dim, x, y + 16 + head_h + 14, cells, start)
    ly = bottom + 12
    lw = text_width("Less", "m400", 15) + 8 + 5 * 18 + 5 + text_width("More", "m400", 15)
    lx = x + dim.card_w - 16 - lw
    lx += s.text(lx, ly + 16, "Less", "m400", 15, "muted") + 8
    for k in range(5):
        s.rect(lx + k * 18, ly + 16 - 15 + 1, 15, 15, lv[k], 3)
    s.text(lx + 5 * 18 + 5, ly + 16, "More", "m400", 15, "muted")
    s.text(x + 16, ly + 16, note, "m400", 15, "muted")
    return s, total, title


# ---------------------------------------------------------------- the 30-day line chart
DAYS = 30


def last_days(data, today):
    """[(date, count)] for the 30 full days before today, yesterday last."""
    end = today - timedelta(days=1)
    return cells_of(data["contrib"]["days"], end - timedelta(days=DAYS - 1), end)


def y_ticks(top):
    """Labels at real values: 0, round steps below the maximum, and the maximum itself."""
    top = max(top, 1)
    step = next(st for st in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000) if top / st <= 4)
    ticks = [v for v in range(0, top, step) if top - v >= step * 0.45]
    return ticks + [top]


def monotone_path(pts):
    """A smooth cubic path through the points that never swings past a neighbour (no dips below zero)."""
    n = len(pts)
    dx = [pts[i + 1][0] - pts[i][0] for i in range(n - 1)]
    d = [(pts[i + 1][1] - pts[i][1]) / dx[i] for i in range(n - 1)]
    m = [d[0]] + [0 if d[i - 1] * d[i] <= 0 else (d[i - 1] + d[i]) / 2 for i in range(1, n - 1)] + [d[-1]]
    for i in range(n - 1):
        if d[i] == 0:
            m[i] = m[i + 1] = 0
            continue
        a, b = m[i] / d[i], m[i + 1] / d[i]
        if a * a + b * b > 9:
            k = 3 / (a * a + b * b) ** 0.5
            m[i], m[i + 1] = k * a * d[i], k * b * d[i]
    out = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(n - 1):
        w = dx[i] / 3
        out += (f" C{pts[i][0] + w:.1f} {pts[i][1] + m[i] * w:.1f} {pts[i + 1][0] - w:.1f} {pts[i + 1][1] - m[i + 1] * w:.1f} "
                f"{pts[i + 1][0]:.1f} {pts[i + 1][1]:.1f}")
    return out


def line_month_labels(cells, xs, size):
    """[(x, text, anchor)] for the month names under the 30-day chart, skipping point 0 if it would crowd the 1st."""
    firsts = [i for i, (d, _) in enumerate(cells) if d.day == 1]
    lead_w = text_width(cells[0][0].strftime("%b"), "m400", size)
    show_lead = (not firsts or firsts[0] == 0 or
                 xs[firsts[0]] - text_width(cells[firsts[0]][0].strftime("%b"), "m400", size) / 2 > xs[0] + lead_w + 6)
    return [(xs[i], d.strftime("%b"), "middle" if i else "start")
            for i, (d, _) in enumerate(cells) if d.day == 1 or (i == 0 and show_lead)]


def line_chart(t, data, today, phone=False):
    """The daily contributions of the last 30 days as a sticker-style line chart. Returns (Svg, total, title)."""
    cells = last_days(data, today)
    total = total_of(cells)
    title = title_of(total, "in the last 30 days")
    W = 440 if phone else 880
    cx, cw = (26, 388) if phone else (28, 824)
    head = 26 if phone else 24
    label = 15
    ph = 220 if phone else 210                               # plot height
    left = cx + 16 + (34 if phone else 38)                    # room for the y labels
    right = cx + cw - (18 if phone else 24)
    top = 28 + 16 + head + (24 if phone else 0) + 34
    top_v = max(c for _, c in cells)
    ticks = y_ticks(top_v)
    ymax = max(top_v, 1)
    inner = (top - 28) + ph + 58
    s = Svg(W, int(inner + 2 * 28), t, title)
    s.board()
    s.rect(cx + 4, 32, cw, inner, "line", 16)
    s.rect(cx, 28, cw, inner, "card", 16, "line", 2)
    nw = s.text(cx + 16, 28 + 16 + head, fmt(total), "f700", head)
    words = title[len(fmt(total)) + 1:]
    if phone:
        s.text(cx + 16, 28 + 16 + head + 24, words, "m400", 16)
    else:
        s.text(cx + 16 + nw + 8, 28 + 16 + head, words, "m400", 18)
    base = top + ph

    def yy(v):
        return base - v / ymax * ph

    grid = mix(s.col("muted"), s.col("card"), 0.3)
    for v in ticks:
        dash = "" if v == 0 else 'stroke-dasharray="5 5"'
        s.add(f'<line x1="{left:.1f}" y1="{yy(v):.1f}" x2="{right:.1f}" y2="{yy(v):.1f}" stroke="{grid}" stroke-width="1.5" {dash}/>')
        s.text(left - 8, yy(v) + 5, str(v), "m400", label, "muted", "end")
    step = (right - left) / (DAYS - 1)
    pts = [(left + i * step, yy(c)) for i, (_, c) in enumerate(cells)]
    every = 2 if phone else 1
    for i, (d, _) in enumerate(cells):
        if (DAYS - 1 - i) % every == 0:
            s.text(pts[i][0], base + 22, str(d.day), "m400", label, "muted", "middle")
    for lx, txt, anchor in line_month_labels(cells, [p[0] for p in pts], label):
        s.text(lx, base + 22 + 20, txt, "m400", label, "text", anchor)
    line = monotone_path(pts)
    s.add(f'<path d="{line} L{pts[-1][0]:.1f} {base:.1f} L{pts[0][0]:.1f} {base:.1f} Z" fill="{mix(s.col("pop"), s.col("card"), 0.16)}"/>')
    s.add(f'<path d="{line}" transform="translate(2 3)" fill="none" stroke="{s.col("line")}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')
    s.add(f'<path d="{line}" fill="none" stroke="{s.col("pop")}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
    r = 4.5 if phone else 5
    for (px, py), (_, c) in zip(pts, cells):
        s.add(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="{s.col("pop")}" stroke="{s.col("line")}" stroke-width="2" data-count="{c}"/>')
    return s, total, title


def graph_specs(data, today):
    """[(key, summary or None, start, end, words)] in README order: 6 months, 12 months, then 2026 back to the first year."""
    c = data["contrib"]
    first = date.fromisoformat(c["grid"]["first"])
    specs = [("6m", None), ("12m", "Last 12 months")]
    specs += [(str(y), str(y)) for y in range(today.year, c["since_year"] - 1, -1)]
    out = []
    for key, summary in specs:
        start, end, words = range_of(key, today, first)
        out.append((key, summary, start, end, words))
    return out


def graph_titles(data, today):
    """[(key, summary or None, total, title)] in README order; the title doubles as the picture's alt text."""
    days = data["contrib"]["days"]
    out = []
    for key, summary, start, end, words in graph_specs(data, today):
        total = total_of(cells_of(days, start, end))
        out.append((key, summary, total, title_of(total, words)))
    return out


def make_graphs(t, data, today):
    """{asset name: Svg} for the desktop and phone image of every range, plus {key: (total, title)}."""
    svgs, info = {}, {}
    days = data["contrib"]["days"]
    svgs[f"line-30d-{t}.svg"] = line_chart(t, data, today)[0]
    svgs[f"line-30d-phone-{t}.svg"] = line_chart(t, data, today, phone=True)[0]
    for key, _, start, end, words in graph_specs(data, today):
        wide = key == "6m"
        for suffix, dim in (("", DESKTOP_WIDE if wide else DESKTOP_YEAR), ("-phone", PHONE_WIDE if wide else PHONE_YEAR)):
            s, total, title = graph_image(t, dim, days, start, end, words, "per day" if suffix else "contributions per day")
            svgs[f"graph-{key}{suffix}-{t}.svg"] = s
            info[key] = (total, title)
    return svgs, info
