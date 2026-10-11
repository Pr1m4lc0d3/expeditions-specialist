# Designing the character, not just the numbers

Two rules learned by getting both wrong in the same afternoon.

## One team, one problem

A specialist pair was built whose modifiers collided with nothing. Zero shared
fields with any existing character, every number beating its vanilla equivalent,
and it was still the wrong pair, because two other specialists already owned that
job. The roster had two teams doing the same thing.

**Check what a character is FOR against the roster, not what fields it writes to.**
A clash detector will tell you the numbers are clean and tell you nothing about
whether the character should exist.

The distinction that matters is the problem, not the object. The ground drone and
the air drone look like one subject and are two: different modifiers, different
play pattern, different moment in a run. Two teams on the *ground* drone would be
a duplicate. One team on each is not.

## Co-dependent pairs

The best design in the shipped roster is a pair that mirrors one field with
opposite signs, so the payoff only arrives when both seats are filled.

```
specialist A    wheelDroneElectricityConsumptionReducedPercent   -40
specialist B    wheelDroneElectricityConsumptionReducedPercent   +90
                                                          net    +50
```

A alone is a liability. B alone is unremarkable. Together they beat anything
vanilla offers and cost two of your seats to do it.

**A negative value inverts the effect.** That is the whole mechanism, and it is
how a penalty is written anywhere in the format.

**Foreshadow the penalty in the description.** The shipped characters do this:
one ends on a warning about your wallet, another on a remark about strange radio
frequencies. The player should meet the drawback in the story before they find it
in the numbers.

## The additive third

A pair is not the only working shape. One specialist on the shipped roster is a
dog, and a dog does not trade a capability away to buy another one, so the mirror
above is wrong for him. He carries **no handicap at all** and still is not
overpowered, because of what he touches rather than how much.

```
Scout   droneAccelerationIncreasedPercent      +150   air drone team
        wheelDroneZoneIncreasedPercent         +125   ground drone team
        winchLengthIncreasedMeters              +40   recovery team
        additionalRewardTasksIncreasedPercent   +50   economy team
```

Four contributions, one per team, and **not one of them is a field any tuned pair
shares**. Every 2.5x net stays exactly where it was set. That is the condition
that lets a third character join any team without being balanced against it, and
it is mechanically checkable: intersect his numeric fields with both halves of
every pair and require the result to be empty.

Two things make the slot findable:

- **Prefer a modifier the roster does not use.** `AdditionalReward` was held by
  nobody, so it cost nothing to claim.
- **A pair's unmirrored stat can be moved.** Nom Nom held `DroneAcceleration`
  against no opposite number, so handing it to Scout left the air-drone net
  untouched and dropped Nom Nom from nine abilities to eight.

⚠ **Check the display contract before claiming an unused modifier.**
`DroneDiscoverScoutZones` looked like the obvious dog ability and is absent from
`display_contract` entirely, which means no vanilla specialist exercises it and
neither its rendering nor its behaviour has ever been observed. Unused is not the
same as free.

## Name people, not equipment

Names assembled from the job read as catalogue parts. Snatchblock, Gusset,
Farsight, Treadwell: every one encodes the role in the surname, and the result
sounds like an NPC list rather than a crew.

The ones that work are **plausible names where the pun is phonetic and
incidental**:

- *Tydewell* is "tied well", which is what a loadmaster does, carried entirely in
  the sound of a real-looking surname.
- *Klimmenstein* is a climber, in Swiss-German, in a name a person could have.
- *Pebblestone* is a rockhound and an abrasive personality and a plausible
  surname at once.
- *Bonnie Sweete* works by contradiction: a weathered, blunt, fifty-five-year-old
  is neither, and the name characterises her by being wrong about her.

Single-layer names fail. Stack two meanings, or let the name contradict the
person.

## The name field is not a name field

Look at what the shipped characters put in `uiName`:

- a joke title rather than the man's name, with his real name in the story
- a leetspeak handle that tells you he is a basement kid before you read a word
- a creature named for the only word it says
- a dog

`uiName` is what the crew calls them. The real name lives in the description.
Use the field for character, not for identification.

## Length

`uiName` is capped at 20 characters and that one is real. `uiDesc` is documented
at 280 and that one is not: a shipped specialist runs 519 and has rendered since
2025. Write the character, then check it fits under 519.

## Contractions

Read the shipped descriptions and count them. "he's actually the last", "you're
in a bind, he's always on call", "don't forget to check your bitcoin wallet".

Prose written entirely in full forms reads as distant and informational whether
you meant it or not, and it is the most reliable surface tell of machine-written
text. Contract by default. Expand only for stress.
