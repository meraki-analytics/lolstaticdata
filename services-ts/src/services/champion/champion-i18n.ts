export const TARGETING_CODES = {
    SELF_AREA: "SELF_AREA",
    SELF: "SELF",
    UNIT_TARGETED: "UNIT_TARGETED",
    DIRECTION: "DIRECTION",
    AREA: "AREA",
    LOCATION: "LOCATION",
    LOCATION_CLAMPED: "LOCATION_CLAMPED"
} as const;

export const AFFECT_CODES = {
    SELF: "SELF",
    ALLIES: "ALLIES",
    ENEMIES: "ENEMIES"
} as const;

type LocaleCode = "en_US" | "de_DE";

type LocaleTerms = {
    targeting: Record<string, string>;
    affects: Record<string, string>;
    resources: Record<string, string>;
    damageTypes: Record<string, string>;
    attackTypes: Record<string, string>;
    units: Record<string, string>;
    projectile: Record<string, string>;
};

const TERMS: Record<LocaleCode, LocaleTerms> = {
    en_US: {
        targeting: {
            SELF_AREA: "Self (Area)",
            SELF: "Self",
            UNIT_TARGETED: "Unit-targeted",
            DIRECTION: "Direction",
            AREA: "Area",
            LOCATION: "Location",
            LOCATION_CLAMPED: "Location Clamped"
        },
        affects: {
            SELF: "Self",
            ALLIES: "Allies",
            ENEMIES: "Enemies"
        },
        resources: {
            NONE: "No Cost",
            NO_COST: "No Cost",
            MANA: "Mana",
            ENERGY: "Energy",
            RAGE: "Rage",
            FURY: "Fury",
            HEALTH: "Health",
            FEROCITY: "Ferocity",
            BLOOD_WELL: "Blood Well",
            OTHER: "Other"
        },
        damageTypes: {
            PHYSICAL_DAMAGE: "Physical Damage",
            MAGIC_DAMAGE: "Magic Damage",
            MIXED_DAMAGE: "Mixed Damage"
        },
        attackTypes: {
            MELEE: "Melee",
            RANGED: "Ranged"
        },
        units: {
            PERCENT: "%",
            SECONDS: "seconds",
            UNITS: "units",
            HEALTH: "health",
            MANA: "mana",
            ENERGY: "energy",
            RAGE: "rage",
            FURY: "fury",
            FEROCITY: "ferocity",
            RESOURCE: "resource",
            STACKS: "stacks",
            DAMAGE: "damage",
            PHYSICAL_DAMAGE: "physical damage",
            MAGIC_DAMAGE: "magic damage"
        },
        projectile: {
            MISSILE: "Missile"
        }
    },
    de_DE: {
        targeting: {
            SELF_AREA: "Selbst (Bereich)",
            SELF: "Selbst",
            UNIT_TARGETED: "Zielgerichtet",
            DIRECTION: "Richtung",
            AREA: "Bereich",
            LOCATION: "Position",
            LOCATION_CLAMPED: "Begrenzte Position"
        },
        affects: {
            SELF: "Selbst",
            ALLIES: "Verbundete",
            ENEMIES: "Gegner"
        },
        resources: {
            NONE: "Keine Kosten",
            NO_COST: "Keine Kosten",
            MANA: "Mana",
            ENERGY: "Energie",
            RAGE: "Wut",
            FURY: "Raserei",
            HEALTH: "Leben",
            FEROCITY: "Wildheit",
            BLOOD_WELL: "Blutbrunnen",
            OTHER: "Sonstige"
        },
        damageTypes: {
            PHYSICAL_DAMAGE: "Physischer Schaden",
            MAGIC_DAMAGE: "Magischer Schaden",
            MIXED_DAMAGE: "Gemischter Schaden"
        },
        attackTypes: {
            MELEE: "Nahkampf",
            RANGED: "Fernkampf"
        },
        units: {
            PERCENT: "%",
            SECONDS: "Sekunden",
            UNITS: "Einheiten",
            HEALTH: "Leben",
            MANA: "Mana",
            ENERGY: "Energie",
            RAGE: "Wut",
            FURY: "Raserei",
            FEROCITY: "Wildheit",
            RESOURCE: "Ressource",
            STACKS: "Stapel",
            DAMAGE: "Schaden",
            PHYSICAL_DAMAGE: "physischer Schaden",
            MAGIC_DAMAGE: "magischer Schaden"
        },
        projectile: {
            MISSILE: "Geschoss"
        }
    }
};

const TARGETING_ALIASES: Record<string, string> = {
    selfarea: TARGETING_CODES.SELF_AREA,
    self: TARGETING_CODES.SELF,
    unittargeted: TARGETING_CODES.UNIT_TARGETED,
    direction: TARGETING_CODES.DIRECTION,
    area: TARGETING_CODES.AREA,
    location: TARGETING_CODES.LOCATION,
    locationclamped: TARGETING_CODES.LOCATION_CLAMPED
};

const AFFECT_ALIASES: Record<string, string> = {
    self: AFFECT_CODES.SELF,
    allies: AFFECT_CODES.ALLIES,
    enemies: AFFECT_CODES.ENEMIES
};

const UNIT_ALIASES: Record<string, string> = {
    "": "",
    "%": "PERCENT",
    percent: "PERCENT",
    seconds: "SECONDS",
    second: "SECONDS",
    units: "UNITS",
    unit: "UNITS",
    health: "HEALTH",
    mana: "MANA",
    energy: "ENERGY",
    rage: "RAGE",
    fury: "FURY",
    ferocity: "FEROCITY",
    resource: "RESOURCE",
    stacks: "STACKS",
    stack: "STACKS",
    damage: "DAMAGE",
    physicaldamage: "PHYSICAL_DAMAGE",
    magicdamage: "MAGIC_DAMAGE"
};

