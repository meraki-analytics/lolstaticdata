import os
import json
import time
import argparse
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


def main(champion: str | None = None, stats: bool = False, abilities: bool = False, skins: bool = False, lore: bool = False):
    """
    Args:
        champion: If provided, process only this champion
        stats: If True, process champion stats
        abilities: If True, process champion abilities
        skins: If True, process champion skins
        lore: If True, process champion lore and faction
    """
    def print_runtime(): 
        elapsed_seconds = end_time - start_time
        minutes = int(elapsed_seconds // 60)
        seconds = int(elapsed_seconds % 60)
        print(f"Champions parser completed in {minutes}m {seconds}s")

    process_all = not (stats or skins or lore or abilities)
    if process_all:
        stats = skins = lore = abilities = True

    start_time = time.time()
    directory = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))
    if not os.path.exists(os.path.join(directory, "champions")):
        os.mkdir(os.path.join(directory, "champions"))

    handler = LolWikiDataHandler(
        use_cache=False,
        target_champion=champion,
        process_stats=stats or process_all,
        process_abilities=abilities or process_all,
        process_skins=skins or process_all,
    )

    latest_version = utils.get_latest_patch_version()
    ddragon_champions = utils.download_json(
        f"http://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/championFull.json"
    )["data"]

    factions = {}
    if lore or process_all:
        try:
            universe_stats = utils.download_json(
                "https://universe-meeps.leagueoflegends.com/v1/en_us/champion-browse/index.json",
                False
            )["champions"]

            for universe_entry in universe_stats:
                factions[universe_entry["slug"]] = universe_entry["associated-faction-slug"]
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
        champion_key = champion.key

        if champion_key not in ddragon_champions:
            print(f"WARNING: Skipping champion '{champion_key}' (not present in Data Dragon metadata).")
            continue

        ddragon_champion = ddragon_champions[champion_key]

        champion.icon = (
            f"http://ddragon.leagueoflegends.com/cdn/{latest_version}/img/champion/{ddragon_champion['image']['full']}"
        )

        if lore or process_all:
            champion.lore = ddragon_champion["lore"]
            champion.faction = factions[champion_key.lower()] if champion_key.lower() in factions else ""
            # Fix faction bug for e.g. Renata Glasc
            if champion.faction == "" and champion.name.lower().replace(" ","") in factions:
                champion.faction = factions[champion.name.lower().replace(" ","")]

        if (abilities or process_all) and champion.abilities:
            ability_icon_filenames = get_ability_filenames(
                f"http://raw.communitydragon.org/latest/game/assets/characters/{champion_key.lower()}/hud/icons2d/"
            )
            for ability_key, abilities_list in champion.abilities.items():
                for ability_index, ability in enumerate(abilities_list, start=1):
                    url = _get_ability_url(
                        champion_key,
                        ability_key_to_identifier[ability_key],
                        ability_index,
                        ability.name,
                        latest_version,
                        ddragon_champion,
                        ability_icon_filenames,
                    )
                    ability.icon = url

        champion_payload = json.loads(champion.__json__(ensure_ascii=False))
        if not stats:
            champion_payload.pop("stats", None)
        if not abilities:
            champion_payload.pop("abilities", None)
        if not skins:
            champion_payload.pop("skins", None)
        if not lore:
            champion_payload.pop("lore", None)
            champion_payload.pop("faction", None)

        champions.append(champion_payload)
        jsonfn = os.path.join(directory, "champions", str(champion_key) + ".json")
        with open(jsonfn, "w", encoding="utf8") as f:
            json.dump(champion_payload, f, indent=2, ensure_ascii=False)

    if champion and not champions:
        end_time = time.time()
        print_runtime()
        print(f"WARNING: Champion '{champion}' was not found. Try the exact in-game name, e.g. \"Jarvan IV\".")
        return

    jsonfn = os.path.join(directory, "champions.json")
    jsons = {payload["key"]: payload for payload in champions}
    with open(jsonfn, "w", encoding="utf8") as f:
        json.dump(jsons, f, indent=2, ensure_ascii=False)
    del jsons

    end_time = time.time()
    print_runtime()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process League of Legends champion data")
    parser.add_argument(
        "--champion",
        type=str,
        help="Process a single champion by name (case-insensitive; spaces/apostrophes optional)",
    )
    parser.add_argument("--stats", action="store_true", help="Process champion stats")
    parser.add_argument("--skins", action="store_true", help="Process champion skins")
    parser.add_argument("--lore", action="store_true", help="Process champion lore")
    parser.add_argument("--abilities", action="store_true", help="Process champion abilities")

    args = parser.parse_args()
    main(
        champion=args.champion,
        stats=args.stats,
        abilities=args.abilities,
        skins=args.skins,
        lore=args.lore,
    )
