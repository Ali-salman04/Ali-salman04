# Fetches every number the profile shows. All sources are public and need no secret.
# GITHUB_TOKEN, when it is in the environment, only lifts the REST rate limit.
#
# Net.get() is the one place that touches the network. In offline mode it reads scripts/fixtures/
# instead, and with record=True it saves every live response there (the contribution pages are
# slimmed to the parts the parser reads).
import base64, json, os, re, urllib.error, urllib.request
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
UA = "ali-salman-profile-build (github.com/Ali-salman04/Ali-salman04)"


class SourceError(Exception):
    """One source could not be read or understood."""


class CalendarError(SourceError):
    """The contribution calendar could not be read: the build stops and keeps yesterday's cards."""


# ------------------------------------------------------------------ network and fixtures
class Net:
    def __init__(self, offline=False, record=False, fixtures=FIXTURES, token=None):
        self.offline, self.record, self.fixtures = offline, record, fixtures
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN")

    def get(self, url, name, binary=False):
        if self.offline:
            path = os.path.join(self.fixtures, name)
            if not os.path.exists(path):
                raise SourceError(f"no fixture {name}")
            with open(path, "rb") as f:
                data = f.read()
        else:
            headers = {"User-Agent": UA}
            if self.token and url.startswith("https://api.github.com/"):
                headers["Authorization"] = f"Bearer {self.token}"
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
                    data = r.read()
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                raise SourceError(f"{url}: {e}")
            if self.record:
                os.makedirs(self.fixtures, exist_ok=True)
                saved = slim_contrib(data.decode("utf8")).encode("utf8") if name.startswith("contrib-") else data
                with open(os.path.join(self.fixtures, name), "wb") as f:
                    f.write(saved)
        return data if binary else data.decode("utf8")


