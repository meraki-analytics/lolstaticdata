from typing import List, Optional
import bs4
from bs4 import BeautifulSoup
import os
import json
import re
from lolstaticdata.util import download_webpage
from collections import OrderedDict

from modelitem import Stats, Shop, Item, Passive, Active, Aura, ItemAttributes
from modelcommon import DamageType, Health, HealthRegen, Mana, ManaRegen, Armor, MagicResistance, AttackDamage, AbilityPower, AttackSpeed, AttackRange, Movespeed, CriticalStrikeChance, Lethality, CooldownReduction, GoldPer10, HealAndShieldPower, Lifesteal, MagicPenetration


class ItemParser:
    @classmethod
    def parse_passives(cls, item_data: dict) -> List[Passive]:
        print("PASSIVES")
        effects = []
        for i in range(1, 6):
            passive = "pass" + str(i)
            if passive == "pass1":
                passive = "pass"
            passive = item_data[passive].strip()
            if passive:
                effect = cls._parse_passive(passive)
                effects.append(effect)
        return effects

    @classmethod
    def parse_auras(cls, item_data: dict) -> List[Aura]:
        print("AURAS")
        effects = []
        for i in range(1, 4):
            passive = "aura" + str(i)
            if passive == "aura1":
                passive = "aura"
            passive = item_data[passive].strip()
            if passive:
                effect = cls._parse_passive(passive)
                effect = Aura(unique=effect.unique, name=effect.name, effects=effect.effects)  # This is hacky...
                effects.append(effect)
        return effects

    @classmethod
    def parse_actives(cls, item_data: dict) -> List[Active]:
        print("ACTIVES")
        effects = []
        passive = item_data["act"].strip()
        if passive:
            effect = cls._parse_passive(passive)
            effect = Active(unique=effect.unique, name=effect.name, effects=effect.effects)  # This is hacky...
            effects.append(effect)
        return effects

    @staticmethod
    def _parse_passive(passive: str) -> Passive:
        print(f"Parsing passive: {passive}")
        if passive.startswith("Unique"):
            unique = True
            passive = passive[len("Unique"):].strip()
            if passive.startswith(":"):
                passive = passive[1:].strip()
        else:
            unique = False
        while "  " in passive:
            passive = passive.replace("  ", " ")
        if unique:
            # I changed util to detect unique items regardless of name or not
            # Before it had "Unique \u2013 passive name :"
            if ':' in passive:
                unique_split = passive.split(':')
                name = unique_split[0]
                passive = ':'.join(unique_split[1:])
            else:
                name = None
            effect = Passive(
                unique=unique,
                name=name,
                effects=passive.strip()
            )
        else:
            # return normal passive
            if ':' in passive:
                not_unique_split = passive.split(':')
                name = not_unique_split[0]
                passive = ':'.join(not_unique_split[1:])
            else:
                name = None
            effect = Passive(
                unique=unique,
                name=name,
                effects=passive.strip()
            )
        print(effect)
        return effect

    @staticmethod
    def _parse_float(number: str, backup: float = 0.) -> float:
        try:
            stat = float(number)
            return stat
        except ValueError:
            return backup

    @staticmethod
    def _parse_int(number: str, backup: int = 0) -> int:
        try:
            stat = int(number)
            return stat
        except ValueError:
            return backup

    @staticmethod
    def _parse_item_id(code: str) -> Optional[int]:
        try:
            if code in ("N/A", ""):
                return None
            else:
                stat = int(code)
                return stat
        except ValueError:
            print(f"WARNING! Could not parse item with id {code}")
            return None

    @staticmethod
    def get_item_attributes(item_data: dict) -> List[str]:
        # Gets all item attributes from the item tags
        # This is a mess. The wiki has tons of miss named tags, this is to get them
        tags = []
        for i in range(1, 8):
            menu = "menu" + str(i)
            menua = menu+"a"
            menub = menu+"b"
            if item_data[menua]:
                primary_tag = item_data[menua]
                secondary_tag = item_data[menub]
                if item_data[menua] in ('Offense', 'Attack'):
                    primary_tag = "Attack"
                elif item_data[menua] in ('Starter Items', 'Starting Items'):
                    primary_tag = "Starter Items"

                elif item_data[menua] in ('Movement', 'Movement Speed', 'Other'):
                    primary_tag = "Movement"

                else:
                    primary_tag = ItemAttributes.from_string(primary_tag)

                if item_data[menub]:
                    if item_data[menub] in ('Health Regeneration', "Health Regen", "Health Renegeration"):
                        secondary_tag = "Health Regen"

                    elif item_data[menub] in ("Magic Resist", "Magic Resistance"):
                        secondary_tag = "Magic Resist"

                    elif item_data[menub] in ("Mana Regen", "Mana Regeneration"):
                        secondary_tag = "Mana Regen"

                    elif item_data[menub] in ("Jungling", "Jungle"):
                        secondary_tag = "Jungling"

                    elif item_data[menub] in ("Other Movement Items", "Other Movement", "Others", "Other Items", "Movement Speed"):
                        secondary_tag = "Other Movement Items"

                    elif item_data[menub] in ('Attack Damage', 'Damage', ' Damage'):
                        secondary_tag = "Damage"

                    elif item_data[menub] in ('Laning', 'Lane'):
                        secondary_tag = "Laning"

                    elif item_data[menub] in ('Lifesteal', 'Life steal'):
                        secondary_tag = "Life Steal"

                    elif secondary_tag in ('Vision andamp;Trinkets', 'VISION AND TRINKETS', 'Vision and&; Trinkets', 'Vision & Trinkets', 'Vision'):
                        secondary_tag = "Vision and Trinkets"

                    if ';' in item_data[menub]:
                        secondary_tag = item_data[menub].replace("; ", ";")
                        # I don't think this is needed (the vision stuff)
                        if secondary_tag in ('Vision andamp;Trinkets', 'VISION AND TRINKETS', 'Vision and&; Trinkets', 'Vision & Trinkets', 'Vision'):
                            secondary_tag = "Vision and Trinkets"
                            tag = primary_tag.name + ':' + secondary_tag.upper()
                        else:
                            secondary_tag = secondary_tag.split(";")
                            secondary_tag1 = ItemAttributes.from_string(secondary_tag[0])
                            secondary_tag2 = ItemAttributes.from_string(secondary_tag[1])
                            secondary_tag = secondary_tag1.name + "," + secondary_tag2.name
                            tag = primary_tag.name + ":" + secondary_tag.upper()
                    else:
                        secondary_tag = ItemAttributes.from_string(secondary_tag)
                        try:
                            # there was an error with a couple primary tags not having the right tags so this fixes it
                            tag = primary_tag.name + ":" + secondary_tag.name
                        except AttributeError:
                            tag = primary_tag.upper() + ':' + secondary_tag.name
                    tags.append(tag)
                else:
                    # Titanic Hydra decided to mess everything up so I needed to put something to allow a Primary tag without a secondary tag
                    tag = primary_tag.upper() + ":None"
                    tags.append(tag)
        return tags

    @classmethod
    def download(cls, url: str):
        # All item data has a html attribute "data-name" so I put them all in an ordered dict while stripping the new lines and spaces from the data
        use_cache = False
        html = download_webpage(url, use_cache)
        soup = BeautifulSoup(html, 'lxml')
        item_data = OrderedDict()
        for td in soup.findAll('td', {"data-name": True}):
            attributes = td.find_previous("td").text.rstrip()
            attributes = attributes.lstrip()
            values = td.text.rstrip()
            # replace("\n", "")
            values = values.lstrip().rstrip()
            item_data[attributes] = values
        item = cls._parse_item_data(item_data)
        return item

    @classmethod
    def _parse_item_data(cls, item_data: dict) -> Item:
        not_unique = re.compile('[A-z]')
        builds_into = []
        builds_from = []
        # Create the json files from the classes in modelitem.py
        if item_data["removed"] == "true":
            removed = True
        else:
            removed = False
        if not_unique.match(item_data["noe"]):
            no_effects = True
        else:
            no_effects = False
        if not_unique.search(item_data["builds"]):
            build = item_data["builds"]
            if "," in build:
                for i in build.split(","):
                    builds_into.append(i.strip())
            else:
                builds_into.append(build.strip())

        if not_unique.match(item_data["recipe"]):
            component = item_data["recipe"]
            if "," in component:
                for i in component.split(","):
                    builds_from.append(i.strip())
            else:
                builds_from.append(component.strip())

        item = Item(
            name=item_data["1"],
            id=cls._parse_item_id(code=item_data["code"].strip()),
            tier=item_data["tier"],
            builds_from=builds_from,
            builds_into=builds_into,
            no_effects=no_effects,
            removed=removed,
            nickname=item_data["nickname"],
            passives=cls.parse_passives(item_data),
            auras=cls.parse_auras(item_data),
            active=cls.parse_actives(item_data),
            stats=Stats(
                ability_power=AbilityPower(flat=cls._parse_float(item_data["ap"])),
                armor=Armor(flat=cls._parse_float(item_data['armor'])),
                armor_penetration=cls._parse_float(item_data['rpen']),
                attack_damage=AttackDamage(flat=cls._parse_float(item_data['ad'])),
                attack_speed=AttackSpeed(flat=cls._parse_float(item_data['as'])),
                cooldown_reduction=CooldownReduction(
                    flat=cls._parse_float(item_data['cdr']),
                    unique=cls._parse_float(item_data['cdrunique']),
                ),
                critical_strike_chance=CriticalStrikeChance(
                    percent=cls._parse_float(item_data['crit']),
                    unique_percent=cls._parse_float(item_data['critunique']),
                ),
                gold_per_10=GoldPer10(flat=cls._parse_float(item_data["gp10"])),
                heal_and_shield_power=HealAndShieldPower(flat=cls._parse_float(item_data["hsp"])),
                health=Health(flat=cls._parse_float(item_data["health"])),
                health_regen=HealthRegen(
                    flat=cls._parse_float(item_data["hp5flat"]),
                    percent=cls._parse_float(item_data["hp5"]),
                ),
                lifesteal=Lifesteal(percent=cls._parse_float(item_data["lifesteal"])),
                magic_penetration=MagicPenetration(flat=cls._parse_float(item_data["mpen"])),
                magic_resistance=MagicResistance(flat=cls._parse_float(item_data["mr"])),
                mana=Mana(flat=cls._parse_float(item_data["mana"])),
                mana_regen=ManaRegen(
                    flat=cls._parse_float(item_data["mp5flat"]),
                    percent=cls._parse_float(item_data["mp5"]),
                ),
                movespeed=Movespeed(
                    flat=cls._parse_float(item_data["msflat"]),
                    percent=cls._parse_float(item_data["ms"]),
                    unique_percent=cls._parse_float(item_data["msunique"]),
                ),
            ),
            shop=Shop(
                price_total=cls._parse_int(item_data["buy"]),
                price_combined=cls._parse_int(item_data["comb"]),
                price_sell=cls._parse_int(item_data["sell"]),
                tags=cls.get_item_attributes(item_data)
            )
        )
        return item


