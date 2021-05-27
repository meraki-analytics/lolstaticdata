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
    data2 = requests.get("https://apix1.op.lol/tierlist/7/?lane=default&patch={}&tier=platinum_plus&queue=420&region=all".format(patch)).json()
    totalPicked = data2["pick"]
   # data = requests.get("https://flash.blitz.gg/graphql?query=" + urllib.parse.quote(query, safe="/()=&")).json()["data"]["lolChampionsListOverview"]

    role_name_map = {"TOP": "TOP", "JUNGLE": "JUNGLE", "MID": "MIDDLE", "ADC": "BOTTOM", "SUPPORT": "UTILITY"}
    roles = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]

    final = {}
    for datum in data2["cid"]:
        id = datum
        roleId = data2["cid"][datum][1]
        role = roles[roleId-1]
        wins = data2["cid"][datum][3]
        totalChamp = data2["cid"][datum][4]

        final[id] = {
            role: {
                "playRate": round(totalChamp/totalPicked,2),
                "winRate": round(wins/totalChamp,2),
                "banRate": data2["cid"][datum][6],
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
