from typing import List, Type, Collection, Mapping, Union
import os
import json
import requests
import itertools
import re
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


def strip_lua_comments(data):
    """
    Strip single-line (--) and block (--[[ ... ]]) Lua comments while
    leaving string literals (single, double, or long bracket strings) intact.
    """
    result: List[str] = []
    in_block_comment = False
    block_eq_count = 0

    def starts_with_long_bracket(s: str, idx: int):
        """Return number of '=' characters if s[idx:] starts with [[ or [=...=[."""
        if s[idx] != '[':
            return None
        j = idx + 1
        while j < len(s) and s[j] == '=':
            j += 1
        if j < len(s) and s[j] == '[':
            return j - idx - 1  # number of '=' between the brackets
        return None

    def ends_with_long_bracket(s: str, idx: int, eq_count: int):
        """Return True if s[idx:] starts with ]=...=] using eq_count equals."""
        if s[idx] != ']':
            return False
        j = idx + 1
        while j < len(s) and s[j] == '=':
            j += 1
        return j < len(s) and s[j] == ']' and (j - idx - 1) == eq_count

    in_long_string = False
    long_string_eq = 0

    in_single_quotes = False
    in_double_quotes = False

    for line in data:
        i = 0
        cleaned = []

        while i < len(line):
            c = line[i]

            if in_block_comment:
                if ends_with_long_bracket(line, i, block_eq_count):
                    in_block_comment = False
                    i += 2 + block_eq_count
                else:
                    i += 1
                continue

            if in_long_string:
                if ends_with_long_bracket(line, i, long_string_eq):
                    closing_segment = line[i : i + 2 + long_string_eq]
                    cleaned.extend(closing_segment)
                    in_long_string = False
                    i += len(closing_segment)
                else:
                    cleaned.append(c)
                    i += 1
                continue

            if in_single_quotes:
                cleaned.append(c)
                if c == '\\':
                    if i + 1 < len(line):
                        cleaned.append(line[i + 1])
                        i += 2
                    else:
                        i += 1
                elif c == "'":
                    in_single_quotes = False
                    i += 1
                else:
                    i += 1
                continue

            if in_double_quotes:
                cleaned.append(c)
                if c == '\\':
                    if i + 1 < len(line):
                        cleaned.append(line[i + 1])
                        i += 2
                    else:
                        i += 1
                elif c == '"':
                    in_double_quotes = False
                    i += 1
                else:
                    i += 1
                continue

            # Outside any string/comment
            if c == "'" and not in_double_quotes:
                in_single_quotes = True
                cleaned.append(c)
                i += 1
                continue

            if c == '"' and not in_single_quotes:
                in_double_quotes = True
                cleaned.append(c)
                i += 1
                continue

            # Block comment start
            if c == '-' and (i + 1) < len(line) and line[i + 1] == '-':
                eq_count = starts_with_long_bracket(line, i + 2)
                if eq_count is not None:
                    in_block_comment = True
                    block_eq_count = eq_count
                    i += 4 + eq_count  # skip "--[=...[" 
                    continue
                else:
                    break  # strip rest of line
            # Long string start
            eq_count = starts_with_long_bracket(line, i)
            if eq_count is not None:
                in_long_string = True
                long_string_eq = eq_count
                end_idx = i + 2 + eq_count
                cleaned.extend(line[i:end_idx])
                i = end_idx
                continue

            cleaned.append(c)
            i += 1

        result.append(''.join(cleaned).rstrip())

    return result

