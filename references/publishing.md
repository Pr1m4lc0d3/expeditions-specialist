# Publishing to mod.io

The wizard makes you upload each platform zip separately, tick its platform by
hand, then walk back to step 3 for the next one. Six platforms per mod. Six mods
is thirty-six passes through a web form, and a mis-ticked platform box fails
silently.

```
python scripts/pack_distribution.py --all      # paks  -> 6 zips each
python scripts/make_modio_logo.py              # badges -> 1280x720 logos
python scripts/modio_publish.py --manifest     # write the plan, then edit it
python scripts/modio_publish.py                # DRY RUN
python scripts/modio_publish.py --publish      # create HIDDEN
python scripts/modio_publish.py --publish --public
```

## What the game expects

Packing emits one zip per platform. Each holds **the same pak plus a zero-byte
marker file named after the platform**:

```
SpecialistDesc_X_pc.zip   ->  SpecialistDesc_X.pak   deflated
                              pc.pak                 stored, 0 bytes
```

That is the whole difference between the six. `pack_distribution.py` makes them
from one pak, so the editor does not need to be open.

**The byte profile matters.** A map distribution zip rebuilt in Python once made
the map stop listing in game. The editor writes: no extra fields in either the
local or central header, pak deflated, marker stored, `external_attr` 0x20, no
archive comment. The packer reproduces that and `--verify` checks it.

## The platform names do not match

This is the trap. The zip suffix, the marker file and mod.io's API all use
different spellings, and uploading a Switch build tagged `windows` produces no
error at all.

| zip suffix and marker | mod.io API |
|---|---|
| `pc` | `windows` |
| `nx64` | `switch` |
| `playstation_4` | `ps4` |
| `playstation_5` | `ps5` |
| `xbox_one` | `xboxone` |
| `xbox_series` | `xboxseriesx` |

## Auth

The game's own MOD BROWSER stores a full-scope user token at
`<My Games>/Expeditions/base/Mods/.modio/authentication.json`. Sign in there once
and the publisher uses it. `MODIO_TOKEN` overrides.

🚨 **Cloudflare rejects the default `urllib` user agent with a 403 whose body
reads like an auth failure.** It is not one. Error 1010, "blocked based on your
browser's signature". Send a normal browser UA and the same token works.

## The API, in two calls

Game id for Expeditions is **5734**.

```
POST /v1/games/5734/mods
     multipart: logo (file, REQUIRED), name, summary (<=250), description,
                visible, maturity_option, tags[]

POST /v1/games/5734/mods/{mod-id}/files
     multipart: filedata (the zip), version, changelog, active, platforms[]
```

One `files` call per platform. The mod record then carries a `modfile_live` per
platform, which is how you confirm all six landed.

## Consoles go to review

Console zips are not live on upload. Saber reviews them, and the mod picks up a
`Console_Selected` tag when they pass. **Do not set that tag yourself**; it is
not in the game's public tag vocabulary. Upload all six platforms and let the
console ones sit in review.

Hard requirements for console eligibility: English title and description, no
offensive content, no new branded vehicles. Specialists are unaffected by the
brand rules.

## Tags

The game's vocabulary, from `GET /v1/games/5734/tags`:

| group | values |
|---|---|
| Type | Vehicle New, Vehicle Tweak, Map, **Specialist**, Base Module, Inventory item |
| Players | Multiplayer, Singleplayer |
| Installation | **Subscribe**, Manual |

A specialist wants `Specialist`, `Subscribe` and `Singleplayer`.

## Safety

`modio_publish.py` dry-runs by default and prints exactly what it would send.
`--publish` creates **hidden** mods; `--public` is a second, separate flag.
Publishing is hard to take back, so both are required to put something in front
of people.

It is also idempotent on name: if a mod with the same title already exists on
your account it adds files to it rather than creating a duplicate.
