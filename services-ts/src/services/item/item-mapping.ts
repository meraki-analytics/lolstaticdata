import type {
    DDragonItem,
    DDragonMapPayload,
    ItemStats,
    MapAvailability,
    MappedEffect,
    StatValue,
    WrappedItem
} from "./item-types.js";

const MAP_MODE_BY_ID: Record<number, string> = {
    11: "SUMMONERS_RIFT",
    12: "ARAM",
    14: "ARAM",
    21: "NEXUS_BLITZ",
    30: "ARENA"
};

const STAT_FIELD_MAPPINGS: Record<string, { field: keyof ItemStats; dimension: "flat" | "percent" }> = {
    FlatArmorMod: { field: "armor", dimension: "flat" },
    FlatCritChanceMod: { field: "criticalStrikeChance", dimension: "percent" },
    FlatHPPoolMod: { field: "health", dimension: "flat" },
    FlatHPRegenMod: { field: "healthRegen", dimension: "flat" },
    FlatMPPoolMod: { field: "mana", dimension: "flat" },
    FlatMagicDamageMod: { field: "abilityPower", dimension: "flat" },
    FlatMovementSpeedMod: { field: "movespeed", dimension: "flat" },
    FlatPhysicalDamageMod: { field: "attackDamage", dimension: "flat" },
    FlatSpellBlockMod: { field: "magicResistance", dimension: "flat" },
    PercentAttackSpeedMod: { field: "attackSpeed", dimension: "percent" },
    PercentLifeStealMod: { field: "lifesteal", dimension: "percent" },
    PercentMovementSpeedMod: { field: "movespeed", dimension: "percent" }
};

export type MapNameIndex = Record<number, string>;

