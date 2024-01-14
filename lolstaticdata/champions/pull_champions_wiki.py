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
    Role,
    Leveling,
    Skin,
    Chroma,
    Description,
    Rarities,
)


class UnparsableLeveling(Exception):
    pass


class HTMLAbilityWrapper:
    def __init__(self, soup):
        self.soup = soup
        self.table = self.soup.find_all(["th", "td"])
        # Do a little html modification based on the "viewsource"
        strip_table = [item.text.strip() for item in self.table]
        start = strip_table.index("Parameter") + 3
        self.table = self.table[start:]
        self.data = {}
        for i, (parameter, value, desc) in enumerate(grouper(self.table, 3)):
            if not value:
                continue
            if i == 0:  # parameter is '1' for some reason but it's the ability name
                parameter = "name"
            else:
                parameter = parameter.text.strip()
            # desc = desc.text.strip()
            text = value.text.strip()
            if text:
                self.data[parameter] = value

    def __getitem__(self, item):
        return self.data[item].text.strip()

    def __delitem__(self, item):
        del self.data[item]

    def get(self, item, backup=None):
        try:
            return self[item]
        except KeyError:
            return backup

    def get_source(self, item, backup=None):
        try:
            return self.data[item]
        except KeyError:
            return backup

    def __str__(self):
        d = {}
        for key in self.data:
            d[key] = self[key]
        return str(d)


