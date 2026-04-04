import fs from "node:fs/promises";
import path from "node:path";
import type { GenerationService } from "../contracts.js";
import type { GenerationContext, GenerationResult } from "../types.js";

const CDRAGON_BASE = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default";
const CDRAGON_CHAMPION_SUMMARY_URL = `${CDRAGON_BASE}/v1/champion-summary.json`;

interface CDragonChampionSummary {
    id: number;
    name: string;
    description: string;
    alias: string;
    squarePortraitPath: string;
    roles: string[];
}

interface CDragonSpell {
    spellKey?: string;
    name?: string;
    description?: string;
    dynamicDescription?: string;
    abilityIconPath?: string;
    cost?: number[] | number | string;
    cooldown?: number[] | number | string;
    range?: number[] | number;
    costCoefficients?: number[];
    cooldownCoefficients?: number[];
    effectAmounts?: Record<string, number[]>;
}

interface CDragonChampionDetail {
    id: number;
    name: string;
    alias: string;
    title: string;
    shortBio?: string;
    squarePortraitPath?: string;
    tacticalInfo?: {
        style?: number;
        difficulty?: number;
        damageType?: string;
        attackType?: string;
    };
    playstyleInfo?: {
        damage?: number;
        durability?: number;
        crowdControl?: number;
        mobility?: number;
        utility?: number;
    };
    roles?: string[];
    passive?: {
        name?: string;
        description?: string;
        abilityIconPath?: string;
    };
    spells?: CDragonSpell[];
    skins?: Array<{
        id: number;
        name: string;
        isBase: boolean;
        skinClassification?: string;
        splashPath?: string;
        uncenteredSplashPath?: string;
        tilePath?: string;
        loadScreenPath?: string;
    }>;
}

interface DDragonChampion {
    partype?: string;
    stats?: Record<string, number>;
}

interface DDragonChampionFull {
    data: Record<string, DDragonChampion>;
}

interface StatValue {
    flat: number;
    percent: number;
    perLevel: number;
    percentPerLevel: number;
}

function stat(flat = 0, perLevel = 0): StatValue {
    return {
        flat,
        percent: 0,
        perLevel,
        percentPerLevel: 0
    };
}

function toAssetUrl(assetPath: string | undefined): string {
    if (!assetPath) {
        return "";
    }
    if (assetPath.startsWith("http://") || assetPath.startsWith("https://")) {
        return assetPath;
    }
    const normalized = assetPath.replace(/\\/g, "/");
    if (normalized.startsWith("/lol-game-data/assets/")) {
        const tail = normalized.replace("/lol-game-data/assets", "");
        return `${CDRAGON_BASE}${tail}`;
    }
    if (normalized.startsWith("/")) {
        return `${CDRAGON_BASE}${normalized}`;
    }
    return `${CDRAGON_BASE}/${normalized}`;
}

function normalizeArray(value: unknown): number[] {
    if (Array.isArray(value)) {
        return value
            .map((v) => Number(v))
            .filter((v) => Number.isFinite(v));
    }
    if (typeof value === "number") {
        return [value];
    }
    return [];
}

function hasNonZeroValue(values: number[]): boolean {
    return values.some((v) => v !== 0);
}

function buildLeveling(effectAmounts: Record<string, number[]> | undefined): Array<Record<string, unknown>> {
    if (!effectAmounts) {
        return [];
    }

    return Object.entries(effectAmounts)
        .map(([attribute, rawValues]) => ({
            attribute,
            values: normalizeArray(rawValues)
        }))
        .filter((entry) => entry.values.length > 0 && hasNonZeroValue(entry.values))
        .slice(0, 12)
        .map((entry) => ({
            attribute: entry.attribute,
            modifiers: [
                {
                    values: entry.values,
                    units: [""]
                }
            ]
        }));
}

function splitAbilityVariantNames(name: string | undefined, fallback: string): string[] {
    if (!name || !name.trim()) {
        return [fallback];
    }
    const parts = name
        .split("/")
        .map((part) => part.trim())
        .filter(Boolean);
    return parts.length > 0 ? parts : [fallback];
}

type AbilitySlot = "P" | "Q" | "W" | "E" | "R";
type AbilityGroups = Record<AbilitySlot, Array<Record<string, unknown>>>;

