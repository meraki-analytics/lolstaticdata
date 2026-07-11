import os
import shutil
import json
import requests

from .pull_items_wiki import WikiItem, get_item_urls
from .pull_items_dragon import DragonItem
from collections import OrderedDict
from ..common.utils import print_error

def main():
    directory = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))
    try:
        latest_version = DragonItem.get_latest_version()
    except requests.exceptions.RequestException as e:
        print_error(f"Unable to determine latest patch version from Data Dragon: {e}")
        return False
    print(f"Fetching Item data for patch version: {latest_version}")
    if not os.path.exists(os.path.join(directory, "items")):
        os.mkdir(os.path.join(directory, "items"))

    if os.path.exists(os.path.join(directory, "__wiki__")):
        shutil.rmtree(os.path.join(directory, "__wiki__"))

    if not os.path.exists(os.path.join(directory, "__wiki__")):
        os.mkdir(os.path.join(directory, "__wiki__"))
    try:
        cdragon = DragonItem.get_cdragon()
    except requests.exceptions.RequestException as e:
        print_error(f"Unable to load CommunityDragon items list: {e}")
        return False
    wikiItems = get_item_urls(False)

    jsons = {}
    for name,data in wikiItems.items():
        item = None
        if "id" in data:
          print(data["id"], name)
        else: 
          print(name)
        l = [x for x in cdragon if "id" in data and x["id"] == data["id"]]

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
    if os.path.exists(os.path.join(directory, "__wiki__")):
        shutil.rmtree(os.path.join(directory, "__wiki__"))
    jsonfn = os.path.join(directory, "items.json")
    jsons = OrderedDict(sorted(jsons.items(), key=lambda x: x[1]["id"]))
    with open(jsonfn, "w", encoding="utf8") as f:
        json.dump(jsons, f, indent=2, ensure_ascii=False)
    del jsons
    return True


if __name__ == "__main__":
    if main():
        print("Hello! What a surprise, it worked!")
