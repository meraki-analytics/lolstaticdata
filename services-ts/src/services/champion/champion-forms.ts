import { RAW_CDRAGON_BASE, toPatchChannel } from "./champion-assets.js";
import { clampValuesToMaxRank, inferLevelingUnit, normalizeArray } from "./champion-mapping.js";
import type { AbilitySlot, FormAbilityVariantLookup, FormAbilityVariantOverride } from "./champion-types.js";

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

    const matchWithUnderscore = lower.match(/[_-]([qwer])\d*$/);
    if (matchWithUnderscore) {
        const key = matchWithUnderscore[1].toUpperCase();
        if (key === "Q" || key === "W" || key === "E" || key === "R") {
            return key;
        }
    }

    const trailingMatch = lower.match(/([qwer])\d*$/);
    if (trailingMatch) {
        const key = trailingMatch[1].toUpperCase();
        if (key === "Q" || key === "W" || key === "E" || key === "R") {
            return key;
        }
    }

    return undefined;
}

function normalizeBinIconPath(iconPath: string): string {
    const normalized = iconPath
        .replace(/\\/g, "/")
        .replace(/^\/+/, "")
        .replace(/\.dds$/i, ".png");
    return `/lol-game-data/assets/${normalized}`;
}

function isNoiseSpell(pathKey: string, scriptName: string): boolean {
    const text = `${pathKey} ${scriptName}`.toLowerCase();
    return /missile|buff|debuff|indicator|trail|return|ready|cooldown|proc|attack|basic|crit|land|jump/.test(text);
}

function buildLevelingFromDataValues(
    spellData: Record<string, unknown>,
    adaptiveType: string,
    resource: string,
    maxRank?: number
): Array<Record<string, unknown>> {
    const raw = (spellData.DataValues ?? spellData.mDataValues) as unknown;
    if (!Array.isArray(raw)) {
        return [];
    }

    const leveling: Array<Record<string, unknown>> = [];
    for (const item of raw) {
        if (!item || typeof item !== "object") {
            continue;
        }

        const entry = item as Record<string, unknown>;
        const attribute = String(entry.name ?? entry.mName ?? "");
        const values = clampValuesToMaxRank(normalizeArray(entry.values ?? entry.mValues), maxRank);
        if (!attribute || values.length === 0 || values.every((v) => v === 0)) {
            continue;
        }

        leveling.push({
            attribute,
            modifiers: [
                {
                    values,
                    units: values.map(() => inferLevelingUnit(attribute, adaptiveType, resource, values))
                }
            ]
        });
    }

    return leveling.slice(0, 12);
}

function splitAttributePrefix(attribute: string): { prefix: string; suffix: string } | undefined {
    const tokens = attribute.match(/[A-Z]+(?![a-z])|[A-Z]?[a-z]+|[0-9]+/g);
    if (!tokens || tokens.length < 2) {
        return undefined;
    }
    const prefix = tokens[0] ?? "";
    const suffix = tokens.slice(1).join("");
    if (!prefix || !suffix) {
        return undefined;
    }
    return { prefix, suffix };
}

function getLevelingAttributePrefixes(leveling: Array<Record<string, unknown>>): Set<string> {
    const prefixes = new Set<string>();
    for (const entry of leveling) {
        const attribute = String(entry.attribute ?? "");
        const parts = splitAttributePrefix(attribute);
        if (parts) {
            prefixes.add(parts.prefix);
        }
    }
    return prefixes;
}

