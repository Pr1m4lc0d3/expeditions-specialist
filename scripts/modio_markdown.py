#!/usr/bin/env python3
"""Convert a listing's markdown to the HTML mod.io actually renders.

🚨 **mod.io stores the description verbatim and converts nothing.** Posting
markdown puts literal `##` headings and raw `|` table pipes on the public page,
which reads as a broken listing. Six listings went up that way before anyone
looked at the stored value instead of the tool's own success message.

Which tags survive was measured, not assumed, by probing a hidden mod and
reading the description back:

    h2 h3 h4 p strong em code a table thead tbody tr th td ul li hr   all KEPT

So the conversion can be faithful instead of a flattening.

    python modio_markdown.py listing.md        # print the HTML
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_RULES = ("---", "***", "___")
_BULLET = ("- ", "* ")


def inline(s: str) -> str:
    """Spans: bold, code, links, and bare URLs. Escapes first, so order matters."""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', s)

    # Bare URLs become links. Anchors built above are parked behind sentinels
    # first, because the alternative is a lookbehind, and a lookbehind cannot
    # tell "inside an href" from "right after a tag". One that excluded '>'
    # silently left **{{URL}}** as plain text on six live pages: the URL sat
    # immediately after <strong>, so the guard fired on the wrong thing.
    parked: list[str] = []

    def park(m: re.Match) -> str:
        parked.append(m.group(0))
        return f"\x00{len(parked) - 1}\x00"

    s = re.sub(r"<a href=.*?</a>", park, s)
    s = re.sub(r"(https?://[^\s<)]+)", r'<a href="\1">\1</a>', s)
    return re.sub(r"\x00(\d+)\x00", lambda m: parked[int(m.group(1))], s)


def md_to_html(md: str) -> str:
    out: list[str] = []
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        cur = lines[i].strip()

        if not cur:
            i += 1

        elif cur in _RULES:
            out.append("<hr>")
            i += 1

        elif cur.startswith("#"):
            depth = len(cur) - len(cur.lstrip("#"))
            # '##' becomes h3, which is the level his own listings already use.
            out.append(f"<h{min(depth + 1, 4)}>{inline(cur.lstrip('#').strip())}"
                       f"</h{min(depth + 1, 4)}>")
            i += 1

        elif cur.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            # drop the |---|---| alignment row
            body = [r for r in rows[1:] if not all(set(c) <= set("-: ") for c in r)]
            out.append(
                "<table><thead><tr>"
                + "".join(f"<th>{inline(c)}</th>" for c in rows[0])
                + "</tr></thead><tbody>"
                + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
                          for r in body)
                + "</tbody></table>")

        elif cur.startswith(_BULLET):
            items: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(_BULLET):
                item = lines[i].strip()[2:]
                i += 1
                # a wrapped bullet continues on an indented line
                while (i < len(lines) and lines[i].startswith("  ")
                       and lines[i].strip()
                       and not lines[i].strip().startswith(("-", "*", "|", "#"))):
                    item += " " + lines[i].strip()
                    i += 1
                items.append(item)
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")

        else:
            para: list[str] = []
            while i < len(lines):
                ln = lines[i].strip()
                if not ln or ln in _RULES or ln.startswith(("|", "#") + _BULLET):
                    break
                para.append(ln)
                i += 1
            out.append(f"<p>{inline(' '.join(para))}</p>")

    return "".join(out)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    print(md_to_html(Path(sys.argv[1]).read_text(encoding="utf-8")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
