# NOT FINAL
# NOT FINAL
# NOT FINAL
#TODO Something with unique values ie: CDRUnique and CDR.

from bs4 import BeautifulSoup
import json
import re
from lolstaticdata.util import download_webpage_items
from model2 import Stat, Shop, Item, Passive, itemAttributes
from collections import OrderedDict
import os


class get_Items():
    def __init__(self):
        self.not_unique = re.compile('[A-z]')



    def uniquePassive(self,passive):

        effects = []
        if passive == "pass":
            for i in range(1,6):
                passive = "pass" + str(i)
                if passive == "pass1":
                    passive = "pass"
                passive = self.test3[passive]
                effect =self.uniquePassiveFunc(passive)
                effects.append(effect)
                print(effects)
                if effects == [None]:
                    effects = []
                return effects


        elif passive == "aura":
            for i in range(1,4):
                passive = "aura" + str(i)
                if passive == "aura1":
                    passive = "aura"
                print(passive)
                passive = self.test3[passive]
                effect = self.uniquePassiveFunc(passive)
                effects.append(effect)
                if effects == [None]:
                    effects = []
                return effects

        elif passive == "act":
            passive = self.test3[passive]
            effect = self.uniquePassiveFunc(passive)
            effects.append(effect)
            if effects == [None]:
                effects = []
            return effects


    def uniquePassiveFunc(self,passive):
        unique_no_space = re.compile('(Unique:).*')
        unique_reg = re.compile('(?:(?<=Unique:)|(?<=Unique :)).*')
        not_unique = re.compile('[A-z]')
        try:
            if unique_no_space.match(passive):
                #I changed util to detect unique items regardless of name or not
                #Before it had "Unique \u2013 passive name :"
                uniqueData = unique_reg.search(passive).group(0).replace("  ", " ")
                if ':' in uniqueData:
                    unique_split = uniqueData.split(':')
                    name = unique_split[0]
                    passive = unique_split[1]
                    unique = True
                else:
                    unique = True
                    name = None
                    passive = uniqueData
                effect = Passive(
                    unique = unique,
                    name = name,
                    effects = passive
                )
                return effect

            else:
                # return normal passive
                notUnique = not_unique.search(passive)
                if not_unique.match(passive):
                    if ':' in passive:
                        notUnique_split = passive.split(':')
                        unique = False
                        name = notUnique_split[0]
                        passive = notUnique_split[1]
                    else:
                        unique = False
                        name = None
                        passive = passive

                    effect = Passive(
                        unique=unique,
                        name=name,
                        effects=passive
                    )

                    return effect

        except AttributeError:
            print(passive, "TESTING")
            raise






    def prices(self, statistic):
        try:
            if statistic in ("N/A"):
                return 0

            else:
                stat = eval(statistic)
                return stat
        except SyntaxError:
            return 0

    def itemid(self):
        try:
            if self.test3["code"] in ("N/A"):
                return None
            else:
                stat = eval(self.test3["code"])
                return stat
        except SyntaxError:
            return None



    def get_item_attributes(self):
        #gets all item attributes from the item tags
        #This is a mess. The wiki has tons of miss named tags, this is to get them
        tags = []
        for i in range(1,8):
            menu = "menu" + str(i)
            print(menu)

            menua = menu+"a"
            menub = menu+"b"
            primaryTag = "null"
            secondaryTag = "null"
            if self.test3[menua]:
                primaryTag = self.test3[menua]
                secondaryTag = self.test3[menub]
                print(self.test3[menua], self.test3[menub])
                if self.test3[menua] in ('Offense', 'Attack'):
                    primaryTag = "Attack"
                elif self.test3[menua] in ('Starter Items', 'Starting Items'):
                    primaryTag = "Starter Items"

                elif self.test3[menua] in ('Movement', 'Movement Speed', 'Other'):
                    primaryTag = "Movement"

                else:
                    primaryTag = itemAttributes.from_string(primaryTag)

                if self.test3[menub]:
                    if self.test3[menub] in ('Health Regeneration', "Health Regen", "Health Renegeration"):
                        secondaryTag = "Health Regen"

                    elif self.test3[menub] in ("Magic Resist", "Magic Resistance"):
                        secondaryTag = "Magic Resist"

                    elif self.test3[menub] in ("Mana Regen", "Mana Regeneration"):
                        secondaryTag = "Mana Regen"

                    elif self.test3[menub] in ("Jungling", "Jungle"):
                        secondaryTag = "Jungling"

                    elif self.test3[menub] in ("Other Movement Items", "Other Movement", "Others", "Other Items", "Movement Speed"):
                        secondaryTag = "Other Movement Items"

                    elif self.test3[menub] in ('Attack Damage', 'Damage', ' Damage'):
                        secondaryTag = "Damage"

                    elif self.test3[menub] in ('Laning', 'Lane'):
                        secondaryTag = "Laning"

                    elif self.test3[menub] in ('Lifesteal', 'Life steal'):
                        secondaryTag = "Life Steal"

                    elif secondaryTag in ('Vision andamp;Trinkets', 'VISION AND TRINKETS', 'Vision and&; Trinkets',
                                        'Vision & Trinkets', 'Vision'):
                        secondaryTag = "Vision and Trinkets"

                    if ';' in self.test3[menub]:
                        print(self.test3[menub], "Test")
                        secondaryTag= self.test3[menub].replace("; ", ";")
                        #I don't think this is needed (the vision stuff)
                        if secondaryTag in ('Vision andamp;Trinkets', 'VISION AND TRINKETS', 'Vision and&; Trinkets',
                                                   'Vision & Trinkets', 'Vision'):
                            secondaryTag = "Vision and Trinkets"
                            tag = primaryTag.name + ':' + secondaryTag.upper()
                        else:
                            secondaryTag= secondaryTag.split(";")
                            print(secondaryTag)
                            secondaryTag1 = itemAttributes.from_string(secondaryTag[0])
                            print(secondaryTag1.name)
                            print(secondaryTag[1])
                            secondaryTag2 = itemAttributes.from_string(secondaryTag[1])
                            print(secondaryTag[1])
                            secondaryTag = secondaryTag1.name + "," + secondaryTag2.name
                            tag = primaryTag.name + ":" + secondaryTag.upper()
                    else:
                        secondaryTag = itemAttributes.from_string(secondaryTag)
                        try:
                            #there was an error with a couple primary tags not having the right tags so this fixes it
                            tag = primaryTag.name + ":" + secondaryTag.name
                        except AttributeError:
                            tag = primaryTag.upper() + ':' + secondaryTag.name
                    tags.append(tag)
                else:
                    #Titanic Hydra decided to mess everything up so I needed to put something to allow a Primary tag
                    # without a secondary tag
                    tag = primaryTag.upper() + ":None"
                    tags.append(tag)
        return tags





    def get_items(self):
        #All item data has a html attribute "data-name" so I put them all in an ordered dict while stripping the new lines
        #and spaces from the data
        use_cache = False

        base_url = 'https://leagueoflegends.fandom.com'

        url = 'https://leagueoflegends.fandom.com/wiki/Category:Item_data_templates?from=A'

        html = download_webpage_items(url, use_cache)
        soup = BeautifulSoup(html, 'lxml')

        next_button = soup.find("a", {"class": "category-page__pagination-next wds-button wds-is-secondary"})

        test2 = soup.find_all("a", {"class": "category-page__member-link"})
        last_page = False
        while not last_page:
            for url in test2:
                # print(url.text.strip())

                item_url = base_url + url['href']
                item = item_url
                html1 = download_webpage_items(item, use_cache)
                soup1 = BeautifulSoup(html1, 'lxml')
                self.test3 = OrderedDict()

                for td in soup1.findAll('td', {"data-name": True}):
                    self.attributes = td.find_previous("td").text.rstrip()
                    self.attributes = self.attributes.lstrip()
                    self.values = td.text.rstrip()
                    # replace("\n", "")
                    self.values = self.values.lstrip().rstrip()
                    self.test3[self.attributes] = self.values
                item = self.item_stats()
                yield item

            try:
                url = (next_button['href'])
                html = download_webpage_items(url, use_cache)
            except TypeError:
                last_page = True
            soup = BeautifulSoup(html, 'lxml')
            next_button = soup.find("a", {"class": "category-page__pagination-next wds-button wds-is-secondary"})
            test2 = soup.find_all("a", {"class": "category-page__member-link"})

    def item_stats(self):
        builds = []
        recipes = []
        #Create the json files from the classes in model2.py
        self.removed = self.test3.get("hp", None)
        if self.test3["removed"] == "true":
            self.removed = True
        else:
            self.removed = False
        if self.not_unique.match(self.test3["noe"]):
            no_effects = True
        else:
            no_effects = False
        if self.not_unique.search(self.test3["builds"]):
            build = self.test3["builds"]
            if "," in build:
                for i in build.split(","):
                    builds.append(i.strip())
            else:
                builds.append(build.strip())

        if self.not_unique.match(self.test3["recipe"]):
            component = self.test3["recipe"]
            if "," in component:
                for i in component.split(","):
                    recipes.append(i.strip())
            else:
                recipes.append(component.strip())



        item = Item(
            Name=self.test3["1"],
            itemID=self.itemid(),
            tier=self.test3["tier"],
            type=self.test3["type"],
            recipe=recipes,
            builds =builds,
            no_effects = no_effects,
            removed=self.removed,
            nickname=self.test3["nickname"],
            passives = self.uniquePassive("pass"),
            auras = self.uniquePassive("aura"),
            active= self.uniquePassive("act"),
            stats=Stat(
                abilityPower=self.prices(self.test3["ap"]),
                armor=self.prices(self.test3['armor']),
                armorPenetration=self.prices(self.test3['rpen']),
                attackDamage=self.prices(self.test3['ad']),
                attackSpeed=self.prices(self.test3['as']),
                cdr=self.prices(self.test3['cdr']),
                cdrUnique=self.prices(self.test3['cdrunique']),
                crit=self.prices(self.test3['crit']),
                critUnique=self.prices(self.test3['critunique']),
                goldPer10=self.prices(self.test3["gp10"]),
                healShield=self.prices(self.test3["hsp"]),
                health=self.prices(self.test3["health"]),
                healthRegen=self.prices(self.test3["hp5"]),
                healthRegenFlat=self.prices(self.test3["hp5flat"]),
                lifesteal=self.prices(self.test3["lifesteal"]),
                magicPenetration=self.prices(self.test3["mpen"]),
                magicResist=self.prices(self.test3["mr"]),
                mana=self.prices(self.test3["mana"]),
                manaRegenPer5=self.prices(self.test3["mp5"]),
                manaRegenPer5Flat=self.prices(self.test3["mp5flat"]),
                moveSpeed=self.prices(self.test3["ms"]),
                moveSpeedUnique=self.prices(self.test3["msunique"]),
                moveSpeedFlat=self.prices(self.test3["msflat"]),
            ),
            shop=Shop(
                priceFull=self.prices(self.test3["buy"]),
                priceCombined=self.prices(self.test3["comb"]),
                priceSell=self.prices(self.test3["sell"]),
                itemTags=self.get_item_attributes()
            )

            )
        return item



def main():
    jsons = {}
    items = []
    directory = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..","itemData"))
    if not os.path.exists(directory):
        os.mkdir(directory)
    print(directory)
    startItems = get_Items()
    for item in startItems.get_items():
        fileName = item.Name.replace(" ", "_")
        if fileName in ("Champion", "Tower"):
            continue
        items.append(item)
        print(fileName)

        jsonfn = os.path.join(directory, fileName.strip() + ".json")
        print(jsonfn)
        with open(jsonfn, 'w') as p:
            p.write(item.to_json(indent=2))
            p.close()
    for item in items:
        jsons[item.Name.replace(" ", "_").strip()] = json.loads(item.to_json())
        print(jsons, "yeet")
    itemFile = os.path.join(directory, "items.json")
    for item in items:
        jsons[item.Name.replace(" ", "_")] = json.loads(item.to_json())
    with open(itemFile, 'w') as p:
       json.dump(jsons, p, indent=2)
    del jsons


if __name__ == "__main__":
    main()