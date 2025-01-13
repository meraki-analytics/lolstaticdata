from typing import Tuple, List, Union, Iterator, Dict
import re
from bs4 import BeautifulSoup
from collections import Counter
from slpp import slpp as lua
from datetime import datetime

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
from ..common.utils import (
    download_soup,
    parse_top_level_parentheses,
    grouper,
    to_enum_like,
    download_json,
)
from .modelchampion import (
    Champion,
    Stats,
    Ability,
    AttackType,
    AttributeRatings,
    Cooldown,
    Cost,
    Effect,
    Price,
    Resource,
    Modifier,
    Position,
    Role,
    Leveling,
    Skin,
    Chroma,
    Description,
    Rarities,
)


class UnparsableLeveling(Exception):
    pass

class LolWikiDataHandler:
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache

    def check_ability(self, data):
        for x in data:
            if data[x] in self.abil_test:
                continue
            else:
                return False

    def get_champions(self) -> Iterator[Champion]:
        # Download the page source
        url = "https://wiki.leagueoflegends.com/en-us/Module:ChampionData/data"
        html = download_soup(url, self.use_cache)
        soup = BeautifulSoup(html, "lxml")

        # Pull the relevant champData from the html tags
        spans = soup.find("pre", {"class": "mw-code mw-script"})
        start = None
        spans = spans.text.split("\n")

        for i, span in enumerate(spans):
            if str(span) == "return {":
                start = i
                spans[i] = "{"
        split_stuff = re.compile("({)|(})")
        spans = spans[start:]
        for i, span in enumerate(spans):
            if span in ["-- </pre>", "-- [[Category:Lua]]"]:
                spans[i] = ""

        spans = "".join(spans)
        data = lua.decode(spans)

        # Return the champData as a list of Champions
        self.skin_data = self._get_skins()

        for name, d in data.items():
            print(name)
            if name in [
                "Kled & Skaarl",
                "GnarBig",
                "Mega Gnar",
            ]:
                continue
            if name in ["Kled"]:
                # champion = self._render_champion_data(name, d)
                d["skill_i"] = {1: d["skills"][1], 2: d["skills"][2]}
                d["skill_q"] = {1: d["skills"][3], 2: d["skills"][4]}
                d["skill_e"] = {1: d["skills"][6], 2: d["skills"][7]}
                d["skill_r"] = {1: d["skills"][8], 2: d["skills"][9]}
            # if (
            #     d["id"] == 9999
            #     or d["date"] == "Upcoming"
            #     or d["date"] == ""
            #     or datetime.strptime(d["date"], "%Y-%m-%d") > datetime.today()
            # ):  # Champion not released yet
            #     continue
            champion = self._render_champion_data(name, d)
            yield champion

    def _render_champion_data(self, name: str, data: Dict) -> Champion:

        sale = self._get_sale()
        sale_price = 0
        if name in sale:
            if sale[name]["price"] != 0:
                sale_price = int(sale[name]["price"])
        champion = Champion(
            id=data["id"],
            key=data["apiname"],
            name=name,
            title=data["title"],
            full_name=data.get("fullname", ""),
            icon=None,
            skins=self._get_champ_skin(name, sale),
        )
        # "nickname": "nickname",
        # "disp_name": "dispName",
        return champion

    def _get_sale(self):

        get_prices = re.compile(r"(\d+) (\d+)")
        url = f"https://wiki.leagueoflegends.com/en-us/Sales"
        html = download_soup(url, False)
        soup = BeautifulSoup(html, "lxml")
        spans = soup.findAll("div", {"class": "skin_portrait skin-icon"})
        sale = {}
        for i in spans:
            prices = get_prices.findall(i.text)
            champion = i["data-champion"]
            if not sale.get(champion):
                sale[champion] = {}
                sale[champion]["price"] = 0
            skin = i["data-skin"]
            if skin != "":
                sale[champion][skin] = prices[0][1]
            else:
                sale[champion]["price"] = prices[0][1]

        return sale

    def _get_skin_id(self, id, skin_id):
        while len(str(skin_id)) < 3:
            skin_id = "0" + str(skin_id)
        return str(id) + str(skin_id)

    def _get_chroma_attribs(self, id, name):
        if "chromas" in self.cdragDict[0]:
            for c in self.cdragDict[0]["chromas"]:
                if int(id) == c["id"]:
                    descriptions = []
                    rarities = []
                    if c["descriptions"]:
                        for desc in c["descriptions"]:
                            descriptions.append(Description(desc["description"], desc["region"]))
                    else:
                        descriptions.append(Description(None, None))
                    if c["rarities"]:
                        for rarity in c["rarities"]:
                            rarities.append(Rarities(rarity["rarity"], rarity["region"]))
                    else:
                        rarities.append(Rarities(None, None))
                    chroma = Chroma(
                        name=name,
                        id=c["id"],
                        chroma_path=self._get_skin_path(c["chromaPath"]),
                        colors=c["colors"],
                        descriptions=descriptions,
                        rarities=rarities,
                    )
                    return chroma
            available = [n['id'] for n in self.cdragDict[0]["chromas"]]
            print(f"Chroma Mismatch: {id} not available in {available}")

    def _get_skins(self):
        url = f"https://wiki.leagueoflegends.com/en-us/Module:SkinData/data"

        html = download_soup(url, False)
        soup = BeautifulSoup(html, "lxml")

        # Pull the relevant champData from the html tags
        spans = soup.find("pre", {"class": "mw-code mw-script"})
        start = None
        spans = spans.text.split("\n")

        for i, span in enumerate(spans):
            if str(span) == "return {":
                start = i
                spans[i] = "{"
        spans = spans[start:]
        test1 = re.compile("\w -- \w|.\w--\w|\w --\w|.\w--\s")
        for i, span in enumerate(spans):
            if span in ["-- </pre>", "-- [[Category:Lua]]"]:
                spans[i] = ""

            if re.search(test1, span):
                test2 = re.search(test1, span)
                spans[i] = span.replace(test2.group()[2] + test2.group()[3], " ")
                span = spans[i]

            comment_start = span.find("--")
            # text = text.replace("-", " ")
            if comment_start > -1:
                spans[i] = span[:comment_start]

        spans = "".join(spans)
        skin_data = lua.decode(spans)
        return skin_data

    def _get_skin_path(self, path):
        if "/assets/ASSETS" in path:
            path = path.split("ASSETS")[1]
            path = path.lower()
            path = "https://raw.communitydragon.org/pbe/plugins/rcp-be-lol-game-data/global/default/assets" + path
            return path
        base_url = "http://raw.communitydragon.org/pbe/plugins/rcp-be-lol-game-data/global/default/v1"
        # /lol-game-data/assets/v1/champion-chroma-images/32/32014.png
        path = path.split("v1")[1]
        return base_url + path

    def _get_champ_skin(self, name, sale):
        """
        Pulls champion skin data from wiki and cdragon
        """
        champ_data = self.skin_data[name]["skins"]
        skins = []
        champ_id = self.skin_data[name]["id"]

        cdragon = "http://raw.communitydragon.org/pbe/plugins/rcp-be-lol-game-data/global/default/v1/champions/{0}.json".format(
            champ_id
        )
        cdrag_json = download_json(cdragon, False)

        for s in champ_data:
            # Default values for LOL Wiki attributes
            if champ_data[s]["id"] == None:
                continue
            skin_ID = self._get_skin_id(champ_id, champ_data[s]["id"])
            new_effects = False
            new_recall = False
            new_animations = False
            new_voice = False
            new_quotes = False
            chromas = []
            distribution = None
            sets = []
            format_name = s
            voice_actors = []
            splash_arist = []
            loot_eligible = True
            lore = None
            cdragon_ids = []
            self.cdragDict = [i for i in cdrag_json["skins"] if i["id"] == int(skin_ID)]  # Cdragon Dict
            for skin in cdrag_json["skins"]:
                cdragon_ids.append(skin["id"])
            if int(skin_ID) not in cdragon_ids:
                continue
            # cdragon attributes

            is_base = self.cdragDict[0]["isBase"]
            splash_path = self._get_skin_path(self.cdragDict[0]["splashPath"])
            uncentered_splash_path = self._get_skin_path(self.cdragDict[0]["uncenteredSplashPath"])
            tile_path = self._get_skin_path(self.cdragDict[0]["tilePath"])
            load_screen_path = self._get_skin_path(self.cdragDict[0]["loadScreenPath"])
            if "loadScreenVintagePath" in self.cdragDict[0]:
                load_screen_vintage_path = self._get_skin_path(self.cdragDict[0]["loadScreenVintagePath"])
            else:
                load_screen_vintage_path = None

            rarity = self.cdragDict[0]["rarity"][1:]

            if "neweffects" in champ_data[s]:
                new_effects = True

            if "newrecall" in champ_data[s]:
                new_recall = True

            if "newanimations" in champ_data[s]:
                new_animations = True

            if "newquotes" in champ_data[s]:
                new_quotes = True

            if "newvoice" in champ_data[s]:
                new_voice = True

            if "chromas" in champ_data[s]:
                for chroma in champ_data[s]["chromas"]:
                    if "id" not in champ_data[s]["chromas"][chroma] or not str(champ_data[s]["chromas"][chroma]["id"]).isnumeric():
                        continue
                    if "availability" in champ_data[s]["chromas"][chroma] and champ_data[s]["chromas"][chroma]["availability"] == "Canceled":
                        continue
                    chromas.append(
                        self._get_chroma_attribs(
                            self._get_skin_id(champ_id, champ_data[s]["chromas"][chroma]["id"]),
                            chroma,
                        )
                    )

            if "distribution" in champ_data[s]:
                distribution = champ_data[s]["distribution"]
            if "set" in champ_data[s]:
                for set in champ_data[s]["set"]:
                    sets.append(set)

            if "formatname" in champ_data[s]:
                format_name = champ_data[s]["formatname"]

            if "voiceactor" in champ_data[s]:
                for va in champ_data[s]["voiceactor"]:
                    voice_actors.append(va)

            if "lore" in champ_data[s]:
                lore = champ_data[s]["lore"]

            if "splashartist" in champ_data[s]:
                for sa in champ_data[s]["splashartist"]:
                    splash_arist.append(sa)

            if "looteligible" in champ_data[s]:
                loot_eligible = champ_data[s]["looteligible"]

            if "release" in champ_data[s]:
                if "N/A" in champ_data[s]["release"]:
                    timestamp = "0000-00-00"
                else:
                    timestamp = champ_data[s]["release"]
            sale_rp = 0
            if name in sale:
                if s in sale[name]:
                    sale_rp = sale[name][s]
            skin = Skin(
                name=s,
                id=int(skin_ID),
                availability=champ_data[s]["availability"],
                format_name=format_name,
                loot_eligible=loot_eligible,
                cost=champ_data[s]["cost"],
                sale=int(sale_rp),
                release=timestamp,
                distribution=distribution,
                set=sets,
                new_effects=new_effects,
                new_animations=new_animations,
                new_recall=new_recall,
                voice_actor=voice_actors,
                splash_artist=splash_arist,
                chromas=chromas,
                lore=lore,
                new_quotes=new_quotes,
                new_voice=new_voice,
                is_base=is_base,
                splash_path=splash_path,
                uncentered_splash_path=uncentered_splash_path,
                tile_path=tile_path,
                load_screen_path=load_screen_path,
                load_screen_vintage_path=load_screen_vintage_path,
                rarity=rarity,
            )
            skins.append(skin)
        return skins


