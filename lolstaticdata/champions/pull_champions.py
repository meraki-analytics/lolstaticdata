import os
import json
from bs4 import BeautifulSoup

from ..common import utils
from .pull_champions_wiki import LolWikiDataHandler
from .pull_champions_dragons import get_ability_url as _get_ability_url


def get_ability_filenames(url):
    soup = utils.download_soup(url)
    soup = BeautifulSoup(soup, "lxml")

    filenames = []
    for td in soup.findAll("td"):
        a = td.a
        if a is not None:
            fn = a["href"]
            if ".." not in fn:
                filenames.append(fn)
    return filenames


def main():
    handler = LolWikiDataHandler(use_cache=False)
    directory = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))
    if not os.path.exists(os.path.join(directory, "champions")):
        os.mkdir(os.path.join(directory, "champions"))

    # Load some information for pulling champion ability icons
    ddragon_champions = utils.download_json(
        "http://ddragon.leagueoflegends.com/cdn/10.8.1/data/en_US/championFull.json"
    )["data"]
    ability_key_to_identifier = {
        "P": "passive",
        "Q": "q",
        "Q2": "q",
        "W": "w",
        "E": "e",
        "R": "r",
    }

    champions = []
    for champion in handler.get_champions():
        # Load some information for pulling champion ability icons
        if champion.key == "GnarBig":
            champion.key = "Gnar"
        ddragon_champion = ddragon_champions[champion.key]
        ability_icon_filenames = get_ability_filenames(
            f"http://raw.communitydragon.org/latest/game/assets/characters/{champion.key.lower()}/hud/icons2d/"
        )

        for ability_key, abilities in champion.abilities.items():
            for ability_index, ability in enumerate(abilities, start=1):
                url = _get_ability_url(
                    champion.key,
                    ability_key_to_identifier[ability_key],
                    ability_index,
                    ability.name,
                    ddragon_champion,
                    ability_icon_filenames,
                )
                ability.icon = url

        champions.append(champion)
        jsonfn = os.path.join(directory, "champions", str(champion.key) + ".json")
        with open(jsonfn, "w", encoding="utf8") as f:
            f.write(champion.__json__(indent=2, ensure_ascii=False))

    jsonfn = os.path.join(directory, "champions.json")
    jsons = {}
    for champion in champions:
        jsons[champion.key] = json.loads(champion.__json__(ensure_ascii=False))
    with open(jsonfn, "w", encoding="utf8") as f:
        json.dump(jsons, f, indent=2, ensure_ascii=False)
    del jsons


if __name__ == "__main__":
    main()
