import os
import json
from bs4 import BeautifulSoup

from ..common import utils
from .pull_champions_wiki import LolWikiDataHandler
from .pull_champions_dragons import get_ability_url as _get_ability_url


def get_ability_filenames(url):
    soup = utils.download_soup(url, use_cache=False)
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
    latest_version = utils.get_latest_patch_version()
    ddragon_champions = utils.download_json(
        f"http://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/championFull.json"
    )["data"]

    # Load a list of champions from universe.leagueoflegends.com => added request fail detection because of unreliable source
    factions = {}
    try:
        universe_stats = utils.download_json(
            "https://universe-meeps.leagueoflegends.com/v1/en_us/champion-browse/index.json",
            False
        )["champions"]

        for champion in universe_stats:
            factions[champion["slug"]] = champion["associated-faction-slug"]
    except Exception:
        print("ERROR: Unable to load/parse universe file, location may have changed")

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
        ddragon_champion = ddragon_champions[champion.key]
        ability_icon_filenames = get_ability_filenames(
            f"http://raw.communitydragon.org/latest/game/assets/characters/{champion.key.lower()}/hud/icons2d/"
        )

        # Set the champion icon
        champion.icon = (
            f"http://ddragon.leagueoflegends.com/cdn/{latest_version}/img/champion/{ddragon_champion['image']['full']}"
        )

        # Set the lore
        champion.lore = ddragon_champion["lore"]

        # Set the faction
        champion.faction = factions[champion.key.lower()] if champion.key.lower() in factions else ""

        # Fix faction bug for e.g. renata
        if champion.faction == "" and champion.name.lower().replace(" ","") in factions:
            champion.faction = factions[champion.name.lower().replace(" ","")]

        # Set the champion ability icons
        for ability_key, abilities in champion.abilities.items():
            for ability_index, ability in enumerate(abilities, start=1):
                url = _get_ability_url(
                    champion.key,
                    ability_key_to_identifier[ability_key],
                    ability_index,
                    ability.name,
                    latest_version,
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
