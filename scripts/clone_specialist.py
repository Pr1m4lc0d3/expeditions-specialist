#!/usr/bin/env python3
"""
Clone an existing custom-specialist .pak into a new one with a new id, a new
UI name and its own set of textures.

Everything else - modifiers, cost, speciality, description - is copied verbatim
from the source descriptor, so the clone is the same specialist wearing a
different face.

    python clone_specialist.py \
        --source "<Mods>\\SpecialistDesc_Emergency Response Unit.pak" \
        --id Doc_Windsor_Ryan --ui-name "Daladim" --prefix ryan \
        --bage ryan_bage.png --bg ryan_bg.png --bgsmall ryan_bgsmall.png

Notes that matter (learned the hard way, see the memory vault):
  - The canonical descriptor inside a pak is the EXTENSIONLESS `SpecialistDesc`
    entry. Some paks carry a `SpecialistDesc.json` twin. BOTH are written here
    and asserted byte-identical.
  - `bage` is 364 x 364 in the current build, not the 293 x 293 the Saber guide
    documents. `bg` is 380 x 92, `bgSmall` is 124 x 52. Sizes are enforced.
  - `speciality` must not be NONE - that crashes the game. It is copied from the
    source, so it is whatever the source used.
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import zipfile

SIZES = {"bage": (364, 364), "bg": (380, 92), "bgsmall": (124, 52)}


def png_size(data: bytes):
    if data[:8] != b"\x89PNG\r\n\x1a\x0a":
        return None
    return struct.unpack(">II", data[16:24])


def read_descriptor(zf: zipfile.ZipFile) -> dict:
    for entry in ("SpecialistDesc", "SpecialistDesc.json"):
        try:
            return json.loads(zf.read(entry).decode("utf-8-sig"))
        except KeyError:
            continue
    raise SystemExit("no SpecialistDesc in the source pak")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--id", required=True,
                    help="descriptor `name` and the pak filename suffix")
    ap.add_argument("--ui-name", required=True, help="max 20 characters")
    ap.add_argument("--prefix", required=True,
                    help="texture name stem, e.g. `ryan` -> ryan_bage / ryan_bg / ryan_bgsmall")
    ap.add_argument("--bage", required=True)
    ap.add_argument("--bg", required=True)
    ap.add_argument("--bgsmall", required=True)
    ap.add_argument("--out-dir", default=None,
                    help="defaults to the source pak's directory")
    ap.add_argument("--ui-desc", default=None,
                    help="override the description; omitted = copy the source's")
    args = ap.parse_args()

    if len(args.ui_name) > 20:
        return print(f"uiName is {len(args.ui_name)} chars, the game allows 20") or 1

    with zipfile.ZipFile(args.source) as zf:
        desc = read_descriptor(zf)

    textures = {}
    for kind, path in (("bage", args.bage), ("bg", args.bg), ("bgsmall", args.bgsmall)):
        data = open(path, "rb").read()
        size = png_size(data)
        if size != SIZES[kind]:
            return print(f"{path} is {size}, `{kind}` must be {SIZES[kind]}") or 1
        textures[kind] = data

    names = {"bage": f"{args.prefix}_bage",
             "bg": f"{args.prefix}_bg",
             "bgsmall": f"{args.prefix}_bgsmall"}

    desc["name"] = args.id
    v = desc["SslValue"]
    v["uiName"] = args.ui_name
    v["bage"] = names["bage"]
    v["bg"] = names["bg"]
    v["bgSmall"] = names["bgsmall"]
    if args.ui_desc is not None:
        v["uiDesc"] = args.ui_desc
        if len(v["uiDesc"]) > 280:
            # NOT a refusal. The guide's 280 is not enforced by the game: Doc
            # Windsor ships 291 and Nom Nom ships 519, and both have rendered
            # since 2025. Refusing here blocked two specialists that were fine.
            print(f"  note: uiDesc is {len(v['uiDesc'])} chars (guide says 280); "
                  f"the longest that renders in game is 519, so this is allowed")
    elif len(v.get("uiDesc", "")) > 280:
        # The guide says 280. Doc Windsor's blurb is 291 and renders fine in
        # game, so the limit is not enforced - warn, do not refuse, when the
        # over-length text is the source's own and already known to work.
        print(f"  note: copied uiDesc is {len(v['uiDesc'])} chars (guide says 280); "
              f"the source ships this and it renders, so keeping it")

    blob = json.dumps(desc, indent=4).encode("utf-8")

    out_dir = args.out_dir or os.path.dirname(os.path.abspath(args.source))
    out = os.path.join(out_dir, f"SpecialistDesc_{args.id}.pak")
    if os.path.exists(out):
        return print(f"{out} already exists; delete it first") or 1

    with zipfile.ZipFile(out, "w") as z:
        z.writestr("SpecialistDesc", blob, zipfile.ZIP_DEFLATED)
        z.writestr(zipfile.ZipInfo("ui/"), b"")
        z.writestr(zipfile.ZipInfo("ui/textures/"), b"")
        for kind in ("bage", "bg", "bgsmall"):
            z.writestr(f"ui/textures/{names[kind]}.png", textures[kind],
                       zipfile.ZIP_DEFLATED)
        z.writestr("SpecialistDesc.json", blob, zipfile.ZIP_DEFLATED)

    with zipfile.ZipFile(out) as z:
        assert z.read("SpecialistDesc") == z.read("SpecialistDesc.json"), \
            "descriptor twins diverged"
        listing = [(i.filename, i.file_size) for i in z.infolist()]
    print(f"wrote {out}")
    for n, s in listing:
        print(f"   {s:>8}  {n}")
    print(f"   id={args.id}  uiName={args.ui_name!r}  speciality={v['speciality']}  cost={v['cost']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
