from typing import Tuple, List, Optional, Mapping, Dict
import os
import re
import json
import glob
import requests
import itertools
from bs4 import BeautifulSoup
from collections import Counter, defaultdict

from .model import Champion, Stats, Ability, AdaptiveType, AttackType, AttributeRatings, Cooldown, Cost, Effect, Price, Resource, Modifier, Role, Leveling
from .util import download_webpage, save_json


class UnparsableLeveling(Exception):
    pass


class LolWikiDataHandler:
    @staticmethod
    def pull_champion_stats() -> List[Champion]:
        # Download the page source
        url = "https://leagueoflegends.fandom.com/wiki/Module:ChampionData/data"
        html = download_webpage(url)
        soup = BeautifulSoup(html, 'html5lib')

        # Pull the relevant data from the html tags
        spans = soup.find_all('span')
        start = None
        for i, span in enumerate(spans):
            if str(span) == '<span class="kw1">return</span>':
                start = i
        spans = spans[start:]
        data = ""
        brackets = Counter()
        for span in spans:
            text = span.text
            if text == "{" or text == "}":
                brackets[text] += 1
            if brackets["{"] != 0:
                data += text
            if brackets["{"] == brackets["}"] and brackets["{"] > 0:
                break

        # Sanitize the data
        data = data.replace('=', ':')
        data = data.replace('["', '"')
        data = data.replace('"]', '"')
        data = data.replace('[1]', '1')
        data = data.replace('[2]', '2')
        data = data.replace('[3]', '3')
        data = data.replace('[4]', '4')
        data = data.replace('[5]', '5')
        data = data.replace('[6]', '6')

        # Return the data as a list of champions
        data = eval(data)
        results = []
        for name, d in data.items():
            r = LolWikiDataHandler._render_champion_data(name, d)
            results.append(r)
        return results

    @staticmethod
    def _render_champion_data(name: str, data: Mapping) -> Champion:
        champion = Champion(
            id=data["id"],
            key=data["apiname"],
            name=name,
            title=data["title"],
            full_name=data["fullname"],
            resource=data["resource"],
            attack_type=data["rangetype"],
            adaptive_type=data["adaptivetype"],
            stats=Stats(
                health_base=data["hp_base"],
                health_per_level=data["hp_lvl"],
                health_per_5_seconds_base=data["hp5_base"],
                health_per_5_seconds_per_level=data["hp5_lvl"],
                mana_base=data["mp_base"],
                mana_per_level=data["mp_lvl"],
                mana_per_5_seconds_base=data["mp5_base"],
                mana_per_5_seconds_per_level=data["mp5_lvl"],
                armor_base=data["arm_base"],
                armor_per_level=data["arm_lvl"],
                magic_resistance_base=data["mr_base"],
                magic_resistance_per_level=data["mr_lvl"],
                attack_damage_base=data["dam_base"],
                attack_damage_per_level=data["dam_lvl"],
                attack_range=data["attack_range"],
                attack_speed_base=data["as_base"],
                attack_speed_per_level=data["as_lvl"],
                attack_speed_ratio=data["as_ratio"],
                attack_cast_time=data["attack_cast_time"],
                attack_total_time=data["attack_total_time"],
                attack_delay_offset=data["attack_delay_offset"],
                attack_range_base=data["range"],
                attack_range_per_level=data["range_lvl"],
                critical_strike_base=data["crit_base"],
                critical_strike_modifier=data["crit_mod"],
                movespeed=data["ms"],
                acquisition_radius=data["acquisition_radius"],
                selection_radius=data["selection_radius"],
                pathing_radius=data["pathing_radius"],
                gameplay_radius=data["gameplay_radius"],
                aram_damage_taken=data["aram_dmg_taken"],
                aram_damage_dealt=data["aram_dmg_dealt"],
                aram_healing=data["aram_healing"],
                aram_shielding=data["aram_shielding"],
                urf_damage_taken=data["urf_dmg_taken"],
                urf_damage_dealt=data["urf_dmg_dealt"],
                urf_healing=data["urf_healing"],
                urf_shielding=data["urf_shielding"],
            ),
            roles={
                *(Role.from_string(r), for r in data["role"]),
                Role.from_string(data["herotype"]),
                Role.from_string(data["alttype"]),
            },
            attribute_ratings=AttributeRatings(
                damage=data["damage"],
                toughness=data["toughness"],
                control=data["control"],
                mobility=data["mobility"],
                utility=data["utility"],
                ability_reliance=data["style"],
                attack=data["attack"],
                defense=data["defense"],
                magic=data["magic"],
                difficulty=data["difficulty"],
            ),
            abilities=dict([
                LolWikiDataHandler._render_abilities(data["skill_i"]),
                LolWikiDataHandler._render_abilities(data["skill_q"]),
                LolWikiDataHandler._render_abilities(data["skill_w"]),
                LolWikiDataHandler._render_abilities(data["skill_e"]),
                LolWikiDataHandler._render_abilities(data["skill_r"]),
            ]),
            release_date=data["data"],
            release_patch=data["patch"][1:],  # remove the leading "V"
            patch_last_changed=data["changes"][1:],  # remove the leading "V"
            price=Price(rp=data["rp"], blue_essence=data["be"]),
        )
        # "nickname": "nickname",
        # "disp_name": "dispName",
        return champion

    @staticmethod
    def _render_abilities(inputs: List[Dict]) -> Tuple[str, List[Ability]]:
        abilities = []
        skill_key = inputs[0]["skill"]
        for data in inputs:
            assert data["skill"] == skill_key
            # del data["champion"]
            ability = Ability(
                name=data["name"],
                effects=...,
                cost=LolWikiDataHandler._render_ability_cost(data["cost"]) or LolWikiDataHandler._render_ability_cost(data["Cost"]),
                cooldown=LolWikiDataHandler._render_ability_cooldown(data["cooldown"]),
                targeting=data["targeting"],
                affects=data["affects"],
                spellshieldable=data["spellshield"],
                resource=data["costtype"],
                damageType=data["damagetype"],
                spellEffects=data["spelleffects"],
                projectile=data["projectile"],
                onHitEffects=data["onhiteffects"],
                occurrence=data["occurrence"],
                blurb=data["blurb"],
                notes=data["notes"] if data["notes"] != "* No additional notes." else None,
                missile_speed=data["missile_speed"],
                recharge_rate=data["recharge"],
                collision_radius=data["collision radius"],
                tether_radius=data["tether radius"],
                on_target_cd_static=data["ontargetcdstatic"],
                inner_radius=data["inner radius"],
                speed=data["speed"],
                width=data["width"],
                angle=data["angle"],
                cast_time=data["cast time"],
                effect_radius=data["effect radius"],
                target_range=data["target range"],
            )
            abilities.append(ability)
        return skill_key, abilities

    @staticmethod
    def _render_effects(data: Dict) -> List[Effect]:
        effects = []
        for ending in ['', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']:
            d = f"description{ending}"
            i = f"icon{ending}"
            l = f"leveling{ending}"
            description = data[d] if d in data else None
            icon = data[i] if i in data else None
            leveling = LolWikiDataHandler._render_levelings(data[l]) if l in data else None
            effect = Effect(description=description, icon=icon, leveling=leveling)
            effects.append(effect)
        return effects

    @staticmethod
    def _render_levelings(data: Dict) -> List[Leveling]:
        levelings = []

        map = {
            "customlabel": "customLabel",
            "custominfo": "customInfo",
            "windup_modifier": "windupModifier",
            "static": "staticCooldown",
            "affectedByCDR": "affectedByCDR",
            "attribute": "attribute",
            "values": "values",
            "units": "units",
            "modifiers": "modifiers",
            "secondary attributes": "secondaryAttributes",
        }
        return levelings

    @staticmethod
    def _render_leveling(data: Dict) -> Leveling:
        leveling = Leveling(
            attribute=...,
            modifiers=[Modifier],
        )
        return leveling

    @staticmethod
    def _render_modifier(data: Dict) -> Modifier:
        modifier = Modifier(
            values=...,
            units=...,
        )
        return modifier

    @staticmethod
    def _render_ability_cost(data: Dict) -> Cost:
        cost = Cost(
            modifiers=[Modifier]
        )
        return cost

    @staticmethod
    def _render_ability_cooldown(data: Dict) -> Cooldown:
        cooldown = Cooldown(
            modifiers=[Modifier],
            affected_by_cdr=...,
        )
        return cooldown


def main():
    pass


if __name__ == "__main__":
    main()
