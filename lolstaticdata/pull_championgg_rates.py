import json
from collections import defaultdict
from bs4 import BeautifulSoup
from lolstaticdata.utils import download_soup


soup = BeautifulSoup(download_soup("https://champion.gg/statistics/", use_cache=False), 'lxml')
scripts = [script.text.strip() for script in soup.find_all("script")]
data = [script for script in scripts if script.startswith("matchupData.stats =")][0]
data = data[len("matchupData.stats ="):].strip()[:-1]
data = json.loads(data)
patch = [script for script in scripts if script.startswith("var currentPatch =")][0]
patch = json.loads(patch[len("var currentPatch ="):].split()[0].strip())
ids = [script for script in scripts if script.startswith("var champData =")][0]
ids = ids[len("var champData ="):].strip().split(";")[0].strip()
ids = json.loads(ids)
ids = {k: int(v) for k, v in ids.items()}

final = defaultdict(dict)
for datum in data:
    id = ids[datum["key"]]
    final[id][datum["role"]] = {"playRate": datum["general"]["playPercent"],
                                          "winRate": datum["general"]["winPercent"],
                                          "banRate": datum["general"]["banRate"]}
final = {"data": final, "patch": patch}

filename = "/home/meraki/code/meraki/Data/champion-rates/rates.json"
with open(filename, 'w') as f:
    json.dump(final, f)

