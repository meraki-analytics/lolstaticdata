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
    return f"https://cdn.communitydragon.org/latest/champion/{key}/ability-icon/{ability_key[0]}"
    # Use ddragon if we can
    """
    if ability_index == 1 and ability_key in ("Q", "W", "E", "R"):
        spell_index = {"Q": 0, "W": 1, "E": 2, "R": 3}[ability_key]
        return f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/img/spell/{ddragon_champion['spells'][spell_index]['image']['full']}"

        #WRONG ICONS AS OF 25/5/2020
        # Vladimir(E & R), TwistedFate(PQWE)
        # Shyvana(all), Zed(WER), Rammus(all), Orianna(R),
        # Shaco(all), Qiyana(all), Vayne(R)

        #FIXED AS OF 25/5/2020
        # Ahri(P), AurelionSol(WE), Graves(PQR), Chogath(QE), Corki(P), Darius(All), Diana(All), Draven(E),
        # Elise(all), Fiddlesticks(all), Gnar(R), Janna(R), Jax(all), Leblanc(P), LeeSin(all), Lulu(E),
        # Lux(Q & E swapped), Malphite(W), Morgana(R), Naut(R & E swapped)

    # Special cases
    if key.lower() == "gnar" and ability_key == "r":
        key = "gnarbig"
    if key.lower() == "ahri" and ability_key == "passive":
        ability_name = "souleater"
    if key.lower() == "aurelionsol" and ability_key == "w":
        ability_name = "starsin"
    if key.lower() == "aurelionsol" and ability_key == "e":
        ability_name = "fly"
    if key.lower() == "graves" and ability_key == "passive":
        ability_name = "truegrit"
    if key.lower() == "graves" and ability_key == "q":
        ability_name = "buckshot"
    if key.lower() == "graves" and ability_key == "q":
        ability_name = "highnoon"
    if key.lower() == "chogath":
        key = "greenterror"
        if ability_key == "passive":
            ability_name = "tailspike"
        if ability_key == "q":
            ability_name = "spikeslam"
        if ability_key == "e":
            ability_name = "chitinousexoplates"
    if key.lower() == "corki" and ability_key == "passive":
        ability_name = "thepackage"
    if key.lower() == "darius":
        if ability_key == 'w':
            ability_name = "hamstring"
        if ability_key == 'e':
            ability_name = "axe_grab"
        if ability_key == 'r':
            ability_name = "sudden_death"
        ability_name = "icon_" + ability_name
    if key.lower() == "diana":
        if ability_key == "passive":
            ability_name = "lunarblade"
        if ability_key == "q":
            ability_name = "moonsedge"
        if ability_key == "w":
            ability_name = "lunarshower"
        if ability_key == "e":
            ability_name = "fasterthanlight"
        if ability_key == "r":
            ability_name = "moonfall"
    if key.lower() == "draven" and ability_key == "e":
        ability_name = "twinaxe"
    if key.lower() == "elise" and ability_key != "r":
        key = "spiderhuman"  # leave off the real ability_name
    if key.lower() == "fiddlesticks":
        ability_name += ".fiddlesticksrework"
    if key.lower() == "janna" and ability_key == "r":
        ability_name = "reapthewhirlwind"
    if key.lower() == "jax":
        key = "armsmaster"
        if ability_key == "passive":
            ability_name = "masterofarms"
        if ability_key == "q":
            ability_name = "relentlessassault"
        if ability_key == "w":
            ability_name = "empower"
        if ability_key == "e":
            ability_name = "disarm"
        if ability_key == "r":
            ability_name = "coupdegrace"
    if key.lower() == "leblanc" and ability_key == "passive":
        ability_name = ""
    if key.lower() == "leesin":
        key = "blindmonk"
        if ability_key != "passive" and ability_key != "r":
            ability_key += "one"
    if key.lower() == "lulu":
        if ability_key == "q":
            ability_name = "glitterbolt"
        if ability_key == "e":
            ability_name = "commandpix"
        if ability_key == "r":
            ability_name = "giantgrowth"
    if key.lower() == "lux":
        if ability_key == "q":
            ability_name = "crashingblitz2"
        if ability_key == "e":
            ability_name = "lightstrikekugel"
    if key.lower() == "malphite" and ability_key == "w":
        ability_name = "brutalstrikes"
    if key.lower() == "morgana":
        key = "fallenangel"
        if ability_key == "passive":
            ability_name = "empathize"
        if ability_key == "r":
            ability_name = "purgatory"
    if key.lower() == "rammus":
        key = "armordillo"
    if key.lower() == "armordillo" and ability_key == "passive":
        ability_name = "Scavenge Armor"
    if key.lower() == "riven" and ability_key == "r":
        ability_name = "Wind Scar"
    if key.lower() == "shaco":
        key = "jester"
    if key.lower() == "jester" and ability_key == "passive":
        ability_name = "Careful Strikes"
    if key.lower() == "shyvana" and ability_key == "passive":
        ability_name = "Reinforced Scales"
    if key.lower() == "sion" and ability_name == "Death Surge":
        ability_name = "passive2"
    if key.lower() == "twistedfate":
        key = "cardmaster"
    if key.lower() == "cardmaster" and ability_key == "passive":
        ability_name = "Seal Fate"
    if key.lower() == "veigar" and ability_key == "passive":
        ability_name = "Entropy"
    if key.lower() == "ziggs" and ability_key == "passive":
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
    """