function normalizeSharedFormLeveling(overrides: FormAbilityVariantOverride[]): FormAbilityVariantOverride[] {
    if (overrides.length <= 1) {
        return overrides;
    }

    const normalized = overrides.map((override) => ({
        ...override,
        leveling: [...override.leveling]
    }));

    const suffixToPrefixes = new Map<string, Set<string>>();
    for (const override of normalized) {
        for (const entry of override.leveling) {
            const parts = splitAttributePrefix(String(entry.attribute ?? ""));
            if (!parts) {
                continue;
            }
            if (!suffixToPrefixes.has(parts.suffix)) {
                suffixToPrefixes.set(parts.suffix, new Set());
            }
            suffixToPrefixes.get(parts.suffix)!.add(parts.prefix);
        }
    }

    const formPrefixes = new Set<string>();
    for (const prefixes of suffixToPrefixes.values()) {
        if (prefixes.size >= 2) {
            for (const prefix of prefixes) {
                formPrefixes.add(prefix);
            }
        }
    }

    if (formPrefixes.size === 0) {
        return normalized;
    }

    for (const prefix of formPrefixes) {
        const variantsWithPrefix = normalized
            .map((override, index) => ({ index, prefixes: getLevelingAttributePrefixes(override.leveling) }))
            .filter((entry) => entry.prefixes.has(prefix));

        if (variantsWithPrefix.length <= 1) {
            continue;
        }

        const pureOwner = variantsWithPrefix.find((entry) => {
            const otherFormPrefixes = Array.from(entry.prefixes).filter((p) => formPrefixes.has(p) && p !== prefix);
            return otherFormPrefixes.length === 0;
        });

        if (!pureOwner) {
            continue;
        }

        for (const variant of variantsWithPrefix) {
            if (variant.index === pureOwner.index) {
                continue;
            }
            normalized[variant.index].leveling = normalized[variant.index].leveling.filter((entry) => {
                const parts = splitAttributePrefix(String(entry.attribute ?? ""));
                return !parts || parts.prefix !== prefix;
            });
            normalized[variant.index].hasLeveling = normalized[variant.index].leveling.length > 0;
        }
    }

    return normalized;
}

function buildVariantOverride(
    pathKey: string,
    scriptName: string,
    iconPathRaw: string,
    spellData: Record<string, unknown>,
    adaptiveType: string,
    resource: string,
    maxRank?: number
): FormAbilityVariantOverride {
    const normalizedIconPath = normalizeBinIconPath(iconPathRaw);
    const iconKey = iconKeyFromPath(iconPathRaw);

    const cooldownRaw = clampValuesToMaxRank(normalizeArray(spellData.cooldownTime), maxRank);
    const hasCooldown = Array.isArray((spellData as Record<string, unknown>).cooldownTime) || typeof (spellData as Record<string, unknown>).cooldownTime === "number";

    const manaRaw = clampValuesToMaxRank(normalizeArray(spellData.mana), maxRank);
    const hasCost = Array.isArray((spellData as Record<string, unknown>).mana) || typeof (spellData as Record<string, unknown>).mana === "number";
    const cost = manaRaw.some((value) => value !== 0) ? manaRaw : [];

    const rangeDisplay = clampValuesToMaxRank(normalizeArray(spellData.castRangeDisplayOverride), maxRank);
    const rangeCast = clampValuesToMaxRank(normalizeArray(spellData.castRange), maxRank);
    const rangeCandidate = rangeDisplay.length > 0 ? rangeDisplay : rangeCast;
    const hasRange = rangeCandidate.length > 0;

    const leveling = buildLevelingFromDataValues(spellData, adaptiveType, resource, maxRank);
    const hasLeveling = leveling.length > 0;
    const calculationNames = spellData.mSpellCalculations && typeof spellData.mSpellCalculations === "object"
        ? Object.keys(spellData.mSpellCalculations as Record<string, unknown>).filter(Boolean)
        : [];

    let score = 0;
    if (hasCooldown) {
        score += 2;
    }
    if (hasCost) {
        score += 2;
    }
    if (hasRange) {
        score += 1;
    }
    if (hasLeveling) {
        score += 2;
    }
    if (calculationNames.length > 0) {
        score += 1;
    }
    if (!isNoiseSpell(pathKey, scriptName)) {
        score += 2;
    }
    if (String(scriptName).toLowerCase().includes("ability")) {
        score += 1;
    }
    if (String(scriptName).toLowerCase().includes("cast")) {
        score += 1;
    }

    return {
        iconPath: normalizedIconPath,
        iconKey,
        score,
        calculationNames,
        hasCooldown,
        cooldown: cooldownRaw,
        hasCost,
        cost,
        hasRange,
        range: rangeCandidate,
        hasLeveling,
        leveling
    };
}

