"""Entry: fetch public data, draw SVGs into assets/, write README.md."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timezone

import board
import cards
import fetch
import graphs
import readme

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
THEMES = cards.THEMES


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf8") as f:
        return json.load(f)


def make_assets(data: dict, P: dict) -> dict:
    out = {}
    for t in THEMES:
        out[f"hero-{t}.svg"] = cards.hero(t, data, P)
        out[f"whoami-{t}.svg"] = cards.whoami(t, data, P)
        out[f"github-{t}.svg"] = board.github_board(t, data)
        out[f"label-ship-{t}.svg"] = cards.label_bar(
            t, "What I ship", f"{len(P['apps'])} focus areas · production & shipped work"
        )
        L = P["links"]
        out[f"badge-gh-{t}.svg"] = cards.badge(t, L["github"]["label"], L["github"]["handle"], "teal")
        out[f"badge-li-{t}.svg"] = cards.badge(t, L["linkedin"]["label"], L["linkedin"]["handle"], "deep")
        out[f"badge-email-{t}.svg"] = cards.badge(t, L["email"]["label"], L["email"]["handle"], "mint")
        for a in P["apps"]:
            out[f"app-{a['id']}-{t}.svg"] = cards.app_card(t, a)
        out.update(graphs.make_graphs(t, data, date.fromisoformat(data["today"])))
    return out


def run(offline=False, record=False, out_root=ROOT, state_path=None, today=None, net=None, log=print):
    P = load_json(os.path.join(ROOT, "profile.json"))
    state_path = state_path or os.path.join(HERE, "state.json")
    state = None if offline else load_json(state_path)
    net = net or fetch.Net(offline=offline, record=record)
    if today is None:
        if offline:
            meta = load_json(os.path.join(fetch.FIXTURES, "meta.json"), {"today": date.today().isoformat()})
            today = date.fromisoformat(meta["today"])
        else:
            today = datetime.now(timezone.utc).date()

    data, new_state, notes = fetch.collect(net, P, today, state)
    svgs = make_assets(data, P)
    files = {}
    for name, s in svgs.items():
        files[f"assets/{name}"] = s.render()
    files["README.md"] = readme.render(data, P)

    assets_dir = os.path.join(out_root, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    # remove old generated profile svgs we own (keep legacy folders elsewhere)
    keep_prefixes = ("hero-", "whoami-", "github-", "label-", "badge-", "app-", "graph-")
    for old in os.listdir(assets_dir):
        if old.endswith(".svg") and old.startswith(keep_prefixes) and f"assets/{old}" not in files:
            os.remove(os.path.join(assets_dir, old))

    for rel, text in files.items():
        path = os.path.join(out_root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf8", newline="\n") as f:
            f.write(text if rel != "README.md" else text.rstrip("\n") + "\n")

    if not offline:
        with open(state_path, "w", encoding="utf8", newline="\n") as f:
            json.dump(new_state, f, indent=1, ensure_ascii=False)
            f.write("\n")

    log(f"built {len(svgs)} SVGs for {today.isoformat()} ({'offline' if offline else 'live'})")
    for what, where in notes:
        log(f"  source {what}: {where}")
    c = data["contrib"]
    log(f"  contributions last year: {c['last_year']:,}")
    log(f"  contributions this year: {c['this_year']:,}")
    log(f"  public repos: {data['repos']['public_repos']} · stars: {data['repos']['stars']}")

    stale = fetch.stale_sources(new_state.get("good", {}), today)
    return {"data": data, "files": files, "stale": stale}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--record-fixtures", action="store_true")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = run(offline=args.offline, record=args.record_fixtures)
    except fetch.SourceError as e:
        print(f"build stopped: {e}", file=sys.stderr)
        return 1
    if result["stale"]:
        what = ", ".join(f"{k} (last good {d})" for k, d in result["stale"])
        print(f"::error::stale sources: {what}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
