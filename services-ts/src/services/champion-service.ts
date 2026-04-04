import fs from "node:fs/promises";
import path from "node:path";
import type { GenerationService } from "../contracts.js";
import type { GenerationContext, GenerationResult } from "../types.js";

const CDRAGON_BASE = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default";
const CDRAGON_CHAMPION_SUMMARY_URL = `${CDRAGON_BASE}/v1/champion-summary.json`;
const RAW_CDRAGON_BASE = "https://raw.communitydragon.org";
const CDRAGON_PLUGIN_PATH = "plugins/rcp-be-lol-game-data/global/default";

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

interface PassiveAbilityNumbers {
    cooldown: number[];
    cost: number[];
    costUnit: string;
}

interface DDragonChampion {
    partype?: string;
    stats?: Record<string, number>;
    spells?: Array<{
        id?: string;
        costType?: string;
    }>;
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

function toPatchChannel(patchVersion: string): string {
    const parts = patchVersion
        .split(".")
        .map((value) => value.trim())
        .filter(Boolean);
    if (parts.length >= 2) {
        return `${parts[0]}.${parts[1]}`;
    }
    return patchVersion || "latest";
}

function toPluginAssetUrl(assetPath: string | undefined, patchVersion: string): string {
    if (!assetPath) {
        return "";
    }
    if (assetPath.startsWith("http://") || assetPath.startsWith("https://")) {
        return assetPath;
    }

    const normalized = assetPath.replace(/\\/g, "/");
    const normalizedLower = normalized.toLowerCase();
    const pluginBase = `${RAW_CDRAGON_BASE}/${toPatchChannel(patchVersion)}/${CDRAGON_PLUGIN_PATH}`;

    if (normalizedLower.startsWith("/lol-game-data/assets/")) {
        const tail = normalizedLower.slice("/lol-game-data/assets/".length);
        return `${pluginBase}/${tail}`;
    }

    if (normalizedLower.startsWith("/")) {
        return `${pluginBase}${normalizedLower}`;
    }

    return `${pluginBase}/${normalizedLower}`;
}

function toPatchGameAssetUrl(assetPath: string, patchVersion: string): string {
    if (assetPath.startsWith("http://") || assetPath.startsWith("https://")) {
        return assetPath;
    }

    const normalized = assetPath.replace(/\\/g, "/");
    const normalizedLower = normalized.toLowerCase();
    const patchChannel = toPatchChannel(patchVersion);

    if (normalizedLower.startsWith("/lol-game-data/assets/")) {
        let tail = normalizedLower.slice("/lol-game-data/assets/".length);
        if (tail.startsWith("assets/")) {
            tail = tail.slice("assets/".length);
        }
        return `${RAW_CDRAGON_BASE}/${patchChannel}/game/assets/${tail}`;
    }

    if (normalizedLower.startsWith("/")) {
        return `${RAW_CDRAGON_BASE}/${patchChannel}${normalizedLower}`;
    }

    return `${RAW_CDRAGON_BASE}/${patchChannel}/${normalizedLower}`;
}

function buildFallbackAbilityIconUrl(championKey: string, slot: AbilitySlot, patchVersion: string): string {
    const patchChannel = toPatchChannel(patchVersion);
    const championKeyLower = championKey.toLowerCase();
    const suffix = slot === "P" ? "passive" : slot.toLowerCase();
    return `${RAW_CDRAGON_BASE}/${patchChannel}/game/assets/characters/${championKeyLower}/hud/icons2d/${championKeyLower}_${suffix}.png`;
}

function resolveAbilityIconUrl(
    championKey: string,
    slot: AbilitySlot,
    iconPath: string | undefined,
    patchVersion: string
): string {
    if (iconPath && iconPath.trim()) {
        return toPatchGameAssetUrl(iconPath, patchVersion);
    }
    return buildFallbackAbilityIconUrl(championKey, slot, patchVersion);
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

function buildLinearValues(start: number, end: number, steps: number): number[] {
    if (!Number.isFinite(start) || !Number.isFinite(end) || steps <= 0) {
        return [];
    }
    if (steps === 1) {
        return [start];
    }
    const result: number[] = [];
    for (let i = 0; i < steps; i += 1) {
        const t = i / (steps - 1);
        result.push(start + (end - start) * t);
    }
    return result;
}

function inferUnitFromText(raw: string | undefined): string {
    const value = (raw ?? "").toLowerCase();
    if (value.includes("mana")) {
        return "MANA";
    }
    if (value.includes("energy")) {
        return "ENERGY";
    }
    if (value.includes("health") || value.includes("hp")) {
        return "HEALTH";
    }
    if (value.includes("rage")) {
        return "RAGE";
    }
    if (value.includes("fury")) {
        return "FURY";
    }
    if (value.includes("ferocity")) {
        return "FEROCITY";
    }
    return "";
}

function extractSpellDataValues(spellData: Record<string, unknown>): Array<{ name: string; values: number[] }> {
    const raw = (spellData.DataValues ?? spellData.mDataValues) as unknown;
    if (!Array.isArray(raw)) {
        return [];
    }

    const values: Array<{ name: string; values: number[] }> = [];
    for (const item of raw) {
        if (!item || typeof item !== "object") {
            continue;
        }
        const entry = item as Record<string, unknown>;
        const name = String(entry.name ?? entry.mName ?? "");
        const data = normalizeArray(entry.values ?? entry.mValues);
        if (name && data.length > 0) {
            values.push({ name, values: data });
        }
    }
    return values;
}

function extractCooldownFromCalculations(spellData: Record<string, unknown>): number[] {
    const calculations = spellData.mSpellCalculations as unknown;
    if (!calculations || typeof calculations !== "object") {
        return [];
    }

    for (const [name, calc] of Object.entries(calculations as Record<string, unknown>)) {
        if (!name.toLowerCase().includes("cooldown") || !calc || typeof calc !== "object") {
            continue;
        }

        const formulaParts = (calc as Record<string, unknown>).mFormulaParts as unknown;
        if (!Array.isArray(formulaParts)) {
            continue;
        }

        for (const part of formulaParts) {
            if (!part || typeof part !== "object") {
                continue;
            }
            const record = part as Record<string, unknown>;
            const start = Number(record.mStartValue);
            const end = Number(record.mEndValue);
            if (Number.isFinite(start) && Number.isFinite(end)) {
                return buildLinearValues(start, end, 18);
            }
            const flat = Number(record.mNumber ?? record.mValue);
            if (Number.isFinite(flat)) {
                return [flat];
            }
        }
    }

    return [];
}

function compactText(value: string | undefined): string {
    return (value ?? "").toLowerCase().replace(/[^a-z0-9]+/g, "");
}

function findPassiveSpellData(
    binData: Record<string, unknown>,
    championKey: string,
    passiveName: string | undefined
): Record<string, unknown> | undefined {
    let bestScore = -1;
    let best: Record<string, unknown> | undefined;
    const passiveNameCompact = compactText(passiveName);
    const passiveNameTokens = (passiveName ?? "")
        .toLowerCase()
        .split(/[^a-z0-9]+/)
        .map((token) => token.trim())
        .filter((token) => token.length >= 4);
    const championKeyCompact = compactText(championKey);

    for (const [pathKey, value] of Object.entries(binData)) {
        if (!value || typeof value !== "object") {
            continue;
        }
        const entry = value as Record<string, unknown>;
        if (!entry.mSpell || typeof entry.mSpell !== "object") {
            continue;
        }

        const text = `${pathKey} ${String(entry.mScriptName ?? "")} ${String(entry.ObjectName ?? "")}`.toLowerCase();
        const textCompact = compactText(text);
        let score = 0;

        if (passiveNameCompact && textCompact.includes(passiveNameCompact)) {
            score += 12;
        }
        for (const token of passiveNameTokens) {
            if (text.includes(token)) {
                score += 3;
            }
        }
        if (championKeyCompact && textCompact.includes(championKeyCompact)) {
            score += 1;
        }
        if (text.includes("passive")) {
            score += 4;
        }
        if (text.includes("ability")) {
            score += 1;
        }
        const spellData = entry.mSpell as Record<string, unknown>;
        if (spellData.mSpellCalculations) {
            score += 1;
        }

        const dataValueNames = extractSpellDataValues(spellData).map((item) => item.name.toLowerCase());
        if (dataValueNames.some((name) => name.includes("cooldown") || name.includes("cost") || name.includes("mana"))) {
            score += 2;
        }

        if (score > bestScore) {
            bestScore = score;
            best = spellData;
        }
    }

    return best;
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

function normalizeUnitValue(values: number[], unit: string): string[] {
    if (values.length === 0) {
        return [];
    }
    return values.map(() => unit);
}

function fallbackCostUnitFromResource(resource: string): string {
    if (resource === "NONE" || resource === "NO_COST" || resource === "OTHER") {
        return "";
    }
    return resource;
}

function resolveCostUnit(costTypeRaw: string | undefined, resource: string): string {
    const fallback = fallbackCostUnitFromResource(resource);
    const value = (costTypeRaw ?? "").toLowerCase();

    if (!value.trim()) {
        return fallback;
    }
    if (value.includes("no cost")) {
        return "";
    }
    if (value.includes("mana") || value.includes("abilityresourcename") || value.includes("manacostpersecond")) {
        return "MANA";
    }
    if (value.includes("energy")) {
        return "ENERGY";
    }
    if (value.includes("health") || value.includes("hp")) {
        return "HEALTH";
    }
    if (value.includes("rage")) {
        return "RAGE";
    }
    if (value.includes("fury")) {
        return "FURY";
    }
    if (value.includes("ferocity")) {
        return "FEROCITY";
    }

    return fallback;
}

async function fetchPassiveAbilityNumbers(
    championKey: string,
    patchVersion: string,
    resource: string,
    passiveName: string | undefined
): Promise<PassiveAbilityNumbers> {
    const empty: PassiveAbilityNumbers = {
        cooldown: [],
        cost: [],
        costUnit: ""
    };

    const key = championKey.toLowerCase();
    const patchChannel = toPatchChannel(patchVersion);
    const url = `${RAW_CDRAGON_BASE}/${patchChannel}/game/data/characters/${key}/${key}.bin.json`;
    const response = await fetch(url);
    if (!response.ok) {
        return empty;
    }
    const binData = await response.json() as Record<string, unknown>;

    if (!binData) {
        return empty;
    }

    const spellData = findPassiveSpellData(binData, championKey, passiveName);
    if (!spellData) {
        return empty;
    }

    const dataValues = extractSpellDataValues(spellData);
    const cooldownFromDataValue = dataValues.find((entry) => entry.name.toLowerCase().includes("cooldown"))?.values ?? [];
    const cooldown = cooldownFromDataValue.length > 0
        ? cooldownFromDataValue
        : extractCooldownFromCalculations(spellData);

    const costEntry = dataValues.find((entry) => /cost/i.test(entry.name));
    const cost = costEntry?.values ?? [];
    const costUnit = cost.length > 0
        ? (inferUnitFromText(costEntry?.name) || fallbackCostUnitFromResource(resource))
        : "";

    return {
        cooldown,
        cost,
        costUnit
    };
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
    iconUrl: string,
    resource: string,
    adaptiveType: string,
    cooldown: number[],
    affectedByCdr: boolean,
    cost: number[],
    costUnit: string,
    range: number[],
    leveling: Array<Record<string, unknown>>
): Record<string, unknown> {
    return {
        name,
        icon: iconUrl,
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
                    units: normalizeUnitValue(cost, costUnit)
                }
            ]
        },
        cooldown: {
            modifiers: [
                {
                    values: cooldown,
                    units: normalizeUnitValue(cooldown, "seconds")
                }
            ],
            affectedByCdr
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
                const ddragonChampion = ddragon.data[entry.alias];
                const resource = mapResource(ddragonChampion?.partype);

                const detail = await fetchJson<CDragonChampionDetail>(`${CDRAGON_BASE}/v1/champions/${entry.id}.json`);
                const passiveNumbers = await fetchPassiveAbilityNumbers(
                    entry.alias,
                    context.patchVersion,
                    resource,
                    detail.passive?.name
                );

                return {
                    summary: entry,
                    detail,
                    passiveNumbers
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
                const ddragonCostTypeBySlot: Partial<Record<AbilitySlot, string>> = {};
                (ddragonChampion?.spells ?? []).forEach((spell, index) => {
                    const slot = resolveAbilitySlot(spell.id, index);
                    ddragonCostTypeBySlot[slot] = spell.costType ?? "";
                });

                const passiveAbility = buildAbility(
                    detail.passive?.name ?? "Passive",
                    detail.passive?.description ?? "",
                    resolveAbilityIconUrl(key, "P", detail.passive?.abilityIconPath, context.patchVersion),
                    resource,
                    adaptiveType,
                    item.passiveNumbers.cooldown,
                    false,
                    item.passiveNumbers.cost,
                    item.passiveNumbers.costUnit,
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
                    const costTypeRaw = ddragonCostTypeBySlot[slot] ?? "";
                    const costUnit = resolveCostUnit(costTypeRaw, resource);
                    const range = normalizeArray(spell.range);
                    const leveling = buildLeveling(spell.effectAmounts);

                    for (const variantName of variantNames) {
                        abilities[slot].push(buildAbility(
                            variantName,
                            description,
                            resolveAbilityIconUrl(key, slot, spell.abilityIconPath, context.patchVersion),
                            resource,
                            adaptiveType,
                            cooldown,
                            true,
                            cost,
                            costUnit,
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
                    splashPath: toPluginAssetUrl(skin.splashPath, context.patchVersion),
                    uncenteredSplashPath: toPluginAssetUrl(skin.uncenteredSplashPath, context.patchVersion),
                    tilePath: toPluginAssetUrl(skin.tilePath, context.patchVersion),
                    loadScreenPath: toPluginAssetUrl(skin.loadScreenPath, context.patchVersion),
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
                    icon: toPluginAssetUrl(detail.squarePortraitPath ?? item.summary.squarePortraitPath, context.patchVersion),
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
