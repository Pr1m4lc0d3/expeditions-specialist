#!/usr/bin/env python3
"""Turn one specialist .pak into the six platform zips mod.io wants.

The editor's File > Pack does this, but it needs the editor open with the
specialist loaded. The output is simple enough to make directly:

    SpecialistDesc_X_pc.zip  ->  SpecialistDesc_X.pak   (deflated)
                                 pc.pak                 (stored, ZERO BYTES)

Every platform zip holds the SAME pak. The only difference between them is the
name of an empty marker file, which is how the game and mod.io learn which
platform the upload is for.

    python pack_distribution.py "<path to>/SpecialistDesc_Treadwell.pak"
    python pack_distribution.py --all          # every specialist in Media/Mods

🚨 The byte profile matters. A map distribution zip rebuilt in Python once made
the map stop listing in game, so this reproduces the editor's output exactly:
no extra fields in either header, pak deflated, marker stored, external_attr
0x20, no archive comment. `--verify` checks a result against that profile.
"""
from __future__ import annotations

import argparse
import os
import struct
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import specialist as sp  # noqa: E402

#: zip suffix -> the platform marker file inside it. Both differ from the names
#: mod.io's API uses; see modio_publish.PLATFORM.
PLATFORMS = ("pc", "nx64", "playstation_4", "playstation_5", "xbox_one", "xbox_series")

_ARCHIVE_ATTR = 0x20  # FILE_ATTRIBUTE_ARCHIVE, what the editor writes


def pack(pak: Path, out_dir: Path) -> list[Path]:
    """Write the six platform zips for one pak. Returns the paths written."""
    data = pak.read_bytes()
    stamp = __import__("time").localtime(pak.stat().st_mtime)[:6]
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for plat in PLATFORMS:
        dest = out_dir / f"{pak.stem}_{plat}.zip"
        with zipfile.ZipFile(dest, "w") as z:
            inner = zipfile.ZipInfo(pak.name, date_time=stamp)
            inner.compress_type = zipfile.ZIP_DEFLATED
            inner.external_attr = _ARCHIVE_ATTR
            z.writestr(inner, data)
            marker = zipfile.ZipInfo(f"{plat}.pak", date_time=stamp)
            marker.compress_type = zipfile.ZIP_STORED
            marker.external_attr = _ARCHIVE_ATTR
            z.writestr(marker, b"")
        written.append(dest)
    return written


def verify(zip_path: Path) -> list[str]:
    """Check one zip against the editor's profile. Empty list means it matches."""
    problems = []
    blob = zip_path.read_bytes()
    off = 0
    names = []
    while off + 30 <= len(blob) and struct.unpack_from("<I", blob, off)[0] == 0x04034B50:
        _, flag, meth, _, _, _, csize, _, nlen, elen = struct.unpack_from("<HHHHHIIIHH", blob, off + 4)
        name = blob[off + 30:off + 30 + nlen].decode("utf-8", "replace")
        names.append(name)
        if elen:
            problems.append(f"{name}: local header extra field ({elen} bytes); the editor writes none")
        if flag:
            problems.append(f"{name}: general-purpose flags {flag:#06x}; the editor writes 0")
        off += 30 + nlen + elen + csize
    with zipfile.ZipFile(zip_path) as z:
        if z.comment:
            problems.append("archive comment present; the editor writes none")
        for i in z.infolist():
            if len(i.extra):
                problems.append(f"{i.filename}: central extra field; the editor writes none")
            if i.external_attr != _ARCHIVE_ATTR:
                problems.append(f"{i.filename}: external_attr {i.external_attr:#010x}, expected 0x20")
        if len(names) != 2:
            problems.append(f"expected 2 entries, found {len(names)}: {names}")
        else:
            marker = [n for n in names if n.rsplit(".", 1)[0] in PLATFORMS]
            if not marker:
                problems.append(f"no platform marker among {names}")
            elif z.getinfo(marker[0]).file_size:
                problems.append(f"{marker[0]} is not empty; the marker must be zero bytes")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pak", nargs="*", help="specialist .pak files")
    ap.add_argument("--all", action="store_true", help="every SpecialistDesc_*.pak in the mods folder")
    ap.add_argument("--out", default=None, help="output folder (default: dist/ beside this script)")
    ap.add_argument("--verify", action="store_true", help="check existing zips instead of writing")
    args = ap.parse_args()

    out = Path(args.out) if args.out else Path(__file__).parent.parent / "dist"
    paks = [Path(p) for p in args.pak]
    if args.all:
        paks += [p for p in sorted(sp.mods_dir().glob("SpecialistDesc_*.pak")) if p.stat().st_size]
    if not paks:
        ap.error("give one or more .pak paths, or --all")

    if args.verify:
        bad = 0
        for z in sorted(out.glob("*.zip")):
            problems = verify(z)
            print(f"  {'OK  ' if not problems else 'FAIL'} {z.name}")
            for p in problems:
                print(f"         {p}"); bad += 1
        print(f"\n{'profile matches the editor' if not bad else str(bad) + ' deviations'}")
        return 1 if bad else 0

    for pak in paks:
        if not pak.is_file():
            print(f"  missing: {pak}"); return 1
        written = pack(pak, out)
        problems = [p for z in written for p in verify(z)]
        total = sum(z.stat().st_size for z in written)
        print(f"  {pak.name} -> {len(written)} zips, {total/1024:.0f} KB total"
              f"{'' if not problems else '  PROFILE MISMATCH: ' + str(problems)}")
    print(f"\nwritten to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
