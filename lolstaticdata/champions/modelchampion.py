from typing import Mapping, List, Union
from dataclasses import dataclass
import dataclasses_json
import json

from ..common.modelcommon import (
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
    Lethality,
    CooldownReduction,
    GoldPer10,
    HealAndShieldPower,
    Lifesteal,
    MagicPenetration,
    Stat,
)
from ..common.utils import OrderedEnum, ExtendedEncoder


class Resource(OrderedEnum):
    NO_COST = "NO_COST"
    BLOODTHIRST = "BLOODTHIRST"
    MANA = "MANA"
    ENERGY = "ENERGY"
    RAGE = "RAGE"
    FURY = "FURY"
    FEROCITY = "FEROCITY"
    HEALTH = "HEALTH"
    MAXIMUM_HEALTH = "MAXIMUM_HEALTH"
    CURRENT_HEALTH = "CURRENT_HEALTH"
    HEALTH_PER_SECOND = "HEALTH_PER_SECOND"
    MANA_PER_SECOND = "MANA_PER_SECOND"
    CHARGE = "CHARGE"
    COURAGE = "COURAGE"
    HEAT = "HEAT"
    GRIT = "GRIT"
    FLOW = "FLOW"
    SHIELD = "SHIELD"
    OTHER = "OTHER"
    NONE = "NONE"
    SOUL_UNBOUND = "SOUL_UNBOUND"
    BLOOD_WELL = "BLOOD_WELL"


class AttackType(OrderedEnum):
    MELEE = "MELEE"
    RANGED = "RANGED"


class Role(OrderedEnum):
    TANK = "TANK"
    FIGHTER = "FIGHTER"
    MAGE = "MAGE"
    MARKSMAN = "MARKSMAN"
    SUPPORT = "SUPPORT"
    WARDEN = "WARDEN"
    VANGUARD = "VANGUARD"
    JUGGERNAUT = "JUGGERNAUT"
    CONTROLLER = "CONTROLLER"
    SKIRMISHER = "SKIRMISHER"
    DIVER = "DIVER"
    SLAYER = "SLAYER"
    BURST = "BURST"
    BATTLEMAGE = "BATTLEMAGE"
    ENCHANTER = "ENCHANTER"
    CATCHER = "CATCHER"
    ASSASSIN = "ASSASSIN"
    SPECIALIST = "SPECIALIST"
    ARTILLERY = "ARTILLERY"


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Stats(object):
    health: Health
    health_regen: HealthRegen
    mana: Mana
    mana_regen: ManaRegen
    armor: Armor
    magic_resistance: MagicResistance
    attack_damage: AttackDamage
    movespeed: Movespeed
    acquisition_radius: Stat
    selection_radius: Stat
    pathing_radius: Stat
    gameplay_radius: Stat
    critical_strike_damage: Stat
    critical_strike_damage_modifier: Stat
    attack_speed: AttackSpeed
    attack_speed_ratio: Stat
    attack_cast_time: Stat
    attack_total_time: Stat
    attack_delay_offset: Stat
    attack_range: AttackRange
    aram_damage_taken: Stat
    aram_damage_dealt: Stat
    aram_healing: Stat
    aram_shielding: Stat
    urf_damage_taken: Stat
    urf_damage_dealt: Stat
    urf_healing: Stat
    urf_shielding: Stat


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class AttributeRatings(object):
    damage: int
    toughness: int
    control: int
    mobility: int
    utility: int
    ability_reliance: int
    difficulty: int


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Modifier(object):
    values: List[Union[int, float]]
    units: List[str]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Cooldown(object):
    modifiers: List[Modifier]
    affected_by_cdr: bool


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Cost(object):
    modifiers: List[Modifier]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Leveling(object):
    attribute: str
    modifiers: List[Modifier]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Effect(object):
    description: str
    leveling: List[Leveling]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Ability(object):
    name: str
    icon: str
    effects: List[Effect]
    cost: Cost
    cooldown: Cooldown
    targeting: str
    affects: str
    spellshieldable: str
    resource: Resource
    damage_type: DamageType
    spell_effects: str
    projectile: str
    on_hit_effects: str
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


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Price(object):
    blue_essence: int
    rp: int
    sale_rp: int


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Description(object):
    description: str
    region: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Rarities(object):
    rarity: int
    region: str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Chroma(object):
    name: str
    id: id
    chroma_path: str
    colors: list
    descriptions: List[Description]
    rarities: List[Rarities]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Skin(object):
    name: str
    id: int
    is_base: bool
    availability: str
    format_name: str
    loot_eligible: bool
    cost: str
    sale: int
    distribution: str
    rarity: str
    chromas: List[Chroma]
    lore: str
    release: float
    set: list
    splash_path: str
    uncentered_splash_path: str
    tile_path: str
    load_screen_path: str
    load_screen_vintage_path: str
    new_effects: bool
    new_animations: bool
    new_recall: bool
    new_voice: bool
    new_quotes: bool
    voice_actor: list
    splash_artist: list


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Champion(object):
    id: int
    key: str
    name: str
    title: str
    full_name: str
    icon: str
    resource: Resource
    attack_type: AttackType
    adaptive_type: DamageType
    stats: Stats
    roles: List[Role]
    attribute_ratings: AttributeRatings
    abilities: Mapping[str, List[Ability]]
    release_date: str
    release_patch: str
    patch_last_changed: str
    price: Price
    lore: str
    faction: str
    skins: List[Skin]

    def __json__(self, *args, **kwargs):
        # Use dataclasses_json to get the dict
        d = self.to_dict()
        # Delete the two stat objects that don't apply to champions
        for name, stat in d["stats"].items():
            if isinstance(stat, dict):
                del stat["percentBase"]
                del stat["percentBonus"]
        # Return the (un)modified dict
        return json.dumps(d, cls=ExtendedEncoder, *args, **kwargs)
