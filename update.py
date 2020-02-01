import os
import json
import time
import itertools
from collections import Counter
from bs4 import BeautifulSoup
import requests
import urllib.request


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


def pull_champion_stats():
    # Download the page source
    url = "https://leagueoflegends.fandom.com/wiki/Module:ChampionData/data"
    page = requests.get(url)
    html = page.content.decode(page.encoding)
    soup = BeautifulSoup(html, 'html.parser')

    # Parse out the data
    spans = soup.find_all('span')
    start = None
    for i, span in enumerate(spans):
        if str(span) == '<span class="kw1">return</span>':
            start = i
    spans = spans[start:]
    data = ""
    brackets = Counter()
    for span in spans:
        text = span.text
        if text == "{" or text == "}":
            brackets[text] += 1
        if brackets["{"] != 0 :
            data += text
        if brackets["{"] == brackets["}"] and brackets["{"] > 0:
            break
    # Reformat the data
    data = data.replace('=', ':')
    data = data.replace('["', '"')
    data = data.replace('"]', '"')
    data = data.replace('[1]', '1')
    data = data.replace('[2]', '2')
    data = data.replace('[3]', '3')
    data = data.replace('[4]', '4')
    data = data.replace('[5]', '5')
    data = data.replace('[6]', '6')
    data = eval(data)
    return data


def pull_champion_ability(champion_name, ability_name):
    ability_name = ability_name.replace(' ', '_')

    url = f"https://leagueoflegends.fandom.com/wiki/Template:Data_{champion_name}/{ability_name}"
    page = requests.get(url)
    html = page.content.decode(page.encoding)
    #with urllib.request.urlopen(url) as response:
    #    html = response.read().decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    table = soup.find_all(['th', 'td'])
    table = [item.text.strip() for item in table]
    table = table[table.index("Parameter")+3:]
    table[0] = "name"  # this is '1' for some reason but it's the ability name

    data = {}
    for parameter, value, desc in grouper(table, 3):
        data[parameter] = value
    return data


def save_json(data, filename):
    def set_default(obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError
    sdata = json.dumps(data, indent=2, default=set_default)
    with open(filename, 'w') as of:
        of.write(sdata)
    with open(filename, 'r') as f:
        sdata = f.read()
        sdata = sdata.replace(u'\\u00a0', ' ')
        sdata = sdata.replace(u'\\u300d', ' ')
        sdata = sdata.replace(u'\\u300c', ' ')
        sdata = sdata.replace(u'\\u00ba', ' ')
    with open(filename, 'w') as of:
        of.write(sdata)


def main():
    statsfn = "data/champion_stats.json"
    #if not os.path.exists(statsfn):
    stats = pull_champion_stats()
    save_json(stats, statsfn)

    with open(statsfn) as f:
        stats = json.load(f)

    # Missing skills
    missing_skills = {
        "Annie": ["Command Tibbers"] ,
        "Jinx": ["Switcheroo! 2"] ,
        "Nidalee": ["Aspect of the Cougar 2"] ,
        "Pyke": ["Death from Below 2"],
        "Rumble": ["Electro Harpoon 2"] ,
        "Shaco": ["Command Hallucinate"] ,
        "Syndra": ["Force of Will 2"] ,
        "Taliyah": ["Seismic Shove 2"],
    }

    for champion_name, details in stats.items():
        jsonfn = f"data/{details['apiname']}.json"
        #if os.path.exists(jsonfn):
        #    continue
        print(champion_name)
        if champion_name == "Kled & Skaarl":
            champion_name = "Kled"
        success = True
        for ability in ['i', 'q', 'w', 'e', 'r']:
            result = {}
            for ability_name in details[f"skill_{ability}"].values():
                if champion_name in missing_skills and ability_name in missing_skills[champion_name]:
                    continue
                print(ability_name)
                try:
                    r = pull_champion_ability(champion_name, ability_name)
                    # check to see if this ability was already pulled
                    found = False
                    for r0 in result.values():
                        if r == r0:
                            found = True
                    if not found:
                        result[ability_name] = r
                except Exception as exception:
                    print(f"FAILED TO PARSE! {exception}")
                    #success = False
            details[f"skill_{ability}"] = result
        if success:
            save_json(details, jsonfn)
        print()



if __name__ == "__main__":
    main()
