"""Minimal SVG builder for the Ali Salman profile cards."""
from __future__ import annotations

import json
import os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
TOK = json.load(open(os.path.join(HERE, "tokens.json"), encoding="utf8"))
FONT_SANS = TOK["font"]["sans"]
FONT_MONO = TOK["font"]["mono"]


class Svg:
    def __init__(self, w: int, h: int, theme: str, label: str):
        self.w, self.h, self.theme, self.label = w, h, theme, label
        self.c = TOK["color"][theme]
        self.parts: list[str] = []
        self.defs: list[str] = []
        self._id = 0

    def uid(self, p: str = "i") -> str:
        self._id += 1
        return f"{p}{self._id}"

    def col(self, k: str) -> str:
        return self.c.get(k, k)

    def add(self, s: str) -> None:
        self.parts.append(s)

    def rect(
        self,
        x,
        y,
        w,
        h,
        fill="card",
        r=0,
        stroke=None,
        sw=1.5,
        extra="",
    ) -> None:
        s = f' stroke="{self.col(stroke)}" stroke-width="{sw}"' if stroke else ""
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
            f'fill="{self.col(fill)}"{s}{extra}/>'
        )

    def circle(self, cx, cy, r, fill="teal", stroke=None, sw=2) -> None:
        s = f' stroke="{self.col(stroke)}" stroke-width="{sw}"' if stroke else ""
        self.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{self.col(fill)}"{s}/>')

    def text(
        self,
        x,
        y,
        s: str,
        size=16,
        fill="text",
        weight=600,
        anchor="start",
        mono=False,
        extra="",
    ) -> None:
        fam = FONT_MONO if mono else FONT_SANS
        self.add(
            f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" '
            f'font-weight="{weight}" fill="{self.col(fill)}" text-anchor="{anchor}"{extra}>'
            f"{escape(s)}</text>"
        )

    def board(self, dots: bool = True) -> None:
        self.rect(0, 0, self.w, self.h, "bg", 20, "line", 1.5)
        if dots:
            pid = self.uid("dots")
            self.defs.append(
                f'<pattern id="{pid}" width="24" height="24" patternUnits="userSpaceOnUse">'
                f'<circle cx="2" cy="2" r="1.1" fill="{self.col("grid")}" opacity="0.55"/>'
                f"</pattern>"
            )
            self.add(f'<rect width="{self.w}" height="{self.h}" rx="20" fill="url(#{pid})"/>')

    def card(self, x, y, w, h, fill="card", r=16) -> None:
        self.rect(x, y, w, h, fill, r, "line", 1.5)

    def chip(self, x, y, label: str, fill="panel") -> int:
        # approximate width
        w = max(56, 8 * len(label) + 20)
        self.rect(x, y, w, 26, fill, 8, "line", 1)
        self.text(x + w / 2, y + 17, label, 11, "mint", 600, "middle", mono=True)
        return w

    def render(self) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" role="img">'
            f"<title>{escape(self.label)}</title>"
            f"<defs>{''.join(self.defs)}</defs>"
            f"{''.join(self.parts)}</svg>\n"
        )
