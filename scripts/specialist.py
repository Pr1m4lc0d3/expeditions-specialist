"""Read, edit and rewrite Expeditions specialist .pak files.

One module so there is one answer to "how is a specialist pak written". The CLIs
(`set_specialist_texture.py`, `clone_specialist.py`, `fix_specialist_badges.py`),
the Deliberon tool and the shared skill all go through here.

Saber documents almost none of this. Everything below was measured off the live
build or off his own working mods, and the load-bearing facts are marked.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import struct
import zipfile
from pathlib import Path

#: Bundled fallback, so a machine with the game but not the editor still works.
#: `Sources\BinEditor\meta_desc_ssl.ps` ships with the editor tools, not the game.
#: Saber ended support in September 2026, so the snapshot cannot go stale.
SNAPSHOT = Path(__file__).with_name("schema_snapshot.json")

#: Where the editor schema lives, if the editor is installed at all.
_SCHEMA_TAIL = Path("Sources") / "BinEditor" / "meta_desc_ssl.ps"
_GAME_GUESSES = [
    r"D:\Games\ExpeditionsAMudRunnerGame",
    r"C:\Program Files (x86)\Steam\steamapps\common\Expeditions A MudRunner Game",
    r"C:\Program Files\Epic Games\ExpeditionsAMudRunnerGame",
]


def game_root() -> Path | None:
    """The game install. `EXPEDITIONS_GAME` wins, then the usual store paths."""
    env = os.environ.get("EXPEDITIONS_GAME")
    if env and Path(env).is_dir():
        return Path(env)
    for g in _GAME_GUESSES:
        if Path(g).is_dir():
            return Path(g)
    return None


def mods_dir() -> Path:
    """The folder the game enumerates for local mods.

    `EXPEDITIONS_MODS` wins. Otherwise the standard per-user location, which is
    the same on every Windows install because the game builds it from the
    Documents shell folder.
    """
    env = os.environ.get("EXPEDITIONS_MODS")
    if env:
        return Path(env)
    return Path.home() / "Documents" / "My Games" / "Expeditions" / "Media" / "Mods"


def schema_path() -> Path | None:
    """The live editor schema, or None when only the snapshot is available."""
    env = os.environ.get("EXPEDITIONS_SCHEMA")
    if env and Path(env).is_file():
        return Path(env)
    root = game_root()
    if root and (root / _SCHEMA_TAIL).is_file():
        return root / _SCHEMA_TAIL
    return None


SCHEMA = schema_path()

#: The canonical descriptor is the EXTENSIONLESS entry. Some paks carry a
#: `SpecialistDesc.json` twin and some do not; when both exist they must match.
#: Editing only the twin changes nothing the game reads.
DESCRIPTOR = "SpecialistDesc"
DESCRIPTOR_TWIN = "SpecialistDesc.json"

#: Texture slot -> exact pixel size the current build reserves. `bage` grew from
#: 293 in a Saber update; the guide still says 293 and the guide is stale.
#: Scaleform draws the badge at its native size, top-left anchored, never scaled,
#: so an undersized badge sits high-left with bare card showing.
SLOT_SIZES = {"bage": (364, 364), "bg": (380, 92), "bgSmall": (124, 52)}

#: Valid ability icons. Grepping the game paks for these returns a false
#: negative: only two are stored as plain strings. This list is from his own
#: reference file and is the real one.
ABILITY_ICONS = (
    "specAbilityAddonFuel36", "specAbilityAirdrop36", "specAbilityAnchor36",
    "specAbilityArmor36", "specAbilityBinocular36", "specAbilityDrone36",
    "specAbilityEcho36", "specAbilityEngine36", "specAbilityFord36",
    "specAbilityFuel36", "specAbilityJackscrew36", "specAbilityMoney36",
    "specAbilityOutposts36", "specAbilityRecovery36", "specAbilityRepair36",
    "specAbilityShortcut36", "specAbilityTrucks36", "specAbilityUphills36",
    "specAbilityWheels36", "specAbilityWinch36",
    # Not in his reference file, which lists 20. Found in the vanilla records in
    # initial.cache_block, where Mechanic_05 uses it for the ground drone group.
    # His list is incomplete; trust the shipped data over the reference note.
    "specAbilityDroneGround36",
)

#: Types in the schema that are plumbing, not abilities.
_PLUMBING = {"Base", "BaseWithDescs", "BaseWithOverrideDesc",
             "GroupUiDesc", "Info", "UiDesc", "ValueType"}


# ----------------------------------------------------------------- zip layer

def local_extra_lengths(pak: str | Path) -> dict[str, int]:
    """Extra-field length of every LOCAL file header, keyed by entry name.

    🚨 `zipfile` only ever exposes the CENTRAL DIRECTORY. The game's reader does
    not honour the local header's extra length, so an entry carrying one loads
    36 bytes of NTFS timestamp as the head of its payload and fails. A 36-byte
    block written by `ZipInfo.extra` blanked Doc Windsor's three avatar slots
    for a day while the specialist itself loaded perfectly, because the
    descriptor entries happened to carry none. Any writer here must keep this
    at zero, and any verify must call this function.
    """
    blob = Path(pak).read_bytes()
    out: dict[str, int] = {}
    off = 0
    while off + 30 <= len(blob) and struct.unpack_from("<I", blob, off)[0] == 0x04034B50:
        _, _, _, _, _, _, csize, _, nlen, elen = struct.unpack_from("<HHHHHIIIHH", blob, off + 4)
        out[blob[off + 30:off + 30 + nlen].decode("utf-8", "replace")] = elen
        off += 30 + nlen + elen + csize
    return out


def rewrite_pak(pak: str | Path, payloads: dict[str, bytes]) -> None:
    """Rewrite `pak`, swapping the named entries, preserving everything else.

    Entry order, names, compression method, timestamps and attributes are kept.
    `ZipInfo.extra` is deliberately NOT carried over - see local_extra_lengths.
    Python rezipping is safe for specialist paks (proven: a Python-written clone
    rendered in game). It is NOT safe for level distribution zips, which stop
    listing - use `expeditions.pack` for those.
    """
    pak = str(pak)
    with zipfile.ZipFile(pak) as src:
        entries = [(i, src.read(i.filename)) for i in src.infolist()]
    unknown = set(payloads) - {i.filename for i, _ in entries}
    if unknown:
        raise KeyError(f"not in {os.path.basename(pak)}: {sorted(unknown)}")
    tmp = pak + ".tmp"
    with zipfile.ZipFile(tmp, "w") as out:
        for info, data in entries:
            new = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            new.compress_type = info.compress_type
            new.external_attr = info.external_attr
            new.internal_attr = info.internal_attr
            new.create_system = info.create_system
            new.comment = info.comment
            out.writestr(new, payloads.get(info.filename, data))
    os.replace(tmp, pak)
    stray = {n: e for n, e in local_extra_lengths(pak).items() if e}
    if stray:
        raise AssertionError(f"local header extra fields written: {stray}")


def backup_path(pak: str | Path, override: str | Path | None = None) -> Path:
    """ONE backup, fixed name, overwritten. Never beside the pak.

    `Media\\Mods` is the folder the game enumerates. 37 stale `*.pak.pre-*-bak`
    files accumulated there before anyone noticed, and the game's own error
    string ("Files of classes can't have equal names") shows duplicates in that
    folder are a real failure mode. A timestamp in the filename is what turns a
    backup into a backup chain; 295 of those had to be deleted by hand.
    """
    pak = Path(pak)
    d = Path(override) if override else pak.parent.parent.parent / "ModBackups"
    d.mkdir(parents=True, exist_ok=True)
    return d / (pak.name + ".bak")


# ---------------------------------------------------------- descriptor layer

def read_descriptor(pak: str | Path) -> dict:
    """The parsed canonical descriptor."""
    with zipfile.ZipFile(str(pak)) as z:
        return json.loads(z.read(DESCRIPTOR).decode("utf-8-sig"))


def descriptor_entries(pak: str | Path) -> list[str]:
    with zipfile.ZipFile(str(pak)) as z:
        return [n for n in z.namelist() if n in (DESCRIPTOR, DESCRIPTOR_TWIN)]


def write_descriptor(pak: str | Path, desc: dict, backup: str | Path | None = None) -> Path:
    """Write the descriptor to every twin present, after taking one backup.

    Both entries get byte-identical content. Writing only the `.json` twin is
    the classic silent no-op: values were "changed" and reported live while the
    canonical file still held the originals.
    """
    bak = backup_path(pak, backup)
    shutil.copy2(str(pak), bak)
    blob = json.dumps(desc, indent=4, ensure_ascii=False).encode("utf-8")
    rewrite_pak(pak, {name: blob for name in descriptor_entries(pak)})
    with zipfile.ZipFile(str(pak)) as z:
        names = descriptor_entries(pak)
        if len(names) == 2 and z.read(names[0]) != z.read(names[1]):
            raise AssertionError("descriptor twins differ after write")
    return bak


# ------------------------------------------------------------- the modifiers

def _snapshot() -> dict:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def catalogue(schema: str | Path | None = None) -> list[str]:
    """Every real ability modifier the game defines, from the editor schema.

    47 at time of writing. This is the only complete list: the modifier names do
    not appear as strings in Expeditions.exe at all.
    """
    schema = schema or SCHEMA
    if schema is None:
        return sorted(_snapshot()["modifiers"])
    text = Path(schema).read_text(encoding="utf-8", errors="replace")
    names = set(re.findall(r"SpecialistModifier([A-Za-z0-9_]+)", text))
    return sorted(n for n in names if n not in _PLUMBING)


def _block(text: str, name: str) -> str | None:
    """The brace-matched definition block for a top-level schema type."""
    m = re.search(r"(?m)^" + re.escape(name) + r"\s*=\s*\{", text)
    if not m:
        return None
    i = text.index("{", m.start())
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
    return None


def modifier_fields(short_name: str, schema: str | Path | None = None) -> dict[str, str]:
    """field name -> engine type, for one modifier. Brace-matched, not windowed.

    A fixed-size window over the schema bleeds into the NEXT type's members and
    silently invents fields that belong to a different modifier. Match braces.
    """
    schema = schema or SCHEMA
    if schema is None:
        snap = _snapshot()["modifiers"]
        if short_name not in snap:
            raise KeyError(short_name)
        return {f: "?" for f in snap[short_name]}
    text = Path(schema).read_text(encoding="utf-8", errors="replace")
    blk = _block(text, "SpecialistModifier" + short_name)
    if blk is None:
        raise KeyError(short_name)
    members = _block(blk, "__members") or _block("x" + blk[blk.index("__members"):], "__members") \
        if "__members" in blk else None
    if members is None:
        i = blk.index("__members")
        j = blk.index("{", i)
        depth = 0
        for k in range(j, len(blk)):
            if blk[k] == "{":
                depth += 1
            elif blk[k] == "}":
                depth -= 1
                if depth == 0:
                    members = blk[j:k + 1]
                    break
    out: dict[str, str] = {}
    for fm in re.finditer(r"(?m)^      ([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", members or ""):
        fname = fm.group(1)
        if fname.endswith("UiDesc") or fname in ("name", "group"):
            continue
        tail = (members or "")[fm.end():fm.end() + 400]
        t = re.search(r'__typeEngine\s*=\s*"([^"]+)"', tail)
        out[fname] = t.group(1) if t else "?"
    return out


def modifiers_in_use(mods_dir: str | Path) -> dict[str, list[str]]:
    """modifier short name -> the uiNames of the specialists holding it.

    Two specialists holding the same numeric field is a balance clash, not a
    feature. Check this before adding an ability to anyone.
    """
    out: dict[str, list[str]] = {}
    for pak in sorted(Path(mods_dir).glob("SpecialistDesc_*.pak")):
        if pak.stat().st_size == 0:
            continue
        v = read_descriptor(pak)["SslValue"]
        for m in v.get("modifiers", []):
            out.setdefault(m["$type"].replace("SpecialistModifier", ""), []).append(v.get("uiName"))
    return out


def find_modifier(desc: dict, short_name: str) -> dict | None:
    want = "SpecialistModifier" + short_name
    for m in desc["SslValue"].get("modifiers", []):
        if m["$type"] == want:
            return m
    return None


def remove_modifier(desc: dict, short_name: str) -> dict:
    """Drop a modifier and return it. Raises if it is not there."""
    m = find_modifier(desc, short_name)
    if m is None:
        raise KeyError(f"{short_name} not on {desc['SslValue'].get('uiName')!r}")
    desc["SslValue"]["modifiers"].remove(m)
    return m


def add_modifier(desc: dict, modifier: dict) -> None:
    """Append a modifier, refusing a duplicate type.

    🚨 EVERY MODIFIER HAS ITS OWN DISPLAY CONTRACT. There is no single rule.

    The obvious one, "give every numeric field a `<field>UiDesc`", is right for
    many modifiers and silently wrong for others. Three shipped in a build that
    passed every structural check and rendered NOTHING on the card:

      ImproveWinchedTruck        one `overrideUiDesc` line, fields unlabelled
      EmergencyWinch             `group` only, the field carries no label
      RepairBuildingConsumption  labelled by `repairBuildingConsumptionDesc`,
                                 a field with a NON-STANDARD name

    And the reverse trap: vanilla deliberately leaves some fields unlabelled,
    such as `echolotApplicationAdditionalTime`. "Fixing" those adds a label the
    game never shows.

    So the contract is taken from how the 25 shipped specialists actually do it,
    in `schema_snapshot.json -> display_contract`, rather than from a rule.
    Copy vanilla's shape for the modifier you are writing.
    """
    short = modifier["$type"].replace("SpecialistModifier", "")
    if find_modifier(desc, short) is not None:
        raise ValueError(f"{short} already on {desc['SslValue'].get('uiName')!r}")
    for problem in display_problems(modifier):
        raise ValueError(problem)
    desc["SslValue"]["modifiers"].append(modifier)


def display_contract(short_name: str) -> dict | None:
    """How the shipped specialists display this modifier, or None if unused.

    Useful as a reference when authoring. NOT a predictor of what renders: see
    display_problems.
    """
    return _snapshot().get("display_contract", {}).get(short_name)


#: Modifiers proven NOT to render with ordinary per-field `<field>UiDesc`
#: labels, each confirmed by a screenshot of the card showing nothing where the
#: ability should be. The working shape, copied from vanilla, is given.
#:
#: ⚠ THIS IS A LIST OF OBSERVATIONS, NOT A RULE. Plenty of modifiers whose
#: vanilla shape also uses override/allSame render per-field labels perfectly:
#: WinchImprove, ArmorCapacity, DroneAcceleration, BinocularRadius and others
#: were all confirmed rendering with per-field labels on the same screen. Why
#: these three differ is not established, so do not extend the list by analogy.
#: Add to it only when a card has been seen with the ability missing.
_WILL_NOT_RENDER_PER_FIELD = {
    # modifier: (what the working shape requires, how to say it)
    "ImproveWinchedTruck": (
        lambda m, nums: bool(m.get("overrideUiDesc") or m.get("allSameUiDesc"))
                        and not any(m.get(k + "UiDesc") for k in nums),
        "set a single overrideUiDesc line and remove the per-field labels; "
        "vanilla uses SPEC_MODS_WINCHED_BUFF"),
    "EmergencyWinch": (
        lambda m, nums: not any(m.get(k + "UiDesc") for k in nums),
        "give it a group and NO field label at all; vanilla labels nothing here"),
    "RepairBuildingConsumption": (
        lambda m, nums: bool(m.get("repairBuildingConsumptionDesc"))
                        and not any(m.get(k + "UiDesc") for k in nums),
        "label it with repairBuildingConsumptionDesc, a descriptor field with a "
        "non-standard name, and remove the per-field label"),
}


def display_problems(modifier: dict) -> list[str]:
    """Reasons this modifier is known not to render.

    Only reports cases actually observed failing on a card. An earlier version
    inferred a rule from vanilla's shape and flagged a dozen abilities that
    screenshots showed working, which is worse than not checking at all.
    """
    short = modifier["$type"].replace("SpecialistModifier", "")
    nums = [k for k, v in modifier.items()
            if isinstance(v, (int, float)) and not k.endswith("UiDesc")
            and k not in ("$type", "name", "group")]
    out: list[str] = []
    if short in _WILL_NOT_RENDER_PER_FIELD:
        ok, advice = _WILL_NOT_RENDER_PER_FIELD[short]
        if not ok(modifier, nums):
            out.append(f"{short} will not render as written (observed on a card): {advice}")
        return out
    if not (modifier.get("overrideUiDesc") or modifier.get("allSameUiDesc")):
        never = set((display_contract(short) or {}).get("never_labelled", []))
        silent = [k for k in nums if modifier.get(k + "UiDesc") is None and k not in never]
        if silent:
            out.append(f"no UiDesc on {silent}: those apply but may not show on the card")
    return out


def ui_desc(text: str, value_prefix: str = " +", icon30: str = "", hidden: bool = False) -> dict:
    return {"$type": "SpecialistModifierUiDesc", "hidden": hidden, "icon30": icon30,
            "text": text, "valuePrefix": value_prefix, "valueType": 0}


def group(text: str, icon36: str) -> dict:
    if icon36 not in ABILITY_ICONS:
        raise ValueError(f"{icon36!r} is not one of the 20 valid ability icons")
    return {"$type": "SpecialistModifierGroupUiDesc", "icon36": icon36, "text": text}
