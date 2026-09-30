#!/usr/bin/env python3
"""
Replace one or more textures inside a specialist .pak with PNGs from disk.

The pak is rewritten with entry order, names, compression method and timestamps
preserved - only the named payloads change. The original is copied to
ModBackups\<pak>.bak first - ONE backup, fixed name, overwritten every run - and
the result is diffed against it before the script returns. What was done is
appended to ModBackups\history.log; the tag lives there, never in a filename.

Pass every texture you are changing in ONE run. Running the script three times
in a row would leave the single backup holding two of the three new payloads
instead of the state you actually wanted back.

    python set_specialist_texture.py "<pak>" ui/textures/emt_bage.png new.png
    python set_specialist_texture.py "<pak>" emt_bage a.png emt_bg b.png emt_bgSmall c.png

🚨 LOCAL HEADER EXTRA FIELDS ARE NOT PRESERVED, DELIBERATELY. See rewrite().

Sizes are checked against what the current game build reserves:
    bage     364 x 364      (NOT the 293 x 293 the Saber guide documents)
    bg       380 x 92
    bgSmall  124 x 52
Pass --no-size-check to write something else deliberately.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import shutil
import struct
import sys
import zipfile

EXPECTED = {"bage": (364, 364), "bg": (380, 92), "bgsmall": (124, 52)}


def backup_dir(pak: str, override: str | None) -> str:
    """Where backups go.

    🚨 NEVER beside the pak. `Media\\Mods` is the folder the game enumerates for
    mods, and 37 stale `*.pak.pre-*-bak` files accumulated there before anyone
    noticed. The game's own strings ("Files of classes can't have equal names,
    please rename next files:") show duplicate definitions in that folder are a
    real failure mode, so a backup sitting next to its original is not inert.
    Default: <My Games>\\Expeditions\\ModBackups, one level above Media.
    """
    if override:
        d = override
    else:
        mods = os.path.dirname(os.path.abspath(pak))          # ...\Media\Mods
        d = os.path.join(os.path.dirname(os.path.dirname(mods)), "ModBackups")
    os.makedirs(d, exist_ok=True)
    return d


def png_size(data: bytes):
    if data[:8] != b"\x89PNG\r\n\x1a\x0a":
        return None
    return struct.unpack(">II", data[16:24])


def resolve_member(zf: zipfile.ZipFile, wanted: str) -> str:
    names = zf.namelist()
    if wanted in names:
        return wanted
    stem = os.path.splitext(os.path.basename(wanted))[0].lower()
    hits = [n for n in names
            if n.lower().startswith("ui/textures/")
            and os.path.splitext(os.path.basename(n))[0].lower() == stem]
    if len(hits) == 1:
        return hits[0]
    raise SystemExit(f"cannot resolve '{wanted}' in the pak; entries: {names}")


def expected_for(member: str):
    stem = os.path.splitext(os.path.basename(member))[0].lower()
    for suffix, dims in EXPECTED.items():
        if stem.endswith(suffix):
            return suffix, dims
    return None, None


def rewrite(path: str, payloads: dict[str, bytes]) -> None:
    """Rewrite the pak, swapping the named members.

    🚨 `new.extra` is left EMPTY on purpose. This line used to read
    `new.extra = info.extra`, copying the 36-byte NTFS-timestamp block out of the
    central directory - but Python writes ZipInfo.extra into the LOCAL header as
    well, and his 2025 paks carry that block in the central directory ONLY. The
    game's reader does not honour the local header's extra length, so it began
    every affected entry's payload 36 bytes early and the deflate stream failed.

    That is what killed Doc Windsor's avatar: his descriptor entries carried no
    extra field and loaded fine, so the specialist appeared in game with correct
    name, story and stats - and all three texture slots came up empty. It was the
    only one of his ten live mods with a non-zero local extra field.

    Both published mod.io mods checked (NOA Scout Trucks, RosenRot's Buggy) have
    local extra = 0, as do all seven of his other specialists. Zero is the
    proven-good profile. Do not "restore" the extra field.
    """
    with zipfile.ZipFile(path) as src:
        entries = [(i, src.read(i.filename)) for i in src.infolist()]
    tmp = path + ".tmp"
    with zipfile.ZipFile(tmp, "w") as out:
        for info, data in entries:
            data = payloads.get(info.filename, data)
            new = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            new.compress_type = info.compress_type
            new.external_attr = info.external_attr
            new.internal_attr = info.internal_attr
            new.create_system = info.create_system
            new.comment = info.comment
            out.writestr(new, data)
    os.replace(tmp, path)


def local_extra_lengths(path: str) -> dict[str, int]:
    """Walk the LOCAL file headers and report each entry's extra-field length.

    zipfile only ever shows the central directory, which is exactly why the
    36-byte local extra field that broke Doc Windsor survived a verify that
    reported "no metadata drift". Read the local headers or you are not checking.
    """
    blob = open(path, "rb").read()
    out, off = {}, 0
    while off + 30 <= len(blob) and struct.unpack_from("<I", blob, off)[0] == 0x04034B50:
        _, _, _, _, _, _, csize, _, nlen, elen = struct.unpack_from("<HHHHHIIIHH", blob, off + 4)
        name = blob[off + 30:off + 30 + nlen].decode("utf-8", "replace")
        out[name] = elen
        off += 30 + nlen + elen + csize
    return out


def verify(pak: str, backup: str, members: list[str]) -> list[str]:
    changed = []
    with zipfile.ZipFile(backup) as a, zipfile.ZipFile(pak) as b:
        na = [i.filename for i in a.infolist()]
        nb = [i.filename for i in b.infolist()]
        if na != nb:
            return [f"ENTRY LIST CHANGED: {na} -> {nb}"]
        for f in na:
            ia, ib = a.getinfo(f), b.getinfo(f)
            if (ia.compress_type, ia.date_time) != (ib.compress_type, ib.date_time):
                changed.append(f + " METADATA")
            if a.read(f) != b.read(f):
                changed.append(f + " DATA")
    stray = {n: e for n, e in local_extra_lengths(pak).items() if e}
    if stray:
        return [f"LOCAL HEADER EXTRA FIELD PRESENT (the game cannot read these): {stray}"]
    # A named member whose new bytes equal its old bytes produces no diff, and
    # that is not a failure: re-running a build where only one of three textures
    # actually changed is normal. Only report members that changed WITHOUT being
    # asked to, which is the drift this check exists to catch.
    unexpected = sorted(set(changed) - {m + " DATA" for m in members})
    if unexpected:
        return unexpected
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pak")
    ap.add_argument("pairs", nargs="+", metavar="MEMBER PNG",
                    help="one or more `member png` pairs; member may be just the texture stem")
    ap.add_argument("--tag", default="pre-texture")
    ap.add_argument("--backup-dir", default=None,
                    help="where to put the backup; default is <My Games>\\Expeditions\\ModBackups, "
                         "deliberately OUTSIDE the folder the game scans for mods")
    ap.add_argument("--no-size-check", action="store_true")
    args = ap.parse_args()

    if len(args.pairs) % 2:
        return print("pairs must be `member png` - got an odd number of arguments") or 1

    payloads: dict[str, bytes] = {}
    report: list[str] = []
    with zipfile.ZipFile(args.pak) as zf:
        for member_arg, png in zip(args.pairs[0::2], args.pairs[1::2]):
            payload = open(png, "rb").read()
            size = png_size(payload)
            if size is None:
                return print(f"{png} is not a PNG") or 1
            member = resolve_member(zf, member_arg)
            old = png_size(zf.read(member))
            kind, want = expected_for(member)
            if want and size != want and not args.no_size_check:
                print(f"REFUSING: {member} is a `{kind}` slot and wants {want[0]}x{want[1]}, "
                      f"got {size[0]}x{size[1]}. Pass --no-size-check to override.")
                return 1
            payloads[member] = payload
            report.append(f"{member} {old[0]}x{old[1]} -> {size[0]}x{size[1]}")

    # ONE backup, fixed name, overwritten every run. No timestamp in the
    # filename - a timestamp is what turns a backup into a backup chain, and
    # 295 of those had to be deleted by hand. The previous state is the only
    # one anybody has ever wanted back.
    bdir = backup_dir(args.pak, args.backup_dir)
    backup = os.path.join(bdir, os.path.basename(args.pak) + ".bak")
    shutil.copy2(args.pak, backup)
    with open(os.path.join(bdir, "history.log"), "a", encoding="utf-8") as log:
        log.write(f"{_dt.datetime.now():%Y-%m-%d %H:%M:%S}  {args.tag}  "
                  f"{os.path.basename(args.pak)}  {', '.join(payloads)}\n")
    rewrite(args.pak, payloads)

    problems = verify(args.pak, backup, list(payloads))
    print(f"{os.path.basename(args.pak)}   backup {os.path.basename(backup)}")
    for line in report:
        print("  " + line)
    if problems:
        print("  VERIFY FAILED:", problems)
        return 1
    print(f"  verified: exactly {len(payloads)} payload(s) changed, no metadata drift, "
          f"no local-header extra fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
