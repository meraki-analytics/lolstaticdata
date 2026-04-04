import fs from "node:fs/promises";
import path from "node:path";
import type { GenerationService } from "../contracts.js";
import type { GenerationContext, GenerationResult } from "../types.js";
import { ObservabilityService } from "./observability-service.js";

interface DDragonItemImage {
    full?: string;
    sprite?: string;
    group?: string;
    x?: number;
    y?: number;
    w?: number;
    h?: number;
}

interface DDragonItemGold {
    base?: number;
    total?: number;
    sell?: number;
    purchasable?: boolean;
}

interface DDragonItem {
    name?: string;
    description?: string;
    plaintext?: string;
    colloq?: string;
    from?: string[];
    into?: string[];
    depth?: number;
    tags?: string[];
    maps?: Record<string, boolean>;
    stats?: Record<string, number>;
    effect?: Record<string, string>;
    image?: DDragonItemImage;
    gold?: DDragonItemGold;
    inStore?: boolean;
    specialRecipe?: number;
    requiredChampion?: string;
    consumed?: boolean;
    consumeOnFull?: boolean;
    hideFromAll?: boolean;
}

interface DDragonItemPayload {
    data: Record<string, DDragonItem>;
}

interface DDragonMapEntry {
    MapName?: string;
    MapId?: string;
}

interface DDragonMapPayload {
    data: Record<string, DDragonMapEntry>;
}

interface MapAvailability {
    id: number;
    key: string;
    label: string;
    mode: string;
}

interface StatValue {
    flat: number;
    percent: number;
    perLevel: number;
    percentPerLevel: number;
    percentBase: number;
    percentBonus: number;
}

interface ItemStats {
    abilityPower: StatValue;
    armor: StatValue;
    armorPenetration: StatValue;
    attackDamage: StatValue;
    attackSpeed: StatValue;
    cooldownReduction: StatValue;
    criticalStrikeChance: StatValue;
    goldPer10: StatValue;
    healAndShieldPower: StatValue;
    health: StatValue;
    healthRegen: StatValue;
    lethality: StatValue;
    lifesteal: StatValue;
    magicPenetration: StatValue;
    magicResistance: StatValue;
    mana: StatValue;
    manaRegen: StatValue;
    movespeed: StatValue;
    abilityHaste: StatValue;
    omnivamp: StatValue;
    tenacity: StatValue;
    criticalStrikeDamage: StatValue;
}

interface MappedEffect {
    code: string;
    index: number;
    key: string;
    token: string;
    raw: string;
    values: number[];
}

interface WrappedItem {
    id: number;
    name: string;
    availableOn: string[];
    description: {
        rich: string;
        plain: string;
        short: string;
    };
    icon: {
        full: string;
        sprite: string;
        url: string;
    };
    build: {
        from: number[];
        into: number[];
        depth: number;
        specialRecipe: number;
    };
    availability: {
        inStore: boolean;
        purchasable: boolean;
        consumed: boolean;
        consumeOnFull: boolean;
        hideFromAll: boolean;
        requiredChampion: string;
        maps: MapAvailability[];
    };
    gold: {
        base: number;
        total: number;
        sell: number;
    };
    tags: string[];
    colloq: string[];
    stats: ItemStats;
    effects: MappedEffect[];
}

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

function parseMapAvailability(
    maps: Record<string, boolean> | undefined,
    mapNames: Record<number, string>
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
            label: mapNames[mapId] ?? `MAP_${mapId}`,
            mode: mapModeFromId(mapId)
        }));
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

async function fetchItemPayload(patchVersion: string, locale: string): Promise<DDragonItemPayload> {
    const url = `https://ddragon.leagueoflegends.com/cdn/${patchVersion}/data/${locale}/item.json`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Request failed (${response.status}) for ${url}`);
    }
    return (await response.json()) as DDragonItemPayload;
}

async function fetchMapPayload(patchVersion: string, locale: string): Promise<DDragonMapPayload> {
    const url = `https://ddragon.leagueoflegends.com/cdn/${patchVersion}/data/${locale}/map.json`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Request failed (${response.status}) for ${url}`);
    }
    return (await response.json()) as DDragonMapPayload;
}

export class ItemService implements GenerationService {
    readonly name = "ItemService";

    constructor(private readonly logger: ObservabilityService = new ObservabilityService()) { }

    async generate(context: GenerationContext): Promise<GenerationResult> {
        try {
            this.logger.info(`[items:${context.locale}] Starting DDragon item generation for patch ${context.patchVersion}.`);

            const targetItemsDir = path.join(context.outputDir, "items");
            await fs.mkdir(targetItemsDir, { recursive: true });

            const existingTargetEntries = await fs.readdir(targetItemsDir);
            await Promise.all(
                existingTargetEntries
                    .filter((name) => name.endsWith(".json"))
                    .map((name) => fs.unlink(path.join(targetItemsDir, name)))
            );

            const [payload, mapPayload] = await Promise.all([
                fetchItemPayload(context.patchVersion, context.locale),
                fetchMapPayload(context.patchVersion, context.locale)
            ]);
            const mapNames = Object.fromEntries(
                Object.entries(mapPayload.data)
                    .map(([id, map]) => [Number(id), String(map.MapName ?? "").trim()])
                    .filter(([id]) => Number.isInteger(id))
            ) as Record<number, string>;
            const allItems = Object.entries(payload.data)
                .map(([id, item]) => ({ id: Number(id), item }))
                .filter(({ id }) => Number.isInteger(id));
            const inStoreItems = allItems.filter(({ item }) => item.inStore !== false);

            this.logger.info(
                `[items:${context.locale}] Filtered to ${inStoreItems.length}/${allItems.length} items (inStore != false).`
            );

            const wrapped: Record<string, WrappedItem> = {};
            let written = 0;
            const progressStep = 50;

            for (const { id, item } of inStoreItems) {
                const imageName = item.image?.full ?? "";
                const richDescription = String(item.description ?? "");
                const maps = parseMapAvailability(item.maps, mapNames);
                const mappedItem: WrappedItem = {
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
                        url: imageName
                            ? `https://ddragon.leagueoflegends.com/cdn/${context.patchVersion}/img/item/${imageName}`
                            : ""
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

                wrapped[String(id)] = mappedItem;

                const filePath = path.join(targetItemsDir, `${id}.json`);
                await fs.writeFile(filePath, JSON.stringify(mappedItem, null, 2), "utf8");

                written += 1;
                if (written % progressStep === 0 || written === inStoreItems.length) {
                    this.logger.info(`[items:${context.locale}] Wrote item payloads ${written}/${inStoreItems.length}.`);
                }
            }

            const sorted = Object.fromEntries(
                Object.entries(wrapped).sort((a, b) => Number(a[0]) - Number(b[0]))
            );
            await fs.writeFile(path.join(context.outputDir, "items.json"), JSON.stringify(sorted, null, 2), "utf8");

            const mapCoverage = new Set<string>();
            Object.values(sorted).forEach((item) => {
                item.availableOn.forEach((mode) => mapCoverage.add(mode));
            });

            return {
                service: this.name,
                success: true,
                details: `Item generation completed via DDragon wrapper (${context.locale}, ${inStoreItems.length} items, maps: ${Array.from(mapCoverage).sort().join(", ")})`
            };
        } catch (error) {
            const msg = error instanceof Error ? error.message : String(error);
            this.logger.error(`[items:${context.locale}] Generation failed: ${msg}`);
            return {
                service: this.name,
                success: false,
                details: `Item generation failed: ${msg}`
            };
        }
    }
}
