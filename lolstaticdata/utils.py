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

Json = Union[dict, list, str, int, float, bool, None]


def to_enum_like(string: str) -> str:
    return string.upper().replace(' ', '_')


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
        if c == '(':
            stack.append(i)
        elif c == ')' and stack:
            start = stack.pop()
            yield (len(stack), string[start + 1: i])

def parse_top_level_parentheses(string):
    parsed = parenthetic_contents(string)
    results = []
    for level, result in parsed:
        if level == 0:
            results.append(f"({result})")
    return results



#NONASCII = Counter()
def download_webpage(url: str, use_cache: bool = True):
    directory = os.path.dirname(os.path.realpath(__file__)) + "/"
    fn = directory + f"../__cache__/{url.replace('/', '@')}"
    if use_cache and os.path.exists(fn):
        with open(fn) as f:
            html = f.read()
    else:
        page = requests.get(url)
        html = page.content.decode(page.encoding)
        if use_cache:
            with open(fn, 'w') as f:
                f.write(html)
    soup = BeautifulSoup(html, 'lxml')
    html = str(soup)
    html = html.replace(u'\u00a0', u' ')
    html = html.replace(u'\u300c', u'[')
    html = html.replace(u'\u300d', u']')
    html = html.replace(u'\u00ba', u'°')
    html = html.replace(u'\u200b', u'')  # zero width space
    html = html.replace(u'\u200e', u'')  # left-to-right mark
    html = html.replace(u'\u2013', u':')  # left-to-right mark
    html = html.replace(u'\xa0', u' ')
    html = html.replace(u"\uFF06", u'&')
    #html = html.replace(u'☂', u'')
    #html = html.replace(u'•', u'*')
    #html = html.replace(u'’', u'')
    #html = html.replace(u'↑', u'')
    #html = html.replace(u'…', u'...')
    #html = html.replace(u'↑', u'')
    #NON-ASCII CHARACTERS: Counter({'…': 130, '°': 76, '×': 74, '–': 28, '÷': 20, '∞': 18, '\u200e': 8, '≈': 4, '≤': 2})

    #for a in html:
    #    if ord(a) > 127:
    #        NONASCII[a] += 1
    #if NONASCII:
    #    print("NON-ASCII CHARACTERS:", NONASCII)

    assert u'\xa0' not in html
    return html


def save_json(data, filename):
    def set_default(obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError(f"Cannot serialize object of type: {type(obj)} ... {obj}")
    sdata = json.dumps(data, indent=2, default=set_default)
    with open(filename, 'w') as of:
        of.write(sdata)
    with open(filename, 'r') as f:
        sdata = f.read()
        sdata = sdata.replace(u'\u00a0', u' ')
        sdata = sdata.replace(u'\u300d', u' ')
        sdata = sdata.replace(u'\u300c', u' ')
        sdata = sdata.replace(u'\u00ba', u' ')
        sdata = sdata.replace(u'\xa0', u' ')
    with open(filename, 'w') as of:
        of.write(sdata)
