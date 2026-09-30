# The 25 shipped specialists

Pulled from `initial.cache_block` inside `preload/paks/client/initial.pak`, where
they are stored as plain text. They are **not** in `initial_release.sslbundle`,
which is where people look and conclude the values are unreadable.

Names are localisation keys, so searching the paks for a specialist's name finds
nothing. The table is `[strings]/strings_english.str` in the same pak, UTF-16LE,
keyed `MECHANIC_05_UI_NAME` and so on. It also holds all 77 `SPEC_MODS_*` ability
label strings.

Beat these numbers rather than guessing at them.

## Mechanic_01  (Mechanic, cost 600)

AnchorSupplies, AnchorRadius, TruckDamage

| field | value |
|---|---|
| `anchorMaxLimitCount` | 5 |
| `anchorRadiusIncreasedPercent` | 100 |
| `truckDamageEngineReducedPercent` | 30 |
| `truckDamageGearboxReducedPercent` | 30 |
| `truckDamageGasTankReducedPercent` | 30 |
| `truckDamageSuspensionReducedPercent` | 30 |

## Mechanic_02  (Mechanic, cost 1400)

RepairConsumption, TruckDamage, FuelConsumption

| field | value |
|---|---|
| `repairConsumpionReducedPercent` | 30 |
| `truckDamageEngineReducedPercent` | 15 |
| `truckDamageGearboxReducedPercent` | 15 |
| `truckDamageGasTankReducedPercent` | 15 |
| `truckDamageSuspensionReducedPercent` | 15 |
| `fuelConsumpionReducedPercent` | 15 |

## Mechanic_03  (Mechanic, cost 800)

ArmorCapacity, ArmorRestoreEverywhere, FuelConsumption

| field | value |
|---|---|
| `armorEngineIncreasedPercent` | 30 |
| `armorGearboxIncreasedPercent` | 30 |
| `armorGasTankIncreasedPercent` | 30 |
| `armorSuspencionIncreasedPercent` | 30 |
| `fuelConsumpionReducedPercent` | 20 |

## Mechanic_04  (Mechanic, cost 1500)

EmergencyWinch, RepairBuildingConsumption, TruckDamage

| field | value |
|---|---|
| `winchFuelPerMinute` | 20 |
| `repairBuildingConsumptionReducedPercent` | 40 |
| `truckDamageEngineReducedPercent` | 10 |
| `truckDamageGearboxReducedPercent` | 10 |
| `truckDamageGasTankReducedPercent` | 10 |
| `truckDamageSuspensionReducedPercent` | 10 |
| `truckDamageWheelReducedPercent` | 10 |

## Mechanic_05  (Mechanic, cost 1200)

ElectricityConsumption, WheelDroneTorque, WheelDroneArmor, WheelDroneArmorRestoreEverywhere

| field | value |
|---|---|
| `wheelDroneElectricityConsumptionReducedPercent` | 30 |
| `wheelDroneAbilityElectricityConsumptionReducedPercent` | 30 |
| `metaldetectorElectricityConsumptionReducedPercent` | 30 |
| `radarElectricityConsumptionReducedPercent` | 30 |
| `wheelDroneTorqueIncreasedPercent` | 50 |
| `wheelDroneArmorEngineIncreasedPercent` | 30 |
| `wheelDroneArmorBatteryIncreasedPercent` | 30 |
| `wheelDroneArmorSuspencionIncreasedPercent` | 30 |

## Logistics_Specialist_01  (Logistics, cost 500)

AdditionalDeployResources, BinocularRadius, MayDiscoverZones

| field | value |
|---|---|
| `additionalDeployFuelCount` | 100 |
| `additionalDeployRepairsCount` | 200 |
| `binocularPartRadiusIncreasedMeters` | 150 |

## Logistics_Specialist_02  (Logistics, cost 900)

GuaranteedAirdropResource, AdditionalAddonSupplies, BinocularRadius, MayDiscoverZones

