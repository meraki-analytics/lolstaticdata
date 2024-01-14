from typing import List, Optional, Tuple
from bs4 import BeautifulSoup
import re
from collections import OrderedDict
from slpp import slpp as lua

from .modelitem import (
    Stats,
    Prices,
    Shop,
    Item,
    Passive,
    Active,
    ItemAttributes,
    ItemRanks,
)
from ..common.utils import download_soup
from ..common.modelcommon import (
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
    OmniVamp,
    AbilityHaste,
    Tenacity,
)


class WikiItem:
    @classmethod
    def _parse_passives(cls, item_data: dict) -> List[Passive]:
        effects = []
        not_unique = re.compile("[0-9]")


        # Parse both passives and auras the same way
        def _parse(passive: dict,) -> Passive:
            (
                unique,
                mythic,
                passive_name,
                passive_effects,
                item_range,
				cd,
            ) = cls._parse_passive_info(passive)
            stats = cls._parse_passive_descriptions(passive_effects)
            effect = Passive(
                unique=unique,
                name=passive_name,
                effects=passive_effects,
                range=item_range,
                stats=stats,
                mythic=mythic,
				cooldown=cd,
            )
            return effect

        # Passives
        if "effects" in item_data:
            for x in item_data["effects"]:
                if "pass" in x:
                    passive = item_data["effects"][x]
                    effect = _parse(passive)
                    effects.append(effect)
                if "aura" in x:
                    effect = _parse(item_data["effects"][x])
                    effects.append((effect))
                if "mythic" in x:
                    stats = cls.get_stats(item_data["effects"][x])
                    effect = Passive(
                unique=True,
                name="Mythic",
                effects=None,
                range=0,
                cooldown=0,
                stats=stats,
                mythic=True,
            )
                    effects.append((effect))
        return effects

    @classmethod
    def _parse_actives(cls, item_data: dict) -> List[Active]:
        get_cooldown = re.compile(r"(\d+ second cooldown)|(\d+ seconds cooldown)")
        effects = []
        passive = None
        if "effects" in item_data:
            for x in item_data["effects"]:
                if x in "act":
                    passive = item_data["effects"][x]

        if passive:
            (
                unique,
                mythic,
                passive_name,
                passive_effects,
                item_range,
                cd,
            ) = cls._parse_passive_info(passive)
            if get_cooldown.search(passive_effects):
                cooldown = get_cooldown.search(passive_effects).group(0).split(" ", 1)
                cooldown = cls._parse_float(cooldown[0])
            else:
                cooldown = None
            effect = Active(
                unique=unique,
                name=passive_name,
                effects=passive_effects,
                cooldown=cooldown,
                range=item_range,
            )  # This is hacky...

            effects.append(effect)
        return effects

    @classmethod
    def _parse_passive_info(cls, passive: dict) -> Tuple[bool, bool, Optional[str], str, Optional[int], Optional[str]]:
        if "unique" in passive:
            unique = True
            mythic = False
        else:
            unique = False
            mythic = False
        if "name" in passive:
            name = passive["name"]
        else:
            name = None
        if "cd" in passive:
            cd = passive["cd"]
        else:
            cd = None
        # elif passive.startswith("Mythic"):
        #     mythic = True
        #     unique = True
        #     passive = passive[len("Unique") :].strip()
        #     if passive.startswith(":"):
        #         passive = passive[1:].strip()
        passive = passive

        if "radius" in passive:
            item_range = cls._parse_int(passive["radius"])
        elif "range" in passive:
            item_range = cls._parse_int(passive["range"])
        else:
            item_range = None
        return unique, mythic, name, passive["description"], item_range, cd

    @classmethod
    def _parse_passive_descriptions(cls, passive: str) -> Stats:
        # Regex stuff
        cdr = re.compile(r"\d.* cooldown reduction")
        crit = re.compile(r"\d.* critical strike chance")
        lethality = re.compile(r"(?:lethality|Lethality)\|(\d*)", re.IGNORECASE)
        movespeed = re.compile(r"(\d+)(?: '*bonus'* |% | |% '*bonus'* )movement speed", re.IGNORECASE) 
        armorpen = re.compile(r"(\d+)% armor penetration")
        magicpen = re.compile(r"(\d+).*? magic penetration")
        lifesteal = re.compile(r"\d+.*? life steal")
        omnivamp = re.compile(r"\d+.*? omni ?vamp")
        # ability_power = re.compile(r"\+\d+% ability power")
        ability_power = re.compile(r"(\d+)(?: |% |% bonus )ability power")
        ability_power_percent = re.compile(r"(?:ability power by )(\d+)%")
        ability_haste = re.compile(r"(\d+) ability haste")
        attack_speed = re.compile(r"(\d+)(?:% bonus) attack speed")
        health_re = re.compile(r"(\d+) (bonus health|health)")
        bonus_ad = re.compile(r"(\d+) bonus attack damage")
        # onHit = re.compile(r"basic attack (?:.*?)(?: (?:as|in))?\d+ (?:bonus|seconds |deals).*? (\d+.*) (?:bonus|seconds|deals) (?:magic|physical)")
        # test = re.compile(r"basic attack (?:.*?)(?: (?:as|in))?(\d+) (?:bonus|deals).*?")#taken from https://github.com/TheKevJames/league/blob/a62f5e3697392094aedd3d0bd1df37012824963b/league_utils/models/item/stats.py
        health = Health(flat=cls._parse_float(0.0))
        ad = AttackDamage(flat=cls._parse_float(0.0))
        tenacity_re = re.compile(r"(\d+)% TENACITY")
        # print(passive)
        if "Empowers each of your other Legendary items" in passive:
            if health_re.search(passive):
                print(passive)
                health = Health(flat=float(health_re.search(passive).groups()[0]))
            else:
                health = Health(flat=cls._parse_float(0.0))

            if bonus_ad.search(passive):
                ad = AttackDamage(flat=cls._parse_float(bonus_ad.search(passive).groups()[0]))
        if tenacity_re.search(passive.upper()):
            tenacity = Tenacity(percent=cls._parse_float(tenacity_re.search(passive.upper()).groups()[0]))
        else:
            tenacity = Tenacity(percent=cls._parse_float(0.0))
        if cdr.search(passive):
            cooldown = cdr.search(passive).group(0).split("%")[0]
            cooldown = cls._parse_float(cooldown)
        else:
            cooldown = 0.0

        if movespeed.search(passive):
            mvspeed = movespeed.search(passive).group(0)
            if "%" in mvspeed:
                movespeed = Movespeed(percent=float(movespeed.search(passive).groups()[0]))
            else:
                movespeed = Movespeed(flat=float(movespeed.search(passive).groups()[0]))
        else:
            movespeed = Movespeed(flat=cls._parse_float(0.0))
        if crit.search(passive):
            crit = crit.search(passive).group(0).split("%")[0]
            crit = cls._parse_float(crit)
        else:
            crit = 0.0

        if ability_power.search(passive):
            # ap = ability_power.search(passive).group(0).split("%")[0]
            ap = ability_power.search(passive).groups()[0]
            ap = cls._parse_float(ap)
        else:
            ap = 0.0

        if ability_power_percent.search(passive):
            ap_percent = ability_power_percent.search(passive).groups()[0]
            ap_percent = cls._parse_float(ap_percent)
        else:
            ap_percent = 0.0

        if ability_haste.search(passive):
            ah = ability_haste.search(passive).groups()[0]
            ah = cls._parse_float(ah)
        else:
            ah = 0.0

        if lethality.search(passive):
            lethal = lethality.search(passive).groups()[0]
            lethal = cls._parse_float(lethal)
        else:
            lethal = 0.0

        if armorpen.search(passive):
            armorpen = armorpen.search(passive).groups()[0]
            armorpen = cls._parse_float(armorpen)
        else:
            armorpen = 0.0

        if attack_speed.search(passive):
            attack_speed = cls._parse_float(attack_speed.search(passive).groups()[0])
        else:
            attack_speed = cls._parse_float(0.0)

        if magicpen.search(passive):
            magpen = magicpen.search(passive).group(0)
            if "%" in magpen:
                magicpen = MagicPenetration(percent=float(magicpen.search(passive).groups()[0]))
            else:
                magicpen = MagicPenetration(flat=float(magicpen.search(passive).groups()[0]))
        else:
            magicpen = MagicPenetration(flat=0.0)

        if lifesteal.search(passive):
            lifesteal = lifesteal.search(passive).group(0).split("%")[0]
            lifesteal = cls._parse_float(lifesteal)
        else:
            lifesteal = 0.0

        if omnivamp.search(passive):
            omniv = omnivamp.search(passive).group(0).split("%")[0]
            omniv = cls._parse_float(omniv)
        else:
            omniv = 0.0
        stats = Stats(
            ability_power=AbilityPower(flat=ap, percent=ap_percent),
            armor=Armor(flat=cls._parse_float(0.0)),
            armor_penetration=ArmorPenetration(percent=armorpen),
            attack_damage=ad,
            attack_speed=AttackSpeed(percent=attack_speed),
            cooldown_reduction=CooldownReduction(percent=cooldown),
            critical_strike_chance=CriticalStrikeChance(percent=cls._parse_float(crit)),
            gold_per_10=GoldPer10(flat=cls._parse_float(0.0)),
            heal_and_shield_power=HealAndShieldPower(flat=cls._parse_float(0.0)),
            health=health,
            health_regen=HealthRegen(flat=cls._parse_float(0.0)),
            lethality=Lethality(flat=lethal),
            lifesteal=Lifesteal(percent=lifesteal),
            magic_penetration=magicpen,
            magic_resistance=MagicResistance(flat=cls._parse_float(0.0)),
            mana=Mana(flat=cls._parse_float(0.0)),
            mana_regen=ManaRegen(flat=cls._parse_float(0.0)),
            movespeed=movespeed,
            omnivamp=OmniVamp(percent=omniv),
            ability_haste=AbilityHaste(flat=ah),
            tenacity=tenacity
        )
        return stats

    @staticmethod
    def _parse_float(number: str, backup: float = 0.0) -> float:
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
        if "menu" in item_data:

            for tag in item_data["menu"]:
                tags.append(ItemAttributes.from_string(tag))
        # After all that, let's just return the secondary tag and drop the primary tag.
        return tags

    @classmethod
    def _parse_recipe_build(cls, item: str):
        item = item.replace(" ", "_")

        if item in "Hextech_Alternator_Hextech_Alternator":
            item = "Hextech_Alternator"
        elif item in "Blasting_Wand_Blasting_Wand":
            item = "Blasting_Wand"
        elif item in "Ruby_Crystal_Ruby_Crystal":
            item = "Ruby_Crystal"

        url = "https://leagueoflegends.fandom.com/wiki/Template:Item_data_" + item
        use_cache = True
        html = download_soup(url, use_cache, dir="__wiki__")
        soup = BeautifulSoup(html, "lxml")
        code = soup.findAll("td", {"data-name": "code"})
        return cls._parse_item_id(code=code[0].text)

    @classmethod
    def get_stats(cls,item_data):
        hp = 0.0
        mr = 0.0
        ah = 0.0
        armor = 0.0
        ap = 0.0
        mana = 0.0
        hsp = 0.0
        mp5 = 0.0
        tenacity = Tenacity(cls._parse_float(0.0))
        ad = 0.0
        mpenflat = 0.0
        hspunique = 0.0
        hp5flat = 0.0
        armpen = 0.0
        omnivamp = 0.0
        lethality = 0.0
        ms = 0.0
        hp5 = 0.0
        spec = 0.0
        crit = 0.0
        mpen = 0.0
        lifesteal = 0.0
        gp10 = 0.0
        msflat = 0.0
        attack_speed = 0.0
        if type(item_data) == str:
            print(item_data)
            stats = Stats(
                ability_power=AbilityPower(flat=cls._parse_float(ap)),
                armor=Armor(flat=cls._parse_float(armor)),
                armor_penetration=ArmorPenetration(percent=cls._parse_float(armpen)),
                attack_damage=AttackDamage(flat=cls._parse_float(ad)),
                attack_speed=AttackSpeed(flat=cls._parse_float(attack_speed)),
                cooldown_reduction=CooldownReduction(percent=cls._parse_float(0.0)),
                critical_strike_chance=CriticalStrikeChance(percent=cls._parse_float(crit)),
                gold_per_10=GoldPer10(flat=cls._parse_float(gp10)),
                heal_and_shield_power=HealAndShieldPower(flat=cls._parse_float(hsp)),
                health=Health(flat=cls._parse_float(hp)),
                health_regen=HealthRegen(
                    flat=cls._parse_float(hp5flat),
                    percent=cls._parse_float(hp5),
                ),
                lethality=Lethality(flat=lethality),
                lifesteal=Lifesteal(percent=cls._parse_float(lifesteal)),
                magic_penetration=MagicPenetration(
                    flat=cls._parse_float(mpenflat), percent=cls._parse_float(mpen)
                ),
                magic_resistance=MagicResistance(flat=cls._parse_float(mr)),
                mana=Mana(flat=cls._parse_float(mana)),
                mana_regen=ManaRegen(
                    percent=cls._parse_float(mp5),
                ),
                movespeed=Movespeed(
                    flat=cls._parse_float(msflat),
                    percent=cls._parse_float(ms),
                ),
                omnivamp=OmniVamp(
                    percent=cls._parse_float(omnivamp),  # takes omnivamp from
                ),
                ability_haste=AbilityHaste(flat=cls._parse_float(ah)),
                tenacity=tenacity
            )
            return stats

        if 'hp' in item_data:
            hp = item_data['hp']



        if 'mr' in item_data:
            mr = item_data['mr']



        if 'ah' in item_data:
            ah = item_data['ah']


        if 'armor' in item_data:
            armor = item_data['armor']



        if 'ap' in item_data:
            ap = item_data['ap']



        if 'mana' in item_data:
            mana = item_data['mana']



        if 'hsp' in item_data:
            hsp = item_data['hsp']



        if 'mp5' in item_data:
            mp5 = item_data['mp5']



        if 'ad' in item_data:
            ad = item_data['ad']



        if 'as' in item_data:
            attack_speed = item_data['as']



        if 'msflat' in item_data:
            msflat = item_data['msflat']


        if 'gp10' in item_data:
            gp10 = item_data['gp10']


        if 'lifesteal' in item_data:
            lifesteal = item_data['lifesteal']


        if 'mpen' in item_data:
            mpen = item_data['mpen']



        if 'crit' in item_data:
            crit = item_data['crit']



        if 'spec' in item_data:
            spec = item_data['spec']



        if 'hp5' in item_data:
            hp5 = item_data['hp5']


        if 'ms' in item_data:
            ms = item_data['ms']



        if 'lethality' in item_data:
            lethality = item_data['lethality']


        if 'omnivamp' in item_data:
            omnivamp = item_data['omnivamp']


        if 'mpenflat' in item_data:
            mpenflat = item_data['mpenflat']



        if 'hspunique' in item_data:
            hspunique = item_data['hspunique']


        if 'hp5flat' in item_data:
            hp5flat = item_data['hp5flat']


        if 'armpen' in item_data:
            armpen = item_data['armpen']

        if 'pvamp' in item_data:
            pvamp = item_data['pvamp']
        else:
            pvamp = None
        if "spec" in item_data:
            if "TENACITY" in item_data["spec"].upper():
                tenacity = Tenacity(
                    cls._parse_float(re.search(r"(\d+)%", item_data["spec"].upper()).groups()[0]))
                print(tenacity)
        stats = Stats(
            ability_power=AbilityPower(flat=cls._parse_float(ap)),
            armor=Armor(flat=cls._parse_float(armor)),
            armor_penetration=ArmorPenetration(percent=cls._parse_float(armpen)),
            attack_damage=AttackDamage(flat=cls._parse_float(ad)),
            attack_speed=AttackSpeed(flat=cls._parse_float(attack_speed)),
            cooldown_reduction=CooldownReduction(percent=cls._parse_float(0.0)),
            critical_strike_chance=CriticalStrikeChance(percent=cls._parse_float(crit)),
            gold_per_10=GoldPer10(flat=cls._parse_float(gp10)),
            heal_and_shield_power=HealAndShieldPower(flat=cls._parse_float(hsp)),
            health=Health(flat=cls._parse_float(hp)),
            health_regen=HealthRegen(
                flat=cls._parse_float(hp5flat),
                percent=cls._parse_float(hp5),
            ),
            lethality=Lethality(flat=lethality),
            lifesteal=Lifesteal(percent=cls._parse_float(lifesteal)),
            magic_penetration=MagicPenetration(
                flat=cls._parse_float(mpenflat), percent=cls._parse_float(mpen)
            ),
            magic_resistance=MagicResistance(flat=cls._parse_float(mr)),
            mana=Mana(flat=cls._parse_float(mana)),
            mana_regen=ManaRegen(
                percent=cls._parse_float(mp5),
            ),
            movespeed=Movespeed(
                flat=cls._parse_float(msflat),
                percent=cls._parse_float(ms),
            ),
            omnivamp=OmniVamp(
                percent=cls._parse_float(omnivamp),  # takes omnivamp from
            ),
            ability_haste=AbilityHaste(flat=cls._parse_float(ah)),
            tenacity=tenacity
        )
        return stats




    @classmethod
    def get(cls, url: str) -> Optional[Item]:
        # All item data has a html attribute "data-name" so I put them all in an ordered dict while stripping the new lines and spaces from the data
        # use_cache = False
        html = download_soup(url, True, "__wiki__")
        soup = BeautifulSoup(html, "lxml")
        item_data = OrderedDict()
        for td in soup.findAll("td", {"data-name": True}):
            attributes = td.find_previous("td").text.rstrip()
            attributes = attributes.lstrip()
            values = td.text.rstrip()
            # replace("\n", "")
            values = values.lstrip().rstrip()
            item_data[attributes] = values
        item = cls._parse_item_data(item_data)
        return item

    @classmethod
    def _parse_item_data(cls, item_data: dict, item_name:str,wiki_data:dict) -> Item:
        not_unique = re.compile("[A-z]")
        clear_keys = []
        builds_from = []
        nicknames = []

        for x in item_data:
            if type(item_data[x]) == str:
                if "=>" in item_data[x]:
                    try:
                        item_data[x] = wiki_data[item_data[x].replace("=>", "")][x]
                    except KeyError as e:
                        clear_keys.append(x)
            if x in "effects":
                for l in item_data[x]:
                    if "=>" in item_data[x][l]:
                        item_data[x][l] = wiki_data[item_data[x][l].replace("=>", "")][x][l]
            if x in "stats":
                for l in item_data[x]:
                    if type(item_data[x][l]) ==str and "=>" in item_data[x][l]:
                        item_data[x][l] = wiki_data[item_data[x][l].replace("=>", "")][x][l]
        for key in clear_keys:
            item_data.pop(key)
        try:
            tier = item_data["tier"]
        except SyntaxError:
            tier = None
        except NameError:
            tier = item_data["tier"]
        except KeyError:
            tier = "tier 3"
        # Create the json files from the classes in modelitem.py
        if "id" in item_data:
            id = item_data["id"]

        else:
            id = None
        name = item_name
        if "removed" in item_data:
            if item_data["removed"] == "true":
                removed = True
            else:
                removed = False
        else:
            removed = False
        if "type" in item_data:
            rank = []
            if item_data["type"]:
                if "," in item_data["type"][0]:
                    ranks = item_data["type"][0].split(",")
                    for i in ranks:
                        rank.append(ItemRanks.from_string(i.strip()))
                else:
                    rank.append(ItemRanks.from_string(item_data["type"][0]))
            else:
                rank = None
        else:
            rank = []
        if "effects" not in item_data:
            no_effects = True
        else:
            no_effects = False
        if "buy" in item_data:     
            while isinstance(item_data["buy"], str) and "=>" in item_data["buy"]:
                item_data["buy"] = wiki_data[item_data["buy"].replace("=>", "")]["buy"]       
            sell = item_data["buy"] * .40
        else:
            sell = 0
        if "nickname" in item_data:
            nickname = item_data["nickname"]
            for i in nickname:
                nicknames.append(i.strip())
        else:
            nickname = None
        # if not_unique.search(item_data["builds"]):
        #     build = item_data["builds"]
        #     if "," in build:
        #         for i in build.split(","):
        #             i = cls._parse_recipe_build(i.strip())
        #             if i is not None:
        #                 builds_into.append(i)
        #             else:
        #                 continue
        #     else:
        #         build = cls._parse_recipe_build(build.strip())
        #         builds_into.append(build)
        #
        # if not_unique.match(item_data["recipe"]):
        #     component = item_data["recipe"]
        #     if "," in component:
        #         for i in component.split(","):
        #             i = cls._parse_recipe_build(i.strip())
        #             if i is not None:
        #                 builds_from.append(i)
        #             else:
        #                 continue
        #     else:
        #         component = cls._parse_recipe_build(component.strip())
        #         builds_from.append(component)
        if "stats" in item_data:
            stats = cls.get_stats(item_data["stats"])
        else:
            stats = cls.get_stats(item_data)
        ornn = False
        if "limit" in item_data:
            if "ORNN" in item_data["limit"].upper():
                print(item_data["limit"])
                ornn = True

        if "buy" in item_data:
            buy = item_data["buy"]
        else:
            buy = 0
        item = Item(
            name=name,
            id=id,
            tier=tier,
            builds_from=[],
            builds_into=[],
            no_effects=no_effects,
            removed=removed,
            nicknames=nicknames,
            icon="",
            passives=cls._parse_passives(item_data),
            active=cls._parse_actives(item_data),
            required_champion="",
            required_ally="",
            simple_description="",
            stats=stats,

            shop=Shop(
                prices=Prices(
                    total=cls._parse_int(buy),
                    combined=cls._parse_int(0),
                    sell=cls._parse_int(sell),
                ),
                tags=cls.get_item_attributes(item_data),
                purchasable="",
            ),
            rank=rank,
            special_recipe=0,
            iconOverlay=ornn,
        )
        return item

def get_item_urls(use_cache: bool) -> List[str]:
    url = "https://leagueoflegends.fandom.com/wiki/Module:ItemData/data"
    html = download_soup(url, False)
    soup = BeautifulSoup(html, "lxml")
    spans = soup.find("pre", {"class": "mw-code mw-script"})
    start = None
    spans = spans.text.split("\n")

    # Find beginning of item data
    for i, span in enumerate(spans):
        if str(span) == "return {":
            start = i
            spans[i] = "{"
            break
    spans = spans[start:]

    # Find end of item data
    for i, span in enumerate(reversed(spans)):
        if span in ["-- </pre>", "-- [[Category:Lua]]"]:
            spans[len(spans) - i - 1] = ""
            break

    spans = "\n".join(spans)
    data = lua.decode(spans)
    return data
