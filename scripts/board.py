# The "On GitHub" stats board: sticker counters with an icon each. The contribution graphs are graphs.py.
# Desktop is 880 wide; the phone variant is 440 wide with a 2-column counter grid.
from cards import fmt, long_date, short_date
from svgkit import Svg, wrap

FILLS = ["lx", "li", "rd", "x", "bd", "yt", "li"]
ROT = [-1.2, 1, -0.8, 1.2, -1, 0.8, -1.2]


def streak_text(cur):
    """The caption under the current streak. With no streak right now there is no start date to print."""
    if cur["days"] <= 0 or not cur["start"]:
        return "no streak right now"
    return f"current streak, since {short_date(cur['start'])}"


def counters(data):
    c, r = data["contrib"], data["repos"]
    cur, best = c["current_streak"], c["longest_streak"]
    since = f"contributions since {c['since_year']}"
    return [
        (fmt(c["last_year"]), "contributions in the last year"),
        (f"{cur['days']} days", streak_text(cur)),
        (f"{best['days']} days", "longest streak ever"),
        (fmt(c["all_time"]), since),
        (fmt(r["public_repos"]), "public repos"),
        (fmt(r["stars"]), "stars earned"),
        (fmt(r["downloads"]), "release downloads"),
    ]


def board_label(data):
    c, r = data["contrib"], data["repos"]
    cur, best = c["current_streak"], c["longest_streak"]
    streak = (f"a {cur['days']}-day current streak, since {short_date(cur['start'])}" if cur["days"] > 0 and cur["start"]
              else "no streak right now")
    return (f"On GitHub: {fmt(c['last_year'])} contributions in the last year, {streak}, "
            f"longest streak {best['days']} days, {fmt(c['all_time'])} contributions since {c['since_year']}, "
            f"{r['public_repos']} public repos, {r['stars']} stars earned, {fmt(r['downloads'])} downloads of my releases.")


def sticker(s, x, y, w, h, fill, rot):
    s.add(f'<g transform="rotate({rot} {x + w / 2:.1f} {y + h / 2:.1f})">')
    s.rect(x + 4, y + 4, w, h, "line", 18)
    s.rect(x, y, w, h, fill, 18, "line", 2)


# Simple 24 x 24 icons: (path, closed). Closed shapes get the token fill, all get the ink outline.
ICONS = {
    "calendar": [("M5 5H19A2 2 0 0 1 21 7V19A2 2 0 0 1 19 21H5A2 2 0 0 1 3 19V7A2 2 0 0 1 5 5Z", True),
                 ("M3 10H21", False), ("M8 3V7", False), ("M16 3V7", False)],
    "flame": [("M12 2.5C12.5 7 18 9 18 14.5A6 6 0 0 1 6 14.5C6 11.5 8 10 9 8C10 10 11 10.5 12 9.5C12.5 7 12 4.5 12 2.5Z", True)],
    "trophy": [("M7 4H17V10A5 5 0 0 1 7 10Z", True), ("M7 6H4V8A3 3 0 0 0 7 11", False),
               ("M17 6H20V8A3 3 0 0 1 17 11", False), ("M12 15V19", False), ("M8 20.5H16", False)],
    "chart": [("M4 20V12H8V20Z", True), ("M10 20V5H14V20Z", True), ("M16 20V9H20V20Z", True)],
    "folder": [("M3 7A2 2 0 0 1 5 5H9L11 7.5H19A2 2 0 0 1 21 9.5V18A2 2 0 0 1 19 20H5A2 2 0 0 1 3 18Z", True)],
    "star": [("M12 3L14.7 8.6L20.8 9.5L16.4 13.8L17.4 19.9L12 17L6.6 19.9L7.6 13.8L3.2 9.5L9.3 8.6Z", True)],
    "download": [("M10 3H14V9H18L12 16L6 9H10Z", True), ("M4 18.5H20V21H4Z", True)],
}
ICON_OF = ["calendar", "flame", "trophy", "chart", "folder", "star", "download"]


def icon(s, kind, x, y, size, fill="pop"):
    """A sticker-style icon: ink outline from the tokens, one token fill, drawn from inline paths."""
    k = size / 24
    parts = "".join(f'<path d="{d}" fill="{s.col(fill) if closed else "none"}"/>' for d, closed in ICONS[kind])
    s.add(f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.3f})" stroke="{s.col("line")}" stroke-width="{1.9 / k:.2f}" '
          f'stroke-linecap="round" stroke-linejoin="round">{parts}</g>')


def github_board(t, data):
    cs = counters(data)
    W = 880
    s = Svg(W, 340, t, board_label(data))
    s.board()
    s.text(32, 54, "On GitHub", "f700", 30)
    s.text(848, 52, f"redrawn every night · {long_date(data['today'])}", "m400", 15, "muted", "end")
    for i in range(4):
        x, y = 32 + i * 208, 78
        sticker(s, x, y, 190, 138, FILLS[i], ROT[i])
        icon(s, ICON_OF[i], x + 190 - 14 - 30, y + 10, 30)       # top right, above the number's top
        num, lab = cs[i]
        s.text(x + 16, y + 70, num, "f700", 40)
        ly = y + 94
        for line in wrap(lab, "m400", 15, 160)[:3]:
            s.text(x + 16, ly, line, "m400", 15)
            ly += 19
        s.add("</g>")
    for j in range(3):
        x, y = (32, 292, 552)[j], 238
        sticker(s, x, y, (240, 240, 296)[j], 66, FILLS[4 + j], ROT[4 + j] * 0.6)
        icon(s, ICON_OF[4 + j], x + 14, y + 17, 32)
        num, lab = cs[4 + j]
        nw = s.text(x + 56, y + 44, num, "f700", 34)
        s.text(x + 56 + nw + 10, y + 40, lab, "m400", 15)
        s.add("</g>")
    return s
