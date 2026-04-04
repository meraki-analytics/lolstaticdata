import { RAW_CDRAGON_BASE, toPatchChannel } from "./champion-assets.js";
import { fallbackCostUnitFromResource, normalizeArray } from "./champion-mapping.js";
import type { PassiveAbilityNumbers } from "./champion-types.js";

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

export async function fetchPassiveAbilityNumbers(
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
