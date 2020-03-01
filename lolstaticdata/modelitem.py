from typing import List
from dataclasses import dataclass
import dataclasses_json
import json
import stringcase

from modelcommon import DamageType, Health, HealthRegen, Mana, ManaRegen, Armor, MagicResistance, AttackDamage, AbilityPower, AttackSpeed, AttackRange, Movespeed, CriticalStrikeChance, Lethality, CooldownReduction, GoldPer10, HealAndShieldPower, Lifesteal, MagicPenetration
from utils import OrderedEnum, ExtendedEncoder


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Stats(object):
    ability_power: AbilityPower
    armor: Armor
    armor_penetration: float  # aka lethality  # TODO: See if this is ever non-zero  # TODO: Can we parse out lethality instead?
    attack_damage: AttackDamage
    attack_speed: AttackSpeed
    cooldown_reduction: CooldownReduction
    critical_strike_chance: CriticalStrikeChance
    gold_per_10: GoldPer10
    heal_and_shield_power: HealAndShieldPower
    health: Health
    health_regen: HealthRegen
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


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Active(object):
    unique: bool
    name: str
    effects: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Aura(object):
    unique: bool
    name: str
    effects: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Item(object):
    name: str
    id: int
    tier: str
    builds_from: List[str]
    builds_into: List[str]
    no_effects: bool
    removed: bool
    nickname: str
    passives: List[Passive]
    active: List[Active]
    auras: List[Aura]
    stats: Stats
    shop: Shop

    def __json__(self, *args, **kwargs):
        d = self.to_dict()
        for name in ("health", "health_regen", "mana", "mana_regen", "armor", "magic_resistance", "attack_damage", "movespeed", "critical_strike_chance", "attack_speed", "ability_power", "cooldown_reduction", "gold_per_10", "heal_and_shield_power", "lifesteal", "magic_penetration"):
            stat = getattr(self.stats, name)
            if stat.flat == stat.percent == stat.unique == stat.unique_percent == stat.per_level == stat.percent_per_level == stat.percent_base == stat.percent_bonus == 0:
                camel = stringcase.camelcase(name)
                del d['stats'][camel]
        if d['stats'].get('armor_penetration') == 0:
            del d['stats']['armor_penetration']
        return json.dumps(d, cls=ExtendedEncoder, *args, **kwargs)