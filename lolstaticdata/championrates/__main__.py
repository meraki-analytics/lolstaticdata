import json
import requests
import urllib.parse
import cassiopeia as cass

from ..common.utils import download_soup


def main():
    patch = cass.Patch.latest(region="NA")
    query = """query ($region: String, $language: String, $queue: Int, $tier: String, $role: String, $patch: String) {{
  lolChampionsListOverview(region: $region, language: $language, queue: $queue, tier: $tier, role: $role, patch: $patch) {{
    champion_id
    champion {{
      name
      key
    }}
    role
    tier
    stats {{
      winRate
      pickRate
      banRate
      games
    }}
  }}
}}
&variables={{"language":"en","role":"ALL","region":"world","queue":420,"tier":"PLATINUM_PLUS","patch":"{patch}"}}
""".format(patch=patch.name)
    data = requests.get("https://flash.blitz.gg/graphql?query=" + urllib.parse.quote(query, safe="/()=&")).json()["data"]["lolChampionsListOverview"]

    role_name_map = {"TOP": "TOP", "JUNGLE": "JUNGLE", "MID": "MIDDLE", "ADC": "BOTTOM", "SUPPORT": "UTILITY"}

    final = {}
    for datum in data:
        id = datum["champion_id"]
        role = role_name_map[datum["role"]]
        final[id] = {
            role: {
                "playRate": datum["stats"]["pickRate"],
                "winRate": datum["stats"]["winRate"],
                "banRate": datum["stats"]["banRate"],
            }
        }
    for champion in cass.get_champions(region="NA"):
        if champion.id not in final:
            final[champion.id] = {}

    final = {"data": final, "patch": patch.name}


    filename = "/home/meraki/code/meraki/Data/champion-rates/rates.json"
    with open(filename, "w") as f:
        json.dump(final, f)


if __name__ == "__main__":
    main()
