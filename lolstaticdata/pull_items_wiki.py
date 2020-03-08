from typing import List, Optional, Tuple
from bs4 import BeautifulSoup
import re
from lolstaticdata.utils import download_soup
from collections import OrderedDict

from modelitem import Stats, Prices, Shop, Item, Passive, Active, ItemAttributes
from modelcommon import ArmorPenetration, DamageType, Health, HealthRegen, Mana, ManaRegen, Armor, MagicResistance, AttackDamage, AbilityPower, AttackSpeed, AttackRange, Movespeed, CriticalStrikeChance, Lethality, CooldownReduction, GoldPer10, HealAndShieldPower, Lifesteal, MagicPenetration


class WikiItem:
    @classmethod
    def _parse_passives(cls, item_data: dict) -> List[Passive]:
        effects = []
        not_unique = re.compile('[0-9]')
        if not_unique.search(item_data["cdrunique"]):
            cooldown = cls._parse_float(item_data['cdrunique'])
            description = "{}% cooldown reduction".format(cooldown)
            stats = cls._parse_passive_descriptions(description)
            effect = Passive(unique=True, name=None, effects=description, range=None, stats=stats)
            effects.append(effect)
        if not_unique.search(item_data['critunique']):
            crit = cls._parse_float(item_data['critunique'])
            description = "{}% critical strike chance".format(crit)
            stats = cls._parse_passive_descriptions(description)
            effect = Passive(unique=True, name=None, effects=description, range=None, stats=stats)
            effects.append(effect)

        # Parse both passives and auras the same way
        def _parse(passive: str) -> Passive:
            unique, passive_name, passive_effects, item_range = cls._parse_passive_info(passive)
            stats = cls._parse_passive_descriptions(passive_effects)
            effect = Passive(unique=unique, name=passive_name, effects=passive_effects, range=item_range, stats=stats)
            return effect

        # Passives
        for i in range(1, 6):
            passive = "pass" + str(i)
            if passive == "pass1":
                passive = "pass"
            passive = item_data[passive].strip()
            if passive:
                effect = _parse(passive)
                effects.append(effect)

        # Auras
        for i in range(1, 4):
            passive = "aura" + str(i)
            if passive == "aura1":
                passive = "aura"
            passive = item_data[passive].strip()
            if passive:
                effect = _parse(passive)
        return effects

    @classmethod
    def _parse_actives(cls, item_data: dict) -> List[Active]:
        get_cooldown = re.compile(r"(\d+ second cooldown)|(\d+ seconds cooldown)")
        effects = []
        passive = item_data["act"].strip()
        if passive:
            unique, passive_name, passive_effects, item_range = cls._parse_passive_info(passive)
            if get_cooldown.search(passive_effects):
                cooldown = get_cooldown.search(passive_effects).group(0).split(" ", 1)
                cooldown = cls._parse_float(cooldown[0])
            else:
                cooldown = None
            effect = Active(unique=unique, name=passive_name, effects=passive_effects, cooldown=cooldown, range=item_range)  # This is hacky...

            effects.append(effect)
        return effects

    @classmethod
    def _parse_passive_info(cls, passive: str) -> Tuple[bool, Optional[str], str, Optional[int]]:
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
            if ':' in " ".join(passive.split()[:4]):
                unique_split = passive.split(':')
                name = unique_split[0]
                passive = ':'.join(unique_split[1:])
            else:
                name = None
        else:
            # Return normal passive
            if ':' in " ".join(passive.split()[:4]):
                not_unique_split = passive.split(':')
                name = not_unique_split[0]
                passive = ':'.join(not_unique_split[1:])
            else:
                name = None

        passive = passive.strip()

        get_range = re.compile(r"\d+ range")
        if get_range.search(passive):
            item_range = get_range.search(passive).group(0).split(" ", 1)
            item_range = cls._parse_int(item_range[0])
        else:
            item_range = None
        return unique, name, passive, item_range

    @classmethod
    def _parse_passive_descriptions(cls, passive: str) -> Stats:
        # Regex stuff
        cdr = re.compile(r"\d.* cooldown reduction")
        crit = re.compile(r"\d.* critical strike chance")
        lethality = re.compile(r"\d.* lethality", re.IGNORECASE)
        movespeed = re.compile(r"\d+.*? flat movement speed$", re.IGNORECASE)  # movespeed needs fixing
        armorpen = re.compile(r"\d+.*? armor penetration\.\"")
        magicpen = re.compile(r"\d+.*? magic penetration")
        lifesteal = re.compile(r"\d+.*? life steal")
        ability_power = re.compile(r"\+\d+% ability power")

        if cdr.search(passive):
            cooldown = cdr.search(passive).group(0).split("%")[0]
            cooldown = cls._parse_float(cooldown)
        else:
            cooldown = 0.

        if movespeed.search(passive):
            movespeed = movespeed.search(passive).group(0).split("flat")[0]
            movespeed = cls._parse_float(movespeed)
        else:
            movespeed = 0.

        if crit.search(passive):
            crit = crit.search(passive).group(0).split("%")[0]
            crit = cls._parse_float(crit)
        else:
            crit = 0.

        if ability_power.search(passive):
            ap = ability_power.search(passive).group(0).split("%")[0]
            ap = cls._parse_float(ap)
        else:
            ap = 0.
        if lethality.search(passive):
            lethal = lethality.search(passive).group(0).split(" ")[0]
            lethal = cls._parse_float(lethal)
        else:
            lethal = 0.
        if armorpen.search(passive):
            armorpen = armorpen.search(passive).group(0).split("%")[0]
            armorpen = cls._parse_float(armorpen)
        else:
            armorpen = 0.

        if magicpen.search(passive):
            magicpen = magicpen.search(passive).group(0)
            if "%" in magicpen:
                magicpen = MagicPenetration(percent=magicpen.split("%")[0])
            else:
                magicpen = MagicPenetration(flat=magicpen.split(" ")[0])
        else:
            magicpen =  MagicPenetration(flat=0.)

        if lifesteal.search(passive):
            lifesteal = lifesteal.search(passive).group(0).split("%")[0]
            lifesteal = cls._parse_float(lifesteal)
        else:
            lifesteal = 0.
        stats = Stats(
            ability_power=AbilityPower(percent=ap),
            armor=Armor(flat=cls._parse_float(0.0)),
            armor_penetration=ArmorPenetration(percent=armorpen),
            attack_damage=AttackDamage(flat=cls._parse_float(0.0)),
            attack_speed=AttackSpeed(flat=cls._parse_float(0.0)),
            cooldown_reduction=CooldownReduction(percent=cooldown),
            critical_strike_chance=CriticalStrikeChance(percent=cls._parse_float(crit)),
            gold_per_10=GoldPer10(flat=cls._parse_float(0.0)),
            heal_and_shield_power=HealAndShieldPower(flat=cls._parse_float(0.0)),
            health=Health(flat=cls._parse_float(0.0)),
            health_regen=HealthRegen(flat=cls._parse_float(0.0)),
            lethality=Lethality(flat=lethal),
            lifesteal=Lifesteal(percent=lifesteal),
            magic_penetration=magicpen,
            magic_resistance=MagicResistance(flat=cls._parse_float(0.0)),
            mana=Mana(flat=cls._parse_float(0.0)),
            mana_regen=ManaRegen(flat=cls._parse_float(0.0)),
            movespeed=Movespeed(flat=cls._parse_float(movespeed))
            )
        return stats

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
        # After all that, let's just return the secondary tag and drop the primary tag.
        tags = [tag.split(':')[1] for tag in tags]
        return tags

    @classmethod
    def _parse_recipe_build(cls, item: str):
        item = item.replace(" ", "_")
        url = "https://leagueoflegends.fandom.com/wiki/Template:Item_data_" + item
        use_cache = False
        html = download_soup(url, use_cache)
        soup = BeautifulSoup(html, 'lxml')
        code = soup.findAll('td', {"data-name": "code"})
        return cls._parse_item_id(code=code[0].text)

    @classmethod
    def get(cls, url: str) -> Optional[Item]:
        # All item data has a html attribute "data-name" so I put them all in an ordered dict while stripping the new lines and spaces from the data
        use_cache = False
        html = download_soup(url, use_cache)
        soup = BeautifulSoup(html, 'lxml')
        item_data = OrderedDict()
        for td in soup.findAll('td', {"data-name": True}):
            attributes = td.find_previous("td").text.rstrip()
            attributes = attributes.lstrip()
            values = td.text.rstrip()
            # replace("\n", "")
            values = values.lstrip().rstrip()
            item_data[attributes] = values
        if cls._parse_item_id(item_data["code"]) is not None:
            item = cls._parse_item_data(item_data)
            return item
        else:
            raise ValueError(f"Item at url {url} has no id!")

    @classmethod
    def _parse_item_data(cls, item_data: dict) -> Item:
        not_unique = re.compile('[A-z]')
        builds_into = []
        builds_from = []
        nicknames = []
        try:
            tier = eval(item_data["tier"].replace("Tier ", ""))
        except SyntaxError:
            tier = None
        except NameError:
            tier = item_data["tier"]
        # Create the json files from the classes in modelitem.py
        if item_data["removed"] == "true":
            removed = True
        else:
            removed = False
        if not_unique.match(item_data["noe"]):
            no_effects = True
        else:
            no_effects = False

        if not_unique.search(item_data["nickname"]):
            nickname = item_data["nickname"]
            if "," in nickname:
                for i in nickname.split(","):
                    nicknames.append(i.strip())
            else:
                nicknames.append(nickname.strip())

        if not_unique.search(item_data["builds"]):
            build = item_data["builds"]
            if "," in build:
                for i in build.split(","):
                    i = cls._parse_recipe_build(i.strip())
                    if i is not None:
                        builds_into.append(i)
                    else:
                        continue
            else:
                build = cls._parse_recipe_build(build.strip())
                builds_into.append(build)

        if not_unique.match(item_data["recipe"]):
            component = item_data["recipe"]
            if "," in component:
                for i in component.split(","):
                    i = cls._parse_recipe_build(i.strip())
                    if i is not None:
                        builds_from.append(i)
                    else:
                        continue
            else:
                component = cls._parse_recipe_build(component.strip())
                builds_from.append(component)
        item = Item(
            name=item_data["1"],
            id=cls._parse_item_id(code=item_data["code"].strip()),
            tier=tier,
            builds_from=builds_from,
            builds_into=builds_into,
            no_effects=no_effects,
            removed=removed,
            nicknames=nicknames,
            icon="",
            passives=cls._parse_passives(item_data),
            active=cls._parse_actives(item_data),
            stats=Stats(
                ability_power=AbilityPower(flat=cls._parse_float(item_data["ap"])),
                armor=Armor(flat=cls._parse_float(item_data['armor'])),
                armor_penetration=ArmorPenetration(flat=cls._parse_float(item_data['rpen'])),
                attack_damage=AttackDamage(flat=cls._parse_float(item_data['ad'])),
                attack_speed=AttackSpeed(flat=cls._parse_float(item_data['as'])),
                cooldown_reduction=CooldownReduction(percent=cls._parse_float(item_data['cdr'])),
                critical_strike_chance=CriticalStrikeChance(percent=cls._parse_float(item_data['crit'])),
                gold_per_10=GoldPer10(flat=cls._parse_float(item_data["gp10"])),
                heal_and_shield_power=HealAndShieldPower(flat=cls._parse_float(item_data["hsp"])),
                health=Health(flat=cls._parse_float(item_data["health"])),
                health_regen=HealthRegen(
                    flat=cls._parse_float(item_data["hp5flat"]),
                    percent=cls._parse_float(item_data["hp5"]),
                ),
                lethality=Lethality(flat=0.0),
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
                    percent=cls._parse_float(item_data["ms"]) + cls._parse_float(item_data["msunique"])
                ),
            ),
            shop=Shop(
                prices=Prices(
                    total=cls._parse_int(item_data["buy"]),
                    combined=cls._parse_int(item_data["comb"]),
                    sell=cls._parse_int(item_data["sell"]),
                ),
                tags=cls.get_item_attributes(item_data)
            )
        )
        return item


def get_item_urls(use_cache: bool) -> List[str]:
    all_urls = []
    url = 'https://leagueoflegends.fandom.com/wiki/Category:Item_data_templates?from=A'
    while True:
        html = download_soup(url, use_cache)
        soup = BeautifulSoup(html, 'lxml')
        urls = soup.find_all("a", {"class": "category-page__member-link"})
        all_urls.extend(urls)
        next_button = soup.find("a", {"class": "category-page__pagination-next wds-button wds-is-secondary"})
        if not next_button:
            break
        url = next_button['href']

    base_url = 'https://leagueoflegends.fandom.com'
    all_urls = [base_url + url['href'] for url in all_urls]
    return all_urls
