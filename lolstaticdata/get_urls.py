import json
import re
from bs4 import BeautifulSoup
from util import download_webpage
from lolwikiItem import get_Items
from collections import OrderedDict


use_cache = False

base_url = 'https://leagueoflegends.fandom.com'

url = 'https://leagueoflegends.fandom.com/wiki/Category:Item_data_templates?from=A'


html = download_webpage(url, use_cache)
soup = BeautifulSoup(html, 'lxml')


test2 = soup.find_all("a", href=re.compile("/wiki/Template:Item_data_"))
for url in test2:
    # print(url.text.strip())

    item_url = base_url + url['href']
    item = get_Items(item_url)
    print(item_url)
    print(item.get_items())



next_button = soup.find("a", {"class": "category-page__pagination-next wds-button wds-is-secondary"})
if next_button:
    url = (next_button['href'])
    html = download_webpage(url, use_cache)
    soup = BeautifulSoup(html, 'lxml')

    html = download_webpage(url, use_cache)
    soup2 = BeautifulSoup(html, 'lxml')
    test2 = soup2.find_all("a", href=re.compile("/wiki/Template:Item_data_"))
    for url in test2:
        # print(url.text.strip())

        item_url = base_url + url['href']
        item = get_Items(item_url)
        print(item_url)
        print(item.get_items())

else:
    print("done")



next_button = soup.find("a", {"class": "category-page__pagination-next wds-button wds-is-secondary"})
if next_button:
    url = (next_button['href'])
    html = download_webpage(url, use_cache)
    soup = BeautifulSoup(html, 'lxml')

    html = download_webpage(url, use_cache)
    soup3 = BeautifulSoup(html, 'lxml')
    test2 = soup3.find_all("a", href=re.compile("/wiki/Template:Item_data_"))
    for url in test2:
        # print(url.text.strip())

        item_url = base_url + url['href']
        item = get_Items(item_url)
        print(item_url)
        print(item.get_items())

else:
    print("done")

next_button = soup.find("a", {"class": "category-page__pagination-next wds-button wds-is-secondary"})
if next_button:
    url = (next_button['href'])
    html = download_webpage(url, use_cache)
    soup = BeautifulSoup(html, 'lxml')

    html = download_webpage(url, use_cache)
    soup4 = BeautifulSoup(html, 'lxml')
    test2 = soup4.find_all("a", href=re.compile("/wiki/Template:Item_data_"))
    for url in test2:
        # print(url.text.strip())

        item_url = base_url + url['href']
        item = get_Items(item_url)
        print(item_url)
        print(item.get_items())

else:
    print("done")


