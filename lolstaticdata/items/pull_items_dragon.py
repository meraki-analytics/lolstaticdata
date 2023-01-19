import json
import os

from ..common.utils import download_json
from .pull_items_wiki import WikiItem
from .modelitem import Item, Shop


def get_latest_version():
    url = "http://ddragon.leagueoflegends.com/api/versions.json"
    j = download_json(url, use_cache=False)
    return j[0]


class DragonItem:
    latest_version = get_latest_version()
    version = latest_version.split(".")
    version = str(version[0]) + "." + str(version[1])

    @staticmethod
    def get_cdragon():  # cdragon to list

        url = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/items.json"

        j = download_json(url, use_cache=False)
        cdragon = [i for i in j if str(i["id"])]
        return cdragon

    @staticmethod
    def get_item_plaintext(item):
        url = f"https://raw.communitydragon.org/{DragonItem.version}/game/data/menu/main_en_us.stringtable.json"
        j = download_json(url, use_cache=True)
        try:
            return j['entries']["game_item_plaintext_" + str(item)]
        except:
            return None

    @classmethod
    def get_item_cdragon(cls, cdrag):

        builds_from = []
        builds_to = []
        ally = None
        champ = None
        purchasable = None
        cdragid = None
        icon = ""
        builds_from = cdrag["from"]
        builds_to = cdrag["to"]
        ally = cdrag["requiredAlly"]
        special_recipe = cdrag["specialRecipe"]
        champ = cdrag["requiredChampion"]
        purchasable = cdrag["inStore"]
        cdragid = cdrag["id"]
        icon = cdrag["iconPath"]
        plaintext = cls.get_item_plaintext(cdragid)
        shop = Shop(purchasable=purchasable, prices=[], tags=[])
        item = Item(
            builds_from=builds_from,
            builds_into=builds_to,
            icon=cls._get_skin_path(icon),
            name="",
            id=cdragid,
            tier=[],
            no_effects=[],
            removed=[],
            required_ally=ally,
            required_champion=champ,
            simple_description=plaintext,
            nicknames=[],
            passives=[],
            active=[],
            stats=[],
            shop=shop,
            rank="",
            special_recipe=special_recipe,
            iconOverlay=None,
        )
        return item

    @classmethod
    def _get_skin_path(cls, path):

        if path is not None:

            if "/assets/ASSETS" in path:
                path = path.split("ASSETS")[1]
                path = path.lower()
                path = (
                    "https://raw.communitydragon.org/{}/plugins/rcp-be-lol-game-data/global/default/assets".format(
                        DragonItem.version
                    )
                    + path
                )
                return path
        else:
            return None

    @classmethod
    def get_json_ddragon(
        cls,
    ):  # Main Function, gets items from ddragon, compares them with cdragon and then gets the items from the wiki
        # I didn't want make a request to cdragon for every item
        url = "http://ddragon.leagueoflegends.com/cdn/{}/data/en_US/item.json".format(get_latest_version())
        p = download_json(url, use_cache=True)
        return p["data"]

    @classmethod
    def get_ddragon(cls, ddragon: int, p: dict):
        # print(ddragon)
        baseurl = "http://ddragon.leagueoflegends.com/cdn/{}/img/item/".format(get_latest_version())  # icon base url
        icon = baseurl + p[ddragon]["image"]["full"]
        plaintext = p[ddragon]["plaintext"]  # simple description
        purchasable = p[ddragon]["gold"]["purchasable"]  # is this purchasable or is it upgraded (seraph's embrace)
        name = p[ddragon]["name"]
        if str(ddragon) in "2423":  # stopwatch needs to be fixed for the wiki
            name = "Stopwatch"
        if name in (
            "Warding Totem (Trinket)",
            "Greater Stealth Totem (Trinket)",
            "Greater Vision Totem (Trinket)",
        ):
            name = "Warding Totem"  # stupid names
        shop = Shop(purchasable=purchasable, prices=[], tags=[])
        item = Item(
            builds_from=[],
            builds_into=[],
            icon=icon,
            name=name,
            id=ddragon,
            tier=[],
            no_effects=[],
            removed=[],
            required_ally="",
            required_champion="",
            simple_description=plaintext,
            nicknames=[],
            passives=[],
            active=[],
            stats=[],
            shop=shop,
            rank="",
        )
        return item
