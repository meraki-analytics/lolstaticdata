import { RAW_CDRAGON_BASE, toPatchChannel } from "./champion-assets.js";
import { AFFECT_CODES, TARGETING_CODES } from "./champion-i18n.js";
import { clampValuesToMaxRank, normalizeArray, resolveAbilitySlot, splitAbilityVariantNames } from "./champion-mapping.js";
import type { AbilitySlot, CDragonSpell } from "./champion-types.js";

type JsonRecord = Record<string, unknown>;

export interface AbilityMetadata {
    targeting?: string;
    affects?: string;
    spellshieldable?: boolean;
    spellEffects?: string;
    projectile?: string;
    onHitEffects?: string;
    occurrence?: string;
    notes?: string;
    blurb?: string;
    missileSpeed?: string;
    rechargeRate?: string;
    collisionRadius?: string;
    tetherRadius?: string;
    onTargetCdStatic?: string;
    innerRadius?: string;
    speed?: string;
    width?: string;
    angle?: string;
    castTime?: string;
    effectRadius?: string;
    targetRange?: string;
}

export interface ChampionAbilityMetadataOverrides {
    bySlotIndex: Partial<Record<AbilitySlot, Record<number, AbilityMetadata>>>;
    bySlotName: Partial<Record<AbilitySlot, Record<string, AbilityMetadata>>>;
}

interface BinSpellCandidate {
    iconKey: string;
    metadata: AbilityMetadata;
    score: number;
}

