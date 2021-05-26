import os
import shutil
import json

from .pull_items_wiki import WikiItem, get_item_urls
from .pull_items_dragon import DragonItem
from collections import OrderedDict


def _name_to_wiki(name: str):  # Change item name for wiki url
    url = "https://leagueoflegends.fandom.com/wiki/Template:Item_data_"
    name = name.replace(" ", "_")
    if "Enchantment:" in name:
        name = name.split("Enchantment:")[1]
    wikiUrl = url + name.strip()
    if wikiUrl == "https://leagueoflegends.fandom.com/wiki/Template:Item_data_Blade_of_The_Ruined_King":
        wikiUrl = "https://leagueoflegends.fandom.com/wiki/Template:Item_data_Blade_of_the_Ruined_King"

    if (
        wikiUrl == "https://leagueoflegends.fandom.com/wiki/Template:Item_data_Slightly_Magical_Footware"
        or wikiUrl == "https://leagueoflegends.fandom.com/wiki/Template:Item_data_Slightly_Magical_Footwear"
    ):
        wikiUrl = "https://leagueoflegends.fandom.com/wiki/Template:Item_data_Slightly_Magical_Boots"

    if wikiUrl == "https://leagueoflegends.fandom.com/wiki/Template:Item_data_Kalista's_Black_Spear":
        wikiUrl = "https://leagueoflegends.fandom.com/wiki/Template:Item_data_Black_Spear"

    if wikiUrl == "https://leagueoflegends.fandom.com/wiki/Template:Item_data_Your_Cut":
        wikiUrl = "https://leagueoflegends.fandom.com/wiki/Template:Item_data_%27Your_Cut%27"
    print(wikiUrl)
    wiki_item = WikiItem.get(wikiUrl)
    return wiki_item


def rewrite():
    directory = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))
    use_cache = False
    if not os.path.exists(os.path.join(directory, "items")):
        os.mkdir(os.path.join(directory, "items"))

    if os.path.exists(os.path.join(directory, "__wiki__")):
        shutil.rmtree(os.path.join(directory, "__wiki__"))

    if not os.path.exists(os.path.join(directory, "__wiki__")):
        os.mkdir(os.path.join(directory, "__wiki__"))
    # ddragon = DragonItem.get_json_ddragon()
    cdragon = DragonItem.get_cdragon()
    wikiItems = get_item_urls(False)

    # print(wikiItems)


    for i in cdragon:
        i["name"] = i["name"].replace("%i:ornnIcon% ", "")
        i["name"] = i["name"].replace("<rarityLegendary>", "")
        if "</rarityLegendary>" in i["name"]:
            i["name"] = i["name"].split("</rarityLegendary>")[0]
    jsons = {}
    for x in wikiItems:
        if x not in ["goose", "goose1"]:
            continue
        else:
            item = None
            print(x)
            # try:
            #     cdragon_item = DragonItem.get_item_cdragon(d, ddragon)
            # except ValueError:
            #     continue
            if x == "'Your Cut'":
                x = "Your Cut"
                # l = [d for d in cdragon if x.upper() == d["name"].upper()]
                l = list(filter(lambda d: d["name"].upper() == x.upper(), cdragon))
                x = "'Your Cut'"
            elif x == "Slightly Magical Boots":
                if list(filter(lambda d: d["name"].upper() == x.upper(), cdragon)):
                    l = list(filter(lambda d: d["name"].upper() == x.upper(), cdragon))
                else:
                    x = "Slightly Magical Footwear"
                    # l = [d for d in cdragon if x.upper() == d["name"].upper()]
                    l = list(filter(lambda d: d["name"].upper() == x.upper(), cdragon))
                    x = "Slightly Magical Boots"
            else:
                # l = [d for d in cdragon if x.upper() == d["name"].upper()]
                l = list(filter(lambda d: d["name"].upper() == x.upper(), cdragon))

            if len(l) >= 1:
                for i in l:

                    cdrag_item = DragonItem.get_item_cdragon(i)
                    wiki_item = _name_to_wiki(x)
                    item = wiki_item
                    item.icon = cdrag_item.icon
                    item.id = int(cdrag_item.id)
                    item.builds_from = cdrag_item.builds_from
                    item.builds_into = cdrag_item.builds_into
                    item.simple_description = cdrag_item.simple_description
                    item.required_ally = cdrag_item.required_ally
                    item.required_champion = cdrag_item.required_champion
                    item.shop.purchasable = cdrag_item.shop.purchasable
                    item.special_recipe = cdrag_item.special_recipe
                    if item.iconOverlay == True:
                        item.iconOverlay = (
                            "http://raw.communitydragon.org/latest/game/data/items/icons2d/bordertreatmentornn.png"
                        )
                    else:
                        item.iconOverlay = False
                    if item is not None:
                        jsonfn = os.path.join(directory, "items", str(item.id) + ".json")
                        with open(jsonfn, "w", encoding="utf8") as f:
                            j = item.__json__(indent=2, ensure_ascii=False)
                            f.write(j)
                        jsons[int(item.id)] = json.loads(item.__json__(ensure_ascii=False))
                        print(item.id)
    if os.path.exists(os.path.join(directory, "__wiki__")):
        shutil.rmtree(os.path.join(directory, "__wiki__"))
    jsonfn = os.path.join(directory, "items.json")
    jsons = OrderedDict(sorted(jsons.items(), key=lambda x: x[1]["id"]))
    with open(jsonfn, "w", encoding="utf8") as f:
        json.dump(jsons, f, indent=2, ensure_ascii=False)
    del jsons