| field | value |
|---|---|
| `guarantedAirdropFuelCount` | 50 |
| `additionalAddonFuelCount` | 10 |
| `binocularPartRadiusIncreasedMeters` | 100 |

## Logistics_Specialist_03  (Logistics, cost 1000)

EmergencyStockSupplies, AdditionalAddonSupplies, BinocularRadius, MayDiscoverZones

| field | value |
|---|---|
| `emergencyStockRepairs` | 50 |
| `emergencyStockWheels` | 2 |
| `additionalAddonRepairsCount` | 20 |
| `binocularPartRadiusIncreasedMeters` | 100 |

## Logisitics_Specialist_04  (Logistics, cost 1000)

WheelDroneZone, WheelDroneFriction, WheelDroneScoutRadius, MayDiscoverZones

| field | value |
|---|---|
| `wheelDroneZoneIncreasedPercent` | 50 |
| `wheelDroneOnModelFrictionIncreasedPercent` | 200 |
| `wheelDroneBodyFrictionAsphaltIncreasedPercent` | 200 |
| `wheelDroneSubstanceFrictionIncreasedPercent` | 200 |
| `wheelDroneBodyFrictionIncreasedPercent` | 200 |
| `wheelDroneFullScoutRadiusIncreasedMeters` | 100 |
| `wheelDronePartScoutRadiusIncreasedMeters` | 100 |

## Hydrologist_01  (Hydrologist, cost 600)

EngineUnderwaterDamage, MayDiscoverZones

| field | value |
|---|---|
| `engineUnderwaterDamageReducedPercent` | 100 |

## Hydrologist_02  (Hydrologist, cost 1500)

EcholotModeAura, UnderwaterAnchorSetup, MayDiscoverZones

| field | value |
|---|---|
| `echolotRadiusOverrideMeters` | 7 |
| `echolotStepCountOverride` | 9 |
| `echolotApplicationAdditionalTime` | 1 |

## Hydrologist_03  (Hydrologist, cost 1000)

EcholotModeCone, EngineUnderwaterDamage, MayDiscoverZones

| field | value |
|---|---|
| `echolotRadiusOverrideMeters` | 75 |
| `echolotStepCountOverride` | 20 |
| `echolotConeAngle` | 45 |
| `echolotApplicationAdditionalTime` | 1 |
| `engineUnderwaterDamageReducedPercent` | 50 |

## Hydrologist_04  (Hydrologist, cost 1200)

EcholotModeSnow, MayDiscoverZones

| field | value |
|---|---|
| `echolotRadiusOverrideMeters` | 20 |
| `echolotStepCountOverride` | 20 |

## Jaeger_01  (Jaeger, cost 700)

JackscrewSupplies, FogOfWarTranspRadius, MayDiscoverZones

| field | value |
|---|---|
| `jackscrewMaxLimitCount` | 2 |
| `fogOfWarTranspRadiusInceasedMeters` | 10 |

## Jaeger_02  (Jaeger, cost 900)

TruckDamage, BinocularRadius, MayDiscoverZones

| field | value |
|---|---|
| `truckDamageWheelReducedPercent` | 50 |
| `binocularFullRadiusIncreasedMeters` | 100 |

## Jaeger_03  (Jaeger, cost 1300)

WinchImprove, FogOfWarTranspRadius, MayDiscoverZones

| field | value |
|---|---|
| `winchLengthIncreasedMeters` | 10 |
| `winchPowerIncreasedPercent` | 30 |
| `fogOfWarTranspRadiusInceasedMeters` | 10 |

## Jaeger_04  (Jaeger, cost 1100)

ImproveWinchedTruck, FogOfWarTranspRadius, MayDiscoverZones

| field | value |
|---|---|
| `engineResponsivenessIncreasedPercent` | 30 |
| `torqueIncreasedPercent` | 30 |
| `onModelFrictionIncreasedPercent` | 30 |
| `bodyFrictionAsphaltIncreasedPercent` | 30 |
| `substanceFrictionIncreasedPercent` | 30 |
| `bodyFrictionIncreasedPercent` | 30 |
| `fuelConsumptionReducedPercent` | 30 |
| `fogOfWarTranspRadiusInceasedMeters` | 20 |

