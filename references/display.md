# Why an ability does not show on the card

An ability can apply perfectly and never appear. The specialist loads, the stat
works in a run, and the hire screen simply does not draw the line. There is no
error, no warning, no placeholder. That silence is the whole difficulty: from
inside the game a missing label is indistinguishable from an ability you forgot
to add.

Three separate causes, and they need different fixes.

## 1. The field name is not in the schema

**This is the one that cost real labels on a shipped roster.** A descriptor whose
field name the schema does not define is discarded on load.

Saber misspelled three descriptor members, so the *correct* spelling is the
broken one:

| what the schema defines | what you would naturally write |
|---|---|
| `winchLenghtIncreasedMetersUiDesc` | `winchLength...`, and "Lenght" is the real one |
| `additionalAddonFuelCountCountUiDesc` | `...FuelCountUiDesc` |
| `additionalAddonWheelsCountCountUiDesc` | `...WheelsCountUiDesc` |
| `additionalAddonRepairsCountUiDesc` | correct here, which is what makes it a trap |

Repairs is spelled normally while fuel and wheels double the word `Count`. There
is no rule to infer. **Never build a descriptor name as `field + "UiDesc"`.**

```python
sp.desc_field("AdditionalAddonSupplies", "additionalAddonFuelCount")
# -> 'additionalAddonFuelCountCountUiDesc'
```

A roster sweep found 21 invented field names across thirteen specialists. Three
carried real label text that had never been drawn; one of those was a character
verified working in game by screenshot, because everything else about him was.

```
python scripts/schema_members.py --check     # scan installed specialists
python scripts/schema_members.py WinchImprove
```

`specialist.display_problems` now reports these, so the doctor catches them.

## 2. The modifier wants one line, not per-field labels

Some modifiers draw a single sentence for the whole ability and ignore per-field
labels entirely. `ImproveWinchedTruck` defines no per-field descriptor members at
all, only `overrideUiDesc` and `allSameUiDesc`, so labelling its eight numeric
fields individually produces nothing.

`schema_snapshot.json` carries a `display_contract` built from how all 25 shipped
specialists display all 46 modifiers they use. Read it before inventing a shape.
Three abilities once failed here, and the over-correction that followed flagged a
dozen working ones, which is worse than not checking.

## 3. The field is deliberately never labelled

Vanilla leaves some fields unlabelled on purpose. `WinchImprove` labels neither
cable length nor power; `EmergencyWinch` labels nothing. The contract records
these as `never_labelled`, and "fixing" one is a regression. Aphi Darlington's
`echolotApplicationAdditionalTime` was "fixed" this way and had to be reverted.

## Unused is not the same as free

A modifier absent from `display_contract` is used by no shipped specialist, so
neither its rendering nor its behaviour has ever been observed.
`DroneDiscoverScoutZones` looks like an obvious pick and is one of these. It may
work, it may draw nothing, and the only way to find out is in game.
