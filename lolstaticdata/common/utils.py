from typing import Type, Collection, Mapping, Union
import os
import json
import requests
import itertools
from bs4 import BeautifulSoup
from enum import Enum
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from natsort import natsorted

Json = Union[dict, list, str, int, float, bool, None]


def to_enum_like(string: str) -> str:
    return string.upper().replace(" ", "_")


# Monkey patch this method onto Enums
@classmethod
def from_string(cls: Type[Enum], string: str) -> Enum:
    string = to_enum_like(string)
    for e in cls:
        if e.name == string:
            return e
    raise ValueError(f"Unknown {cls.__name__} type: {string}")


Enum.from_string = from_string


class OrderedEnum(Enum):
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


# From dataclasses_json -> utils.py
def _isinstance_safe(o, t):
    try:
        result = isinstance(o, t)
    except Exception:
        return False
    else:
        return result


# From dataclasses_json -> core.py
class ExtendedEncoder(json.JSONEncoder):
    def default(self, o) -> Json:
        result: Json
        if _isinstance_safe(o, Collection):
            if _isinstance_safe(o, Mapping):
                result = dict(o)
            else:
                result = list(o)
        elif _isinstance_safe(o, datetime):
            result = o.timestamp()
        elif _isinstance_safe(o, UUID):
            result = str(o)
        elif _isinstance_safe(o, Enum):
            result = o.value
        elif _isinstance_safe(o, Decimal):
            result = str(o)
        else:
            result = json.JSONEncoder.default(self, o)
        return result


def grouper(iterable, n, fillvalue=None):
    """Collect champData into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


def parenthetic_contents(string):
    # http://stackoverflow.com/questions/4284991/parsing-nested-parentheses-in-python-grab-content-by-level
    """Generate parenthesized contents in string as pairs (level, contents)."""
    """
        >>> list(parenthetic_contents('(a(b(c)(d)e)(f)g)'))
        [(2, 'c'), (2, 'd'), (1, 'b(c)(d)e'), (1, 'f'), (0, 'a(b(c)(d)e)(f)g')]
    """
    stack = []
    for i, c in enumerate(string):
        if c == "(":
            stack.append(i)
        elif c == ")" and stack:
            start = stack.pop()
            yield (len(stack), string[start + 1 : i])


def parse_top_level_parentheses(string):
    parsed = parenthetic_contents(string)
    results = []
    for level, result in parsed:
        if level == 0:
            results.append(f"({result})")
    return results


def download_json(url: str, use_cache: bool = True) -> Json:
    directory = os.path.dirname(os.path.realpath(__file__))
    fn = os.path.join(directory, "../../__cache__")
    if not os.path.exists(fn):
        os.mkdir(fn)
    url2 = url.replace(":", "")
    fn = os.path.join(fn, url2.replace("/", "@"))

    if use_cache and os.path.exists(fn):
        with open(fn) as f:
            j = json.load(f)
    else:
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"}
        page = requests.get(url, headers=headers)
        j = page.json()
        if use_cache:
            with open(fn, "w") as f:
                json.dump(j, f)
    return j


def download_soup(url: str, use_cache: bool = True, dir: str = f"__cache__"):
    directory = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))
    directory = os.path.join(directory, dir)
    if "ITEM_DATA" not in url.upper():
        fn = os.path.join(directory, url.replace("/", "@"))
    else:
        url_split = url.split("Item_data_")[1]
        if url_split == "'Your_Cut":
            url_split.replace("'", "")
        fn = os.path.join(directory, url_split.replace("/", "@"))
    if use_cache and os.path.exists(fn):
        with open(fn, encoding="utf-8") as f:
            html = f.read()
    else:
        page = requests.get(url)
        # html = page.content.decode(page.encoding)
        html = page.text
        if use_cache:
            with open(fn, "w", encoding="utf-8") as f:
                f.write(html)
    soup = BeautifulSoup(html, "lxml")
    html = str(soup)
    html = html.replace("\u00a0", " ")
    html = html.replace("\u300c", "[")
    html = html.replace("\u300d", "]")
    html = html.replace("\u00ba", "°")
    html = html.replace("\u200b", "")  # zero width space
    html = html.replace("\u200e", "")  # left-to-right mark
    html = html.replace("\u2013", ":")  # left-to-right mark
    html = html.replace("\xa0", " ")
    html = html.replace("\uFF06", "&")
    # NON-ASCII CHARACTERS: Counter({'…': 130, '°': 76, '×': 74, '–': 28, '÷': 20, '∞': 18, '\u200e': 8, '≈': 4, '≤': 2})

    assert "\xa0" not in html
    return html


def save_json(data, filename):
    def set_default(obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError(f"Cannot serialize object of type: {type(obj)} ... {obj}")

    sdata = json.dumps(data, indent=2, default=set_default)
    with open(filename, "w") as of:
        of.write(sdata)
    with open(filename, "r") as f:
        sdata = f.read()
        sdata = sdata.replace("\u00a0", " ")
        sdata = sdata.replace("\u300d", " ")
        sdata = sdata.replace("\u300c", " ")
        sdata = sdata.replace("\u00ba", " ")
        sdata = sdata.replace("\xa0", " ")
    with open(filename, "w") as of:
        of.write(sdata)


def get_latest_patch_version():
    versions = download_json("http://ddragon.leagueoflegends.com/api/versions.json", use_cache=False)
    versions = [v for v in versions if "_" not in v]
    versions = natsorted(versions)
    return versions[-1]
