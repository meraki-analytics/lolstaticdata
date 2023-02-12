import os
import shutil
import json

from .pull_items_wiki import WikiItem, get_item_urls
from .pull_items_dragon import DragonItem
from collections import OrderedDict

def main():
    directory = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))
    if not os.path.exists(os.path.join(directory, "items")):
        os.mkdir(os.path.join(directory, "items"))

    if os.path.exists(os.path.join(directory, "__wiki__")):
        shutil.rmtree(os.path.join(directory, "__wiki__"))

    if not os.path.exists(os.path.join(directory, "__wiki__")):
        os.mkdir(os.path.join(directory, "__wiki__"))
    cdragon = DragonItem.get_cdragon()
    wikiItems = get_item_urls(False)

    jsons = {}
    for name,data in wikiItems.items():
        item = None
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
                print(item.id)
    if os.path.exists(os.path.join(directory, "__wiki__")):
        shutil.rmtree(os.path.join(directory, "__wiki__"))
    jsonfn = os.path.join(directory, "items.json")
    jsons = OrderedDict(sorted(jsons.items(), key=lambda x: x[1]["id"]))
    with open(jsonfn, "w", encoding="utf8") as f:
        json.dump(jsons, f, indent=2, ensure_ascii=False)
    del jsons


if __name__ == "__main__":
    main()
    print("Hello! What a surprise, it worked!")
