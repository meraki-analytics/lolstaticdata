# NOT FINAL
# NOT FINAL
# NOT FINAL
#TODO fix paths
#TODO clean up code
#TODO Clean up item data 
#TODO Lots and lots of cleaning
#TODO Make it easy to add data to champion stats 

from bs4 import BeautifulSoup
import json
import re
from util import download_webpage
from model2 import Stat, Shop, Item, Menu, Other
from collections import OrderedDict


def uniquePassive(passive):
    passive_reg = re.compile('(?<=Unique : ).*')
    try:
        return passive_reg.search(passive).group(0).replace("  ", " ")
    except AttributeError:
        return ""


class get_Items():
    def __init__(self, url):
        self.url = url

    def get_items(self):
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
                spec=self.test3["spec"],
                spec2=self.test3["spec2"],
                passive1=uniquePassive(self.test3["pass"]),
                passive2=uniquePassive(self.test3["pass2"]),
                passive3=uniquePassive(self.test3["pass3"]),
                passive4=uniquePassive(self.test3["pass4"]),
                passive5=uniquePassive(self.test3["pass5"]),
                active=self.test3["act"],
                aura=uniquePassive(self.test3["aura"]),
                aura2=uniquePassive(self.test3["aura2"]),
                aura3=uniquePassive(self.test3["aura3"]),
                no_effects=self.test3["noe"],
            ),
            shop=Shop(
                priceFull=self.test3["buy"],
                priceCombined=self.test3["comb"],
                priceSell=self.test3["sell"],
                menu=Menu(
                    menu1a=self.test3["menu1a"],
                    menu1b=self.test3["menu1b"],
                    menu2a=self.test3["menu2a"],
                    menu2b=self.test3["menu2b"],
                    menu3a=self.test3["menu3a"],
                    menu3b=self.test3["menu3b"],
                    menu4a=self.test3["menu4a"],
                    menu4b=self.test3["menu4b"],
                    menu5a=self.test3["menu5a"],
                    menu5b=self.test3["menu5b"],
                    menu6a=self.test3["menu6a"],
                    menu6b=self.test3["menu6b"],
                    menu7a=self.test3["menu7a"],
                    menu7b=self.test3["menu7b"]
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
        print(self.test3.get("menu1b"), self.test3.get("ap"), self.test3.get("1"))

    def item_to_json(self):
        json.dump(self.test3, self.f, indent=2)
        self.f.close()

        jsonfn = r"C:\Users\dan\PycharmProjects\lolstaticdata\data\{}.json".format(self.test3["1"].replace(" ", "_"))
        with open(jsonfn, 'w') as kek:
            kek.write(self.item.to_json(indent=2))
            kek.close()

