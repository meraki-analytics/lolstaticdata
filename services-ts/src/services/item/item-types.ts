export interface DDragonItemImage {
    full?: string;
    sprite?: string;
    group?: string;
    x?: number;
    y?: number;
    w?: number;
    h?: number;
}

export interface DDragonItemGold {
    base?: number;
    total?: number;
    sell?: number;
    purchasable?: boolean;
}

export interface DDragonItem {
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

export interface DDragonItemPayload {
    data: Record<string, DDragonItem>;
}

export interface DDragonMapEntry {
    MapName?: string;
    MapId?: string;
}

export interface DDragonMapPayload {
    data: Record<string, DDragonMapEntry>;
}

export interface MapAvailability {
    id: number;
    key: string;
    label: string;
    mode: string;
}

export interface StatValue {
    flat: number;
    percent: number;
    perLevel: number;
    percentPerLevel: number;
    percentBase: number;
    percentBonus: number;
}

export interface ItemStats {
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

export interface MappedEffect {
    code: string;
    index: number;
    key: string;
    token: string;
    raw: string;
    values: number[];
}

export interface WrappedItem {
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