# ------------------------------------------------------------------ contribution calendar
class _Calendar(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cells, self.tips, self.heading = [], {}, []
        self._tip_for, self._tip, self._in_h = None, [], False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "td" and a.get("data-date"):
            self.cells.append((a["data-date"], a.get("id"), int(a.get("data-level") or 0)))
        elif tag == "tool-tip" and a.get("for"):
            self._tip_for, self._tip = a["for"], []
        elif tag == "h2" and a.get("id") == "js-contribution-activity-description":
            self._in_h = True

    def handle_data(self, data):
        if self._tip_for is not None:
            self._tip.append(data)
        if self._in_h:
            self.heading.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self._tip_for is not None:
            self.tips[self._tip_for] = " ".join("".join(self._tip).split())
            self._tip_for = None
        elif tag == "h2":
            self._in_h = False


def parse_calendar(html):
    """The public contributions page -> {"heading": int, "days": [(iso date, count, level 0-4), ...]}.
    Counts come from each cell's tooltip ("No contributions on ...", "N contributions on ...").
    The heading total must equal the sum of the cells, otherwise the markup changed: CalendarError."""
    p = _Calendar()
    p.feed(html)
    m = re.search(r"([\d,]+)\s+contributions?", " ".join("".join(p.heading).split()))
    if not m:
        raise CalendarError("contribution heading not found")
    heading = int(m.group(1).replace(",", ""))
    if not p.cells:
        raise CalendarError("no calendar cells found")
    days = []
    for d, cid, level in p.cells:
        tip = p.tips.get(cid)
        if tip is None:
            raise CalendarError(f"no tooltip for {d}")
        t = re.match(r"(No|[\d,]+) contributions? on", tip)
        if not t:
            raise CalendarError(f"unreadable tooltip for {d}: {tip!r}")
        days.append((d, 0 if t.group(1) == "No" else int(t.group(1).replace(",", "")), level))
    if sum(c for _, c, _ in days) != heading:
        raise CalendarError(f"heading says {heading} but the cells add up to {sum(c for _, c, _ in days)}")
    return {"heading": heading, "days": days}


def slim_contrib(html):
    """Keeps only what parse_calendar reads, for the saved fixtures."""
    p = _Calendar()
    p.feed(html)
    out = ['<html><body><h2 id="js-contribution-activity-description">' + " ".join("".join(p.heading).split()) + "</h2><table>"]
    for d, cid, level in p.cells:
        out.append(f'<td data-date="{d}" id="{cid}" data-level="{level}"></td><tool-tip for="{cid}">{p.tips.get(cid, "")}</tool-tip>')
    out.append("</table></body></html>")
    return "\n".join(out)


def streaks(days, today):
    """days: {iso date: count}. A day with no contributions yet today does not break the current streak."""
    iso = lambda d: d.isoformat()
    d = today if days.get(iso(today), 0) > 0 else today - timedelta(days=1)
    cur, start, end = 0, None, d
    while days.get(iso(d), 0) > 0:
        cur += 1
        start = d
        d -= timedelta(days=1)
    best = {"days": 0, "start": None, "end": None}
    run, run_start, prev = 0, None, None
    for k in sorted(k for k, v in days.items() if v > 0 and k <= iso(today)):
        dk = date.fromisoformat(k)
        if prev is not None and dk - prev == timedelta(days=1):
            run += 1
        else:
            run, run_start = 1, dk
        if run >= best["days"]:
            best = {"days": run, "start": iso(run_start), "end": iso(dk)}
        prev = dk
    return ({"days": cur, "start": iso(start) if start else None, "end": iso(end) if start else None}, best)


def fetch_contrib(net, user, created, today, cached_years):
    """Returns (contrib dict, years cache). Completed years are read once and kept in the cache."""
    base = f"https://github.com/users/{user}/contributions"
    try:
        last = parse_calendar(net.get(base, "contrib-last-year.html"))
    except CalendarError:
        raise
    except SourceError as e:
        raise CalendarError(str(e))
    all_days, years = {}, {}
    try:
        for y in range(int(created[:4]), today.year + 1):
            cached = cached_years.get(str(y)) if y < today.year else None
            if cached:
                years[str(y)] = cached
            else:
                cal = parse_calendar(net.get(f"{base}?from={y}-01-01&to={y}-12-31", f"contrib-{y}.html"))
                years[str(y)] = {"total": cal["heading"], "days": {d: c for d, c, _ in cal["days"] if c and d.startswith(str(y))}}
            all_days.update(years[str(y)]["days"])
    except SourceError as e:
        raise CalendarError(str(e))
    for d, c, _ in last["days"]:
        if c:
            all_days[d] = c
        else:
            all_days.pop(d, None)
    iso = today.isoformat()
    all_days = {d: c for d, c in all_days.items() if d <= iso}
    cur, best = streaks(all_days, today)
    cells = sorted(last["days"])
    grid = {"first": cells[0][0], "counts": [c for _, c, _ in cells], "levels": "".join(str(l) for _, _, l in cells)}
    contrib = {
        "last_year": last["heading"],
        "this_year": sum(c for d, c in all_days.items() if d.startswith(str(today.year))),
        "all_time": sum(all_days.values()),
        "since_year": int(created[:4]),
        "current_streak": cur,
        "longest_streak": best,
        "grid": grid,
        "days": all_days,        # date -> count, nonzero days only: the cells of every graph
    }
    return contrib, {k: v for k, v in years.items() if int(k) < today.year}


# ------------------------------------------------------------------ the other sources
def fetch_repos(net, user):
    """Public, non-fork repos owned by the user: count, stars, release downloads, latest release tag."""
    repos, page = [], 1
    while True:
        name = "repos.json" if page == 1 else f"repos-{page}.json"
        batch = json.loads(net.get(f"https://api.github.com/users/{user}/repos?type=owner&per_page=100&page={page}", name))
        repos += batch
        if len(batch) < 100 or page >= 5:
            break
        page += 1
    own = [r for r in repos if not r["fork"] and not r["private"]]
    out = {"public_repos": len(own), "stars": sum(r["stargazers_count"] for r in own), "downloads": 0, "repos": {}}
    for r in own:
        rels = json.loads(net.get(f"https://api.github.com/repos/{user}/{r['name']}/releases?per_page=100", f"releases-{r['name']}.json"))
        rels = [x for x in rels if not x.get("draft")]
        dl = sum(a["download_count"] for x in rels for a in x.get("assets", []))
        tag = next((x["tag_name"] for x in rels if not x.get("prerelease")), None)
        out["downloads"] += dl
        out["repos"][r["name"]] = {"stars": r["stargazers_count"], "downloads": dl, "tag": tag,
                                   "description": r.get("description") or "", "language": r.get("language") or ""}
    return out


def _challenge_blocks(js):
    """[(id, text)] for every challenge in the `challenges: [ ... ]` list of data.js. A challenge starts at
    `{ id: "..."` written at the same indent as the first one; goals and platforms inside are indented deeper."""
    m = re.search(r"\bchallenges:\s*\[", js)
    if not m:
        raise SourceError("no challenges list in data.js")
    rest = js[m.end():]
    first = re.search(r'\{\s*id:\s*"', rest)
    if not first:
        return []
    indent = rest[rest.rfind("\n", 0, first.start()) + 1: first.start()]
    if indent.strip():
        raise SourceError("the challenges list in data.js has an unexpected shape")
    marks = list(re.finditer(r'(?m)^' + re.escape(indent) + r'\{\s*id:\s*"([^"]+)"', rest))
    return [(mk.group(1), rest[mk.start(): marks[i + 1].start() if i + 1 < len(marks) else len(rest)])
            for i, mk in enumerate(marks)]


def _parse_challenge(cid, block):
    """The fields the profile draws from one challenge block; a field that is not there is None."""
    head = re.split(r"\b(?:goals|platforms|entries):", block, maxsplit=1)[0]
    pick = lambda pat, text=head: (re.search(pat, text) or [None, None])[1]
    start, days = pick(r'\bstart:\s*"(\d{4}-\d\d-\d\d)"'), pick(r"\bdays:\s*(\d+)")
    tg = re.search(r'target:\s*\{\s*pid:\s*"([\w-]+)"\s*,\s*n:\s*(\d+)', head)
    target = {"pid": tg.group(1), "n": int(tg.group(2))} if tg else None
    c = {"id": cid, "title": pick(r'\btitle:\s*"([^"]*)"'), "status": pick(r'\bstatus:\s*"([^"]*)"'),
         "start": start, "days": int(days) if days else None, "target": target}
    # one entry per logged day: {"day":N, ... "counts":{"x":2664, ...}}
    plat = re.search(r"\bplatforms:(.*?)(?=\bentries:|$)", block, re.S)
    entries = re.split(r'(?=\{"day":\d+,)', block.split("entries:", 1)[1]) if "entries:" in block else []
    entries = [e for e in entries if e.startswith('{"day":')]
    c["day"] = len(entries)
    c["count"], c["count_is_start"], c["platform"] = None, False, None
    if target:
        pid = target["pid"]
        for e in reversed(entries):
            cm = re.search(r'"counts":\{([^}]*)\}', e)
            hit = re.search(r'"%s":(\d+)' % re.escape(pid), cm.group(1)) if cm else None
            if hit:
                c["count"] = int(hit.group(1))
                break
        po = re.search(r'\{\s*id:\s*"%s"([^}]*)\}' % re.escape(pid), plat.group(1)) if plat else None
        if po:
            c["platform"] = {"name": pick(r'\bname:\s*"([^"]*)"', po.group(1)), "label": pick(r'\blabel:\s*"([^"]*)"', po.group(1))}
            if not entries:                       # day 0: the count before day 1 is the platform's start
                st = pick(r"\bstart:\s*(\d+)", po.group(1))
                c["count"], c["count_is_start"] = (int(st), True) if st else (None, False)
    if start and c["days"]:
        c["end"] = (date.fromisoformat(start) + timedelta(days=c["days"] - 1)).isoformat()
    return c


def fetch_challenge(net):
    """The challenge to show, from zazag.dev/data.js, whatever its id: the one with status "active" (the latest
    start if there are several); when none is active, the most recent "completed" one, shown as finished; when
    there is neither (planned challenges are never shown as running), state "none"."""
    js = net.get("https://zazag.dev/data.js", "data.js")
    found = [_parse_challenge(cid, block) for cid, block in _challenge_blocks(js)]
    latest = lambda cs: max(cs, key=lambda c: c["start"] or "") if cs else None
    chosen, state = latest([c for c in found if c["status"] == "active"]), "active"
    if not chosen:
        chosen, state = latest([c for c in found if c["status"] == "completed"]), "finished"
    if not chosen:
        return {"state": "none"}
    if not (chosen["title"] and chosen["start"] and chosen["days"]):
        raise SourceError(f'challenge "{chosen["id"]}" in data.js has an unexpected shape')
    chosen["state"] = state
    if state == "finished" and chosen["count_is_start"]:
        chosen["count"], chosen["count_is_start"] = None, False   # nothing was ever logged: no last count to show
    return chosen


def _probe_is_short(vid):
    """A Short answers 200 at /shorts/<id>; a long video redirects (303)."""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    try:
        r = urllib.request.build_opener(NoRedirect).open(
            urllib.request.Request(f"https://www.youtube.com/shorts/{vid}", headers={"User-Agent": UA}), timeout=30)
        return r.status == 200
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            return False
        raise SourceError(f"shorts probe for {vid}: {e}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise SourceError(f"shorts probe for {vid}: {e}")


def fetch_videos(net, channel_id, count=3):
    """The latest long videos from the channel feed, each with its thumbnail as base64."""
    xml = net.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}", "youtube-feed.xml")
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    vids = []
    for e in ET.fromstring(xml).findall("a:entry", ns):
        vid = e.findtext("yt:videoId", namespaces=ns)
        href = (e.find("a:link[@rel='alternate']", ns).get("href") if e.find("a:link[@rel='alternate']", ns) is not None else "")
        if "/shorts/" in href:
            short = True
        elif "/watch" in href:
            short = False
        elif net.offline:
            raise SourceError(f"cannot tell if {vid} is a Short")
        else:
            short = _probe_is_short(vid)
        if short:
            continue
        vids.append({"id": vid, "title": e.findtext("a:title", namespaces=ns), "date": e.findtext("a:published", namespaces=ns)[:10]})
        if len(vids) == count:
            break
    if not vids:
        raise SourceError("no long videos in the feed")
    for v in vids:
        raw = net.get(f"https://i.ytimg.com/vi/{v['id']}/mqdefault.jpg", f"thumb-{v['id']}.jpg", binary=True)
        v["thumb"] = "data:image/jpeg;base64," + base64.b64encode(raw).decode()
    return {"videos": vids}


def fetch_appstore(net, martva_id, country):
    mv = json.loads(net.get(f"https://itunes.apple.com/lookup?id={martva_id}&country={country}", "itunes-martva.json"))["results"][0]
    return {"martva_rating": mv.get("averageUserRating") or 0, "martva_count": mv.get("userRatingCount") or 0}


# ------------------------------------------------------------------ all of it
STALE_AFTER_DAYS = 3


def stale_sources(good, today, limit=STALE_AFTER_DAYS):
    """[(source, date of its last good fetch)] for every source whose last good fetch is more than `limit` days old."""
    return [(k, v) for k, v in sorted(good.items()) if (today - date.fromisoformat(v)).days > limit]


def collect(net, profile, today, state=None):
    """Returns (data, new_state, notes). Ali profile: GitHub contrib + repos only (no YT / X / App Store)."""
    state = state or {}
    saved = state.get("sources", {})
    user = profile["user"]
    contrib, years = fetch_contrib(net, user, profile["created"]["value"], today, state.get("years", {}))
    sources = {
        "repos": lambda: fetch_repos(net, user),
    }
    where = {"repos": "api.github.com users/%s/repos and releases" % user}
    data, notes, fresh = {
        "today": today.isoformat(),
        "contrib": contrib,
        "challenge": {"state": "none"},
        "videos": {"videos": []},
        "appstore": {"martva_rating": 0, "martva_count": 0},
    }, [], {}
    good = {k: v for k, v in state.get("good", {}).items() if k in sources}
    for k in saved:
        if k in sources:
            good.setdefault(k, state.get("fetched", today.isoformat()))
    for name, fn in sources.items():
        try:
            data[name] = fn()
            fresh[name] = data[name]
            good[name] = today.isoformat()
            origin = where[name] if not net.offline else "fixture"
        except (SourceError, KeyError, ValueError, IndexError, TypeError, ET.ParseError) as e:
            if name not in saved:
                raise SourceError(f"{name} failed ({e}) and there is no saved copy in state.json")
            data[name] = saved[name]
            origin = f"state.json (live fetch failed: {e})"
        notes.append((name, origin))
    new_state = {"fetched": today.isoformat(), "good": good,
                 "sources": {k: v for k, v in {**saved, **fresh}.items() if k in sources},
                 "years": {**state.get("years", {}), **years}}
    return data, new_state, notes
