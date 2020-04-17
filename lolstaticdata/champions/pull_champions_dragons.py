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
    champion_name, ability_name, ability_key, ability_index, filenames, use_underscores=True,
):
    best_score = -float("inf")
    for include_champion_name in (True, False):
        for include_ability_name in (True, False):
            for include_ability_index in (True, False):
                for include_ability_key in (True, False):
                    if include_champion_name is True and not any(
                        [include_ability_name, include_ability_index, include_ability_key,]
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
    # Use ddragon if we can
    if ability_index == 1 and ability_key in ("Q", "W", "E", "R"):
        spell_index = {"Q": 0, "W": 1, "E": 2, "R": 3}[ability_key]
        return f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/img/spell/{ddragon_champion['spells'][spell_index]['image']['full']}"

    # Special cases
    KEY = key
    if key == "gnar" and ability_key == "r":
        key = "gnarbig"
    if key == "aurelionsol" and ability_key == "w":
        ability_name = "startsin"
    if key == "aurelionsol" and ability_key == "w":
        ability_name = "startsin"
    if key == "graves" and ability_key == "passive":
        ability_name = "True Grit"
    if key == "chogath" and ability_key == "passive":
        ability_name = "Tailspike"
        key = "greenterror"
    if key == "corki" and ability_key == "passive":
        ability_name = "The Package"
    if key == "corki" and ability_name == "Special Delivery":
        ability_name = "Valkyrie Mega"
    if key == "darius":
        ability_name = "icon_" + ability_name
    if key == "diana" and ability_key == "passive":
        ability_name = "lunarblade"
    if key == "elise" and ability_index == 2:
        ability_name = "spider"  # leave off the real ability_name
    if key == "jax":
        key = "armsmaster"
    if key == "jayce" and ability_name == "Shock Blast":
        ability_name = "Shot Blast"
    if key == "jayce" and ability_name == "Transform Mercury Hammer":
        ability_name = "Transform Hammer"
    if key == "leesin":
        key = "blindmonk"
    if key == "blindmonk" and ability_index == 1:
        ability_index = "one"
    if key == "blindmonk" and ability_index == 2:
        ability_index = "two"
    if key == "morgana":
        key = "fallenangel"
    if key == "fallenangel" and ability_key == "passive":
        ability_name = "Empathize"
    if key == "rammus":
        key = "armordillo"
    if key == "armordillo" and ability_key == "passive":
        ability_name = "Scavenge Armor"
    if key == "riven" and ability_key == "r":
        ability_name = "Wind Scar"
    if key == "shaco":
        key = "jester"
    if key == "jester" and ability_key == "passive":
        ability_name = "Careful Strikes"
    if key == "shyvana" and ability_key == "passive":
        ability_name = "Reinforced Scales"
    if key == "sion" and ability_name == "Death Surge":
        ability_name = "passive2"
    if key == "twistedfate":
        key = "cardmaster"
    if key == "cardmaster" and ability_key == "passive":
        ability_name = "Seal Fate"
    if key == "veigar" and ability_key == "passive":
        ability_name = "Entropy"
    if key == "ziggs" and ability_key == "passive":
        ability_name = "passiveready"

    best_fn, best_score, best_guess = perform_guess(
        key, ability_name, ability_key, ability_index, filenames, use_underscores=True
    )

    if best_score < 100 and ability_key == "passive":
        fn, score, guess = perform_guess(key, ability_name, "p", ability_index, filenames, use_underscores=True)
        if score > best_score:
            best_fn, best_score, best_guess = fn, score, guess

    if best_score < 100:
        # Don't use underscores in build_guess
        fn, score, guess = perform_guess(
            key, ability_name, ability_key, ability_index, filenames, use_underscores=False,
        )
        if score > best_score:
            best_fn, best_score, best_guess = fn, score, guess

    if best_score < 100 and ability_key == "passive":
        # Don't use underscores in build_guess
        fn, score, guess = perform_guess(key, ability_name, "p", ability_index, filenames, use_underscores=False)
        if score > best_score:
            best_fn, best_score, best_guess = fn, score, guess

    if False and best_score < 100:
        print(f"{key}-{ability_name}({ability_key}): {best_fn} ~ {best_guess}  {best_score}")

    return f"http://raw.communitydragon.org/latest/game/assets/characters/{KEY.lower()}/hud/icons2d/{best_fn}"
