from typing import List
from dataclasses import dataclass
import dataclasses_json
import json
import stringcase

from ..common.utils import OrderedEnum, ExtendedEncoder
from ..common.modelcommon import (
    ArmorPenetration,
    DamageType,
    Health,
    HealthRegen,
    Mana,
    ManaRegen,
    Armor,
    MagicResistance,
    AttackDamage,
    AbilityPower,
    AttackSpeed,
    AttackRange,
    Movespeed,
    CriticalStrikeChance,
    Lethality,
    CooldownReduction,
    GoldPer10,
    HealAndShieldPower,
    Lifesteal,
    MagicPenetration,
    AbilityHaste,
    OmniVamp,
    Tenacity,
)


class ItemAttributes(OrderedEnum):
    TANK = "TANK"
    SUPPORT = "SUPPORT"
    MAGE = "MAGE"
    MOVEMENT = "MOVEMENT"
    ATTACK_SPEED = "ATTACK_SPEED"
    ONHIT_EFFECTS = "ONHIT_EFFECTS"
    FIGHTER = "FIGHTER"
    MARKSMAN = "MARKSMAN"
    ASSASSIN = "ASSASSIN"
    ARMOR_PEN = "ARMOR_PEN"
    MANA_AND_REG = "MANA_AND_REG"
    HEALTH_AND_REG = "HEALTH_AND_REG"
    LIFESTEAL_VAMP = "LIFESTEAL_VAMP"
    MAGIC_PEN = "MAGIC_PEN"
    ABILITY_POWER = "ABILITY_POWER"
    ATTACK_DAMAGE = "ATTACK_DAMAGE"
    CRITICAL_STRIKE = "CRITICAL_STRIKE"


class ItemRanks(OrderedEnum):
    MYTHIC = "MYTHIC"
    LEGENDARY = "LEGENDARY"
    EPIC = "EPIC"
    BASIC = "BASIC"
    STARTER = "STARTER"
    CONSUMABLE = "CONSUMABLE"
    POTION = "POTION"
    BOOTS = "BOOTS"
    TRINKET = "TRINKET"
    DISTRIBUTED = "DISTRIBUTED"
    MINION = "MINION"
    TURRET = "TURRET"
    SPECIAL = "SPECIAL"


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Stats(object):
    ability_power: AbilityPower
    armor: Armor
    armor_penetration: ArmorPenetration  # aka lethality  # TODO: See if this is ever non-zero  # TODO: Can we parse out lethality instead?
    attack_damage: AttackDamage
    attack_speed: AttackSpeed
    cooldown_reduction: CooldownReduction
    critical_strike_chance: CriticalStrikeChance
    gold_per_10: GoldPer10
    heal_and_shield_power: HealAndShieldPower
    health: Health
    health_regen: HealthRegen
    lethality: Lethality
    lifesteal: Lifesteal
    magic_penetration: MagicPenetration
    magic_resistance: MagicResistance
    mana: Mana
    mana_regen: ManaRegen
    movespeed: Movespeed
    ability_haste: AbilityHaste
    omnivamp: OmniVamp
    tenacity: Tenacity


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Prices(object):
    total: int
    combined: int
    sell: int


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Shop(object):
    prices: Prices
    purchasable: bool
    tags: List[str]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Passive(object):
    unique: bool
    mythic: bool
    name: str
    effects: str
    range: int
    cooldown: str
    stats: Stats


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Active(object):
    unique: bool
    name: str
    effects: str
    range: int
    cooldown: float


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Item(object):
    name: str
    id: int
    tier: int
    rank: List[str]
    builds_from: List[int]
    builds_into: List[int]
    special_recipe: int
    no_effects: bool
    removed: bool
    required_champion: str
    required_ally: str
    icon: str
    simple_description: str
    nicknames: List[str]
    passives: List[Passive]
    active: List[Active]
    stats: Stats
    shop: Shop
    iconOverlay: str

    def __json__(self, *args, **kwargs):
        # Use dataclasses_json to get the dict
        d = self.to_dict()
        # Return the (un)modified dict
        return json.dumps(d, cls=ExtendedEncoder, *args, **kwargs)
