from typing import Set, Mapping, List, Union, Type
from dataclasses import dataclass, asdict
import dataclasses_json
from enum import Enum




def to_enum_like(string: str) -> str:
    return string.upper().replace(' ', '_')


@classmethod
def from_string(cls: Type[Enum], string: str) -> Enum:
    string = to_enum_like(string)
    for e in cls:
        if e.name == string:
            return e
    raise ValueError(f"Unknown {cls.__name__} type: {string}")
Enum.from_string = from_string


class itemAttributes(Enum):
    STARTER_ITEMS = "STARTER ITEMS"
    TOOLS = "TOOLS"
    DEFENSE = "DEFENSE"
    ATTACK = "ATTACK"
    MAGIC = "MAGIC"
    MOVEMENT = "MOVEMENT"
    JUNGLING = "JUNGLING"
    LANING = "LANING"
    ARMOR_PENETRATION = "ARMOR PENETRATION"
    MAGIC_PENETRATION = "MAGIC PENETRATION"
    CONSUMABLE = "CONSUMABLE"
    GOLD_INCOME = "GOLD INCOME"
    VISION_AND_TRINKETS = "VISION AND TRINKETS"
    ARMOR = "ARMOR"
    HEALTH = "HEALTH"
    HEALTH_REGEN = "HEALTH REGEN"
    MAGIC_RESISTANCE = "MAGIC RESISTANCE"
    MAGIC_RESIST = "MAGIC RESIST"
    ATTACK_SPEED = "ATTACK SPEED"
    CRITICAL_STRIKE = "CRITICAL STRIKE"
    DAMAGE = "ATTACK DAMAGE"
    LIFE_STEAL = "LIFE STEAL"
    COOLDOWN_REDUCTION = "COOLDOWN REDUCTION"
    MANA = "MANA"
    MANA_REGEN= "MANA REGEN"
    ABILITY_POWER = "ABILITY POWER"
    BOOTS = "BOOTS"
    OTHER_MOVEMENT_ITEMS = "OTHER MOVEMENT ITEMS"

@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Stat(object):
    abilityPower: int
    armor: int
    armorPenetration: int
    attackDamage: int
    attackSpeed : int
    cdr: int
    cdrUnique: int
    crit: int
    critUnique: int
    goldPer10: int
    healShield: int
    health: int
    healthRegen: int
    healthRegenFlat: int
    lifesteal: int
    magicPenetration: int
    magicResist: int
    mana: int
    manaRegenPer5: int
    manaRegenPer5Flat: int
    moveSpeed: int
    moveSpeedUnique: int
    moveSpeedFlat: int


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Shop(object):
    priceFull : int
    priceCombined : int
    priceSell : int
    itemTags : List[str]


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Passive(object):
    unique : bool
    name : str
    effects : str
    range : int

@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Item(object):
    Name: str
    itemID : int
    tier: str
    type: str
    recipe : List[str]
    builds : List[str]
    no_effects: bool
    removed : bool
    nickname : str
    passives : List[Passive]
    auras : List[Passive]
    active : List[Passive]
    stats: Stat
    shop: Shop




    def __json__(self):
        return self.to_json()


