import requests
import json
from modelitem import Dragon


class ddragon:
    @classmethod
    def get_version(cls):
        url = "http://ddragon.leagueoflegends.com/api/versions.json"
        r = requests.get(url)
        r = r.json()
        return r[0]

    @classmethod
    def _get_icon(cls,id:str):
        base_url = "http://ddragon.leagueoflegends.com/cdn/{}/img/item/".format(cls.get_version())
        item_url = base_url + id
        return item_url


    @classmethod
    def _get_item_ddragon(cls, id):
        base_url = "http://ddragon.leagueoflegends.com/cdn/{}/data/en_US/item.json".format(cls.get_version())
        itemData = requests.get(base_url)
        itemData = itemData.json()
        builds = []
        recipes = []
        item = itemData["data"][id]
        try:
            for x in item["to"]:
                builds.append(eval(x))
        except:
            builds = []
        try:
            for x in item["from"]:
                recipes.append(eval(x))
        except:
            recipes = []
        icon = cls._get_icon(item["image"]["full"])
        return recipes, builds, icon


class cdragon:
    @classmethod
    def _get_item_cdragon(cls, id: int):
        url = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/items.json"
        c = requests.get(url)
        c = c.json()
        for i in c:
           if i["id"] == id:
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
               icon="https://raw.communitydragon.org/latest/game/data/items/icons2d" + i["iconPath"].split("Icons2D")[1].lower()
               return recipes, builds, icon