def rewrite_rewrite():
    #Wiki changed a lot. Items are very different

    directory = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))
    use_cache = False
    if not os.path.exists(os.path.join(directory, "items")):
        os.mkdir(os.path.join(directory, "items"))

    if os.path.exists(os.path.join(directory, "__wiki__")):
        shutil.rmtree(os.path.join(directory, "__wiki__"))

    if not os.path.exists(os.path.join(directory, "__wiki__")):
        os.mkdir(os.path.join(directory, "__wiki__"))
    # ddragon = DragonItem.get_json_ddragon()
    cdragon = DragonItem.get_cdragon()
    wikiItems = get_item_urls(False)

    # print(wikiItems)

    for i in cdragon:
        i["name"] = i["name"].replace("%i:ornnIcon% ", "")
        i["name"] = i["name"].replace("<rarityLegendary>", "")
        if "</rarityLegendary>" in i["name"]:
            i["name"] = i["name"].split("</rarityLegendary>")[0]
    jsons = {}
    for name,data in wikiItems.items():
        if name in ["goose", "goose1"]:
            continue
        else:
            item = None
            print(name)
            # try:
            #     cdragon_item = DragonItem.get_item_cdragon(d, ddragon)
            # except ValueError:
            #     continue
            if name == "'Your Cut'":
                name = "Your Cut"
                # l = [d for d in cdragon if x.upper() == d["name"].upper()]
                l = list(filter(lambda d: d["name"].upper() == name.upper(), cdragon))
                name = "'Your Cut'"
            elif name == "Slightly Magical Boots":
                if list(filter(lambda d: d["name"].upper() == name.upper(), cdragon)):
                    l = list(filter(lambda d: d["name"].upper() == name.upper(), cdragon))
                else:
                    name = "Slightly Magical Footwear"
                    # l = [d for d in cdragon if x.upper() == d["name"].upper()]
                    l = list(filter(lambda d: d["name"].upper() == name.upper(), cdragon))
                    name = "Slightly Magical Boots"
            else:
                # l = [d for d in cdragon if x.upper() == d["name"].upper()]
                l = list(filter(lambda d: d["name"].upper() == name.upper(), cdragon))

            if len(l) >= 1:
                for i in l:

                    cdrag_item = DragonItem.get_item_cdragon(i)
                    wiki_item = WikiItem._parse_item_data(data,name,wikiItems)
                    item = wiki_item
                    item.icon = cdrag_item.icon
                    item.id = int(cdrag_item.id)
                    item.builds_from = cdrag_item.builds_from
                    item.builds_into = cdrag_item.builds_into
                    item.simple_description = cdrag_item.simple_description
                    item.required_ally = cdrag_item.required_ally
                    item.required_champion = cdrag_item.required_champion
                    item.shop.purchasable = cdrag_item.shop.purchasable
                    item.special_recipe = cdrag_item.special_recipe
                    if item.iconOverlay == True:
                        item.iconOverlay = (
                            "http://raw.communitydragon.org/latest/game/data/items/icons2d/bordertreatmentornn.png"
                        )
                    else:
                        item.iconOverlay = False
                    if item is not None:
                        jsonfn = os.path.join(directory, "items", str(item.id) + ".json")
                        with open(jsonfn, "w", encoding="utf8") as f:
                            j = item.__json__(indent=2, ensure_ascii=False)
                            f.write(j)
                        jsons[int(item.id)] = json.loads(item.__json__(ensure_ascii=False))
                        print(item.id)
    if os.path.exists(os.path.join(directory, "__wiki__")):
        shutil.rmtree(os.path.join(directory, "__wiki__"))
    jsonfn = os.path.join(directory, "items.json")
    jsons = OrderedDict(sorted(jsons.items(), key=lambda x: x[1]["id"]))
    with open(jsonfn, "w", encoding="utf8") as f:
        json.dump(jsons, f, indent=2, ensure_ascii=False)
    del jsons


if __name__ == "__main__":
    rewrite_rewrite()
    print("Hello! What a surprise, it worked!")
