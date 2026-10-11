---
name: expeditions-specialist
description: Use when creating, editing or fixing a custom specialist for Expeditions - A MudRunner Game. Covers the three avatar textures (bage, bg, bgSmall), their exact sizes and framing, generating portraits that match the game's art style, the descriptor format, ability modifiers and their values, and the zip-level defects that silently blank an avatar or hide an ability. Also use when a custom specialist loads but its portrait slots are empty, when an ability applies in play but never appears on the card, or when a badge sits high and left with bare card showing.
---

# Building an Expeditions specialist

A specialist is a `.pak` (a plain zip) in `Documents\My Games\Expeditions\Media\Mods\`
holding a descriptor and three PNGs. Saber documented almost none of what matters,
and the parts they did document include a figure that is wrong.

Everything here was measured against the shipped game. Saber ended support in
September 2026 and Focus confirmed no further content on any platform, so none of
it can go stale.

## Before anything else

```
python scripts/specialist_doctor.py
```

It reports where your game, mods folder and editor schema are, and checks every
installed specialist for the five defects in this file. Run it first and run it
again after any change. **A check nobody runs is not a check.**

Paths are discovered automatically. Override with `EXPEDITIONS_GAME`,
`EXPEDITIONS_MODS` or `EXPEDITIONS_SCHEMA` if yours are unusual. The editor
schema is optional: `Sources\BinEditor\meta_desc_ssl.ps` ships with the editor
tools rather than the game, and a snapshot of it is bundled.

## The five ways this goes wrong

Read these before debugging anything. Each one has cost someone a day.

### 1. A zip extra field in the LOCAL headers blanks every texture

Python's `zipfile` writes `ZipInfo.extra` into the local file header as well as
the central directory. Paks built by hand carry that 36-byte NTFS block in the
central directory only. The game's reader does not honour the local header's
extra length, so it starts reading 36 bytes early and the entry fails to decode.

**The symptom is not "my mod is broken".** The descriptor loads fine, so the
specialist appears with the correct name, story, cost and every ability, and only
the three picture slots are empty. That reads as an art problem and sends you
looking in the wrong place.

Never copy `info.extra`. And note that `zipfile` only ever shows you the central
directory, so a verify built on it will pass this defect and report no drift.
`specialist.local_extra_lengths()` walks the local headers.

### 2. `bage` is 364 x 364, not the 293 the guide says

The slot grew in an update and the guide never caught up. Every vanilla badge
shape in `hq_img_lib.gfx` measures 364 x 364.

**Scaleform draws the badge at its own pixel size, anchored top left, and never
scales it.** A 293 px badge covers 80.5% of the slot and sits high and left with
bare card showing right and below. That is not bad framing. It is the wrong canvas.

`bg` at 380 x 92 and `bgSmall` at 124 x 52 are correct. Leave them.

### 3. Editing only `SpecialistDesc.json` changes nothing

The canonical descriptor is the **extensionless** entry, `SpecialistDesc`. Some
paks carry a `.json` twin, some do not. Write every twin present and assert they
are byte identical, or you will change values, see no effect, and conclude the
field does not work.

### 4. An ability applies but never appears on the card

Two different faults share this symptom, and the second one cost a build that
passed every structural check.

**A numeric field with no `<field>UiDesc`** still takes effect and never shows.
`group` alone is not enough. Two shipped specialists carried this for a year.

**Three modifiers do not render with per-field labels at all**, no matter how
correct the labels are. Each needs the shape vanilla uses:

| modifier | what works |
|---|---|
| `ImproveWinchedTruck` | one `overrideUiDesc` line, no per-field labels |
| `EmergencyWinch` | a `group` and no field label at all |
| `RepairBuildingConsumption` | `repairBuildingConsumptionDesc`, a descriptor field with a non-standard name |

⚠ **That is a list of observations, not a rule.** Plenty of modifiers whose
vanilla shape also uses `overrideUiDesc` render per-field labels perfectly:
`WinchImprove`, `ArmorCapacity`, `DroneAcceleration` and `BinocularRadius` were
all confirmed working with per-field labels on the same screen. Why those three
differ is not established. **Do not extend the list by analogy.** Add to it only
when you have seen a card with the ability missing.

`schema_snapshot.json -> display_contract` records how all 25 shipped
specialists display all 46 modifiers, which is the reference to copy from.
`specialist_doctor.py` flags only the three confirmed cases, because an earlier
version inferred a rule from vanilla's shape and reported a dozen working
abilities as broken, which is worse than not checking.

### 5. An opaque source renders as a black rectangle

The textures need alpha. A badge with no transparency fills the card as a solid
photo block.

Cutting off a **dark** backdrop drags the backdrop colour into partial-alpha hair
pixels and leaves grey hair muddy. Generate on flat pale grey, or with alpha
already present. If you must cut off dark, see `references/framing.md` for the
decontamination.

## Making the portrait look like the game

Full method in `references/portraits.md`. The short version, because it took
seven attempts to find:

**Describing the art style in words does not work.** The style sits between
photoreal and cartoon, and prompt wording lands on one attractor or the other.
"Game engine character render" means photoreal in 2026; "animated feature film
character" means Pixar.

**What works is a restyle against reference images.** Attach two existing badges
you like plus the portrait you want restyled, and keep the instruction to about
sixty words. A long description drowns the reference.

**Image prompts have no negative channel.** Writing "no photographic skin pores"
draws photographic skin pores. State what you want, never what you don't.

## Framing

`references/framing.md` has the measurements. The two rules that matter:

**Badge:** whole bust in frame, both shoulders inside it, a margin of backdrop
above the head, bust running to the bottom edge.

**Strips:** these are a tighter crop inside a larger transparent canvas, not the
badge scaled down. Size the window by the head's **height**, never its width.
Head width depends on headgear, so a hard hat and a pair of goggles produce wildly
different crops from the same rule. `scripts/build_specialist_art.py` does this.

## Building one

```
# 1. portrait -> three textures, with a checkerboard preview to inspect
python scripts/build_specialist_art.py myguy=portrait.png

