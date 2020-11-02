from typing import List
from dataclasses import dataclass
import dataclasses_json
import json
import stringcase

from common.utils import OrderedEnum, ExtendedEncoder
from common.modelcommon import (
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
)


class ItemAttributes(OrderedEnum):
    STARTER_ITEMS = "STARTER_ITEMS"
    TOOLS = "TOOLS"
    DEFENSE = "DEFENSE"
    ATTACK = "ATTACK"
    MAGIC = "MAGIC"
    MOVEMENT = "MOVEMENT"
    JUNGLING = "JUNGLING"
    LANING = "LANING"
    ARMOR_PENETRATION = "ARMOR_PENETRATION"
    MAGIC_PENETRATION = "MAGIC_PENETRATION"
    CONSUMABLE = "CONSUMABLE"
    GOLD_INCOME = "GOLD_INCOME"
    VISION_AND_TRINKETS = "VISION_AND_TRINKETS"
    ARMOR = "ARMOR"
    HEALTH = "HEALTH"
    HEALTH_REGEN = "HEALTH_REGEN"
    MAGIC_RESISTANCE = "MAGIC_RESISTANCE"
    MAGIC_RESIST = "MAGIC_RESIST"
    ATTACK_SPEED = "ATTACK_SPEED"
    CRITICAL_STRIKE = "CRITICAL_STRIKE"
    DAMAGE = "ATTACK_DAMAGE"
    LIFE_STEAL = "LIFE_STEAL"
    COOLDOWN_REDUCTION = "COOLDOWN_REDUCTION"
    MANA = "MANA"
    MANA_REGEN = "MANA_REGEN"
    ABILITY_POWER = "ABILITY_POWER"
    BOOTS = "BOOTS"
    OTHER_MOVEMENT_ITEMS = "OTHER_MOVEMENT_ITEMS"


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
    name: str
    effects: str
    range: int
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
    builds_from: List[int]
    builds_into: List[int]
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

    def __json__(self, *args, **kwargs):
        # Use dataclasses_json to get the dict
        d = self.to_dict()
        # Return the (un)modified dict
        return json.dumps(d, cls=ExtendedEncoder, *args, **kwargs)