function normalizeName(value: string): string {
    return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function iconKeyFromPath(iconPath: string | undefined): string {
    if (!iconPath) {
        return "";
    }
    const fileName = iconPath.replace(/\\/g, "/").split("/").pop() ?? "";
    return fileName
        .replace(/\.[^.]+$/, "")
        .toLowerCase()
        .replace(/[^a-z0-9]/g, "");
}

function inferSlotFromIconPath(iconPath: string): AbilitySlot | undefined {
    const fileName = iconPath.replace(/\\/g, "/").split("/").pop()?.replace(/\.[^.]+$/, "") ?? "";
    const lower = fileName.toLowerCase();

    if (/(^|[_-])passive/.test(lower) || /[_-]p\d*$/.test(lower)) {
        return "P";
    }

    const matchWithUnderscore = lower.match(/[_-]([qwer])\d*$/);
    if (matchWithUnderscore) {
        return matchWithUnderscore[1].toUpperCase() as AbilitySlot;
    }

    const trailingMatch = lower.match(/([qwer])\d*$/);
    if (trailingMatch) {
        return trailingMatch[1].toUpperCase() as AbilitySlot;
    }

    return undefined;
}

function readArray(value: unknown, maxRank?: number): number[] {
    return clampValuesToMaxRank(normalizeArray(value), maxRank);
}

function formatNumber(value: number): string {
    if (Number.isInteger(value)) {
        return String(value);
    }
    return value.toFixed(3).replace(/\.0+$/, "").replace(/(\.\d*?)0+$/, "$1");
}

function formatSeries(values: number[]): string {
    return values.map((value) => formatNumber(value)).join(" / ");
}

function nonZeroSeries(values: number[]): number[] {
    return values.filter((value) => Number.isFinite(value) && value !== 0);
}

function mapTargetingType(rawType: string | undefined): string {
    const value = (rawType ?? "").trim();
    if (!value) {
        return "";
    }

    const lower = value.toLowerCase();
    if (lower.includes("selfaoe")) {
        return TARGETING_CODES.SELF_AREA;
    }
    if (lower === "self" || lower.includes("self")) {
        return TARGETING_CODES.SELF;
    }
    if (lower.includes("locationclamped") || lower.includes("clampedlocation")) {
        return TARGETING_CODES.LOCATION_CLAMPED;
    }
    if (lower.includes("location")) {
        return TARGETING_CODES.LOCATION;
    }
    if (lower.includes("target") || lower.includes("unit")) {
        return TARGETING_CODES.UNIT_TARGETED;
    }
    if (lower.includes("line") || lower.includes("direction") || lower.includes("vector")) {
        return TARGETING_CODES.DIRECTION;
    }
    if (lower.includes("area") || lower.includes("aoe") || lower.includes("cone")) {
        return TARGETING_CODES.AREA;
    }

    return value.replace(/([a-z])([A-Z])/g, "$1 $2");
}

function normalizeSpellTag(tag: string): string {
    return tag
        .replace(/^Trait_/i, "")
        .replace(/^SpecialCase_/i, "")
        .replace(/^PositiveEffect_/i, "Positive ")
        .replace(/^NegativeEffect_/i, "Negative ")
        .replace(/_/g, " ")
        .trim();
}

function formatAffects(values: Set<string>): string {
    const ordered = [AFFECT_CODES.SELF, AFFECT_CODES.ALLIES, AFFECT_CODES.ENEMIES].filter((value) => values.has(value));
    return ordered.join(", ");
}

function decodeAffectsBits(affectsTypeFlags: number | undefined): {
    hasSelf: boolean;
    hasAllies: boolean;
    hasEnemies: boolean;
} {
    if (typeof affectsTypeFlags !== "number" || !Number.isFinite(affectsTypeFlags) || affectsTypeFlags <= 0) {
        return {
            hasSelf: false,
            hasAllies: false,
            hasEnemies: false
        };
    }

    const SELF_BITS = 1;
    const ALLY_BITS = 1024 | 16384;
    const ENEMY_BITS = 2 | 8 | 2048 | 4096 | 8192;

    return {
        hasSelf: (affectsTypeFlags & SELF_BITS) !== 0,
        hasAllies: (affectsTypeFlags & ALLY_BITS) !== 0,
        hasEnemies: (affectsTypeFlags & ENEMY_BITS) !== 0
    };
}

function resolveAffects(
    slot: AbilitySlot,
    targeting: string,
    spellTags: string[],
    affectsTypeFlags: number | undefined
): { affects: string; values: Set<string> } {
    const values = new Set<string>();
    const tagsLower = spellTags.map((tag) => tag.toLowerCase());

    const hasPositive = tagsLower.some((tag) =>
        tag.includes("positiveeffect") || tag.includes("boon") || tag.includes("attackreset") || tag.includes("moveblock")
    );
    const hasEnemyIntent = tagsLower.some((tag) =>
        tag.includes("negativeeffect") || tag.includes("immobilizing") || tag.includes("debuff")
    );
    const bits = decodeAffectsBits(affectsTypeFlags);

    if (targeting === TARGETING_CODES.SELF || targeting === TARGETING_CODES.SELF_AREA) {
        values.add(AFFECT_CODES.SELF);
    }

    if (
        targeting === TARGETING_CODES.DIRECTION
        || targeting === TARGETING_CODES.UNIT_TARGETED
        || targeting === TARGETING_CODES.AREA
    ) {
        values.add(AFFECT_CODES.ENEMIES);
    }

    if (targeting === TARGETING_CODES.LOCATION || targeting === TARGETING_CODES.LOCATION_CLAMPED) {
        if (hasPositive && !hasEnemyIntent && !bits.hasEnemies) {
            values.add(AFFECT_CODES.ALLIES);
            values.add(AFFECT_CODES.SELF);
        } else {
            values.add(AFFECT_CODES.ENEMIES);
        }
    }

    if (bits.hasEnemies) {
        values.add(AFFECT_CODES.ENEMIES);
    }
    if (bits.hasAllies && (hasPositive || targeting === TARGETING_CODES.SELF || targeting === TARGETING_CODES.SELF_AREA)) {
        values.add(AFFECT_CODES.ALLIES);
    }
    if (bits.hasSelf && (slot === "P" || hasPositive || targeting === TARGETING_CODES.SELF || targeting === TARGETING_CODES.SELF_AREA)) {
        values.add(AFFECT_CODES.SELF);
    }

    if (targeting === TARGETING_CODES.SELF_AREA && hasPositive && !hasEnemyIntent && !bits.hasEnemies) {
        values.add(AFFECT_CODES.ALLIES);
    }

    if (slot === "P" && values.size === 0) {
        values.add(AFFECT_CODES.SELF);
    }

    if (hasEnemyIntent) {
        values.add(AFFECT_CODES.ENEMIES);
    }

    return {
        affects: formatAffects(values),
        values
    };
}

function deriveTargeting(
    rawTargetingType: string,
    spellTags: string[],
    affectsTypeFlags: number | undefined
): string {
    const base = mapTargetingType(rawTargetingType);
    if (!base) {
        return "";
    }

    if (base !== TARGETING_CODES.SELF_AREA) {
        return base;
    }

    const tagsLower = spellTags.map((tag) => tag.toLowerCase());
    const hasPositive = tagsLower.some((tag) => tag.includes("positiveeffect") || tag.includes("boon"));
    const hasEnemyIntent = tagsLower.some((tag) =>
        tag.includes("negativeeffect") || tag.includes("immobilizing") || tag.includes("debuff")
    );
    const bits = decodeAffectsBits(affectsTypeFlags);

    if (hasPositive && !hasEnemyIntent && !bits.hasEnemies) {
        return TARGETING_CODES.SELF;
    }

    return base;
}

function resolveSpellshieldable(
    targeting: string,
    affectsValues: Set<string>,
    hasProjectile: boolean,
    spellData: JsonRecord | undefined
): boolean {
    if (spellData && typeof spellData.mCanBeBlockedBySpellShield === "boolean") {
        return spellData.mCanBeBlockedBySpellShield;
    }
    if (spellData && typeof spellData.spellShieldable === "boolean") {
        return spellData.spellShieldable;
    }

    if (targeting === TARGETING_CODES.SELF || targeting === TARGETING_CODES.SELF_AREA) {
        return false;
    }

    if (!affectsValues.has(AFFECT_CODES.ENEMIES)) {
        return false;
    }

    if (
        targeting === TARGETING_CODES.UNIT_TARGETED
        || targeting === TARGETING_CODES.DIRECTION
        || targeting === TARGETING_CODES.LOCATION
        || targeting === TARGETING_CODES.LOCATION_CLAMPED
    ) {
        return true;
    }

    if (hasProjectile) {
        return true;
    }

    return true;
}

function readLineWidth(spellData: JsonRecord, maxRank?: number): number[] {
    const direct = readArray(spellData.mLineWidth, maxRank);
    if (direct.length > 0) {
        return direct;
    }

    const clientData = spellData.mClientData;
    if (!clientData || typeof clientData !== "object") {
        return [];
    }

    const targeters = (clientData as JsonRecord).mTargeterDefinitions;
    if (!Array.isArray(targeters)) {
        return [];
    }

    for (const targeter of targeters) {
        if (!targeter || typeof targeter !== "object") {
            continue;
        }
        const lineWidth = (targeter as JsonRecord).lineWidth;
        if (!lineWidth || typeof lineWidth !== "object") {
            continue;
        }
        const perLevelValues = (lineWidth as JsonRecord).mPerLevelValues;
        const values = readArray(perLevelValues, maxRank);
        if (values.length > 0) {
            return values;
        }
    }

    return [];
}

function deriveCastTime(spellData: JsonRecord): number[] {
    const castTime = normalizeArray(spellData.mCastTime);
    if (castTime.length > 0) {
        return castTime;
    }

    const castFrame = Number(spellData.castFrame);
    if (Number.isFinite(castFrame) && castFrame > 0) {
        return [castFrame / 30];
    }

    return [];
}

function deriveMissileSpeed(spellData: JsonRecord): number[] {
    const direct = normalizeArray(spellData.missileSpeed);
    if (direct.some((value) => value > 0)) {
        return direct.filter((value) => value > 0);
    }

    const missileSpec = spellData.mMissileSpec;
    if (!missileSpec || typeof missileSpec !== "object") {
        return [];
    }

    const movement = (missileSpec as JsonRecord).movementComponent;
    if (!movement || typeof movement !== "object") {
        return [];
    }

    const speed = Number((movement as JsonRecord).mSpeed);
    return Number.isFinite(speed) && speed > 0 ? [speed] : [];
}

function deriveRechargeRate(spell: CDragonSpell | undefined, maxRank?: number): number[] {
    const ammo = spell?.ammo;
    if (!ammo || typeof ammo !== "object") {
        return [];
    }
    const recharge = readArray((ammo as Record<string, unknown>).ammoRechargeTime, maxRank);
    return nonZeroSeries(recharge);
}

function buildMetadataFromSources(
    slot: AbilitySlot,
    spellData: JsonRecord | undefined,
    spell: CDragonSpell | undefined,
    maxRank?: number
): AbilityMetadata {
    const metadata: AbilityMetadata = {};

    const spellTags = Array.isArray(spellData?.mSpellTags)
        ? spellData!.mSpellTags.map((tag) => String(tag)).filter(Boolean)
        : [];
    if (spellTags.length > 0) {
        metadata.spellEffects = spellTags.map((tag) => normalizeSpellTag(tag)).join(", ");
    }

    const targetingTypeRaw = spellData && typeof spellData.mTargetingTypeData === "object"
        ? String((spellData.mTargetingTypeData as JsonRecord).__type ?? "")
        : "";
    const affectsTypeFlags = spellData ? Number(spellData.mAffectsTypeFlags) : undefined;
    const targeting = deriveTargeting(
        targetingTypeRaw,
        spellTags,
        Number.isFinite(affectsTypeFlags) ? affectsTypeFlags : undefined
    );
    if (targeting) {
        metadata.targeting = targeting;
    }

    const affects = resolveAffects(
        slot,
        targeting,
        spellTags,
        Number.isFinite(affectsTypeFlags) ? affectsTypeFlags : undefined
    );
    if (affects.affects) {
        metadata.affects = affects.affects;
    }

    const targetRange = spellData
        ? (readArray(spellData.castRangeDisplayOverride, maxRank).length > 0
            ? readArray(spellData.castRangeDisplayOverride, maxRank)
            : readArray(spellData.castRange, maxRank))
        : [];
    const fallbackRange = readArray(spell?.range, maxRank);
    const resolvedRange = targetRange.length > 0 ? targetRange : fallbackRange;
    if (resolvedRange.length > 0) {
        metadata.targetRange = formatSeries(resolvedRange);
    }

    const effectRadius = spellData ? readArray(spellData.castRadius, maxRank) : [];
    if (effectRadius.length > 0) {
        metadata.effectRadius = formatSeries(effectRadius);
    }

    const innerRadius = spellData ? readArray(spellData.castRadiusSecondary, maxRank) : [];
    if (innerRadius.length > 0) {
        metadata.innerRadius = formatSeries(innerRadius);
    }

    const width = spellData ? readLineWidth(spellData, maxRank) : [];
    if (width.length > 0) {
        const widthDisplay = formatSeries(width);
        metadata.width = widthDisplay;
        metadata.collisionRadius = widthDisplay;
    }

    const angle = spellData ? readArray(spellData.mCastConeAngle, maxRank) : [];
    if (angle.length > 0) {
        metadata.angle = formatSeries(angle);
    }

    const castTime = spellData ? deriveCastTime(spellData) : [];
    if (castTime.length > 0) {
        metadata.castTime = formatSeries(castTime);
    }

    const missileSpeed = spellData ? deriveMissileSpeed(spellData) : [];
    if (missileSpeed.length > 0) {
        const speedDisplay = formatSeries(missileSpeed);
        metadata.missileSpeed = speedDisplay;
        metadata.speed = speedDisplay;
    }

    const hasProjectile = Boolean(spellData && spellData.mMissileSpec && typeof spellData.mMissileSpec === "object");
    if (hasProjectile) {
        metadata.projectile = "MISSILE";
    }

    metadata.spellshieldable = resolveSpellshieldable(targeting, affects.values, hasProjectile, spellData);

    const rechargeRate = deriveRechargeRate(spell, maxRank);
    if (rechargeRate.length > 0) {
        metadata.rechargeRate = formatSeries(rechargeRate);
    }

    return metadata;
}

function isNoiseSpell(pathKey: string, scriptName: string): boolean {
    const text = `${pathKey} ${scriptName}`.toLowerCase();
    return /missile|buff|debuff|indicator|trail|return|ready|cooldown|proc|attack|basic|crit|land|jump/.test(text);
}

function metadataScore(metadata: AbilityMetadata): number {
    return Object.values(metadata).filter((value) => Boolean(value && String(value).trim())).length;
}

export function resolveAbilityMetadata(
    overrides: ChampionAbilityMetadataOverrides,
    slot: AbilitySlot,
    variantIndex: number,
    variantName: string
): AbilityMetadata | undefined {
    const byIndex = overrides.bySlotIndex[slot]?.[variantIndex];
    if (byIndex) {
        return byIndex;
    }

    const byName = overrides.bySlotName[slot]?.[normalizeName(variantName)];
    if (byName) {
        return byName;
    }

    return undefined;
}

export class NativeAbilityMetadataResolver {
    static async create(): Promise<NativeAbilityMetadataResolver> {
        return new NativeAbilityMetadataResolver();
    }

    async save(): Promise<void> {
        // Native resolver does not persist external cache.
    }

    async resolveChampion(
        championKey: string,
        patchVersion: string,
        spells: CDragonSpell[],
        maxRankBySlot: Partial<Record<AbilitySlot, number>>
    ): Promise<ChampionAbilityMetadataOverrides> {
        const bySlotIndex: Partial<Record<AbilitySlot, Record<number, AbilityMetadata>>> = {};
        const bySlotName: Partial<Record<AbilitySlot, Record<string, AbilityMetadata>>> = {};

        const patchChannel = toPatchChannel(patchVersion);
        const key = championKey.toLowerCase();
        const url = `${RAW_CDRAGON_BASE}/${patchChannel}/game/data/characters/${key}/${key}.bin.json`;

        let binData: JsonRecord = {};
        try {
            const response = await fetch(url);
            if (response.ok) {
                binData = await response.json() as JsonRecord;
            }
        } catch {
            binData = {};
        }

        const bySlot = new Map<AbilitySlot, Map<string, BinSpellCandidate>>();
        const slotByIconKey = new Map<string, AbilitySlot>();
        spells.forEach((spell, index) => {
            const iconKey = iconKeyFromPath(spell.abilityIconPath);
            if (!iconKey) {
                return;
            }
            const slot = resolveAbilitySlot(spell.spellKey, index);
            slotByIconKey.set(iconKey, slot);
        });

        for (const [pathKey, value] of Object.entries(binData)) {
            if (!value || typeof value !== "object") {
                continue;
            }

            const entry = value as JsonRecord;
            const spellData = entry.mSpell;
            if (!spellData || typeof spellData !== "object") {
                continue;
            }

            const spellDataRecord = spellData as JsonRecord;
            const iconPathRaw = Array.isArray(spellDataRecord.mImgIconName)
                ? String(spellDataRecord.mImgIconName[0] ?? "")
                : "";

            const scriptName = String(entry.mScriptName ?? "");
            const iconKey = iconPathRaw ? iconKeyFromPath(iconPathRaw) : "";
            let slot = iconPathRaw ? (slotByIconKey.get(iconKey) ?? inferSlotFromIconPath(iconPathRaw)) : undefined;
            if (!slot) {
                const scriptKey = `${pathKey} ${scriptName}`.toLowerCase();
                if (scriptKey.includes("passive")) {
                    slot = "P";
                }
            }
            if (!slot) {
                continue;
            }

            const maxRank = maxRankBySlot[slot];
            const metadata = buildMetadataFromSources(slot, spellDataRecord, undefined, maxRank);
            const score = metadataScore(metadata)
                + (isNoiseSpell(pathKey, scriptName) ? 0 : 2)
                + (scriptName.toLowerCase().includes("ability") ? 1 : 0);
            if (score <= 0) {
                continue;
            }

            if (!bySlot.has(slot)) {
                bySlot.set(slot, new Map());
            }

            const slotMap = bySlot.get(slot)!;
            const resolvedIconKey = iconKey || `__${slot}_${normalizeName(scriptName || pathKey)}`;
            const existing = slotMap.get(resolvedIconKey);
            if (!existing || score > existing.score) {
                slotMap.set(resolvedIconKey, {
                    iconKey: resolvedIconKey,
                    metadata,
                    score
                });
            }
        }

        const passiveCandidates = bySlot.get("P");
        if (passiveCandidates && passiveCandidates.size > 0) {
            const bestPassive = Array.from(passiveCandidates.values())
                .sort((a, b) => b.score - a.score)[0];
            if (bestPassive) {
                bySlotIndex.P = { 0: bestPassive.metadata };
            }
        }

        spells.forEach((spell, index) => {
            const slot = resolveAbilitySlot(spell.spellKey, index);
            const maxRank = maxRankBySlot[slot];
            const names = splitAbilityVariantNames(spell.name, slot);
            const slotCandidates = bySlot.get(slot);
            const iconKey = iconKeyFromPath(spell.abilityIconPath);
            const firstCandidate = slotCandidates ? Array.from(slotCandidates.values())[0] : undefined;
            const binMetadata = slotCandidates?.get(iconKey)?.metadata
                ?? firstCandidate?.metadata
                ?? {};
            const cdragonMetadata = buildMetadataFromSources(slot, undefined, spell, maxRank);
            const metadata = {
                ...cdragonMetadata,
                ...binMetadata
            };

            if (metadataScore(metadata) === 0) {
                return;
            }

            names.forEach((name, variantIndex) => {
                if (!bySlotIndex[slot]) {
                    bySlotIndex[slot] = {};
                }
                bySlotIndex[slot]![variantIndex] = metadata;

                if (!bySlotName[slot]) {
                    bySlotName[slot] = {};
                }
                bySlotName[slot]![normalizeName(name)] = metadata;
            });
        });

        return { bySlotIndex, bySlotName };
    }
}