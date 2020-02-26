from lolwikiItem import get_Items
from util import download_webpage

url = 'https://leagueoflegends.fandom.com/wiki/Template:Item_data_Warmog%27s_Armor'
print(get_Items(url).get_items())
