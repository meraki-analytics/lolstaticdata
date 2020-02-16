from typing import Set, Mapping, List, Union
from dataclasses import dataclass
from enum import Enum, auto


@classmethod
def from_string(cls, string: str):
    string = string.upper()
    for e in cls:
        if e.name == string:
            return e
    return None
Enum.from_string = from_string


class Resource(Enum):
    NO_COST = auto()
    MANA = auto()
    ENERGY = auto()
    RAGE = auto()
    FURY = auto()
    HEALTH = auto()
    MAXIMUM_HEALTH = auto()
    CURRENT_HEALTH = auto()
    HEALTH_PER_SECOND = auto()
    MANA_PER_SECOND = auto()
    CHARGE = auto()
    OTHER = auto()


class AttackType(Enum):
    MELEE = auto()
    RANGED = auto()


class AdaptiveType(Enum):
    PHYSICAL_DAMAGE = auto()
    MAGIC_DAMAGE = auto()


class Role(Enum):
    CONTROLLER = auto()
    FIGHTER = auto()
    MAGE = auto()
    MARKSMAN = auto()
    SLAYER = auto()
    TANK = auto()
    SPECIALIST = auto()
    ASSASSIN = auto()
    # TODO: Finish this


@dataclass
class Stats(object):
    health_base: float
    health_per_level: float
    health_per_5_seconds_base: float
    health_per_5_seconds_per_level: float
    mana_base: float
    mana_per_level: float
    mana_per_5_seconds_base: float
    mana_per_5_seconds_per_level: float
    armor_base: float
    armor_per_level: float
    magic_resistance_base: float
    magic_resistance_per_level: float
    attack_damage_base: float
    attack_damage_per_level: float
    attack_range: float
    movespeed: float
    acquisition_radius: float
    selection_radius: float
    pathing_radius: float
    gameplay_radius: float
    critical_strike_base: float
    critical_strike_modifier: float
    attack_speed_base: float
    attack_speed_per_level: float
    attack_speed_ratio: float
    attack_cast_time: float
    attack_total_time: float
    attack_delay_offset: float
    attack_range_base: float
    attack_range_per_level: float
    aram_damage_taken: float
    aram_damage_dealt: float
    aram_healing: float
    aram_shielding: float
    urf_damage_taken: float
    urf_damage_dealt: float
    urf_healing: float
    urf_shielding: float
    # TODO: Should some of these be int?


@dataclass
class AttributeRatings(object):
    damage: int
    toughness: int
    control: int
    mobility: int
    utility: int
    ability_reliance: int
    attack: int
    defense: int
    magic: int
    difficulty: int


@dataclass
class Modifier(object):
    values: List[Union[int, float]]
    units: List[str]


@dataclass
class Cooldown(object):
    modifiers: List[Modifier]
    affected_by_cdr: bool


@dataclass
class Cost(object):
    modifiers: List[Modifier]


@dataclass
class Leveling(object):
    attribute: str
    modifiers: List[Modifier]


@dataclass
class Effect(object):
    description: str
    icon: str
    leveling: List[Leveling]


@dataclass
class Ability(object):
    name: str
    effects: List[Effect]
    cost: Cost
    cooldown: Cooldown
    targeting: str
    affects: str
    spellshieldable: str
    resource: str
    damageType: str
    spellEffects: str
    projectile: str
    onHitEffects: str
    occurrence: str
    notes: str
    blurb: str
    missile_speed: str
    recharge_rate: str
    collision_radius: str
    tether_radius: str
    on_target_cd_static: str
    inner_radius: str
    speed: str
    width: str
    angle: str
    cast_time: str
    effect_radius: str
    target_range: str


@dataclass
class Price(object):
    blue_essence: int
    rp: int


@dataclass
class Champion(object):
    id: int
    key: str
    name: str
    title: str
    full_name: str
    resource: Resource
    attack_type: AttackType
    adaptive_type: AdaptiveType
    stats: Stats
    roles: Set[Role]
    attribute_ratings: AttributeRatings
    abilities: Mapping[str, List[Ability]]
    release_date: str
    release_patch: str
    patch_last_changed: str
    price: Price