def get_item_urls(use_cache: bool) -> List[str]:
    all_urls = []
    url = 'https://leagueoflegends.fandom.com/wiki/Category:Item_data_templates?from=A'
    while True:
        html = download_webpage(url, use_cache)
        soup = BeautifulSoup(html, 'lxml')
        urls = soup.find_all("a", href=re.compile("/wiki/Template:Item_data_"))
        all_urls.extend(urls)
        next_button = soup.find("a", {"class": "category-page__pagination-next wds-button wds-is-secondary"})
        if not next_button:
            break
        url = next_button['href']

    base_url = 'https://leagueoflegends.fandom.com'
    all_urls = [base_url + url['href'] for url in all_urls]
    return all_urls


def main():
    directory = os.path.dirname(os.path.realpath(__file__)) + "/"
    use_cache = False

    item_urls = get_item_urls(use_cache)
    jsons = {}
    for url in item_urls:
        print(url)
        item = ItemParser.download(url)
        jsonfn = directory + f"/../items/{item.name.replace(' ', '_')}.json"
        with open(jsonfn, 'w') as f:
            f.write(item.to_json(indent=2))
        jsons[item.name] = json.loads(item.to_json())

    jsonfn = directory + "/../items.json"
    with open(jsonfn, 'w') as f:
        json.dump(jsons, f, indent=2)
    del jsons


if __name__ == "__main__":
    main()