## Operator_01  (Operator, cost 600)

DroneRadius, DroneHeight, DroneScoutRadius, MayDiscoverZones, DroneAcceleration, DroneControllability

| field | value |
|---|---|
| `droneRadiusIncreasedMeters` | 200 |
| `droneHeightIncreasedMeters` | 20 |
| `droneFullScoutRadiusIncreasedMeters` | 0 |
| `dronePartScoutRadiusIncreasedMeters` | 50 |
| `droneAccelerationIncreasedPercent` | 30 |
| `droneAccelerationHeightIncreasedPercent` | 30 |
| `droneControllabilityResForceIncreasedPercent` | 20 |
| `droneControllabilityResForceRotationIncreasedPercent` | 20 |
| `droneControllabilityForceRotationIncreasedPercent` | 20 |

## Operator_02  (Operator, cost 900)

DroneTrade, DroneRadius, MayDiscoverZones, DroneAcceleration, DroneControllability

| field | value |
|---|---|
| `droneRadiusIncreasedMeters` | 50 |
| `droneAccelerationIncreasedPercent` | 30 |
| `droneAccelerationHeightIncreasedPercent` | 30 |
| `droneControllabilityResForceIncreasedPercent` | 20 |
| `droneControllabilityResForceRotationIncreasedPercent` | 20 |
| `droneControllabilityForceRotationIncreasedPercent` | 20 |

## Operator_03  (Operator, cost 1200)

DroneMaxSpeed, DroneScoutRadius, DroneRadius, DroneControllability, DroneAcceleration, MayDiscoverZones

| field | value |
|---|---|
| `droneMaxSpeedIncreasedPercent` | 70 |
| `droneFullScoutRadiusIncreasedMeters` | 50 |
| `droneRadiusIncreasedMeters` | 50 |
| `droneControllabilityResForceIncreasedPercent` | 30 |
| `droneControllabilityResForceRotationIncreasedPercent` | 30 |
| `droneControllabilityForceRotationIncreasedPercent` | 30 |
| `droneAccelerationIncreasedPercent` | 70 |
| `droneAccelerationHeightIncreasedPercent` | 70 |

## Operator_04  (Operator, cost 1200)

DroneItemSetup, DroneMaxSpeed, DroneMaxSpeed, DroneControllability, MayDiscoverZones

| field | value |
|---|---|
| `droneMaxSpeedIncreasedPercent` | 25 |
| `droneControllabilityResForceIncreasedPercent` | 50 |
| `droneControllabilityResForceRotationIncreasedPercent` | 50 |
| `droneControllabilityForceRotationIncreasedPercent` | 50 |

## Manager_01  (Manager, cost 700)

TreasureItemSellPrice

| field | value |
|---|---|
| `treasureItemSellPriceIncreasedPercent` | 50 |

## Manager_02  (Manager, cost 1500)

FreeEvacuation, ItemCost, ItemSellPrice

| field | value |
|---|---|
| `freeEvacuationMaxLimitCount` | 1 |
| `itemCostReducedPercent` | 10 |
| `itemSellPriceIncreasedPercent` | 30 |

## Manager_03  (Manager, cost 3000)

AdditionalReward, AdditionalTreasureItems

| field | value |
|---|---|
| `additionalRewardExpeditionIncreasedPercent` | 20 |
| `additionalRewardSideQuestsIncreasedPercent` | 20 |
| `additionalRewardTasksIncreasedPercent` | 30 |
| `additionalTreasureItemsCount` | 1 |

## Manager_04  (Manager, cost 2000)

AirdropReroll, ItemSellPrice

| field | value |
|---|---|
| `airdropRerollCost` | 2000 |
| `itemSellPriceIncreasedPercent` | 30 |
