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

function hasNonZeroValue(values: number[]): boolean {
    return values.some((v) => v !== 0);
}

export function buildLeveling(effectAmounts: Record<string, number[]> | undefined): Array<Record<string, unknown>> {
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
}

export function buildAbility(input: BuildAbilityInput): Record<string, unknown> {
    return {
        name: input.name,
        icon: input.iconUrl,
        effects: [
            {
                description: input.description,
                leveling: input.leveling
            }
        ],
        cost: {
            modifiers: [
                {
                    values: input.cost,
                    units: normalizeUnitValue(input.cost, input.costUnit)
                }
            ]
        },
        cooldown: {
            modifiers: [
                {
                    values: input.cooldown,
                    units: normalizeUnitValue(input.cooldown, "seconds")
                }
            ],
            affectedByCdr: input.affectedByCdr
        },
        targeting: "",
        affects: "",
        spellshieldable: "",
        resource: input.resource,
        damageType: input.adaptiveType,
        spellEffects: "",
        projectile: "",
        onHitEffects: "",
        occurrence: "",
        notes: "",
        blurb: input.description,
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
        targetRange: input.range.length > 0 ? input.range.join(" / ") : ""
    };
}