class LolWikiDataHandler:
    MISSING_SKILLS = {
        "Annie": ["Command Tibbers"],
        "Jinx": ["Switcheroo! 2"],
        "Lillia": ["Prance"],
        "Mordekaiser": ["Indestructible 2"],
        "Nidalee": ["Aspect of the Cougar 2"],
        "Pyke": ["Death from Below 2"],
        "Rumble": ["Electro Harpoon 2"],
        "Samira": ["splash coin"],
        "Shaco": ["Command: Hallucinate"],
        "Syndra": ["Force of Will 2"],
        "Taliyah": ["Seismic Shove 2"],
    }

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
        url = "https://leagueoflegends.fandom.com/wiki/Module:ChampionData/data"
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
            if (
                d["id"] == 9999
                or d["date"] == "Upcoming"
                or d["date"] == ""
                or datetime.strptime(d["date"], "%Y-%m-%d") > datetime.today()
            ):  # Champion not released yet
                continue
            champion = self._render_champion_data(name, d)
            yield champion

    def _render_champion_data(self, name: str, data: Dict) -> Champion:

        adaptive_type = data["adaptivetype"]
        if adaptive_type.upper() in ("PHYSICAL", "MIXED,PHYSICAL"):
            adaptive_type = "PHYSICAL_DAMAGE"
        if adaptive_type.upper() in ("MAGIC",):
            adaptive_type = "MAGIC_DAMAGE"
        if adaptive_type.upper() in ("MIXED",):
            adaptive_type = "MIXED_DAMAGE"
        if data["patch"][0] == "V":
            patch = data["patch"][1:]
        else:
            patch = data["patch"]
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
            resource=Resource.from_string(data["resource"]),
            attack_type=AttackType.from_string(data["rangetype"]),
            adaptive_type=DamageType.from_string(adaptive_type),
            stats=Stats(
                health=Health(
                    flat=data["stats"]["hp_base"],
                    per_level=data["stats"]["hp_lvl"],
                ),
                health_regen=HealthRegen(
                    flat=data["stats"]["hp5_base"],
                    per_level=data["stats"]["hp5_lvl"],
                ),
                mana=Mana(
                    flat=data["stats"]["mp_base"],
                    per_level=data["stats"]["mp_lvl"],
                ),
                mana_regen=ManaRegen(
                    flat=data["stats"]["mp5_base"],
                    per_level=data["stats"]["mp5_lvl"],
                ),
                armor=Armor(
                    flat=data["stats"]["arm_base"],
                    per_level=data["stats"]["arm_lvl"],
                ),
                magic_resistance=MagicResistance(
                    flat=data["stats"]["mr_base"],
                    per_level=data["stats"]["mr_lvl"],
                ),
                attack_damage=AttackDamage(
                    flat=data["stats"]["dam_base"],
                    per_level=data["stats"]["dam_lvl"],
                ),
                attack_speed=AttackSpeed(
                    flat=data["stats"]["as_base"],
                    per_level=data["stats"]["as_lvl"],
                ),
                attack_speed_ratio=Stat(flat=data["stats"]["as_ratio"]),
                attack_cast_time=Stat(
                    flat=data["stats"].get("attack_cast_time", 0.3)
                ),  # I don't know if this default is correct, but going off the values the wiki provides, it seems reasonable.
                attack_total_time=Stat(flat=data["stats"].get("attack_total_time", 1.6)),  # ibid
                attack_delay_offset=Stat(flat=data["stats"].get("attack_delay_offset", 0)),
                attack_range=AttackRange(
                    flat=data["stats"]["range"],
                    per_level=data["stats"].get("range_lvl", 0),
                ),
                critical_strike_damage=Stat(flat=data["stats"].get("crit_base", 200)),
                critical_strike_damage_modifier=Stat(flat=data["stats"].get("crit_base", 1.0)),
                movespeed=Movespeed(flat=data["stats"]["ms"]),
                acquisition_radius=Stat(flat=data["stats"].get("acquisition_radius", 800)),
                selection_radius=Stat(flat=data["stats"].get("selection_radius", 100)),
                pathing_radius=Stat(flat=data["stats"].get("pathing_radius", 35)),
                gameplay_radius=Stat(flat=data["stats"].get("gameplay_radius", 65)),
                aram_damage_taken=Stat(flat=data["stats"].get("aram",{}).get("dmg_taken", 1.0)),
                aram_damage_dealt=Stat(flat=data["stats"].get("aram",{}).get("dmg_dealt", 1.0)),
                aram_healing=Stat(flat=data["stats"].get("aram",{}).get("healing", 1.0)),
                aram_shielding=Stat(flat=data["stats"].get("aram",{}).get("shielding", 1.0)),
                urf_damage_taken=Stat(flat=data["stats"].get("urf",{}).get("dmg_taken", 1.0)),
                urf_damage_dealt=Stat(flat=data["stats"].get("urf",{}).get("dmg_dealt", 1.0)),
                urf_healing=Stat(flat=data["stats"].get("urf",{}).get("healing", 1.0)),
                urf_shielding=Stat(flat=data["stats"].get("urf",{}).get("shielding", 1.0)),
            ),
            roles=sorted(
                {
                    *(Role.from_string(r) for r in data["role"]),
                    *(
                        Role.from_string(role)
                        for role in (
                            data.get("herotype"),
                            data.get("alttype"),
                        )
                        if role is not None and role != ""
                    ),
                }
            ),
            attribute_ratings=AttributeRatings(
                damage=data["damage"],
                toughness=data["toughness"],
                control=data["control"],
                mobility=data["mobility"],
                utility=data["utility"],
                ability_reliance=data["style"],
                difficulty=data["difficulty"],
            ),
            abilities=dict(
                [
                    self._render_abilities(
                        champion_name=name,
                        abilities=[
                            self._pull_champion_ability(champion_name=name, ability_name=ability_name)
                            for ability_name in data["skill_i"].values()
                            if not (
                                name in LolWikiDataHandler.MISSING_SKILLS
                                and ability_name in LolWikiDataHandler.MISSING_SKILLS[name]
                            )
                        ],
                        default="I",
                    ),
                    self._render_abilities(
                        champion_name=name,
                        abilities=[
                            self._pull_champion_ability(champion_name=name, ability_name=ability_name)
                            for ability_name in data["skill_q"].values()
                            if not (
                                name in LolWikiDataHandler.MISSING_SKILLS
                                and ability_name in LolWikiDataHandler.MISSING_SKILLS[name]
                            )
                        ],
                        default="Q",
                    ),
                    self._render_abilities(
                        champion_name=name,
                        abilities=[
                            self._pull_champion_ability(champion_name=name, ability_name=ability_name)
                            for ability_name in data["skill_w"].values()
                            if not (
                                name in LolWikiDataHandler.MISSING_SKILLS
                                and ability_name in LolWikiDataHandler.MISSING_SKILLS[name]
                            )
                        ],
                        default="W",
                    ),
                    self._render_abilities(
                        champion_name=name,
                        abilities=[
                            self._pull_champion_ability(champion_name=name, ability_name=ability_name)
                            for ability_name in data["skill_e"].values()
                            if not (
                                name in LolWikiDataHandler.MISSING_SKILLS
                                and ability_name in LolWikiDataHandler.MISSING_SKILLS[name]
                            )
                        ],
                        default="E",
                    ),
                    self._render_abilities(
                        champion_name=name,
                        abilities=[
                            self._pull_champion_ability(champion_name=name, ability_name=ability_name)
                            for ability_name in data["skill_r"].values()
                            if not (
                                name in LolWikiDataHandler.MISSING_SKILLS
                                and ability_name in LolWikiDataHandler.MISSING_SKILLS[name]
                            )
                        ],
                        default="R",
                    ),
                ]
            ),
            release_date=data["date"],
            release_patch=patch,
            # remove the leading "V"
            patch_last_changed=data["changes"][1:],  # remove the leading "V"
            price=Price(rp=data["rp"], blue_essence=data["be"], sale_rp=sale_price),
            lore="",
            faction="",
            skins=self._get_champ_skin(name, sale),
        )
        # "nickname": "nickname",
        # "disp_name": "dispName",
        return champion

    def _pull_champion_ability(self, champion_name, ability_name) -> HTMLAbilityWrapper:
        ability_name = ability_name.replace(" ", "_")

        # Pull the html from the wiki
        # print(f"  {ability_name}")
        url = f"https://leagueoflegends.fandom.com/wiki/Template:Data_{champion_name}/{ability_name}"
        # temporary fix for pyke passive
        if url in "https://leagueoflegends.fandom.com/wiki/Template:Data_Pyke/Gift_of_the_Drowned_Ones":
            url = "https://leagueoflegends.fandom.com/wiki/User:Dryan426/Sandbox"
        html = download_soup(url, self.use_cache)
        soup = BeautifulSoup(html, "lxml")
        return HTMLAbilityWrapper(soup)

    def _render_abilities(self, champion_name, abilities: List[HTMLAbilityWrapper], default: str) -> Tuple[str, List[Ability]]:
        inputs, abilities = abilities, []  # rename variables
        skill_key = inputs[0]["skill"]
        for data in inputs:
            _skill_key = data["skill"]
            if champion_name == "Aphelios" and data["name"] in (
                "Calibrum",
                "Severum",
                "Gravitum",
                "Infernum",
                "Crescendum",
            ):
                _skill_key = "I"
            if champion_name == "Gnar" and data["name"] in ("Boulder Toss",):
                _skill_key = "Q"
            if _skill_key != skill_key:
                _skill_key = default
            assert _skill_key == skill_key

            nvalues = 5 if _skill_key in ("Q", "W", "E") else 3
            if champion_name == "Aphelios" and _skill_key == "I":
                nvalues = 6
            elif champion_name == "Heimerdinger":
                nvalues = None
            elif champion_name == "Janna" and _skill_key == "I":
                nvalues = 2
            elif champion_name == "Sona" and _skill_key in ("Q", "W", "E"):
                nvalues = None
            elif champion_name == "Jayce":
                nvalues = 6
            elif champion_name == "Karma":
                nvalues = None
            elif champion_name == "Kindred" and _skill_key == "I":
                nvalues = 2
            elif champion_name == "Nidalee":
                nvalues = None
            elif champion_name == "Udyr":
                nvalues = 6
            elif champion_name == "Yuumi" and _skill_key == "Q":
                nvalues = 6
            ability_cost = data.get("cost")
            cooldown = data.get("cooldown", data.get("static"))

            damage_type = data.get("damagetype")
            if damage_type is not None:
                damage_type = to_enum_like(damage_type)
                if "/" in damage_type:
                    damage_type = "MIXED_DAMAGE"
                elif damage_type == "PHYSICAL":
                    damage_type = "PHYSICAL_DAMAGE"
                elif damage_type == "MAGIC":
                    damage_type = "MAGIC_DAMAGE"
                elif damage_type == "TRUE":
                    damage_type = "TRUE_DAMAGE"
                elif damage_type == "PURE":
                    damage_type = "PURE_DAMAGE"
                else:
                    damage_type = "OTHER_DAMAGE"
                damage_type = DamageType.from_string(damage_type)

            resource = data.get("costtype")
            if resource is not None:
                resource = to_enum_like(resource)
                if resource in (
                    "MANA",
                    "NO_COST",
                    "HEALTH",
                    "MAXIMUM_HEALTH",
                    "ENERGY",
                    "CURRENT_HEALTH",
                    "HEALTH_PER_SECOND",
                    "MANA_PER_SECOND",
                    "CHARGE",
                    "FURY",
                ):
                    pass
                elif resource in (
                    "MANA_+_4_FOCUS",
                    "MANA_+_4_FROST_STACKS",
                    "MANA_+_6_CHARGES",
                    "MANA_+_1_SAND_SOLDIER",
                    "MANA_+_40_/_45_/_50_/_55_/_60_PER_SECOND",
                    "MAXIMUM_HEALTH_+_50_/_55_/_60_/_65_/_70_MANA",
                    "MANA_+_1_TURRET_KIT",
                    "MANA_+_1_MISSILE",
                    "MANA_+_1_CHARGE",
                    "MANA_+_ALL_CHARGES",
                ):
                    resource = "MANA"
                elif resource == "OF_CURRENT_HEALTH":
                    resource = "CURRENT_HEALTH"
                elif resource == "%_OF_CURRENT_HEALTH":
                    resource = "CURRENT_HEALTH"
                elif resource == "CURRENT_GRIT":
                    resource = "GRIT"
                elif resource == "CURRENT_FURY":
                    resource = "FURY"
                elif resource == "FURY_EVERY_0.5_SECONDS":
                    resource = "FURY"
                else:
                    resource = "OTHER"
                resource = Resource.from_string(resource)

            projectile = data.get("projectile")
            if projectile:
                projectile = to_enum_like(projectile)

            recharge_rate = data.get("recharge")
            if recharge_rate:
                _, recharge_rate = ParsingAndRegex.regex_simple_flat(recharge_rate, nvalues)  # ignore units

            effects = []
            for ending in ["", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
                description = data.get(f"description{ending}")
                while description and "  " in description:
                    description = description.replace("  ", " ")
                leveling = data.get_source(f"leveling{ending}")
                leveling = self._render_levelings(leveling, nvalues) if leveling else []
                if description or leveling:
                    effects.append(Effect(description=description, leveling=leveling))

            ability = Ability(
                name=data["name"],
                icon=data.get(f"icon{ending}"),
                effects=effects,
                cost=self._render_ability_cost(ability_cost, nvalues) if ability_cost else None,
                cooldown=self._render_ability_cooldown(cooldown, "static" in data.data, nvalues) if cooldown else None,
                targeting=data.get("targeting"),
                affects=data.get("affects"),
                spellshieldable=data.get("spellshield"),
                resource=resource,
                damage_type=damage_type,
                spell_effects=data.get("spelleffects"),
                projectile=projectile,
                on_hit_effects=data.get("onhiteffects"),
                occurrence=data.get("occurrence"),
                blurb=data.get("blurb"),
                notes=data.get("notes") if data.get("notes") != "* No additional notes." else None,
                missile_speed=data.get("missile_speed"),
                recharge_rate=recharge_rate,
                collision_radius=data.get("collision radius"),
                tether_radius=data.get("tether radius"),
                on_target_cd_static=data.get("ontargetcdstatic"),
                inner_radius=data.get("inner radius"),
                speed=data.get("speed"),
                width=data.get("width"),
                angle=data.get("angle"),
                cast_time=data.get("cast time"),
                effect_radius=data.get("effect radius"),
                target_range=data.get("target range"),
            )
            if ability.notes is not None and ability.notes.startswith("*"):
                ability.notes = ability.notes[1:].strip()
            abilities.append(ability)
        if skill_key == "I":
            skill_key = "P"
        # Check for duplicate abilities
        hashes = []
        unique_abilities = []
        for ability in abilities:
            h = hash(str(ability))
            if h not in hashes:
                hashes.append(h)
                unique_abilities.append(ability)
        return skill_key, unique_abilities

    def _render_levelings(self, html: BeautifulSoup, nvalues: int) -> List[Leveling]:
        # Do some pre-processing on the html
        if not isinstance(html, str):
            html = str(html)
        html = html.replace("</dt>", "\n</dt>")
        html = html.replace("</dd>", "\n</dd>")
        html = BeautifulSoup(html, "lxml")
        html = html.text.strip()
        while "\n\n" in html:
            html = html.replace("\n\n", "\n")
        while "  " in html:
            html = html.replace("  ", " ")
        levelings = html.replace("\xa0", " ")

        # Get ready
        results = []

        # Let's parse!
        initial_split = levelings.split("\n")
        initial_split = [
            lvling.strip()
            for lvling in initial_split
            if lvling.strip()
            not in (
                "Takedown scales with Aspect of the Cougar's rank",
                "Swipe scales with Aspect of the Cougar's rank",
                "Pounce scales with Aspect of the Cougar's rank",
                "Cougar form's abilities rank up when Aspect of the Cougar does",
            )
        ]
        initial_split = list(grouper(initial_split, 2))

        for attribute, data in initial_split:
            if attribute.endswith(":"):
                attribute = attribute[:-1]
            result = self._render_leveling(attribute, data, nvalues)
            results.append(result)

        return results

    def _render_leveling(self, attribute: str, data: str, nvalues: int) -> Leveling:
        modifiers = self._render_modifiers(data, nvalues)
        leveling = Leveling(
            attribute=attribute,
            modifiers=modifiers,
        )
        return leveling

    def _render_modifiers(self, mods: str, nvalues: int) -> List[Modifier]:
        modifiers = []  # type: List[Modifier]
        try:
            parsed_modifiers = ParsingAndRegex.split_modifiers(mods)
        except Exception as error:
            print("ERROR: FAILURE TO SPLIT MODIFIER")
            print("ERROR:", error)
            return modifiers

        for lvling in parsed_modifiers:
            try:
                modifier = self._render_modifier(lvling, nvalues)
                modifiers.append(modifier)
            except Exception as error:
                print(f"ERROR: FAILURE TO PARSE MODIFIER:  {lvling}")
                print("ERROR:", error)
                while "  " in lvling:
                    lvling = lvling.replace("  ", " ")
                value = 0
                if lvling.lower() == "Siphoning Strike Stacks".lower():  # Nasus
                    value = 1
                if lvling.lower() == "increased by 3% per 1% of health lost in the past 4 seconds".lower():  # Ekko
                    value = 3
                    lvling = "% per 1% of health lost in the past 4 seconds"
                modifier = Modifier(
                    values=[value for _ in range(nvalues)],
                    units=[lvling for _ in range(nvalues)],
                )
                modifiers.append(modifier)
        return modifiers

    def _render_modifier(self, mod: str, nvalues: int) -> Modifier:
        units, values = ParsingAndRegex.get_modifier(mod, nvalues)
        modifier = Modifier(
            values=values,
            units=units,
        )
        return modifier

    def _render_ability_cost(self, mods: str, nvalues: int) -> Cost:
        modifiers = self._render_modifiers(mods, nvalues)
        cost = Cost(modifiers=modifiers)
        return cost

    def _render_ability_cooldown(self, mods: str, static_cooldown: bool, nvalues: int) -> Cooldown:
        modifiers = self._render_modifiers(mods, nvalues)
        cooldown = Cooldown(
            modifiers=modifiers,
            affected_by_cdr=not static_cooldown,
        )
        return cooldown

    def _get_sale(self):

        get_prices = re.compile(r"(\d+) (\d+)")
        url = f"https://leagueoflegends.fandom.com/wiki/Sales"
        # temporary fix for pyke passive
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
        url = f"https://leagueoflegends.fandom.com/wiki/Module:SkinData/data"

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
