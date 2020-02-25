# NOT FINAL
# NOT FINAL
# NOT FINAL


from bs4 import BeautifulSoup
import json
import re
from util import download_webpage
from model2 import Stat, Shop, Item, Menu, Other, Effects, Passive, itemAttributes
from collections import OrderedDict




class get_Items():
    def __init__(self, url):
        self.url = url

    def uniquePassive(self,passive):
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
                    print(name, passive)
                    unique = True
                else:
                    unique = True
                    name = None
                    passive = uniqueData
                    print(name, passive)
                effects = Passive(
                    unique = unique,
                    name = name,
                    effects = passive
                )
                print(effects)
                return effects
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

                    effects = Passive(
                        unique=unique,
                        name=name,
                        effects=passive
                    )
                    return effects

        except AttributeError:
            print(passive, "TESTING")
            raise


    def get_item_attributes(self, menu):
        #gets all item attributes from the item tags
        #This is a mess. The wiki has tons of miss named tags, this is to get them

        not_unique = re.compile('[A-z]')
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
                return tag
            else:
                #Titanic Hydra decided to mess everything up so I needed to put something to allow a Primary tag
                # without a secondary tag
                tag = primaryTag + ":None"
                return tag





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

        self.item = Item(
            Name=self.test3["1"],
            itemID=self.test3["code"],
            tier=self.test3["tier"],
            type=self.test3["type"],
            recipe=self.test3["recipe"],
            builds = self.test3['builds'],
            effects = Effects(
                passive1= self.uniquePassive(self.test3["pass"]) ,
                passive2=self.uniquePassive(self.test3["pass2"]),
                passive3=self.uniquePassive(self.test3["pass3"]),
                passive4=self.uniquePassive(self.test3["pass4"]),
                passive5=self.uniquePassive(self.test3["pass5"]),
                active=self.uniquePassive(self.test3["act"]),
                aura=self.uniquePassive(self.test3["aura"]),
                aura2=self.uniquePassive(self.test3["aura2"]),
                aura3=self.uniquePassive(self.test3["aura3"]),
                no_effects=self.test3["noe"],
            ),
            stats=Stat(
                abilityPower=self.test3["ap"],
                armor=self.test3['armor'],
                armorPenetration=self.test3['rpen'],
                attackDamage=self.test3['ad'],
                attackSpeed=self.test3['as'],
                cdr=self.test3['cdr'],
                cdrUnique=self.test3['cdrunique'],
                crit=self.test3['crit'],
                critUnique=self.test3['critunique'],
                goldPer10=self.test3["gp10"],
                healShield=self.test3["hsp"],
                health=self.test3["health"],
                healthRegen=self.test3["hp5"],
                healthRegenFlat=self.test3["hp5flat"],
                lifesteal=self.test3["lifesteal"],
                magicPenetration=self.test3["mpen"],
                magicResist=self.test3["mr"],
                mana=self.test3["mana"],
                manaRegenPer5=self.test3["mp5"],
                manaRegenPer5Flat=self.test3["mp5flat"],
                moveSpeed=self.test3["ms"],
                moveSpeedUnique=self.test3["msunique"],
                moveSpeedFlat=self.test3["msflat"],
                spec = self.test3["spec"],
                spec2 = self.test3["spec2"]
            ),
            shop=Shop(
                priceFull=self.test3["buy"],
                priceCombined=self.test3["comb"],
                priceSell=self.test3["sell"],
                itemTags=Menu(
                    Tag1 = self.get_item_attributes("menu1"),
                    Tag2 = self.get_item_attributes("menu2"),
                    Tag3 = self.get_item_attributes("menu3"),
                    Tag4 = self.get_item_attributes("menu4"),
                    Tag5 = self.get_item_attributes("menu5"),
                    Tag6 = self.get_item_attributes("menu6"),
                    Tag7 = self.get_item_attributes("menu7")
                )

            ),
            other=Other(
                consume=self.test3["consume"],
                consume2=self.test3["consume2"],
                champion_item=self.test3["champion"],
                limit=self.test3["limit"],
                req=self.test3["req"],
                hp=self.test3["hp"],
                removed=self.removed,
                nickname=self.test3["nickname"]
            )

            )

    def item_to_json(self):
        json.dump(self.test3, self.f, indent=2)
        self.f.close()

        jsonfn = r"C:\Users\dan\PycharmProjects\lolstaticdata\data\{}.json".format(self.test3["1"].replace(" ", "_"))
        with open(jsonfn, 'w') as p:
            p.write(self.item.to_json(indent=2))
            p.close()

