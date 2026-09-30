#!/usr/bin/env python3
"""Report the environment, then scan every installed specialist for known defects.

Run this before theorising about anything. Every check corresponds to a failure
that has actually shipped, and several of them are invisible to the obvious test:
a pak whose textures never load still reports a valid zip, and a descriptor whose
ability never renders still contains the ability.
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import specialist as sp  # noqa: E402

CLASSES = {0: "Mechanic", 1: "Logistics", 2: "Hydrologist",
           3: "Jaeger", 4: "Operator", 5: "Manager", 6: "NONE"}


def environment() -> Path | None:
    print("environment")
    root = sp.game_root()
    mods = sp.mods_dir()
    print(f"  game     {root or 'NOT FOUND  (set EXPEDITIONS_GAME)'}")
    print(f"  mods     {mods}{'' if mods.is_dir() else '   MISSING (set EXPEDITIONS_MODS)'}")
    print(f"  schema   {sp.SCHEMA or 'editor not installed, using bundled snapshot'}")
    print(f"  abilities {len(sp.catalogue())} modifiers known")
    return mods if mods.is_dir() else None


def check(pak: Path) -> tuple[str, list[str]]:
    problems: list[str] = []
    with zipfile.ZipFile(pak) as z:
        if z.testzip() is not None:
            problems.append("corrupt zip")
        names = z.namelist()
        twins = [n for n in names if n in (sp.DESCRIPTOR, sp.DESCRIPTOR_TWIN)]
        if sp.DESCRIPTOR not in names:
            return pak.name, ["no extensionless SpecialistDesc entry"]
        if len(twins) == 2 and z.read(twins[0]) != z.read(twins[1]):
            problems.append("descriptor twins differ (the .json is a decoy; write both)")
        v = json.loads(z.read(sp.DESCRIPTOR).decode("utf-8-sig"))["SslValue"]

        stray = {n: e for n, e in sp.local_extra_lengths(pak).items() if e}
        if stray:
            problems.append(f"LOCAL header extra field on {sorted(stray)} "
                            f"-> those entries will not load")

        for slot in ("bage", "bg", "bgSmall"):
            stem = v.get(slot)
            if not stem:
                problems.append(f"{slot} not set in the descriptor")
                continue
            hits = [n for n in names if n.lower().endswith(f"/{stem.lower()}.png")]
            if not hits:
                problems.append(f"{slot} points at {stem!r} but no such PNG in the pak")
                continue
            from PIL import Image
            im = Image.open(io.BytesIO(z.read(hits[0])))
            im.load()
            want = sp.SLOT_SIZES[slot]
            if im.size != want:
                problems.append(f"{slot} is {im.size[0]}x{im.size[1]}, must be "
                                f"{want[0]}x{want[1]} (it is drawn at native size, never scaled)")
            if im.mode != "RGBA" or (im.convert("RGBA").split()[3].getextrema()[0] > 250):
                problems.append(f"{slot} has no transparency and will render as a solid block")

        if v.get("speciality") == 6:
            problems.append("speciality is NONE, which crashes the game")
        if len(v.get("uiName", "")) > 20:
            problems.append(f"uiName is {len(v['uiName'])} chars, the limit is 20")

        for m in v.get("modifiers", []):
            for k, x in m.items():
                if k.endswith("UiDesc") or k in ("$type", "name", "group",
                                                 "allSameUiDesc", "overrideUiDesc"):
                    continue
                if isinstance(x, (int, float)) and m.get(k + "UiDesc") is None:
                    problems.append(f"{k} has no UiDesc: it applies but never shows on the card")
    return v.get("uiName", pak.stem), problems


def main() -> int:
    mods = environment()
    if mods is None:
        return 1
    paks = [p for p in sorted(mods.glob("SpecialistDesc_*.pak")) if p.stat().st_size]
    print(f"\n{len(paks)} specialists installed")
    holders: dict[str, list[str]] = {}
    bad = 0
    for p in paks:
        name, problems = check(p)
        with zipfile.ZipFile(p) as z:
            v = json.loads(z.read(sp.DESCRIPTOR).decode("utf-8-sig"))["SslValue"]
        for m in v.get("modifiers", []):
            for k, x in m.items():
                if isinstance(x, (int, float)) and not k.endswith("UiDesc"):
                    holders.setdefault(k, []).append(name)
        cls = CLASSES.get(v.get("speciality"), "?")
        if problems:
            bad += 1
            print(f"\n  {name}  [{cls}]")
            for pr in problems:
                print(f"      {pr}")
        else:
            print(f"  OK  {name:22s} {cls:12s} cost {v.get('cost')}")

    clashes = {k: vv for k, vv in holders.items() if len(set(vv)) > 1}
    if clashes:
        print("\nnumeric fields held by more than one specialist")
        print("  (fine if it is a deliberate pair with opposite signs, otherwise a balance clash)")
        for k, vv in sorted(clashes.items()):
            print(f"    {k}: {sorted(set(vv))}")

    print(f"\n{'all clear' if not bad else str(bad) + ' specialist(s) with problems'}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