# 2. clone a pak of the RIGHT SPECIALITY, so the class is already correct
python scripts/clone_specialist.py --source "<a pak>" --id MyGuy \
    --ui-name "Real Name" --prefix myguy \
    --bage build/myguy_bage.png --bg build/myguy_bg.png --bgsmall build/myguy_bgSmall.png \
    --ui-desc "..."

# 3. abilities, cost, lock state
python scripts/set_specialist_stats.py --help

# 4. check
python scripts/specialist_doctor.py
```

## Publishing to mod.io

Full detail in `references/publishing.md`.

```
python scripts/pack_distribution.py --all    # paks -> 6 platform zips each
python scripts/make_modio_logo.py            # badges -> logos (mod.io requires one)
python scripts/modio_publish.py --manifest   # the plan; edit the summaries
python scripts/modio_publish.py              # DRY RUN
python scripts/modio_publish.py --publish    # create hidden; --public to go live
```

Three things that bite:

**The platform names do not match.** The zip suffix is `pc`, the marker inside
is `pc.pak`, and mod.io's API wants `windows`. Uploading a Switch build tagged
`windows` produces no error.

**Cloudflare 403s the default `urllib` user agent** with a body that reads like
an auth failure. Error 1010, blocked browser signature. Send a browser UA.

**Console zips go to Saber's review queue**, and a `Console_Selected` tag
appears when they pass. Do not set it yourself.

## Descriptor rules

| Field | Rule |
|---|---|
| `speciality` | `0 MECHANIC`, `1 LOGISTICS_SPECIALIST`, `2 HYDROLOGIST`, `3 JAEGER`, `4 OPERATOR`, `5 MANAGER`. **6 is `NONE` and crashes the game.** |
| `uiName` | 20 characters. Real. |
| `uiDesc` | The guide says 280. It is not enforced; a shipped specialist runs 519. |
| `cost` | Vanilla spans 500 to 3000. |
| `isLocked` | 24 of 25 vanilla specialists are locked, unlocked by an objective reward. **A locked specialist with no reward wired to it is unobtainable**, so leave it false until the objective exists. |

Two specialists holding the same numeric field is a balance clash, not a feature.
The exception is a deliberate pair, where both hold it with opposite signs.
**A negative value inverts the effect**, which is how a penalty is written.

## Beating the shipped specialists

`references/vanilla.md` lists all 25 with every value, pulled from the game. They
are stored as plain text in `initial.cache_block` inside
`preload/paks/client/initial.pak`. They are **not** in `initial_release.sslbundle`,
which is where people look and give up. Their names are localisation keys, so
searching for a name finds nothing; the table is `[strings]/strings_english.str`
in the same pak, UTF-16LE.

## Designing the character

`references/design.md`. Two rules learned by getting both wrong:

**One team, one problem.** Zero field collisions is not a coherent roster. A pair
whose modifiers collided with nothing was still wrong, because it was the second
team doing the same job as an existing pair.

**Name people, not equipment.** Names built from the job read as catalogue parts.
The ones that work are plausible names where the pun is phonetic and incidental.

## When an ability does not show on the card

`references/display.md`. It applies in a run and the hire screen draws nothing.
No error, no placeholder, so a missing label looks exactly like an ability you
forgot to add.

🚨 **Never build a descriptor name as `field + "UiDesc"`.** Saber misspelled three
of them, so the correct spelling is the broken one and the game discards it in
silence. `winchLenghtIncreasedMetersUiDesc` really is "Lenght", and fuel and
wheels double the word `Count` while repairs does not. Ask the schema:

```
python scripts/schema_members.py --check       # scan installed specialists
sp.desc_field("AdditionalAddonSupplies", "additionalAddonFuelCount")
```

A sweep of thirteen specialists found 21 invented field names, three carrying
label text that had never been drawn once.

## Files

| Path | What |
|---|---|
| `scripts/specialist.py` | the engine: pak read/write, descriptor, modifiers, checks |
| `scripts/specialist_doctor.py` | environment report plus a full defect scan |
| `scripts/schema_members.py` | valid field names per modifier; `--check` scans the roster |
| `references/display.md` | the three reasons an ability renders nothing |
| `scripts/build_specialist_art.py` | portrait to three textures |
| `scripts/clone_specialist.py` | new specialist from an existing pak |
| `scripts/set_specialist_stats.py` | abilities, cost, lock state, from a JSON design |
| `scripts/set_specialist_texture.py` | swap one or more textures in an existing pak |
| `scripts/pack_distribution.py` | pak -> the six platform zips mod.io wants |
| `scripts/make_modio_logo.py` | badge -> a 1280x720 mod.io logo |
| `scripts/modio_publish.py` | create the mod and upload all six platform files |
| `references/publishing.md` | the mod.io process, platform mapping, auth |
| `examples/vera_platt.json` | a worked design file |
| `scripts/schema_snapshot.json` | the 47 modifiers and their fields, for machines without the editor |
| `references/framing.md` | measurements and the crop rules |
| `references/portraits.md` | generating art that matches the game |
| `references/vanilla.md` | all 25 shipped specialists with values |
| `references/design.md` | roster and naming |

Requires Python 3.10+, `pillow`, `numpy`, `opencv-python`, and `rembg` only if
you need to cut an opaque portrait.