function resolveAbilitySlot(spellKey: string | undefined, index: number): AbilitySlot {
    const key = (spellKey ?? "").trim().toUpperCase();
    if (key.startsWith("Q")) {
        return "Q";
    }
    if (key.startsWith("W")) {
        return "W";
    }
    if (key.startsWith("E")) {
        return "E";
    }
    if (key.startsWith("R")) {
        return "R";
    }
    const fallback: AbilitySlot[] = ["Q", "W", "E", "R"];
    return fallback[Math.max(0, Math.min(index, 3))];
}

function mapAttackType(attackType: string | undefined): string {
    if (!attackType) {
        return "MELEE";
    }
    return attackType.toLowerCase().includes("ranged") ? "RANGED" : "MELEE";
}

function mapAdaptiveType(damageType: string | undefined): string {
    if (!damageType) {
        return "MIXED_DAMAGE";
    }
    const value = damageType.toLowerCase();
    if (value.includes("physical")) {
        return "PHYSICAL_DAMAGE";
    }
    if (value.includes("magic")) {
        return "MAGIC_DAMAGE";
    }
    return "MIXED_DAMAGE";
}

function mapResource(partype: string | undefined): string {
    if (!partype) {
        return "NONE";
    }
    const value = partype.toLowerCase().trim();
    if (value === "mana") {
        return "MANA";
    }
    if (value === "energy") {
        return "ENERGY";
    }
    if (value === "rage") {
        return "RAGE";
    }
    if (value === "fury") {
        return "FURY";
    }
    if (value === "none" || value === "manaless") {
        return "NO_COST";
    }
    if (value === "health") {
        return "HEALTH";
    }
    return "OTHER";
}

function buildStats(ddragonChampion: DDragonChampion | undefined): Record<string, StatValue> {
    const s = ddragonChampion?.stats ?? {};
    return {
        health: stat(s.hp ?? 0, s.hpperlevel ?? 0),
        healthRegen: stat(s.hpregen ?? 0, s.hpregenperlevel ?? 0),
        mana: stat(s.mp ?? 0, s.mpperlevel ?? 0),
        manaRegen: stat(s.mpregen ?? 0, s.mpregenperlevel ?? 0),
        armor: stat(s.armor ?? 0, s.armorperlevel ?? 0),
        magicResistance: stat(s.spellblock ?? 0, s.spellblockperlevel ?? 0),
        attackDamage: stat(s.attackdamage ?? 0, s.attackdamageperlevel ?? 0),
        movespeed: stat(s.movespeed ?? 0, 0),
        acquisitionRadius: stat(0, 0),
        selectionRadius: stat(0, 0),
        pathingRadius: stat(0, 0),
        gameplayRadius: stat(0, 0),
        criticalStrikeDamage: stat(175, 0),
        criticalStrikeDamageModifier: stat(1, 0),
        attackSpeed: stat(s.attackspeed ?? 0, s.attackspeedperlevel ?? 0),
        attackSpeedRatio: stat(s.attackspeed ?? 0, 0),
        attackCastTime: stat(0, 0),
        attackTotalTime: stat(0, 0),
        attackDelayOffset: stat(0, 0),
        attackRange: stat(s.attackrange ?? 0, 0),
        aramDamageTaken: stat(1, 0),
        aramDamageDealt: stat(1, 0),
        aramHealing: stat(1, 0),
        aramShielding: stat(1, 0),
        aramTenacity: stat(0, 0),
        aramAbilityHaste: stat(0, 0),
        aramAttackSpeed: stat(0, 0),
        aramEnergyRegen: stat(0, 0),
        urfDamageTaken: stat(1, 0),
        urfDamageDealt: stat(1, 0),
        urfHealing: stat(1, 0),
        urfShielding: stat(1, 0)
    };
}

