import json
import re
import requests

def main():
    all_champs = {}
    data = requests.get("https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-champion-statistics/global/default/rcp-fe-lol-champion-statistics.js")
    matches = re.findall('.exports=({.*)},', data.text)
    if len(matches) > 0:
        match = matches[0]
        match = re.sub("([A-Z0-9]*):", r'"\1":', match)
        match = re.sub("\.([0-9]*)", r'0.\1', match)
        roles = json.loads(match)
        champs = requests.get("https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-summary.json").json()
        all_roles = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
        all_champs = {str(champ['id']):{role:{"playRate": 0, "banRate": 0, "winRate": 0} for role in all_roles} for champ in champs if champ['id'] != -1}
        for role in all_roles:
            for champion, rate in roles["SUPPORT" if role == "UTILITY" else role].items():
                all_champs[champion][role]['playRate'] = round(rate * 100, 5)

    version_split = requests.get("https://raw.communitydragon.org/latest/content-metadata.json").json()["version"].split(".")
    version = version_split[0] + "." + version_split[1]

    with open("/home/meraki/code/meraki/Data/champion-rates/rates.json", "w") as f:
        json.dump({"data":all_champs,"patch":version}, f)

if __name__ == "__main__":
    main()