function stripMarkup(text: string): string {
    return text
        .replace(/&nbsp;/gi, " ")
        .replace(/&amp;/gi, "&")
        .replace(/&quot;/gi, "\"")
        .replace(/&#39;/gi, "'")
        .replace(/<[^>]*>/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

function mapModeFromId(mapId: number): string {
    return MAP_MODE_BY_ID[mapId] ?? `MAP_${mapId}`;
}

function unique(values: string[]): string[] {
    return Array.from(new Set(values));
}

function createZeroStat(): StatValue {
    return {
        flat: 0,
        percent: 0,
        perLevel: 0,
        percentPerLevel: 0,
        percentBase: 0,
        percentBonus: 0
    };
}

function createEmptyItemStats(): ItemStats {
    return {
        abilityPower: createZeroStat(),
        armor: createZeroStat(),
        armorPenetration: createZeroStat(),
        attackDamage: createZeroStat(),
        attackSpeed: createZeroStat(),
        cooldownReduction: createZeroStat(),
        criticalStrikeChance: createZeroStat(),
        goldPer10: createZeroStat(),
        healAndShieldPower: createZeroStat(),
        health: createZeroStat(),
        healthRegen: createZeroStat(),
        lethality: createZeroStat(),
        lifesteal: createZeroStat(),
        magicPenetration: createZeroStat(),
        magicResistance: createZeroStat(),
        mana: createZeroStat(),
        manaRegen: createZeroStat(),
        movespeed: createZeroStat(),
        abilityHaste: createZeroStat(),
        omnivamp: createZeroStat(),
        tenacity: createZeroStat(),
        criticalStrikeDamage: createZeroStat()
    };
}

function normalizePercentStat(value: number): number {
    if (!Number.isFinite(value)) {
        return 0;
    }
    return Math.abs(value) <= 1 ? value * 100 : value;
}

function parseStats(stats: Record<string, number> | undefined): ItemStats {
    const mapped = createEmptyItemStats();
    if (!stats) {
        return mapped;
    }

    for (const [code, value] of Object.entries(stats)) {
        const mapping = STAT_FIELD_MAPPINGS[code];
        if (!mapping) {
            continue;
        }

        const numeric = Number(value ?? 0);
        mapped[mapping.field][mapping.dimension] = mapping.dimension === "percent"
            ? normalizePercentStat(numeric)
            : (Number.isFinite(numeric) ? numeric : 0);
    }

    return mapped;
}

function parseEffects(effects: Record<string, string> | undefined): MappedEffect[] {
    if (!effects) {
        return [];
    }

    return Object.entries(effects)
        .map(([code, raw]) => {
            const match = /^Effect(\d+)Amount$/i.exec(code);
            const index = match ? Number(match[1]) : 0;
            const parsedValues = String(raw ?? "")
                .split("/")
                .map((entry) => Number(entry.trim()))
                .filter((value) => Number.isFinite(value));

            return {
                code,
                index,
                key: index > 0 ? `effect${index}` : code.toLowerCase(),
                token: index > 0 ? `e${index}` : code.toLowerCase(),
                raw: String(raw ?? ""),
                values: parsedValues
            };
        })
        .sort((a, b) => a.index - b.index || a.code.localeCompare(b.code));
}

function parseColloq(colloq: string | undefined): string[] {
    if (!colloq) {
        return [];
    }

    return colloq
        .split(";")
        .map((entry) => entry.trim())
        .filter((entry) => entry.length > 0);
}

function toIntList(values: string[] | undefined): number[] {
    return (values ?? [])
        .map((entry) => Number(entry))
        .filter((entry) => Number.isInteger(entry));
}

function parseMapAvailability(
    maps: Record<string, boolean> | undefined,
    mapNames: MapNameIndex
): MapAvailability[] {
    if (!maps) {
        return [];
    }

    return Object.entries(maps)
        .filter(([, enabled]) => Boolean(enabled))
        .map(([mapId]) => Number(mapId))
        .filter((mapId) => Number.isInteger(mapId))
        .sort((a, b) => a - b)
        .map((mapId) => ({
            id: mapId,
            key: `MAP_${mapId}`,
            label: mapNames[mapId] || `MAP_${mapId}`,
            mode: mapModeFromId(mapId)
        }));
}

function buildItemIconUrl(patchVersion: string, imageName: string): string {
    if (!imageName) {
        return "";
    }
    return `https://ddragon.leagueoflegends.com/cdn/${patchVersion}/img/item/${imageName}`;
}

export function buildMapNameIndex(payload: DDragonMapPayload): MapNameIndex {
    return Object.fromEntries(
        Object.entries(payload.data)
            .map(([id, map]) => [Number(id), String(map.MapName ?? "").trim()])
            .filter(([id]) => Number.isInteger(id))
    ) as MapNameIndex;
}

export function buildWrappedItem(
    patchVersion: string,
    id: number,
    item: DDragonItem,
    mapNames: MapNameIndex
): WrappedItem {
    const imageName = item.image?.full ?? "";
    const richDescription = String(item.description ?? "");
    const maps = parseMapAvailability(item.maps, mapNames);

    return {
        id,
        name: String(item.name ?? ""),
        availableOn: unique(maps.map((map) => map.mode)).sort((a, b) => a.localeCompare(b)),
        description: {
            rich: richDescription,
            plain: stripMarkup(richDescription),
            short: String(item.plaintext ?? "")
        },
        icon: {
            full: imageName,
            sprite: String(item.image?.sprite ?? ""),
            url: buildItemIconUrl(patchVersion, imageName)
        },
        build: {
            from: toIntList(item.from),
            into: toIntList(item.into),
            depth: Number(item.depth ?? 0),
            specialRecipe: Number(item.specialRecipe ?? 0)
        },
        availability: {
            inStore: item.inStore !== false,
            purchasable: Boolean(item.gold?.purchasable),
            consumed: Boolean(item.consumed),
            consumeOnFull: Boolean(item.consumeOnFull),
            hideFromAll: Boolean(item.hideFromAll),
            requiredChampion: String(item.requiredChampion ?? ""),
            maps
        },
        gold: {
            base: Number(item.gold?.base ?? 0),
            total: Number(item.gold?.total ?? 0),
            sell: Number(item.gold?.sell ?? 0)
        },
        tags: Array.isArray(item.tags) ? item.tags.map((tag) => String(tag)) : [],
        colloq: parseColloq(item.colloq),
        stats: parseStats(item.stats),
        effects: parseEffects(item.effect)
    };
}
