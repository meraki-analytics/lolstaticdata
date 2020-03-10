from utils import download_json
from lolstaticdata.pull_items_wiki import WikiItem
from modelitem import Item
import json
import os

class DDragonItem:



    @staticmethod
    def get_cdragon():#cdragon to list
        url = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/items.json"
        j = download_json(url, use_cache=True)
        cdragon = [i for i in j if str(i["id"])]
        print(cdragon)
        return cdragon

    @staticmethod
    def _name_to_wiki(name : str): #Change item name for wiki url
        url = "https://leagueoflegends.fandom.com/wiki/Template:Item_data_"
        name = name.replace(" ", "_")
        if "Enchantment:" in name:
            name = name.split("Enchantment:")[1]
        wikiUrl = url + name.strip()
        print(wikiUrl)
        wiki_item = WikiItem.get(wikiUrl)
        return wiki_item


    @classmethod
    def _get_latest_version(cls):
        url = "http://ddragon.leagueoflegends.com/api/versions.json"
        j = download_json(url, use_cache=True)
        return j[0]


    @classmethod
    def get_ddragon(cls): #Main Function, gets items from ddragon, compares them with cdragon and then gets the items from the wiki
        jsons = {}
        cdragon = cls.get_cdragon() #I didn't want make a request to cdragon for every item
        directory = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
        if not os.path.exists(os.path.join(directory, "items")):
            os.mkdir(os.path.join(directory, "items"))
        url = "http://ddragon.leagueoflegends.com/cdn/{}/data/en_US/item.json".format(cls._get_latest_version())
        p = download_json(url, use_cache=True)
        for ddragon in p["data"]: #gets the item id, excluded a couple because they aren't in the wiki
            if str(ddragon) in ("2006", "2054", '2419', '2424', "3520", "3684", "3685"): # WE NEED TO FIX 2419, 3520(ghost poro)
                print("Should error")
                continue
            for cdrag in cdragon:#for item in the cdragon json, grab build info, map info, required ally and champ info
                if str(cdrag["id"]) == ddragon:
                    builds_from = cdrag["from"]
                    builds_to = cdrag["to"]
                    maps = cdrag["mapStringIdInclusions"]
                    ally = cdrag["requiredAlly"]
                    champ = cdrag["requiredChampion"]
            baseurl = "http://ddragon.leagueoflegends.com/cdn/{}/img/item/".format(cls._get_latest_version()) #icon base url
            icon = baseurl + p["data"][ddragon]["image"]["full"]
            plaintext = p["data"][ddragon]["plaintext"] #simple description
            purchasable = p["data"][ddragon]["gold"]["purchasable"]#is this purchasable or is it upgraded (seraph's embrace)
            name = p["data"][ddragon]["name"]
            print(name)
            if str(ddragon) in "2423": #stopwatch needs to be fixed for the wiki
                name = "Stopwatch"
            if name in ("Warding Totem (Trinket)", "Greater Stealth Totem (Trinket)", "Greater Vision Totem (Trinket)"):
                name = "Warding Totem" #stupid names

            print(name)
            wiki = cls._name_to_wiki(name) #get wiki information
            item = Item(builds_from=builds_from, builds_into=builds_to, icon=icon, name=p["data"][ddragon]["name"],
                        id=ddragon, tier=wiki.tier, no_effects=wiki.no_effects,
                        removed=wiki.removed, nicknames=wiki.nicknames, passives=wiki.passives, active=wiki.active,
                        stats=wiki.stats, shop=wiki.shop)

            if item is not None:
                jsonfn = os.path.join(directory, "items", str(item.id) + ".json")
                with open(jsonfn, 'w', encoding='utf8') as f:
                    j = item.__json__(indent=2, ensure_ascii=False)
                    f.write(j)
                jsons[item.id] = json.loads(item.__json__(ensure_ascii=False))
                print(item.id)


        jsonfn = os.path.join(directory, "items.json")
        with open(jsonfn, 'w', encoding='utf8') as f:
            json.dump(jsons, f, indent=2, ensure_ascii=False)
        del jsons






DDragonItem.get_ddragon()