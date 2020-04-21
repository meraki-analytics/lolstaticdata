import json
from collections import defaultdict
from bs4 import BeautifulSoup
from ..common.utils import download_soup


def main():
    soup = BeautifulSoup(download_soup("https://champion.gg/statistics/", use_cache=False), "lxml")
    scripts = [script.text.strip() for script in soup.find_all("script")]
    data = [script for script in scripts if script.startswith("matchupData.stats =")][0]
    data = data[len("matchupData.stats =") :].strip()[:-1]
    data = json.loads(data)
    patch = [script for script in scripts if script.startswith("var currentPatch =")][0]
    patch = json.loads(patch[len("var currentPatch =") :].split()[0].strip())
    ids = [script for script in scripts if script.startswith("var champData =")][0]
    ids = ids[len("var champData =") :].strip().split(";")[0].strip()
    ids = json.loads(ids)
    ids = {k: int(v) for k, v in ids.items()}

    role_name_map = {"Top": "TOP", "Jungle": "JUNGLE", "Middle": "MIDDLE", "ADC": "BOTTOM", "Support": "UTILITY"}

    final = defaultdict(dict)
    for datum in data:
        id = ids[datum["key"]]
        role = role_name_map[datum["role"]]
        final[id][role] = {
            "playRate": datum["general"]["playPercent"],
            "winRate": datum["general"]["winPercent"],
            "banRate": datum["general"]["banRate"],
        }
    final = {"data": final, "patch": patch}
    for id in ids.values():
        if id not in final["data"]:
            final["data"][id] = {}

    filename = "/home/meraki/code/meraki/Data/champion-rates/rates.json"
    with open(filename, "w") as f:
        json.dump(final, f)


if __name__ == "__main__":
    main()
