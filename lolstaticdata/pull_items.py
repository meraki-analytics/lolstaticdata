import os
import json

from lolstaticdata.pull_items_wiki import WikiItem, get_item_urls
from pull_items_dragon import DDragonItem


def main():
    directory = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
    use_cache = True
    if not os.path.exists(os.path.join(directory, "items")):
        os.mkdir(os.path.join(directory, "items"))
    item_urls = get_item_urls(use_cache)
    jsons = {}
    for url in item_urls:
        print(url)
        try:
            wiki_item = WikiItem.get(url)
        except ValueError:
            continue
        if wiki_item.removed:
            continue
        ddragon_item = DDragonItem.get(wiki_item.id)
        #cdragon_item = CDragonItem.get(wiki_item.id)

        # Manual merge
        item = wiki_item
        item.icon = ddragon_item.icon
        item.builds_from = ddragon_item.builds_from
        item.builds_into = ddragon_item.builds_into

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


if __name__ == "__main__":
    main()
