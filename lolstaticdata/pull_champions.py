import os
import json

from pull_champions_wiki import LolWikiDataHandler


def main():
    handler = LolWikiDataHandler(use_cache=False)
    directory = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
    if not os.path.exists(os.path.join(directory,"champions")):
        os.mkdir(os.path.join(directory,"champions"))

    champions = []
    for champion in handler.get_champions():
        champions.append(champion)
        jsonfn = os.path.join(directory,"champions",str(champion.key) + ".json")
        with open(jsonfn, 'w', encoding='utf8') as f:
            f.write(champion.__json__(indent=2, ensure_ascii=False))

    jsonfn = os.path.join(directory, "champions.json")
    jsons = {}
    for champion in champions:
        jsons[champion.key] = json.loads(champion.__json__(ensure_ascii=False))
    with open(jsonfn, 'w', encoding='utf8') as f:
        json.dump(jsons, f, indent=2, ensure_ascii=False)
    del jsons


if __name__ == "__main__":
    main()
