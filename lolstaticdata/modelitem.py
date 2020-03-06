from typing import List
from dataclasses import dataclass
import dataclasses_json
import json
import stringcase

from modelcommon import ArmorPenetration, DamageType, Health, HealthRegen, Mana, ManaRegen, Armor, MagicResistance, AttackDamage, AbilityPower, AttackSpeed, AttackRange, Movespeed, CriticalStrikeChance, Lethality, CooldownReduction, GoldPer10, HealAndShieldPower, Lifesteal, MagicPenetration
from utils import OrderedEnum, ExtendedEncoder


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
    MANA_REGEN= "MANA_REGEN"
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
class Shop(object):
    price_total: int
    price_combined: int
    price_sell: int
    tags: List[str]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Passive(object):
    unique: bool
    name: str
    effects: str
    range: int
    stats : Stats


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Active(object):
    unique: bool
    name: str
    effects: str
    range : int
    cooldown : float


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Aura(object):
    unique: bool
    name: str
    effects: str
    range : int


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
    icon: str
    nicknames: List[str]
    passives: List[Passive]
    active: List[Active]
    auras: List[Aura]
    stats: Stats
    shop: Shop

    def __json__(self, *args, **kwargs):
        stat_names = ["health", "health_regen", "mana", "mana_regen", "armor", "magic_resistance", "attack_damage", "movespeed", "critical_strike_chance", "attack_speed", "ability_power", "cooldown_reduction", "gold_per_10", "heal_and_shield_power", "lifesteal", "magic_penetration", "lethality", "armor_penetration"]

        # Use dataclasses_json to get the dict
        d = self.to_dict()

        # Remove armor pen if it's 0 (default)
        if d['stats'].get('armorPenetration') == 0:
            del d['stats']['armorPenetration']

        # Remove stats if they are empty
        for name in stat_names:
            stat = getattr(self.stats, name)
            if stat.flat == stat.percent == stat.per_level == stat.percent_per_level == stat.percent_base == stat.percent_bonus == 0:
                camel = stringcase.camelcase(name)
                del d['stats'][camel]

        # Remove passive/active/aura stats if they are empty
        for passive_active_aura in ("passives",): # "actives", "auras"):  # Actually, actives and auras don't have stats
            for i in range(len(d[passive_active_aura])):
                dstats = d[passive_active_aura][i]["stats"]
                stats = getattr(self, passive_active_aura)[i].stats
                for name in stat_names:
                    camel = stringcase.camelcase(name)
                    stat = getattr(stats, name)
                    if stat.flat == stat.percent == stat.per_level == stat.percent_per_level == stat.percent_base == stat.percent_bonus == 0:
                        del dstats[camel]

        # Return the modified dict
        return json.dumps(d, cls=ExtendedEncoder, *args, **kwargs)
