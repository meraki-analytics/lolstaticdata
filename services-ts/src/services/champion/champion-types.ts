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
    ammo?: {
        ammoRechargeTime?: number[] | number;
        maxAmmo?: number[] | number;
    };
    maxLevel?: number;
}

export interface CDragonSkinChroma {
    id: number;
    name?: string;
    contentId?: string;
    skinClassification?: string;
    chromaPath?: string;
    tilePath?: string;
    colors?: string[];
    descriptions?: Array<{ description?: string; region?: string }>;
    rarities?: Array<{ rarity?: number; region?: string }>;
    description?: string;
}

export interface CDragonChampionSkin {
    id: number;
    name: string;
    isBase: boolean;
    skinClassification?: string;
    splashPath?: string;
    uncenteredSplashPath?: string;
    tilePath?: string;
    loadScreenPath?: string;
    loadScreenVintagePath?: string;
    rarity?: string;
    chromas?: CDragonSkinChroma[];
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
    skins?: CDragonChampionSkin[];
}

export interface PassiveAbilityNumbers {
    cooldown: number[];
    cost: number[];
    costUnit: string;
}

export interface DDragonChampion {
    name?: string;
    title?: string;
    blurb?: string;
    lore?: string;
    tags?: string[];
    partype?: string;
    stats?: Record<string, number>;
    passive?: {
        name?: string;
        description?: string;
    };
    spells?: Array<{
        id?: string;
        name?: string;
        description?: string;
        tooltip?: string;
        maxrank?: number;
        costType?: string;
    }>;
    skins?: Array<{
        num?: number;
        name?: string;
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
    calculationNames: string[];
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
