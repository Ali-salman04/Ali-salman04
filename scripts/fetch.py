"""Fetch public GitHub contribution calendar + repo stats. No secret required; GITHUB_TOKEN lifts rate limits."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import date, timedelta
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
UA = "ali-salman04-profile-build (github.com/Ali-salman04/Ali-salman04)"
STALE_AFTER_DAYS = 3


class SourceError(Exception):
    pass


class CalendarError(SourceError):
    pass


class Net:
    def __init__(self, offline=False, record=False, fixtures=FIXTURES, token=None):
        self.offline, self.record, self.fixtures = offline, record, fixtures
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN")

    def get(self, url: str, name: str, binary: bool = False):
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
                with urllib.request.urlopen(
                    urllib.request.Request(url, headers=headers), timeout=45
                ) as r:
                    data = r.read()
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                raise SourceError(f"{url}: {e}") from e
            if self.record:
                os.makedirs(self.fixtures, exist_ok=True)
                saved = (
                    slim_contrib(data.decode("utf8")).encode("utf8")
                    if name.startswith("contrib-")
                    else data
                )
                with open(os.path.join(self.fixtures, name), "wb") as f:
                    f.write(saved)
        return data if binary else data.decode("utf8")


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


def parse_calendar(html: str):
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
            # fallback: use level only
            days.append((d, 0 if level == 0 else level, level))
            continue
        t = re.match(r"(No|[\d,]+) contributions? on", tip)
        if not t:
            days.append((d, 0 if level == 0 else level, level))
            continue
        days.append((d, 0 if t.group(1) == "No" else int(t.group(1).replace(",", "")), level))
    return {"heading": heading, "days": days}


def slim_contrib(html: str) -> str:
    p = _Calendar()
    p.feed(html)
    out = ['<h2 id="js-contribution-activity-description">' + " ".join("".join(p.heading).split()) + "</h2>"]
    for d, cid, level in p.cells:
        out.append(f'<td data-date="{d}" id="{cid}" data-level="{level}"></td>')
        out.append(f'<tool-tip for="{cid}">{p.tips.get(cid, "No contributions on " + d)}</tool-tip>')
    return "\n".join(out)


def streaks(days: dict, today: date):
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
    return (
        {"days": cur, "start": iso(start) if start else None, "end": iso(end) if start else None},
        best,
    )


def fetch_contrib(net: Net, user: str, created: str, today: date, cached_years: dict):
    base = f"https://github.com/users/{user}/contributions"
    try:
        last = parse_calendar(net.get(base, "contrib-last-year.html"))
    except CalendarError:
        raise
    except SourceError as e:
        raise CalendarError(str(e)) from e

    all_days, years = {}, {}
    try:
        for y in range(int(created[:4]), today.year + 1):
            cached = cached_years.get(str(y)) if y < today.year else None
            if cached:
                years[str(y)] = cached
            else:
                cal = parse_calendar(
                    net.get(f"{base}?from={y}-01-01&to={y}-12-31", f"contrib-{y}.html")
                )
                years[str(y)] = {
                    "total": cal["heading"],
                    "days": {d: c for d, c, _ in cal["days"] if c and d.startswith(str(y))},
                }
            all_days.update(years[str(y)]["days"])
    except SourceError as e:
        raise CalendarError(str(e)) from e

    for d, c, _ in last["days"]:
        if c:
            all_days[d] = c
        else:
            all_days.pop(d, None)

    iso = today.isoformat()
    all_days = {d: c for d, c in all_days.items() if d <= iso}
    cur, best = streaks(all_days, today)
    cells = sorted(last["days"])
    grid = {
        "first": cells[0][0],
        "counts": [c for _, c, _ in cells],
        "levels": "".join(str(l) for _, _, l in cells),
        "dates": [d for d, _, _ in cells],
    }
    contrib = {
        "last_year": last["heading"],
        "this_year": sum(c for d, c in all_days.items() if d.startswith(str(today.year))),
        "all_time": sum(all_days.values()),
        "since_year": int(created[:4]),
        "current_streak": cur,
        "longest_streak": best,
        "grid": grid,
        "days": all_days,
        "years": {k: v["total"] for k, v in years.items()},
    }
    # include current year total from all_days
    contrib["years"][str(today.year)] = contrib["this_year"]
    return contrib, {k: v for k, v in years.items() if int(k) < today.year}


def fetch_repos(net: Net, user: str):
    repos, page = [], 1
    while True:
        name = "repos.json" if page == 1 else f"repos-{page}.json"
        batch = json.loads(
            net.get(
                f"https://api.github.com/users/{user}/repos?type=owner&per_page=100&page={page}",
                name,
            )
        )
        repos += batch
        if len(batch) < 100 or page >= 5:
            break
        page += 1
    own = [r for r in repos if not r.get("fork") and not r.get("private")]
    return {
        "public_repos": len(own),
        "stars": sum(r.get("stargazers_count", 0) for r in own),
        "repos": {
            r["name"]: {
                "stars": r.get("stargazers_count", 0),
                "description": r.get("description") or "",
                "language": r.get("language") or "",
            }
            for r in own
        },
    }


def collect(net: Net, profile: dict, today: date, state=None):
    state = state or {}
    saved = state.get("sources", {})
    user = profile["user"]
    contrib, years = fetch_contrib(
        net, user, profile["created"]["value"], today, state.get("years", {})
    )
    notes = []
    try:
        repos = fetch_repos(net, user)
        origin = "api.github.com" if not net.offline else "fixture"
        good_repos = today.isoformat()
    except SourceError as e:
        if "repos" not in saved:
            raise SourceError(f"repos failed ({e}) and no saved copy") from e
        repos = saved["repos"]
        origin = f"state.json ({e})"
        good_repos = state.get("good", {}).get("repos", today.isoformat())
    notes.append(("repos", origin))

    data = {"today": today.isoformat(), "contrib": contrib, "repos": repos}
    new_state = {
        "fetched": today.isoformat(),
        "good": {**state.get("good", {}), "repos": good_repos},
        "sources": {"repos": repos},
        "years": {**state.get("years", {}), **years},
    }
    return data, new_state, notes


def stale_sources(good: dict, today: date, limit: int = STALE_AFTER_DAYS):
    return [(k, v) for k, v in sorted(good.items()) if (today - date.fromisoformat(v)).days > limit]
