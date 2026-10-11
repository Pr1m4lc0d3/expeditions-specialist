#!/usr/bin/env python3
"""Publish specialists to mod.io without the 36-trip wizard.

mod.io's Add Mod wizard makes you upload each platform zip separately, choose
its platform from a checkbox, and come back to step 3 for the next one. Six
platforms times six specialists is thirty-six passes through a web form, and
getting one platform checkbox wrong is silent.

    python modio_publish.py --manifest            # build the plan from your paks
    python modio_publish.py                       # DRY RUN, prints what it would do
    python modio_publish.py --publish             # do it, HIDDEN
    python modio_publish.py --publish --public    # do it, visible to everyone

Nothing is written without --publish, and even then mods are created hidden
unless you also pass --public, because publishing is hard to take back.

Auth comes from the token the game's own MOD BROWSER already stored at
`<My Games>/Expeditions/base/Mods/.modio/authentication.json`. Nothing is
printed from it. Override with MODIO_TOKEN.

🚨 Cloudflare rejects the default urllib user agent with a 403 that reads like
an auth failure. It is not. The UA below is required.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import specialist as sp  # noqa: E402
from modio_markdown import md_to_html  # noqa: E402

GAME_ID = 5734                      # Expeditions: A MudRunner Game
API = "https://api.mod.io/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

#: zip suffix -> the name mod.io uses. These do not match, and a wrong mapping
#: uploads a Switch build as a Windows one with no error.
PLATFORM = {"pc": "windows", "nx64": "switch",
            "playstation_4": "ps4", "playstation_5": "ps5",
            "xbox_one": "xboxone", "xbox_series": "xboxseriesx"}

CLASSES = {0: "Mechanic", 1: "Logistics Specialist", 2: "Hydrologist",
           3: "Jaeger", 4: "Operator", 5: "Manager"}


def token() -> str:
    t = os.environ.get("MODIO_TOKEN")
    if t:
        return t
    auth = (Path.home() / "Documents" / "My Games" / "Expeditions" / "base"
            / "Mods" / ".modio" / "authentication.json")
    if not auth.is_file():
        raise SystemExit("No token. Sign in to the MOD BROWSER in game, or set MODIO_TOKEN.")
    return json.loads(auth.read_text(encoding="utf-8", errors="replace"))["access_token"]


def _req(method: str, path: str, *, fields=None, files=None):
    body, ctype = None, None
    if fields and not files:
        # 🚨 mod.io rejects multipart on any endpoint that carries no file:
        #   415 error_ref 13006, "Incorrect Content-Type header in request,
        #   must be application/x-www-form-urlencoded"
        # Creating a mod is multipart because the logo rides along; EDITING one
        # has no file and must be urlencoded. Sending multipart to PUT /mods
        # silently left a published mod on its original description.
        body = urllib.parse.urlencode(fields).encode("utf-8")
        ctype = "application/x-www-form-urlencoded"
    elif fields or files:
        b = uuid.uuid4().hex
        ctype = f"multipart/form-data; boundary={b}"
        parts = []
        for k, v in (fields or []):
            parts.append(f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n"
                         .encode("utf-8"))
        for k, p in (files or []):
            p = Path(p)
            mt = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            parts.append(f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"; "
                         f"filename=\"{p.name}\"\r\nContent-Type: {mt}\r\n\r\n".encode("utf-8"))
            parts.append(p.read_bytes())
            parts.append(b"\r\n")
        parts.append(f"--{b}--\r\n".encode("utf-8"))
        body = b"".join(parts)
    r = urllib.request.Request(API + path, data=body, method=method,
                               headers={"Authorization": "Bearer " + token(),
                                        "Accept": "application/json", "User-Agent": UA,
                                        **({"Content-Type": ctype} if ctype else {})})
    try:
        return 200, json.loads(urllib.request.urlopen(r, timeout=300).read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:
            return e.code, {}


def summarise(desc: str, limit: int = 250) -> str:
    """mod.io caps the summary at 250 characters, so cut on a sentence."""
    out = ""
    for sentence in desc.replace("\n", " ").split(". "):
        candidate = (out + sentence).strip()
        if len(candidate) + 1 > limit:
            break
        out = candidate + ". "
    return (out or desc[:limit - 1]).strip()


def describe(v: dict) -> str:
    lines = [v["uiDesc"], "", f"Class: {CLASSES.get(v.get('speciality'), '?')}",
             f"Hire cost: {v.get('cost')}", "", "Abilities:"]
    for m in v["modifiers"]:
        for k, x in m.items():
            if k.endswith("UiDesc") or not isinstance(x, (int, float)):
                continue
            u = m.get(k + "UiDesc") or {}
            if u.get("text") and not u.get("hidden"):
                lines.append(f"  {u['text']}{u.get('valuePrefix', ' ')}{x}")
        for k in m:
            if (k.endswith("UiDesc") and k[:-6] not in m
                    and k not in ("allSameUiDesc", "overrideUiDesc")):
                u = m.get(k) or {}
                if u.get("text") and not u.get("hidden"):
                    lines.append(f"  {u['text']}")
    return "\n".join(lines)


def screenshots_for(stem: str, dist: Path) -> list[str]:
    """Gallery images for one specialist.

    Drop in-game screenshots at `dist/screenshots/<pak stem>*.png|jpg`. These
    matter more than the generated logo: they show the real card, which is what
    anyone browsing actually wants to see.
    """
    folder = dist / "screenshots"
    if not folder.is_dir():
        return []
    return [str(p) for p in sorted(folder.glob(f"{stem}*"))
            if p.suffix.lower() in (".png", ".jpg", ".jpeg")]


def prepare_image(src: Path, out_dir: Path) -> Path:
    """Downscale to 1920x1080 JPEG. A 4K PNG screenshot is ~6 MB, near the cap."""
    from PIL import Image
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / (src.stem + ".jpg")
    im = Image.open(src).convert("RGB")
    if im.width > 1920:
        im = im.resize((1920, round(im.height * 1920 / im.width)), Image.LANCZOS)
    im.save(dest, "JPEG", quality=90, optimize=True)
    return dest


def upload_media(mod_id: int, shots: list[str], dist: Path) -> None:
    if not shots:
        print("      no screenshots found; see dist/screenshots/")
        return
    prepared = [prepare_image(Path(s), dist / "_media") for s in shots[:10]]
    files = [(f"image{i+1}", p) for i, p in enumerate(prepared)]
    code, data = _req("POST", f"/games/{GAME_ID}/mods/{mod_id}/media", files=files)
    ok = code in (200, 201)
    total = sum(p.stat().st_size for p in prepared) // 1024
    print(f"      media       {'ok' if ok else 'FAILED ' + str(code)} "
          f"{len(prepared)} image(s), {total} KB"
          f"{'' if ok else ' ' + json.dumps(data)[:200]}")


def read_listing(stem: str, listings: Path) -> tuple[str, str] | None:
    """Authored summary and description for one pak stem, or None if absent.

    `<stem>.md` carries a `summary:` front-matter line and a markdown body. The
    body is followed by `_tail.md`, which holds whatever every listing shares.

    🚨 **A pak with no listing file does not publish.** That is deliberate: the
    directory is the allow-list. Globbing the mods folder instead would sweep in
    specialists the author never meant to upload, and on mod.io that mistake is
    public before you notice it.
    """
    f = listings / f"{stem}.md"
    if not f.is_file():
        return None
    text = f.read_text(encoding="utf-8")
    summary, body = "", text
    if text.startswith("---"):
        end = text.index("\n---", 3)
        front, body = text[3:end], text[end + 4:]
        for line in front.splitlines():
            if line.strip().startswith("summary:"):
                summary = line.split(":", 1)[1].strip()
    tail = listings / "_tail.md"
    if tail.is_file():
        body = body.rstrip() + "\n\n" + tail.read_text(encoding="utf-8")
    # HTML, not markdown. mod.io converts nothing, so markdown ships as literal
    # '##' and raw table pipes on the public page. See modio_markdown.
    return summary, md_to_html(body.strip())


def build_manifest(paks: list[Path], dist: Path, listings: Path | None = None) -> list[dict]:
    out = []
    for pak in paks:
        v = sp.read_descriptor(pak)["SslValue"]
        zips = {plat: dist / f"{pak.stem}_{plat}.zip" for plat in PLATFORM}
        authored = read_listing(pak.stem[len("SpecialistDesc_"):], listings) if listings else None
        if listings and authored is None:
            print(f"  skipped {pak.stem}: no listing file, so it is not cleared to publish")
            continue
        out.append({
            "pak": str(pak),
            "name": v["uiName"],
            "summary": authored[0] if authored else summarise(v["uiDesc"]),
            "description": authored[1] if authored else describe(v),
            "tags": ["Specialist", "Subscribe", "Singleplayer"],
            "logo": str(dist / "logos" / (pak.stem + ".png")),
            "zips": {p: str(z) for p, z in zips.items()},
            "screenshots": screenshots_for(pak.stem, dist),
        })
    return out


def find_existing(name: str) -> dict | None:
    code, data = _req("GET", f"/me/mods?game_id={GAME_ID}&_limit=100")
    if code != 200:
        return None
    for m in data.get("data", []):
        if m.get("name") == name:
            return m
    return None


def publish(entry: dict, public: bool, dist: Path, media_only: bool = False,
            version: str = "1.0", changelog: str = "Initial release.") -> None:
    existing = find_existing(entry["name"])
    if existing:
        mod_id = existing["id"]
        print(f"    exists as mod {mod_id}" + (", media only" if media_only else ""))
        if media_only:
            upload_media(mod_id, entry.get("screenshots", []), dist)
            return
        # Creating a mod sends the text; adding a FILE does not. Without this an
        # existing mod keeps whatever description it was created with, so a
        # rewritten listing would never reach the page it was written for.
        code, data = _req("PUT", f"/games/{GAME_ID}/mods/{mod_id}",
                          fields=[("name", entry["name"]),
                                  ("summary", entry["summary"]),
                                  ("description", entry["description"])])
        print(f"      text        {'updated' if code in (200, 201) else 'FAILED ' + str(code)}"
              f"{'' if code in (200, 201) else ' ' + json.dumps(data)[:200]}")
    elif media_only:
        print("    not published yet, nothing to attach media to")
        return
    else:
        code, data = _req("POST", f"/games/{GAME_ID}/mods",
                          fields=[("name", entry["name"]),
                                  ("summary", entry["summary"]),
                                  ("description", entry["description"]),
                                  ("visible", "1" if public else "0"),
                                  ("maturity_option", "0")]
                                 + [("tags[]", t) for t in entry["tags"]],
                          files=[("logo", entry["logo"])])
        if code != 201 and code != 200:
            print(f"    FAILED to create: {code} {json.dumps(data)[:300]}")
            return
        mod_id = data["id"]
        print(f"    created mod {mod_id} ({'public' if public else 'hidden'})")
    for suffix, modio_name in PLATFORM.items():
        z = Path(entry["zips"][suffix])
        # Not hardcoded: re-uploading to an existing mod is not an initial
        # release, and saying so in a public record is simply wrong.
        code, data = _req("POST", f"/games/{GAME_ID}/mods/{mod_id}/files",
                          fields=[("version", version), ("active", "true"),
                                  ("changelog", changelog),
                                  ("platforms[]", modio_name)],
                          files=[("filedata", z)])
        ok = code in (200, 201)
        print(f"      {modio_name:12s} {'ok' if ok else 'FAILED ' + str(code)}"
              f"{'' if ok else ' ' + json.dumps(data)[:200]}")
    upload_media(mod_id, entry.get("screenshots", []), dist)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", action="store_true", help="write the plan and stop")
    ap.add_argument("--publish", action="store_true", help="actually write to mod.io")
    ap.add_argument("--public", action="store_true", help="create visible instead of hidden")
    ap.add_argument("--only", action="append", help="limit to a pak stem, repeatable")
    ap.add_argument("--media-only", action="store_true",
                    help="attach screenshots to already-published mods and nothing else")
    ap.add_argument("--version", default="1.0", help="modfile version string")
    ap.add_argument("--changelog", default="Initial release.",
                    help="per-file changelog; say what changed on a re-upload")
    ap.add_argument("--listings", default=None, metavar="DIR",
                    help="folder of authored <stem>.md listings. A pak with no "
                         "listing file is NOT published, so this folder is the "
                         "allow-list. Strongly recommended.")
    args = ap.parse_args()

    dist = Path(__file__).parent.parent / "dist"
    listings = Path(args.listings) if args.listings else None
    if listings and not listings.is_dir():
        return print(f"no such listings folder: {listings}") or 1
    mf_path = dist / "modio_manifest.json"
    if args.manifest or not mf_path.is_file():
        paks = [p for p in sorted(sp.mods_dir().glob("SpecialistDesc_*.pak")) if p.stat().st_size]
        if not listings:
            print("⚠ no --listings given, so EVERY installed specialist is in the plan.\n"
                  "  Pass --listings to publish only the ones you have written copy for.")
        mf = build_manifest(paks, dist, listings)
        dist.mkdir(parents=True, exist_ok=True)
        mf_path.write_text(json.dumps(mf, indent=2), encoding="utf-8")
        print(f"manifest written: {mf_path}  ({len(mf)} specialists)")
        print("Edit the summaries and descriptions in it before publishing.")
        if args.manifest:
            return 0
    mf = json.loads(mf_path.read_text(encoding="utf-8"))
    if args.only:
        mf = [e for e in mf if any(o.lower() in Path(e["pak"]).stem.lower() for o in args.only)]

    problems = 0
    print(f"\n{'PUBLISHING' if args.publish else 'DRY RUN'}  game {GAME_ID}  "
          f"{len(mf)} specialists  {'PUBLIC' if args.public else 'hidden'}\n")
    for e in mf:
        print(f"  {e['name']}")
        print(f"    summary  {len(e['summary'])}/250  {e['summary'][:90]}")
        logo = Path(e["logo"])
        if not logo.is_file():
            print("    LOGO MISSING, mod.io will refuse creation"); problems += 1
        missing = [p for p, z in e["zips"].items() if not Path(z).is_file()]
        if missing:
            print(f"    ZIPS MISSING: {missing}"); problems += 1
        else:
            bad = []
            for suffix, z in e["zips"].items():
                with zipfile.ZipFile(z) as zz:
                    if f"{suffix}.pak" not in zz.namelist():
                        bad.append(suffix)
            if bad:
                print(f"    WRONG MARKER inside: {bad}"); problems += 1
            else:
                print(f"    6 zips, markers correct -> "
                      f"{', '.join(PLATFORM[s] for s in e['zips'])}")
        shots = e.get("screenshots", [])
        print(f"    screenshots {len(shots)}" + ("" if shots else "  (none in dist/screenshots/)"))
        if args.publish and not problems:
            publish(e, args.public, dist, args.media_only, args.version, args.changelog)
    if not args.publish:
        print(f"\n{'ready' if not problems else str(problems) + ' problems'}. "
              f"Add --publish to write. Nothing has been sent.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
