import os
import json

from .pull_items_wiki import WikiItem, get_item_urls
from .pull_items_dragon import DragonItem


def _name_to_wiki(name: str):  # Change item name for wiki url
    url = "https://leagueoflegends.fandom.com/wiki/Template:Item_data_"
    name = name.replace(" ", "_")
    if "Enchantment:" in name:
        name = name.split("Enchantment:")[1]
    wikiUrl = url + name.strip()
    if wikiUrl == "https://leagueoflegends.fandom.com/wiki/Template:Item_data_Blade_of_The_Ruined_King":
        wikiUrl = "https://leagueoflegends.fandom.com/wiki/Template:Item_data_Blade_of_the_Ruined_King"

    if wikiUrl == "https://leagueoflegends.fandom.com/wiki/Template:Item_data_Slightly_Magical_Footware":
        wikiUrl = "https://leagueoflegends.fandom.com/wiki/Template:Item_data_Slightly_Magical_Boots"

    if wikiUrl == "https://leagueoflegends.fandom.com/wiki/Template:Item_data_Kalista's_Black_Spear":
        wikiUrl = "https://leagueoflegends.fandom.com/wiki/Template:Item_data_Black_Spear"

    if wikiUrl == "https://leagueoflegends.fandom.com/wiki/Template:Item_data_Your_Cut":
        wikiUrl = "https://leagueoflegends.fandom.com/wiki/Template:Item_data_%27Your_Cut%27"
    print(wikiUrl)
    wiki_item = WikiItem.get(wikiUrl)
    return wiki_item


def main():
    directory = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))
    use_cache = False
    if not os.path.exists(os.path.join(directory, "items")):
        os.mkdir(os.path.join(directory, "items"))
    ddragon = DragonItem.get_json_ddragon()
    cdragon = DragonItem.get_cdragon()
    jsons = {}
    for d in ddragon:
        if str(d) in (
            "2006",
            "2054",
            "2419",
            "2424",
            "3520",
            "3684",
            "3685",
            "3330",
            "4001",
        ):  # WE NEED TO FIX 2419, 3520(ghost poro)
            continue
        # if str(d) not in "6671":
        #     continue
        if str(d) in ["goose", "goose2"]:
            continue
        else:
            try:
                ddragon_item = DragonItem.get_ddragon(d, ddragon)
            except ValueError:
                continue
            for cdrag in cdragon:
                if str(cdrag["id"]) == d:
                    builds_from = cdrag["from"]
                    builds_to = cdrag["to"]
                    maps = cdrag["mapStringIdInclusions"]
                    ally = cdrag["requiredAlly"]
                    champ = cdrag["requiredChampion"]
            wiki_item = _name_to_wiki(ddragon_item.name)
            # Manual merge
            item = wiki_item
            item.name = ddragon_item.name
            item.id = eval(d)
            item.icon = ddragon_item.icon
            item.builds_from = builds_from
            item.builds_into = builds_to
            item.simple_description = ddragon_item.simple_description
            item.required_ally = ally
            item.required_champion = champ
            item.shop.purchasable = ddragon_item.shop.purchasable

            if item is not None:
                jsonfn = os.path.join(directory, "items", str(item.id) + ".json")
                with open(jsonfn, "w", encoding="utf8") as f:
                    j = item.__json__(indent=2, ensure_ascii=False)
                    f.write(j)
                jsons[item.id] = json.loads(item.__json__(ensure_ascii=False))
                print(item.id)

    jsonfn = os.path.join(directory, "items.json")
    with open(jsonfn, "w", encoding="utf8") as f:
        json.dump(jsons, f, indent=2, ensure_ascii=False)
    del jsons


if __name__ == "__main__":
    main()
    print("Hello! What a surprise, it worked!")
