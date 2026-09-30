# Framing the three textures

## Sizes

| Slot | Canvas | Content box inside it | Where |
|---|---|---|---|
| `bage` | 364 x 364 | the whole canvas | the badge on the recruitment card |
| `bg` | 380 x 92 | **115 x 92 at x 23, y 0** | recruitment list row, expedition setup |
| `bgSmall` | 124 x 52 | **67 x 52 at x 27, y 0** | slot strip at the top of the screen |

The strips are mostly empty. The subject sits in a content box at the left and
the rest of the canvas is transparent. That is how the shipped ones are built,
not a mistake.

Cut **one** content box and resample it for both strips. Two separately cropped
strips will disagree with each other; the 2025 originals match at 0.99, so that
is how they were made.

## The badge

Whole bust in frame. Both shoulders inside it, with backdrop visible either side.
A margin of empty backdrop above the head. Bust running down to the bottom edge.

The failure this prevents: a badge cropped so tight the head fills the frame and
both shoulders run off the sides. Two specialists shipped that way for months.

## The strips: anchor to the head's HEIGHT

This took four wrong answers, and the wrong ones are worth knowing because each
looks right until a different portrait breaks it.

**A fraction of the badge.** Template matching a shipped `bg` back into its own
`bage` scores 0.986 and gives a window starting at y = 0.2833. That is exact for
that portrait and wrong for every other. On a more zoomed-in portrait it lands on
the hat brim and crops the hat off above the eyes.

**The widest row of the alpha mask.** On a head-and-shoulders portrait the widest
row is the shoulders, so the window zooms out and the face becomes a speck.

**The head's width.** Head width depends on headgear. A hard hat produced a
full-torso strip with a thumbnail face; narrower goggles produced a face clipped
at both the goggles and the chin, from the same rule.

**Head height is stable across characters where width is not.** The content box is
115 x 92, wider than it is tall, and a head is not. Drive the window from head
height at 0.80 of the content height and let the width follow the box's aspect.

Three details the head box needs, each found by a character breaking it:

- **Measure the head's width across the crown-to-brow band only.** Down at chin
  level the shoulders are already in the row range, and on a broad character
  carrying gear the silhouette there is the body, not the head.
- **Take the crown from the silhouette, not the face detector.** A guess like
  `y - h * 0.95` about how far headgear rises clipped a hard hat and a pair of
  goggles. The topmost opaque row inside the head's columns is the real top.
- **Take the largest face in the upper frame, not the largest overall.** Face
  cascades fire on torsos, and the false positive is larger than the real face.
  One character's "face" was reported 130 px below his actual chin.

## Transparency

All three need alpha. An opaque badge renders as a solid photo block filling the
card.

If the portrait arrives on a flat pale backdrop, any background remover handles
it. If the backdrop is **dark**, partial-alpha edge pixels carry the backdrop
colour and grey hair comes out muddy. Decontaminate rather than just matte:

```
F = (C - (1 - a) * B) / a
```

`B` is the median colour of the pixels the matte called fully transparent. Blend
the correction in proportion to alpha, ramping from about a = 0.15, so low-alpha
noise is not amplified.

Measured evidence that it is needed: on one dark-backdrop source the transparent
pixels sat at RGB 9,8,8 and 3,3,3, and that black was showing up inside the hair.

Best avoided entirely. Generate on flat pale grey, or generate with alpha already
present.

## Verifying

**Crop the region and look at it against a checkerboard.** Do not trust a pixel
detector. One counting "red fringe artifacts" reported 5,046 defects that were a
character's freckles, and 15,106 that were a copper wire coil. Both were nearly
acted on, and a clean image was nearly regenerated because of a number nobody had
looked at.
