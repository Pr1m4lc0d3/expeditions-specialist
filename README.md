# expeditions-specialist

A Claude Code and Codex skill for building custom specialists for
**Expeditions: A MudRunner Game**.

Saber shipped a modding guide that documents the easy parts and gets one number
wrong. This covers the rest: the three portrait textures and how to frame them,
the descriptor format, every ability modifier with the values the shipped
specialists use, and the handful of defects that make a specialist load
perfectly and show nothing.

Six specialists were built with it and confirmed in game.

## The problem it solves

Build a specialist by hand and you will meet at least one of these. Each is
silent, and each reads as a different problem than it is.

**Your avatar slots are empty but the specialist works.** A 36-byte zip extra
field in the *local* headers. Python's `zipfile` writes it, Saber's reader
cannot skip it, and `zipfile` will never show it to you because it only reads
the central directory. The descriptor has no extra field, so the specialist
appears with the right name, cost and every ability, and three blank pictures.
That looks like an art problem. It is not.

**Your badge sits high and left with bare card showing.** The slot is 364 x 364.
The official guide says 293, and the badge is drawn at native size and never
scaled.

**Your ability does nothing visible.** Either the field has no `UiDesc`, or the
modifier is one of three that refuse per-field labels entirely and need the
shape vanilla uses.

**Your changes have no effect.** You edited `SpecialistDesc.json` and the game
reads the extensionless `SpecialistDesc` beside it.

## Install

```powershell
.\install.ps1                # Claude Code  -> ~/.claude/skills
.\install.ps1 -Agent codex   # Codex        -> ~/.codex/skills
.\install.ps1 -Agent both
```

```bash
./install.sh claude|codex|both
```

Then ask your agent to build a specialist, or run the checker directly:

```
python scripts/specialist_doctor.py
```

It prints where your game and mods folder are, then scans every installed
specialist. Run it before you theorise about anything.

## Requirements

Python 3.10+, `pillow`, `numpy`, `opencv-python`. `rembg` only if you need to cut
an opaque portrait; one that already has alpha works without it.

Paths are discovered. Override with `EXPEDITIONS_GAME`, `EXPEDITIONS_MODS` or
`EXPEDITIONS_SCHEMA` if yours are unusual.

**You do not need the editor.** `meta_desc_ssl.ps` ships with the editor tools
rather than the game, so `scripts/schema_snapshot.json` bundles all 47 ability
modifiers, their fields, and how the 25 shipped specialists display each one.
Saber ended support in September 2026, so that snapshot cannot go stale.

## What is in here

| | |
|---|---|
| `SKILL.md` | the process. Your agent reads this. |
| `references/framing.md` | texture sizes, crop rules, transparency |
| `references/portraits.md` | generating art that matches the game |
| `references/vanilla.md` | all 25 shipped specialists, every value |
| `references/design.md` | roster coherence and naming |
| `scripts/specialist.py` | the engine: pak read and write, descriptor, checks |
| `scripts/specialist_doctor.py` | environment report and defect scan |
| `scripts/build_specialist_art.py` | one portrait, three textures |
| `scripts/clone_specialist.py` | a new specialist from an existing pak |
| `scripts/set_specialist_stats.py` | abilities and cost from a JSON design |
| `scripts/set_specialist_texture.py` | swap textures in an existing pak |
| `examples/vera_platt.json` | a worked design file |

## A note on the numbers

`references/vanilla.md` has all 25 shipped specialists with every modifier value,
so you can balance against what Saber actually did rather than guess. They are
stored as plain text inside `initial.cache_block` in
`preload/paks/client/initial.pak`. They are **not** in
`initial_release.sslbundle`, which is where most people look before concluding
the values are unreadable.

## Honesty about scope

Everything here was measured against the shipped game or confirmed on a card in
play. Where something is observed rather than understood, it says so. The list
of modifiers that refuse per-field labels is three entries long and marked as
observations, not a rule, because an earlier version inferred a rule and flagged
a dozen working abilities as broken.

## Support this

Free, and it stays free. No tiers, no membership, nothing locked.

Saber documented almost none of this and then ended support for the game, so
every page here was worked out by reading the schema and testing against the
shipped build. That took considerably longer than building the mods it came
from. If it saved you an afternoon, a dollar covers it:
**https://ko-fi.com/ryanheltemes**

## Licence

MIT. See `LICENSE`.

Not affiliated with Saber Interactive or Focus Entertainment. *Expeditions: A
MudRunner Game* is their trademark. This ships no game assets: the vanilla
reference contains numbers read from your own installation.