function buildAbility(
    name: string,
    description: string,
    iconPath: string | undefined,
    resource: string,
    adaptiveType: string,
    cooldown: number[],
    cost: number[],
    range: number[],
    leveling: Array<Record<string, unknown>>
): Record<string, unknown> {
    return {
        name,
        icon: toAssetUrl(iconPath),
        effects: [
            {
                description,
                leveling
            }
        ],
        cost: {
            modifiers: [
                {
                    values: cost,
                    units: ["resource"]
                }
            ]
        },
        cooldown: {
            modifiers: [
                {
                    values: cooldown,
                    units: ["seconds"]
                }
            ],
            affectedByCdr: true
        },
        targeting: "",
        affects: "",
        spellshieldable: "",
        resource,
        damageType: adaptiveType,
        spellEffects: "",
        projectile: "",
        onHitEffects: "",
        occurrence: "",
        notes: "",
        blurb: description,
        missileSpeed: "",
        rechargeRate: "",
        collisionRadius: "",
        tetherRadius: "",
        onTargetCdStatic: "",
        innerRadius: "",
        speed: "",
        width: "",
        angle: "",
        castTime: "",
        effectRadius: "",
        targetRange: range.length > 0 ? range.join(" / ") : ""
    };
}

async function fetchJson<T>(url: string): Promise<T> {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Request failed (${response.status}) for ${url}`);
    }
    return (await response.json()) as T;
}

async function mapWithConcurrency<T, R>(items: T[], limit: number, mapper: (item: T, index: number) => Promise<R>): Promise<R[]> {
    const results = new Array<R>(items.length);
    let nextIndex = 0;

    async function worker(): Promise<void> {
        while (nextIndex < items.length) {
            const current = nextIndex;
            nextIndex += 1;
            results[current] = await mapper(items[current], current);
        }
    }

    const workers = Array.from({ length: Math.min(limit, items.length) }, () => worker());
    await Promise.all(workers);
    return results;
}

export class ChampionService implements GenerationService {
    readonly name = "ChampionService";

    async generate(context: GenerationContext): Promise<GenerationResult> {
        try {
            const championsDir = path.join(context.outputDir, "champions");
            await fs.mkdir(championsDir, { recursive: true });

            const existingChampionFiles = await fs.readdir(championsDir);
            await Promise.all(
                existingChampionFiles
                    .filter((name) => name.endsWith(".json"))
                    .map((name) => fs.unlink(path.join(championsDir, name)))
            );

            const [summary, ddragon] = await Promise.all([
                fetchJson<CDragonChampionSummary[]>(CDRAGON_CHAMPION_SUMMARY_URL),
                fetchJson<DDragonChampionFull>(`https://ddragon.leagueoflegends.com/cdn/${context.patchVersion}/data/en_US/championFull.json`)
            ]);

            const champions = summary.filter(
                (entry) => entry.id > 0 && entry.alias && entry.alias !== "None" && Boolean(ddragon.data[entry.alias])
            );

            const details = await mapWithConcurrency(champions, 12, async (entry) => {
                const detail = await fetchJson<CDragonChampionDetail>(`${CDRAGON_BASE}/v1/champions/${entry.id}.json`);
                return {
                    summary: entry,
                    detail
                };
            });

            const championPayloads: Record<string, Record<string, unknown>> = {};
            const championIndex: Array<Record<string, unknown>> = [];

            for (const item of details) {
                const detail = item.detail;
                const key = detail.alias || item.summary.alias;
                const ddragonChampion = ddragon.data[key];

                const resource = mapResource(ddragonChampion?.partype);
                const adaptiveType = mapAdaptiveType(detail.tacticalInfo?.damageType);

                const passiveAbility = buildAbility(
                    detail.passive?.name ?? "Passive",
                    detail.passive?.description ?? "",
                    detail.passive?.abilityIconPath,
                    resource,
                    adaptiveType,
                    [],
                    [],
                    [],
                    []
                );

                const spells = Array.isArray(detail.spells) ? detail.spells : [];
                const abilities: AbilityGroups = {
                    P: [passiveAbility],
                    Q: [],
                    W: [],
                    E: [],
                    R: []
                };

                spells.forEach((spell, index) => {
                    const slot = resolveAbilitySlot(spell.spellKey, index);
                    const variantNames = splitAbilityVariantNames(spell.name, slot);
                    const description = spell.description ?? spell.dynamicDescription ?? "";
                    const cooldown = normalizeArray(spell.cooldown).length > 0
                        ? normalizeArray(spell.cooldown)
                        : normalizeArray(spell.cooldownCoefficients);
                    const cost = normalizeArray(spell.cost).length > 0
                        ? normalizeArray(spell.cost)
                        : normalizeArray(spell.costCoefficients);
                    const range = normalizeArray(spell.range);
                    const leveling = buildLeveling(spell.effectAmounts);

                    for (const variantName of variantNames) {
                        abilities[slot].push(buildAbility(
                            variantName,
                            description,
                            spell.abilityIconPath,
                            resource,
                            adaptiveType,
                            cooldown,
                            cost,
                            range,
                            leveling
                        ));
                    }
                });

                const skins = (detail.skins ?? []).map((skin) => ({
                    name: skin.name,
                    id: skin.id,
                    isBase: Boolean(skin.isBase),
                    availability: "AVAILABLE",
                    formatName: skin.name,
                    lootEligible: true,
                    cost: "",
                    sale: 0,
                    distribution: "",
                    rarity: skin.skinClassification ?? "",
                    chromas: [],
                    lore: "",
                    release: 0,
                    set: [],
                    splashPath: toAssetUrl(skin.splashPath),
                    uncenteredSplashPath: toAssetUrl(skin.uncenteredSplashPath),
                    tilePath: toAssetUrl(skin.tilePath),
                    loadScreenPath: toAssetUrl(skin.loadScreenPath),
                    loadScreenVintagePath: "",
                    newEffects: false,
                    newAnimations: false,
                    newRecall: false,
                    newVoice: false,
                    newQuotes: false,
                    voiceActor: [],
                    splashArtist: []
                }));

                const payload: Record<string, unknown> = {
                    id: detail.id,
                    key,
                    name: detail.name,
                    title: detail.title,
                    fullName: `${detail.name}, ${detail.title}`,
                    icon: toAssetUrl(detail.squarePortraitPath ?? item.summary.squarePortraitPath),
                    resource,
                    attackType: mapAttackType(detail.tacticalInfo?.attackType),
                    adaptiveType,
                    stats: buildStats(ddragonChampion),
                    positions: [],
                    roles: (detail.roles ?? item.summary.roles ?? []).map(role => role.toUpperCase()),
                    attributeRatings: {
                        damage: detail.playstyleInfo?.damage ?? 0,
                        toughness: detail.playstyleInfo?.durability ?? 0,
                        control: detail.playstyleInfo?.crowdControl ?? 0,
                        mobility: detail.playstyleInfo?.mobility ?? 0,
                        utility: detail.playstyleInfo?.utility ?? 0,
                        abilityReliance: 0,
                        difficulty: detail.tacticalInfo?.difficulty ?? 0
                    },
                    abilities: {
                        P: abilities.P,
                        Q: abilities.Q,
                        W: abilities.W,
                        E: abilities.E,
                        R: abilities.R
                    },
                    releaseDate: "",
                    releasePatch: "",
                    patchLastChanged: context.patchVersion,
                    price: {
                        blueEssence: 0,
                        rp: 0,
                        saleRp: 0
                    },
                    lore: detail.shortBio ?? "",
                    faction: "",
                    skins
                };

                championPayloads[key] = payload;
                championIndex.push({
                    id: detail.id,
                    key,
                    name: detail.name || item.summary.name || key,
                    slug: key.toLowerCase(),
                    iconUrl: payload.icon,
                    attackType: payload.attackType,
                    roles: payload.roles
                });

                const filePath = path.join(championsDir, `${key}.json`);
                await fs.writeFile(filePath, JSON.stringify(payload, null, 2), "utf8");
            }

            const aggregatePath = path.join(context.outputDir, "champions.json");
            await fs.writeFile(aggregatePath, JSON.stringify(championPayloads, null, 2), "utf8");

            championIndex.sort((a, b) => Number(a.id) - Number(b.id));
            const indexPath = path.join(context.outputDir, "champion-index.json");
            await fs.writeFile(indexPath, JSON.stringify({
                version: context.patchVersion,
                generatedAt: new Date().toISOString(),
                totalChampions: championIndex.length,
                champions: championIndex
            }, null, 2), "utf8");

            return {
                service: this.name,
                success: true,
                details: `Champion generation completed with native CDragon pipeline (${championIndex.length} champions)`
            };
        } catch (error) {
            const msg = error instanceof Error ? error.message : String(error);
            return {
                service: this.name,
                success: false,
                details: `Champion generation failed: ${msg}`
            };
        }
    }
}
