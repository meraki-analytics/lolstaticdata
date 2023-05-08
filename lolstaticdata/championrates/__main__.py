import json
import re
import requests

def main():
    all_meraki_roles = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
    all_json_roles = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "SUPPORT"]
    all_champs = {}
    data = requests.get("https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-champion-statistics/global/default/rcp-fe-lol-champion-statistics.js")
    champs = requests.get("https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-summary.json").json()
    # all_champs = {str(champ['id']): {meraki_role: {"playRate": 0, "banRate": 0, "winRate": 0} for meraki_role in all_meraki_roles} for champ in champs if champ['id'] != -1}
    all_champs = {str(champ['id']): {meraki_role: {"playRate": 0} for meraki_role in all_meraki_roles} for champ in champs if champ['id'] != -1}
    for meraki_role, json_role in zip(all_meraki_roles, all_json_roles):
        matches = re.findall(json_role + r"\":(.*?})", data.text)
        if len(matches) > 0:
            match = matches[0]
            # roles = json.loads(match)
            roles = {key.replace('"', ''): float(value) for key, value in [pair.split(":") for pair in match.replace(" ", "")[1:-1].split(",")]}  # Do a manual JSON.loads because the keys aren't in parentheses.
            for champion, rate in roles.items():
                all_champs[champion][meraki_role]['playRate'] = round(rate * 100, 5)

    version_split = requests.get("https://raw.communitydragon.org/latest/content-metadata.json").json()["version"].split(".")
    version = version_split[0] + "." + version_split[1]

    with open("/home/meraki/code/meraki/Data/champion-rates/rates.json", "w") as f:
        json.dump({"data":all_champs,"patch":version}, f)

if __name__ == "__main__":
    main()

