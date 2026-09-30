#!/usr/bin/env python3
"""Set a specialist's abilities, cost and lock state from a JSON design file.

Abilities are described declaratively so you never hand-assemble a modifier and
forget the part that makes it visible. Every numeric field gets a `UiDesc` or the
write is refused, because a field without one applies in play and never appears
on the card, which reads to a player as a missing ability.

    python set_specialist_stats.py mydesign.json

Design file:

    {
      "pak": "SpecialistDesc_MyGuy.pak",
      "cost": 1800,
      "isLocked": false,
      "modifiers": [
        {
          "type": "WheelDroneTorque",
          "group": "Ground Drone",
          "icon": "specAbilityDroneGround36",
          "fields": {
            "wheelDroneTorqueIncreasedPercent": [120, "Drone power", " +"]
          }
        },
        {
          "type": "WheelDroneArmorRestoreEverywhere",
          "group": "Ground Drone",
          "icon": "specAbilityDroneGround36",
          "flag": ["wheelDroneArmorRestoreEverywhere", "Drone armor repairs anywhere"]
        }
      ]
    }

`fields` maps a field name to [value, label, prefix]. A NEGATIVE VALUE INVERTS
the effect: that is how a penalty is written, and how a co-dependent pair works.
`flag` is for the five modifiers that carry no numbers at all.

Run `--list` to see every modifier and its fields on this machine.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import specialist as sp  # noqa: E402


def build(spec: dict) -> dict:
    kind = spec["type"]
    m = {"$type": "SpecialistModifier" + kind,
         "name": "SpecialistModifier" + kind,
         "allSameUiDesc": None, "overrideUiDesc": None,
         "group": sp.group(spec["group"], spec["icon"])}
    if "flag" in spec:
        field, label = spec["flag"]
        m[field + "UiDesc"] = sp.ui_desc(label, "")
        return m
    known = set(sp.modifier_fields(kind))
    for field, (value, label, prefix) in spec.get("fields", {}).items():
        if known and field not in known:
            raise SystemExit(f"{kind} has no field {field!r}. It has: {sorted(known)}")
        m[field] = value
        m[field + "UiDesc"] = sp.ui_desc(label, prefix)
    return m


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("design", nargs="?", help="JSON design file")
    ap.add_argument("--list", action="store_true", help="every modifier and its fields")
    ap.add_argument("--mods-dir", default=None, help="overrides EXPEDITIONS_MODS")
    args = ap.parse_args()

    if args.list:
        for name in sp.catalogue():
            fields = sp.modifier_fields(name)
            print(f"{name}\n    {', '.join(fields) if fields else '(flag, no numeric fields)'}")
        return 0
    if not args.design:
        ap.error("give a design file, or --list")

    spec = json.loads(Path(args.design).read_text(encoding="utf-8"))
    mods = Path(args.mods_dir) if args.mods_dir else sp.mods_dir()
    pak = mods / spec["pak"]
    if not pak.is_file():
        raise SystemExit(f"no such pak: {pak}")

    desc = sp.read_descriptor(pak)
    v = desc["SslValue"]
    v["modifiers"] = []
    for entry in spec["modifiers"]:
        sp.add_modifier(desc, build(entry))
    if "cost" in spec:
        v["cost"] = spec["cost"]
    if "isLocked" in spec:
        v["isLocked"] = spec["isLocked"]
    if "uiName" in spec:
        v["uiName"] = spec["uiName"]
    if "uiDesc" in spec:
        v["uiDesc"] = spec["uiDesc"]
    bak = sp.write_descriptor(pak, desc)

    out = sp.read_descriptor(pak)["SslValue"]
    stray = {n: e for n, e in sp.local_extra_lengths(pak).items() if e}
    print(f"{out['uiName']}  cost={out['cost']}  locked={out.get('isLocked')}  "
          f"backup={bak.name}  local-extra={stray or 'none'}")
    for m in out["modifiers"]:
        vals = {k: x for k, x in m.items()
                if not k.endswith("UiDesc")
                and k not in ("$type", "name", "group", "allSameUiDesc", "overrideUiDesc")}
        print(f"   {m['$type'].replace('SpecialistModifier', ''):32s} {vals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
