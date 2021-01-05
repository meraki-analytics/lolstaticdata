from typing import Union
from dataclasses import dataclass
import dataclasses_json

from .utils import OrderedEnum

Number = Union[float, int]


class DamageType(OrderedEnum):
    PHYSICAL_DAMAGE = "PHYSICAL_DAMAGE"
    MAGIC_DAMAGE = "MAGIC_DAMAGE"
    TRUE_DAMAGE = "TRUE_DAMAGE"
    PURE_DAMAGE = "PURE_DAMAGE"
    MIXED_DAMAGE = "MIXED_DAMAGE"
    OTHER_DAMAGE = "OTHER_DAMAGE"


@dataclasses_json.dataclass_json(letter_case=dataclasses_json.LetterCase.CAMEL)
@dataclass
class Stat:
    flat: Number = 0.0
    percent: Number = 0.0
    per_level: Number = 0.0
    percent_per_level: Number = 0.0
    percent_base: Number = 0.0
    percent_bonus: Number = 0.0

    @staticmethod
    def _grow_stat(base, per_level, level):
        """Grow a base stat based on the level of the champion."""
        # OLD FORMULA return base + per_level*(7./400.*(level*level-1) + 267./400.*(level-1))
        return base + per_level * (level - 1) * (0.7025 + 0.0175 * (level - 1))

        # NEW formula = b+g×(n−1)×(0.7025+0.0175×(n−1))

    def total(self, level: int):
        """Calculate the total stat value given all its attributes."""
        base = self._grow_stat(self.flat, self.per_level, level)
        total = ((base * (1.0 + self.percent_base)) + self.flat + (self.per_level * level)) * (
            1.0 + self.percent + (self.percent_per_level * level)
        )
        bonus = total - base
        total += self.percent_bonus * bonus
        return total

    def __add__(self, other: "Stat"):
        return Stat(
            flat=self.flat + other.flat,
            percent=self.percent + other.percent,
            per_level=self.per_level + other.per_level,
            percent_per_level=self.percent_per_level + other.percent_per_level,
            percent_base=self.percent_base + other.percent_base,
            percent_bonus=self.percent_bonus + other.percent_bonus,
        )

    def __sub__(self, other: "Stat"):
        return Stat(
            flat=self.flat - other.flat,
            percent=self.percent - other.percent,
            per_level=self.per_level - other.per_level,
            percent_per_level=self.percent_per_level - other.percent_per_level,
            percent_base=self.percent_base - other.percent_base,
            percent_bonus=self.percent_bonus - other.percent_bonus,
        )


class Health(Stat):
    pass


class HealthRegen(Stat):
    pass


class Mana(Stat):
    pass


class ManaRegen(Stat):
    pass


class Armor(Stat):
    pass


class MagicResistance(Stat):
    pass


class AttackDamage(Stat):
    pass


class AbilityPower(Stat):
    pass


class Movespeed(Stat):
    pass


class CriticalStrikeChance(Stat):
    pass


class AttackSpeed(Stat):
    pass


class Lethality(Stat):
    pass


class AttackRange(Stat):
    pass


class CooldownReduction(Stat):
    pass


class GoldPer10(Stat):
    pass


class HealAndShieldPower(Stat):
    pass


class Lifesteal(Stat):
    pass


class MagicPenetration(Stat):
    pass


class ArmorPenetration(Stat):
    pass


class AbilityHaste(Stat):
    pass


class OmniVamp(Stat):
    pass

class Tenacity(Stat):
    pass