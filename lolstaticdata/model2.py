from dataclasses import dataclass, asdict
import dataclasses_json


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
    spec: str
    spec2: str
    passive1 : str
    passive2 : str
    passive3 : str
    passive4 : str
    passive5 : str
    active: str
    aura: str
    aura2: str
    aura3: str
    no_effects : bool


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Menu(object):
    menu1a: str
    menu1b: str
    menu2a: str
    menu2b: str
    menu3a: str
    menu3b: str
    menu4a: str
    menu4b: str
    menu5a: str
    menu5b: str
    menu6a: str
    menu6b: str
    menu7a: str
    menu7b: str

@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Shop(object):
    priceFull : int
    priceCombined : int
    priceSell : int
    menu : Menu



@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Other(object):
    consume: str
    consume2: str
    champion_item : str
    limit : str
    req: str
    hp : int
    removed : bool
    nickname : str


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Item(object):
    Name: str
    itemID : int
    tier: str
    type: str
    recipe : str
    stats: Stat
    shop: Shop
    other : Other




    def __json__(self):
        return self.to_json()


