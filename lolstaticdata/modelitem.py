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
#    stats : Stats


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class PassiveStats(object):
    unique: bool
    name: str
    effects: str
    stats : Stats


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Active(object):
    unique: bool
    name: str
    effects: str
    #stats: Stats
    range : int
    cooldown : float


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Aura(object):
    unique: bool
    name: str
    effects: str
    #stats: Stats
    range : int


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Item(object):
    name: str
    id: int
    tier: str
    builds_from: List[int]
    builds_into: List[int]
    no_effects: bool
    removed: bool
    nickname: str
    passives: List[PassiveStats]
    active: List[Active]
    auras: List[Aura]
    stats: Stats
    shop: Shop

    def __json__(self, *args, **kwargs):
        d = self.to_dict()
        for name in ("health", "health_regen", "mana", "mana_regen", "armor", "magic_resistance", "attack_damage", "movespeed", "critical_strike_chance", "attack_speed", "ability_power", "cooldown_reduction", "gold_per_10", "heal_and_shield_power", "lifesteal", "magic_penetration", "lethality"):
            stat = getattr(self.stats, name)
            if stat.flat == stat.percent == stat.per_level == stat.percent_per_level == stat.percent_base == stat.percent_bonus == 0:
                camel = stringcase.camelcase(name)
                del d['stats'][camel]
        for i in range(len(d["passives"])):
            for name in (
            "health", "health_regen", "mana", "mana_regen", "armor", "magic_resistance", "attack_damage", "movespeed",
            "critical_strike_chance", "attack_speed", "ability_power", "cooldown_reduction", "gold_per_10",
            "heal_and_shield_power", "lifesteal", "magic_penetration", "armorPenetration", "lethality"):
                stats = d["passives"][i]["stats"]
                camel = stringcase.camelcase(name)
                if stats[0][camel]["flat"] == stats[0][camel]["percent"] == stats[0][camel]["perLevel"] == stats[0][camel]["percentPerLevel"] == stats[0][camel]["percentBase"] == stats[0][camel]["percentBonus"] == 0:

                    del stats[0][camel]
                    test = [x for x in stats if x]
                d["passives"][i]["stats"] = test
        #
        # for i in range(len(d["auras"])):
        #
        #     for name in (
        #     "health", "health_regen", "mana", "mana_regen", "armor", "magic_resistance", "attack_damage", "movespeed",
        #     "critical_strike_chance", "attack_speed", "ability_power", "cooldown_reduction", "gold_per_10",
        #     "heal_and_shield_power", "lifesteal", "magic_penetration", "armorPenetration", "lethality"):
        #         stats = d["auras"][i]["stats"]
        #         camel = stringcase.camelcase(name)
        #         if stats[0][camel]["flat"] == stats[0][camel]["percent"] == stats[0][camel]["perLevel"] == stats[0][camel]["percentPerLevel"] == stats[0][camel]["percentBase"] == stats[0][camel]["percentBonus"] == 0:
        #
        #             del stats[0][camel]
        #
        # for i in range(len(d["active"])):
        #
        #     for name in (
        #     "health", "health_regen", "mana", "mana_regen", "armor", "magic_resistance", "attack_damage", "movespeed",
        #     "critical_strike_chance", "attack_speed", "ability_power", "cooldown_reduction", "gold_per_10",
        #     "heal_and_shield_power", "lifesteal", "magic_penetration", "armorPenetration", "lethality"):
        #         stats = d["active"][i]["stats"]
        #         camel = stringcase.camelcase(name)
        #         if stats[0][camel]["flat"] == stats[0][camel]["percent"] == stats[0][camel]["perLevel"] == stats[0][camel]["percentPerLevel"] == stats[0][camel]["percentBase"] == stats[0][camel]["percentBonus"] == 0:
        #
        #             del stats[0][camel]

        if d['stats'].get('armorPenetration') == 0:
            del d['stats']['armorPenetration']
        return json.dumps(d, cls=ExtendedEncoder, *args, **kwargs)
