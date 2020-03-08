from utils import download_json
from modelitem import Item


class DDragonItem:
    @classmethod
    def _get_latest_version(cls):
        url = "http://ddragon.leagueoflegends.com/api/versions.json"
        j = download_json(url, use_cache=True)
        return j[0]

    @classmethod
    def _get_icon(cls, id: str):
        base_url = "http://ddragon.leagueoflegends.com/cdn/{}/img/item/".format(cls._get_latest_version())
        item_url = base_url + id
        return item_url

    @classmethod
    def get(cls, id: int) -> Item:
        base_url = "http://ddragon.leagueoflegends.com/cdn/{}/data/en_US/item.json".format(cls._get_latest_version())
        item_data = download_json(base_url, use_cache=True)
        builds = []
        recipes = []
        item = item_data["data"][str(id)]
        try:
            for x in item["into"]:
                builds.append(int(x))
        except:
            builds = []
        try:
            for x in item["from"]:
                recipes.append(int(x))
        except:
            recipes = []
        icon = cls._get_icon(item["image"]["full"])
        item = Item(builds_from=recipes, builds_into=builds, icon=icon, name=None, id=None, tier=None, no_effects=None, removed=None, nicknames=None, passives=None, active=None, stats=None, shop=None)
        return item


class CDragonItem:
    @classmethod
    def get(cls, id: int) -> Item:
        url = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/items.json"
        j = download_json(url, use_cache=True)
        for i in j:
            if i["id"] == str(id):
                builds = []
                recipes = []
                try:
                    for x in i["to"]:
                        builds.append(x)
                        print(x)
                except:
                    builds = []
                try:
                    for x in i["from"]:
                        recipes.append(x)
                        print(x)
                except:
                    recipes = []
                icon = "https://raw.communitydragon.org/latest/game/data/items/icons2d" + i["iconPath"].split("Icons2D")[1].lower()
                item = Item(builds_from=recipes, builds_into=builds, icon=icon, name=None, id=None, tier=None, no_effects=None, removed=None, nicknames=None, passives=None, active=None, stats=None, shop=None)
                return item
