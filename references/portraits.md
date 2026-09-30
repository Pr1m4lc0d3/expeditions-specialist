# Generating a portrait that matches the game

The specialist art sits between photoreal and cartoon: semi-realistic, painted,
believable anatomy, restrained lighting. Hitting that deliberately took seven
attempts, and the failures are more useful than the success.

## Describing the style in words does not work

The generator has two attractors and no stable ground between them. Wording lands
on one or the other:

| you write | you get |
|---|---|
| "game engine character render" | a photograph. In 2026 that phrase means photoreal. |
| "stylized 3D animated feature film character" | Pixar. |
| "painted digital character portrait" | a photograph again. |
| "semi-realistic painterly illustration" | closer, still photographic. |

Five prompts, all careful, none of them landing between the two.

## What works: restyle against reference images

Attach **two existing badges you like**, plus **the portrait you want restyled**,
and keep the instruction to about sixty words.

```
codex exec -m gpt-5.5 -i ref_a.png -i ref_b.png -i base.png -- "<sixty words>"
```

```
Generate an image. Images 1 and 2 are the target art style. Image 3 is a
character who must be redrawn in that exact style.

Redraw image 3 so its rendering matches images 1 and 2: the same smooth painted
skin, the same soft illustrative shading, the same treatment of hair, the same
overall painted finish.

Keep everything else from image 3 unchanged: the same person, the same face, the
same headgear and equipment, the same clothing, the same pose, the same
head-and-shoulders framing.

Background: a solid opaque flat mid grey field filling every part of the image
the character does not cover. Every pixel of the image is opaque.

Square 1:1. No text anywhere.
```

**Length matters.** A 400-word description drowns the reference and the words
win. Sixty words let the images carry the style.

The same instruction with the subject swapped does the base pass, and the two-pass
shape (describe the character, then restyle) is more reliable than trying to get
both in one generation.

## Prompts are positive only

**There is no negative channel, so naming a thing draws it.** One failed prompt
spent a paragraph on `no photographic skin pores, no broken capillaries, no film
grain`, which is very likely why that attempt came back photographic.

State what you want. "Skin is a smooth even matte surface" rather than "no pores".

## Four ways the command silently produces nothing

Each of these printed success and wrote no file.

- **Pin the model.** The CLI default resolved to a model the installed version
  could not call. It printed `Done - the image has been generated and saved` and
  produced nothing.
- **`--` before the prompt.** `-i` is variadic; without a terminator it swallows
  the prompt as another filename and the CLI blocks reading stdin.
- **Redirect stdin from `/dev/null`.** A preceding heredoc leaves stdin in a
  state where the CLI waits for input.
- **Count the output directories before and after.** When a run produces nothing,
  "newest directory" is the *previous* run's folder. That is how a portrait of
  one character gets copied over another's filename and reviewed as if it were
  new. It happened, and the wrong image was reported as a result.

## Reference images bring their own background

If the badges you attach are cut out, the output inherits their transparency.
That is useful when you want alpha and surprising when you don't. Say explicitly
that every pixel is opaque, or expect a cut-out.

## Text

Caps, patches, coveralls and hi-vis are where lettering gets smuggled in. Ban it
several ways in the same prompt: plain, unmarked, no lettering, no logo, no
printed patch.

## Do not reuse a visual shorthand across characters

Two specialists were each given "a smear of black engine grease" on the cheek in
nearly identical words. They came out looking like a matched set rather than two
people. Whatever the stock visual for a job is, use it once.