class ParsingAndRegex:
    rc_scaling = re.compile(r"(\(\+.+?\))")
    r_number = r"(\d+\.?\d*)"
    rc_number = re.compile(r_number)
    rc_based_on_level = re.compile(r"(\d+\.?\d*) ?− ?(\d+\.?\d*) \(based on level\)")

    @staticmethod
    def regex_slash_separated(string: str, nvalues: int) -> Tuple[List[str], List[Union[int, float]]]:
        for i in range(20, 1, -1):
            regex = " / ".join([ParsingAndRegex.r_number for _ in range(i)])
            result = re.findall(regex, string)
            if result:
                assert len(result) == 1
                result = result[0]
                parsed = " / ".join([f"{{{j}}}" for j in range(i)]).format(*result)
                not_parsed = string.split(parsed)
                values = [eval(r) for r in result]
                # Special case...
                if nvalues == 3 and len(values) == 5:
                    values = [values[0], values[2], values[4]]
                if nvalues is not None and len(values) != nvalues:
                    print(f"WARNING: Unexpected number of modifier values: {values} (expected {nvalues})")
                return not_parsed, values
        raise ValueError(f"Could not parse slash-separated string: {string}")

    @staticmethod
    def parse_based_on_level(start, stop):
        # e.g. 5 − 139 (based on level)
        delta = (stop - start) / 17.0
        values = [start + i * delta for i in range(18)]
        return values

    @staticmethod
    def regex_simple_flat(string: str, nvalues: int) -> Tuple[List[str], List[Union[int, float]]]:
        numbers = ParsingAndRegex.rc_number.findall(string)
        if "/" in string:
            return ParsingAndRegex.regex_slash_separated(string, nvalues)
        elif len(ParsingAndRegex.rc_based_on_level.findall(string)) > 0:
            level = ParsingAndRegex.rc_based_on_level.findall(string)
            assert len(level) == 1
            start, stop = level[0]
            start, stop = eval(start), eval(stop)
            values = ParsingAndRegex.parse_based_on_level(start, stop)
            parsed = f"{start} − {stop} (based on level)"
            not_parsed = string.split(parsed)
            assert len(not_parsed) >= 2
            if len(not_parsed) != 2:  # see below
                not_parsed = not_parsed[0], parsed.join(not_parsed[1:])
            assert len(values) == 18
            return not_parsed, values
        elif len(numbers) - len(re.findall(r" per \d", string)) == 1 + string.count("(+ "):
            number = numbers[0]
            not_parsed = string.split(number)
            assert len(not_parsed) >= 2
            if len(not_parsed) != 2:  # Fix e.g. `15 per 150 AP`
                not_parsed = not_parsed[0], number.join(not_parsed[1:])
            number = eval(number)
            if nvalues is None:
                nvalues = len(numbers)
            values = [number for _ in range(nvalues)]
            assert len(values) == nvalues
            return not_parsed, values
        raise UnparsableLeveling(f"Could not parse a simple flat value: {string}")

    @staticmethod
    def get_units(not_parsed: List[str]) -> str:
        assert len(not_parsed) == 2
        assert not_parsed[0] == ""
        return not_parsed[1]

    @staticmethod
    def get_modifier(mod: str, nvalues: int) -> Tuple[List[str], List[Union[int, float]]]:
        units, parsed = ParsingAndRegex.regex_simple_flat(mod, nvalues)
        units = ParsingAndRegex.get_units(units)
        units = [units for _ in range(len(parsed))]
        return units, parsed

    @staticmethod
    def split_modifiers(mods: str) -> List[str]:
        flat, scalings = ParsingAndRegex.get_scalings(mods)
        if " + " in flat:
            flat = flat.split(" + ")
        else:
            flat = [flat]
        return flat + scalings

    @staticmethod
    def get_scalings(numbers: str):
        scalings = ParsingAndRegex.rc_scaling.findall(numbers)
        if scalings:
            scalings = parse_top_level_parentheses(numbers)
        scalings = [scaling for scaling in scalings if scaling != "(based on level)"]
        for scaling in scalings:
            numbers = numbers.replace(scaling, "").strip()  # remove the scaling part of the string for processing later
        scalings = [x.strip() for x in scalings]
        for i, scaling in enumerate(scalings):
            if scaling.startswith("(") and scaling.endswith(")"):
                scaling = scaling[1:-1].strip()
            if scaling.startswith("+"):
                scaling = scaling[1:].strip()
            scalings[i] = scaling
        return numbers, scalings
