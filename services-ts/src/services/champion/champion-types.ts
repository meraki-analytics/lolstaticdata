export interface CDragonChampionSummary {
    id: number;
    name: string;
    description: string;
    alias: string;
    squarePortraitPath: string;
    roles: string[];
}

export interface CDragonSpell {
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

export interface CDragonChampionDetail {
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

export interface PassiveAbilityNumbers {
    cooldown: number[];
    cost: number[];
    costUnit: string;
}

export interface DDragonChampion {
    partype?: string;
    stats?: Record<string, number>;
    spells?: Array<{
        id?: string;
        costType?: string;
    }>;
}

export interface DDragonChampionFull {
    data: Record<string, DDragonChampion>;
}

export interface StatValue {
    flat: number;
    percent: number;
    perLevel: number;
    percentPerLevel: number;
}

export type AbilitySlot = "P" | "Q" | "W" | "E" | "R";
export type AbilityGroups = Record<AbilitySlot, Array<Record<string, unknown>>>;

export interface FormAbilityVariantOverride {
    iconPath: string;
    iconKey: string;
    score: number;
    hasCooldown: boolean;
    cooldown: number[];
    hasCost: boolean;
    cost: number[];
    hasRange: boolean;
    range: number[];
    hasLeveling: boolean;
    leveling: Array<Record<string, unknown>>;
}

export type FormAbilityVariantLookup = Partial<Record<AbilitySlot, FormAbilityVariantOverride[]>>;

export interface ChampionDetailWithPassive {
    summary: CDragonChampionSummary;
    detail: CDragonChampionDetail;
    passiveNumbers: PassiveAbilityNumbers;
    formVariants: FormAbilityVariantLookup;
}
