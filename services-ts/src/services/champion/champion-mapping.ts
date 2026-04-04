import type { AbilityMetadata } from "./champion-ability-meta.js";
import {
    localizeAffects,
    localizeDamageType,
    localizeLevelingUnits,
    localizeProjectile,
    localizeResource,
    localizeTargeting,
    localizeUnit,
    parseResourceCode
} from "./champion-i18n.js";
import type {
    AbilitySlot,
    DDragonChampion,
    StatValue
} from "./champion-types.js";

export function normalizeArray(value: unknown): number[] {
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

export function clampValuesToMaxRank(values: number[], maxRank: number | undefined): number[] {
    if (!Number.isInteger(maxRank) || !maxRank || maxRank <= 0) {
        return values;
    }
    return values.slice(0, maxRank);
}

function hasNonZeroValue(values: number[]): boolean {
    return values.some((v) => v !== 0);
}

function normalizeLevelingUnit(values: number[], unit: string): string[] {
    if (values.length === 0) {
        return [];
    }
    return values.map(() => unit);
}

function inferDamageUnit(adaptiveType: string): string {
    if (adaptiveType === "PHYSICAL_DAMAGE") {
        return "PHYSICAL_DAMAGE";
    }
    if (adaptiveType === "MAGIC_DAMAGE") {
        return "MAGIC_DAMAGE";
    }
    return "DAMAGE";
}

function isLikelyPercentSeries(values: number[]): boolean {
    if (values.length === 0) {
        return false;
    }
    const bounded = values.every((value) => Math.abs(value) <= 1.5);
    if (!bounded) {
        return false;
    }
    return values.some((value) => !Number.isInteger(value));
}

export function inferLevelingUnit(
    attribute: string,
    adaptiveType: string,
    resource: string,
    values: number[] = []
): string {
    const key = attribute.toLowerCase();

    if (/(refund|reduction)/.test(key)) {
        return "PERCENT";
    }
    if (/(percent|pct)/.test(key)) {
        return "PERCENT";
    }
    if (/(duration|cooldown|lifetime|time|delay)/.test(key)) {
        return "SECONDS";
    }
    if (/(^|[^a-z])cd([^a-z]|$)|cd$/.test(key)) {
        return "SECONDS";
    }
    if (/(damage|dmg)/.test(key)) {
        return inferDamageUnit(adaptiveType);
    }
    if (/cap/.test(key)) {
        return inferDamageUnit(adaptiveType);
    }
    if (/(range|radius|distance|width|length|aoe|area|collision|size)/.test(key)) {
        return "UNITS";
    }
    if (/(ratio|mult|modifier|mod|scale|chance|crit|slow|haste|attackspeed)/.test(key)) {
        return "PERCENT";
    }
    if (/(heal|regen|health|hp)/.test(key)) {
        return "HEALTH";
    }
    if (/mana/.test(key)) {
        return "MANA";
    }
    if (/energy/.test(key)) {
        return "ENERGY";
    }
    if (/(rage|fury|ferocity)/.test(key)) {
        return resource === "RAGE" || resource === "FURY" || resource === "FEROCITY"
            ? resource
            : "RESOURCE";
    }
    if (/(stack|count)/.test(key)) {
        return "STACKS";
    }
    if (/(speed|\bas\b)/.test(key) || isLikelyPercentSeries(values)) {
        return "PERCENT";
    }

    return "";
}

export function buildLeveling(
    effectAmounts: Record<string, number[]> | undefined,
    adaptiveType: string,
    resource: string,
    maxRank?: number
): Array<Record<string, unknown>> {
    if (!effectAmounts) {
        return [];
    }

    return Object.entries(effectAmounts)
        .map(([attribute, rawValues]) => ({
            attribute,
            values: clampValuesToMaxRank(normalizeArray(rawValues), maxRank)
        }))
        .filter((entry) => entry.values.length > 0 && hasNonZeroValue(entry.values))
        .slice(0, 12)
        .map((entry) => ({
            attribute: entry.attribute,
            modifiers: [
                {
                    values: entry.values,
                    units: normalizeLevelingUnit(
                        entry.values,
                        inferLevelingUnit(entry.attribute, adaptiveType, resource, entry.values)
                    )
                }
            ]
        }));
}

export function splitAbilityVariantNames(name: string | undefined, fallback: string): string[] {
    if (!name || !name.trim()) {
        return [fallback];
    }
    const parts = name
        .split("/")
        .map((part) => part.trim())
        .filter(Boolean);
    return parts.length > 0 ? parts : [fallback];
}

export function resolveAbilitySlot(spellKey: string | undefined, index: number): AbilitySlot {
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

export function mapAttackType(attackType: string | undefined): string {
    if (!attackType) {
        return "MELEE";
    }
    return attackType.toLowerCase().includes("ranged") ? "RANGED" : "MELEE";
}

export function mapAdaptiveType(damageType: string | undefined): string {
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

export function mapResource(partype: string | undefined): string {
    if (!partype) {
        return "NONE";
    }
    return parseResourceCode(partype) ?? "OTHER";
}

function normalizeUnitValue(values: number[], unit: string): string[] {
    if (values.length === 0) {
        return [];
    }
    return values.map(() => unit);
}

export function fallbackCostUnitFromResource(resource: string): string {
    if (resource === "NONE" || resource === "NO_COST" || resource === "OTHER") {
        return "";
    }
    return resource;
}

export function resolveCostUnit(costTypeRaw: string | undefined, resource: string): string {
    const fallback = fallbackCostUnitFromResource(resource);
    const value = (costTypeRaw ?? "").toLowerCase();

    if (!value.trim()) {
        return fallback;
    }
    if (value.includes("no cost")) {
        return "";
    }
    if (value.includes("abilityresourcename")) {
        return fallback;
    }
    if (value.includes("mana") || value.includes("manacostpersecond")) {
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

function stat(flat = 0, perLevel = 0): StatValue {
    return {
        flat,
        percent: 0,
        perLevel,
        percentPerLevel: 0
    };
}

export function buildStats(ddragonChampion: DDragonChampion | undefined): Record<string, StatValue> {
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

export interface BuildAbilityInput {
    name: string;
    description: string;
    iconUrl: string;
    resource: string;
    adaptiveType: string;
    cooldown: number[];
    affectedByCdr: boolean;
    cost: number[];
    costUnit: string;
    range: number[];
    leveling: Array<Record<string, unknown>>;
    locale: string;
    metadata?: AbilityMetadata;
}

export function buildAbility(input: BuildAbilityInput): Record<string, unknown> {
    const metadata = input.metadata ?? {};
    const localizedLeveling = localizeLevelingUnits(input.leveling, input.locale);

    function localizedUnitSeries(values: number[], unit: string): string[] {
        if (values.length === 0) {
            return [];
        }
        const localized = localizeUnit(unit, input.locale);
        return values.map(() => localized);
    }

    return {
        name: input.name,
        icon: input.iconUrl,
        effects: [
            {
                description: input.description,
                leveling: localizedLeveling
            }
        ],
        cost: {
            modifiers: [
                {
                    values: input.cost,
                    units: localizedUnitSeries(input.cost, input.costUnit)
                }
            ]
        },
        cooldown: {
            modifiers: [
                {
                    values: input.cooldown,
                    units: localizedUnitSeries(input.cooldown, "SECONDS")
                }
            ],
            affectedByCdr: input.affectedByCdr
        },
        targeting: localizeTargeting(metadata.targeting ?? "", input.locale),
        affects: localizeAffects(metadata.affects ?? "", input.locale),
        spellshieldable: metadata.spellshieldable ?? false,
        resource: localizeResource(input.resource, input.locale),
        damageType: localizeDamageType(input.adaptiveType, input.locale),
        spellEffects: metadata.spellEffects ?? "",
        projectile: localizeProjectile(metadata.projectile ?? "", input.locale),
        onHitEffects: metadata.onHitEffects ?? "",
        occurrence: metadata.occurrence ?? "",
        notes: metadata.notes ?? "",
        blurb: metadata.blurb ?? input.description,
        missileSpeed: metadata.missileSpeed ?? "",
        rechargeRate: metadata.rechargeRate ?? "",
        collisionRadius: metadata.collisionRadius ?? "",
        tetherRadius: metadata.tetherRadius ?? "",
        onTargetCdStatic: metadata.onTargetCdStatic ?? "",
        innerRadius: metadata.innerRadius ?? "",
        speed: metadata.speed ?? "",
        width: metadata.width ?? "",
        angle: metadata.angle ?? "",
        castTime: metadata.castTime ?? "",
        effectRadius: metadata.effectRadius ?? "",
        targetRange: metadata.targetRange ?? (input.range.length > 0 ? input.range.join(" / ") : "")
    };
}