const RESOURCE_ALIASES: Record<string, string> = {
    nocost: "NO_COST",
    manaless: "NO_COST",
    abilityresourcename: "RESOURCE",
    resource: "RESOURCE",
    bloodwell: "BLOOD_WELL",
    blutbrunnen: "BLOOD_WELL",
    blutsee: "BLOOD_WELL"
};

function normalizeResourceToken(value: string): string {
    return value
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "");
}

const RESOURCE_LOOKUP: Record<string, string> = (() => {
    const lookup: Record<string, string> = { ...RESOURCE_ALIASES };

    for (const localeTerms of Object.values(TERMS)) {
        for (const [code, label] of Object.entries(localeTerms.resources)) {
            const normalizedCode = normalizeResourceToken(code);
            if (normalizedCode) {
                lookup[normalizedCode] = code;
            }

            const normalizedLabel = normalizeResourceToken(label);
            if (normalizedLabel) {
                lookup[normalizedLabel] = code;
            }
        }
    }

    return lookup;
})();

const RESOURCE_TOKENS = Object.keys(RESOURCE_LOOKUP)
    .filter((token) => token.length > 2)
    .sort((a, b) => b.length - a.length);

function canonicalResourceCode(code: string): string {
    if (code === "NONE") {
        return "NO_COST";
    }
    if (code === "RESOURCE") {
        return "OTHER";
    }
    return code;
}

function normalizeLocale(locale: string): LocaleCode {
    const lower = locale.toLowerCase();
    if (lower.startsWith("de")) {
        return "de_DE";
    }
    return "en_US";
}

function normalizeToken(value: string): string {
    return value.trim().toLowerCase().replace(/[^a-z0-9%]+/g, "");
}

function resolveAlias(value: string, aliases: Record<string, string>): string {
    const trimmed = value.trim();
    if (!trimmed) {
        return "";
    }

    if (trimmed === trimmed.toUpperCase()) {
        return trimmed;
    }

    return aliases[normalizeToken(trimmed)] ?? trimmed;
}

function translate(lookup: Record<string, string>, key: string): string {
    if (!key) {
        return "";
    }
    return lookup[key] ?? key;
}

export function localizeTargeting(value: string, locale: string): string {
    const localeCode = normalizeLocale(locale);
    const code = resolveAlias(value, TARGETING_ALIASES);
    return translate(TERMS[localeCode].targeting, code);
}

export function localizeAffects(value: string, locale: string): string {
    if (!value.trim()) {
        return "";
    }

    const localeCode = normalizeLocale(locale);
    const tokens = value.split(",").map((part) => part.trim()).filter(Boolean);
    return tokens
        .map((token) => translate(TERMS[localeCode].affects, resolveAlias(token, AFFECT_ALIASES)))
        .join(", ");
}

export function localizeResource(value: string, locale: string): string {
    const localeCode = normalizeLocale(locale);
    const key = value.trim().toUpperCase();
    return translate(TERMS[localeCode].resources, key);
}

export function parseResourceCode(value: string | undefined): string | undefined {
    if (!value) {
        return undefined;
    }

    const normalized = normalizeResourceToken(value);
    if (!normalized) {
        return undefined;
    }

    const exact = RESOURCE_LOOKUP[normalized];
    if (exact) {
        return canonicalResourceCode(exact);
    }

    for (const token of RESOURCE_TOKENS) {
        if (!normalized.includes(token)) {
            continue;
        }
        return canonicalResourceCode(RESOURCE_LOOKUP[token]);
    }

    return undefined;
}

export function localizeDamageType(value: string, locale: string): string {
    const localeCode = normalizeLocale(locale);
    const key = value.trim().toUpperCase();
    return translate(TERMS[localeCode].damageTypes, key);
}

export function localizeAttackType(value: string, locale: string): string {
    const localeCode = normalizeLocale(locale);
    const key = value.trim().toUpperCase();
    return translate(TERMS[localeCode].attackTypes, key);
}

export function localizeUnit(value: string, locale: string): string {
    const localeCode = normalizeLocale(locale);
    const key = resolveAlias(value, UNIT_ALIASES);
    return translate(TERMS[localeCode].units, key);
}

export function localizeProjectile(value: string, locale: string): string {
    const localeCode = normalizeLocale(locale);
    const key = value.trim().toUpperCase();
    return translate(TERMS[localeCode].projectile, key);
}

export function localizeLevelingUnits(
    leveling: Array<Record<string, unknown>>,
    locale: string
): Array<Record<string, unknown>> {
    return leveling.map((entry) => {
        const modifiers = Array.isArray(entry.modifiers)
            ? entry.modifiers.map((modifier) => {
                if (!modifier || typeof modifier !== "object") {
                    return modifier;
                }
                const units = Array.isArray((modifier as Record<string, unknown>).units)
                    ? ((modifier as Record<string, unknown>).units as unknown[]).map((unit) =>
                        localizeUnit(String(unit ?? ""), locale)
                    )
                    : (modifier as Record<string, unknown>).units;
                return {
                    ...(modifier as Record<string, unknown>),
                    units
                };
            })
            : entry.modifiers;

        return {
            ...entry,
            modifiers
        };
    });
}