export async function fetchFormAbilityVariantLookup(
    championKey: string,
    patchVersion: string,
    adaptiveType: string,
    resource: string,
    maxRankBySlot: Partial<Record<AbilitySlot, number>>
): Promise<FormAbilityVariantLookup> {
    const patchChannel = toPatchChannel(patchVersion);
    const key = championKey.toLowerCase();
    const url = `${RAW_CDRAGON_BASE}/${patchChannel}/game/data/characters/${key}/${key}.bin.json`;

    const response = await fetch(url);
    if (!response.ok) {
        return {};
    }

    const binData = await response.json() as Record<string, unknown>;
    const bySlot = new Map<AbilitySlot, Map<string, FormAbilityVariantOverride>>();

    for (const [pathKey, value] of Object.entries(binData)) {
        if (!value || typeof value !== "object") {
            continue;
        }

        const entry = value as Record<string, unknown>;
        const spellData = entry.mSpell as Record<string, unknown> | undefined;
        if (!spellData || typeof spellData !== "object") {
            continue;
        }

        const iconPathRaw = Array.isArray(spellData.mImgIconName)
            ? String(spellData.mImgIconName[0] ?? "")
            : "";
        if (!iconPathRaw) {
            continue;
        }

        const iconKey = iconKeyFromPath(iconPathRaw);
        const slot = inferSlotFromIconPath(iconPathRaw);
        if (!slot) {
            continue;
        }
        const maxRank = maxRankBySlot[slot];

        const scriptName = String(entry.mScriptName ?? "");
        const override = buildVariantOverride(pathKey, scriptName, iconPathRaw, spellData, adaptiveType, resource, maxRank);

        if (!bySlot.has(slot)) {
            bySlot.set(slot, new Map());
        }

        const slotMap = bySlot.get(slot)!;
        const existing = slotMap.get(override.iconKey);
        if (!existing || override.score > existing.score) {
            slotMap.set(override.iconKey, override);
        }
    }

    const lookup: FormAbilityVariantLookup = {};
    for (const [slot, variants] of bySlot.entries()) {
        lookup[slot] = Array.from(variants.values())
            .sort((a, b) => b.score - a.score || a.iconKey.localeCompare(b.iconKey));
    }

    return lookup;
}

export function resolveFormVariantOverrides(
    mergedIconPath: string | undefined,
    slot: AbilitySlot,
    variantCount: number,
    lookup: FormAbilityVariantLookup
): FormAbilityVariantOverride[] {
    if (variantCount <= 1) {
        return [];
    }

    const candidates = lookup[slot] ?? [];
    if (candidates.length === 0) {
        return [];
    }

    const mergedIconKey = iconKeyFromPath(mergedIconPath);
    const exact = mergedIconKey
        ? candidates.find((candidate) => candidate.iconKey === mergedIconKey)
        : undefined;

    const remaining = candidates.filter((candidate) => candidate !== exact);
    const ordered = exact ? [exact, ...remaining] : [...remaining];

    return normalizeSharedFormLeveling(ordered.slice(0, variantCount));
}

export function resolvePrimaryAbilityOverride(
    mergedIconPath: string | undefined,
    slot: AbilitySlot,
    lookup: FormAbilityVariantLookup
): FormAbilityVariantOverride | undefined {
    const candidates = lookup[slot] ?? [];
    if (candidates.length === 0) {
        return undefined;
    }

    const mergedIconKey = iconKeyFromPath(mergedIconPath);
    if (!mergedIconKey) {
        return undefined;
    }

    return candidates.find((candidate) => candidate.iconKey === mergedIconKey);
}
