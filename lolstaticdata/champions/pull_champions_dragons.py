from fuzzywuzzy import fuzz
from functools import partial


def maximize(func, guesses):
    best = None, -float("inf")
    for params in guesses:
        value = func(params)
        if value > best[1]:
            best = params, value
    return best


def build_guess(
    champion_name,
    ability_name,
    ability_key,
    ability_index,
    include_champion_name,
    include_ability_name,
    include_ability_key,
    include_ability_index,
    use_underscores=True,
):
    ability_name = ability_name.replace("-", "").replace(" ", "").replace("_", "")
    guess = ""
    if include_champion_name:
        guess = guess + f"{champion_name}"
    if include_ability_name:
        if use_underscores and not guess.endswith("_"):
            guess = guess + "_"
        guess = guess + f"{ability_name}"
    if include_ability_key:
        if use_underscores and not guess.endswith("_"):
            guess = guess + "_"
        guess = guess + f"{ability_key}"
    if include_ability_index:
        if use_underscores and not guess.endswith("_"):
            guess = guess + "_"
        guess = guess + f"{ability_index}"
    guess = guess + ".png"
    return guess.lower()


def perform_guess(
    champion_name,
    ability_name,
    ability_key,
    ability_index,
    filenames,
    use_underscores=True,
):
    best_score = -float("inf")
    for include_champion_name in (True, False):
        for include_ability_name in (True, False):
            for include_ability_index in (True, False):
                for include_ability_key in (True, False):
                    if include_champion_name is True and not any(
                        [
                            include_ability_name,
                            include_ability_index,
                            include_ability_key,
                        ]
                    ):
                        continue
                    guess = build_guess(
                        champion_name,
                        ability_name,
                        ability_key,
                        ability_index,
                        include_champion_name,
                        include_ability_name,
                        include_ability_key,
                        include_ability_index,
                        use_underscores=use_underscores,
                    )
                    _fn, score = maximize(partial(fuzz.ratio, guess), filenames)
                    if score > best_score:
                        best_fn, best_score, best_guess = _fn, score, guess
    return best_fn, best_score, best_guess


def get_ability_url(key, ability_key, ability_index, ability_name, latest_version, ddragon_champion, filenames):
    return f"https://cdn.communitydragon.org/latest/champion/{key}/ability-icon/{ability_key[0]}"
