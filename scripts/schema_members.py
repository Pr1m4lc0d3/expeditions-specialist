#!/usr/bin/env python3
"""Print every field name the editor schema defines, per modifier.

A field name the schema does not define is **silently ignored**: no error, no
warning, the ability line is simply not drawn. Two of Saber's own member names
are misspelled, so the obvious spelling is the broken one:

    winchLenghtIncreasedMetersUiDesc        "Lenght"
    additionalAddonFuelCountCountUiDesc     "CountCount"
    additionalAddonWheelsCountCountUiDesc   "CountCount"
    additionalAddonRepairsCountUiDesc       ...but repairs is spelled normally

    python schema_members.py WinchImprove     # one modifier
    python schema_members.py                  # all of them
    python schema_members.py --check          # scan installed specialists

The parsing lives in `specialist.schema_members`; this is the CLI over it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import specialist as sp  # noqa: E402


def check() -> int:
    """Report every invented field across the installed specialists."""
    bad = 0
    for pak in sorted(sp.mods_dir().glob("SpecialistDesc_*.pak")):
        if not pak.stat().st_size:
            continue
        v = sp.read_descriptor(pak)["SslValue"]
        hits = [(m, f) for m in v["modifiers"] for f in sp.unknown_fields(m)]
        print(f"{'FAIL' if hits else 'OK  '} {v['uiName'][:24]:26s}"
              f"{'  ' + str(len(hits)) + ' ignored by the game' if hits else ''}")
        for m, f in hits:
            name = f.split(".", 1)[1]
            carried = m.get(name) is not None
            print(f"       {f}"
                  + ("   CARRIES TEXT THAT IS NEVER DRAWN" if carried else "   (null)"))
            bad += 1
    print(f"\n{bad} invented field(s) across the roster")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modifier", nargs="*")
    ap.add_argument("--check", action="store_true",
                    help="scan installed specialists for invented field names")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.check:
        return check()

    t = sp.schema_members()
    if args.json:
        print(json.dumps({k: list(v) for k, v in t.items()}, indent=1, sort_keys=True))
        return 0
    for name in args.modifier or sorted(t):
        if name not in t:
            print(f"{name}: not in the schema")
            continue
        print(name)
        for f in t[name]:
            print(f"    {f}")
    print(f"\n{len(t)} modifiers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
