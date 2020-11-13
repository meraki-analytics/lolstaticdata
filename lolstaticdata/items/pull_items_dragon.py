import json
import os

from ..common.utils import download_json
from .pull_items_wiki import WikiItem
from .modelitem import Item, Shop


class DragonItem:
    @staticmethod
    def get_cdragon():  # cdragon to list
        url = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/items.json"
        j = download_json(url, use_cache=False)
        cdragon = [i for i in j if str(i["id"])]
        return cdragon

    def _get_skin_path(self, path):
        if "/assets/ASSETS" in path:
            path = path.split("ASSETS")[1]
            path = path.lower()
            path = "https://raw.communitydragon.org/pbe/plugins/rcp-be-lol-game-data/global/default/assets" + path

    @classmethod
    def _get_latest_version(cls):
        url = "http://ddragon.leagueoflegends.com/api/versions.json"
        j = download_json(url, use_cache=False)
        return j[0]

    @classmethod
    def get_json_ddragon(
        cls,
    ):  # Main Function, gets items from ddragon, compares them with cdragon and then gets the items from the wiki
        # I didn't want make a request to cdragon for every item
        url = "http://ddragon.leagueoflegends.com/cdn/{}/data/en_US/item.json".format(cls._get_latest_version())
        p = download_json(url, use_cache=True)
        return p["data"]

    @classmethod
    def get_ddragon(cls, ddragon: int, p: dict):
        # print(ddragon)
        baseurl = "http://ddragon.leagueoflegends.com/cdn/{}/img/item/".format(
            cls._get_latest_version()
        )  # icon base url
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
        )
        return item
