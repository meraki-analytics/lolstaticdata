# NOT FINAL
# NOT FINAL
# NOT FINAL
#TODO Something with unique values ie: CDRUnique and CDR.

from bs4 import BeautifulSoup
import json
import re
from lolstaticdata.util import download_webpage
from model2 import Stat, Shop, Item, Other, Passive, itemAttributes
from collections import OrderedDict



class get_Items():
    def __init__(self, url):
        self.url = url
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
                return effects

        elif passive == "act":
            passive = self.test3[passive]
            effect = self.uniquePassiveFunc(passive)
            effects.append(effect)
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
                            tag = primaryTag.name + ':' + secondaryTag
                        else:
                            secondaryTag= secondaryTag.split(";")
                            print(secondaryTag)
                            secondaryTag1 = itemAttributes.from_string(secondaryTag[0])
                            print(secondaryTag1.name)
                            print(secondaryTag[1])
                            secondaryTag2 = itemAttributes.from_string(secondaryTag[1])
                            print(secondaryTag[1])
                            secondaryTag = secondaryTag1.name + "," + secondaryTag2.name
                            tag = primaryTag.name + ":" + secondaryTag
                    else:
                        secondaryTag = itemAttributes.from_string(secondaryTag)
                        try:
                            #there was an error with a couple primary tags not having the right tags so this fixes it
                            tag = primaryTag.name + ":" + secondaryTag.name
                        except AttributeError:
                            tag = primaryTag + ':' + secondaryTag.name
                    tags.append(tag)
                else:
                    #Titanic Hydra decided to mess everything up so I needed to put something to allow a Primary tag
                    # without a secondary tag
                    tag = primaryTag + ":None"
                    tags.append(tag)
        return tags





    def get_items(self):
        #All item data has a html attribute "data-name" so I put them all in an ordered dict while stripping the new lines
        #and spaces from the data
        use_cache = False
        html = download_webpage(self.url, use_cache)
        soup = BeautifulSoup(html, 'lxml')
        with open("html.json", 'w') as self.f:
            self.test3 = OrderedDict()

            for td in soup.findAll('td', {"data-name": True}):
                self.attributes = td.find_previous("td").text.rstrip()
                self.attributes = self.attributes.lstrip()
                self.values = td.text.rstrip()
                # replace("\n", "")
                self.values = self.values.lstrip().rstrip()
                self.test3[self.attributes] = self.values
            self.item_stats()
            self.item_to_json()

    def item_stats(self):
        #Create the json files from the classes in model2.py
        self.removed = self.test3.get("hp", None)
        if self.test3["removed"] == "true":
            self.removed = True
        else:
            self.removed = False
        if self.not_unique.match(self.test3["noe"] ):
            no_effects = True
        else:
            no_effects = False
        builds = []
        if "," in self.test3['builds']:
            build = self.test3["builds"]
            for i in build.split(","):
                builds.append(i)

        recipes = []
        if "," in self.test3['recipe']:
            component = self.test3["recipe"]
            for i in component.split(","):
                recipes.append(i)



        self.item = Item(
            Name=self.test3["1"],
            itemID=self.test3["code"],
            tier=self.test3["tier"],
            type=self.test3["type"],
            recipe=recipes,
            builds = builds,
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
                spec = self.test3["spec"],
                spec2 = self.test3["spec2"]
            ),
            shop=Shop(
                priceFull=self.prices(self.test3["buy"]),
                priceCombined=self.prices(self.test3["comb"]),
                priceSell=self.prices(self.test3["sell"]),
                itemTags=self.get_item_attributes()
            ),
            other=Other(
                consume=self.test3["consume"],
                consume2=self.test3["consume2"],
                champion_item=self.test3["champion"],
                limit=self.test3["limit"],
                req=self.test3["req"],
                hp=self.prices(self.test3["hp"]),
            )

            )

    def item_to_json(self):
        json.dump(self.test3, self.f, indent=2)
        self.f.close()

        jsonfn = r"C:\Users\dan\PycharmProjects\lolstaticdata\data\{}.json".format(self.test3["1"].replace(" ", "_"))
        with open(jsonfn, 'w') as p:
            p.write(self.item.to_json(indent=2))
            p.close()

