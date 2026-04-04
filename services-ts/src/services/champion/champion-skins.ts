import luaparse from "luaparse";
import { toPluginAssetUrl } from "./champion-assets.js";
import type { CDragonChampionSkin, CDragonSkinChroma } from "./champion-types.js";

const WIKI_SKIN_DATA_URL = "https://wiki.leagueoflegends.com/en-us/Module:SkinData/data?action=raw";
const WIKI_SKIN_DATA_HEADERS = {
    Accept: "text/plain",
    "User-Agent": "lolstaticdata-skin-resolver/1.0"
};

interface WikiSkinChromaEntry {
    id?: number | string;
    availability?: string;
}

export interface WikiSkinEntry {
    id?: number | string;
    availability?: string;
    cost?: number | string;
    release?: string;
    looteligible?: boolean;
    formatname?: string;
    distribution?: string;
    set?: string[];
    lore?: string;
    voiceactor?: string[];
    splashartist?: string[];
    neweffects?: boolean;
    newanimations?: boolean;
    newrecall?: boolean;
    newvoice?: boolean;
    newquotes?: boolean;
    chromas?: Record<string, WikiSkinChromaEntry>;
}

export type WikiSkinDataIndex = Record<string, Record<number, WikiSkinEntry>>;

function normalizeName(value: string): string {
    return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function toRecord(value: unknown): Record<string, unknown> {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return {};
    }
    return value as Record<string, unknown>;
}

function toNumber(value: unknown): number | undefined {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
        return undefined;
    }
    return parsed;
}

function combineChampionAndSkinId(championId: number, skinLocalId: number): number {
    return Number(`${championId}${String(skinLocalId).padStart(3, "0")}`);
}

function evaluateLuaExpression(node: any): unknown {
    if (!node) {
        return undefined;
    }

    switch (node.type) {
        case "StringLiteral":
            if (typeof node.value === "string") {
                return node.value;
            }
            if (typeof node.raw === "string" && node.raw.length >= 2) {
                const quote = node.raw[0];
                const endQuote = node.raw[node.raw.length - 1];
                if ((quote === "\"" || quote === "'") && quote === endQuote) {
                    return node.raw
                        .slice(1, -1)
                        .replace(/\\n/g, "\n")
                        .replace(/\\r/g, "\r")
                        .replace(/\\t/g, "\t")
                        .replace(/\\"/g, "\"")
                        .replace(/\\'/g, "'")
                        .replace(/\\\\/g, "\\");
                }
            }
            return "";
        case "NumericLiteral":
        case "BooleanLiteral":
            return node.value;
        case "NilLiteral":
            return null;
        case "UnaryExpression": {
            if (node.operator === "-") {
                const value = Number(evaluateLuaExpression(node.argument));
                if (Number.isFinite(value)) {
                    return -value;
                }
            }
            return undefined;
        }
        case "TableConstructorExpression": {
            const arrayValues: unknown[] = [];
            const objectValues: Record<string, unknown> = {};
            let hasArrayValues = false;
            let hasObjectValues = false;

            for (const field of node.fields ?? []) {
                if (field.type === "TableValue") {
                    arrayValues.push(evaluateLuaExpression(field.value));
                    hasArrayValues = true;
                    continue;
                }

                if (field.type === "TableKeyString") {
                    objectValues[field.key.name] = evaluateLuaExpression(field.value);
                    hasObjectValues = true;
                    continue;
                }

                if (field.type === "TableKey") {
                    const key = evaluateLuaExpression(field.key);
                    const value = evaluateLuaExpression(field.value);

                    if (typeof key === "number" && Number.isInteger(key) && key > 0 && !hasObjectValues) {
                        arrayValues[key - 1] = value;
                        hasArrayValues = true;
                        continue;
                    }

                    if (typeof key === "string" || typeof key === "number") {
                        objectValues[String(key)] = value;
                        hasObjectValues = true;
                    }
                }
            }

            if (hasObjectValues && !hasArrayValues) {
                return objectValues;
            }
            if (hasArrayValues && !hasObjectValues) {
                return arrayValues;
            }
            if (!hasArrayValues && !hasObjectValues) {
                return {};
            }

            objectValues._array = arrayValues;
            return objectValues;
        }
        default:
            return undefined;
    }
}

function parseWikiSkinData(raw: string): Record<string, unknown> {
    const ast = luaparse.parse(raw, { luaVersion: "5.3" });
    const returnStatement = ast.body.find((entry: any) => entry.type === "ReturnStatement") as any;
    const tableExpression = returnStatement?.arguments?.[0];
    const parsed = evaluateLuaExpression(tableExpression);
    return toRecord(parsed);
}

function toStringArray(value: unknown): string[] {
    if (!Array.isArray(value)) {
        return [];
    }
    return value.map((entry) => String(entry)).filter(Boolean);
}

export function skinCostToString(value: number | string | undefined): string {
    if (value === undefined || value === null) {
        return "";
    }
    return String(value);
}

export function normalizeSkinReleaseDate(value: string | undefined): string {
    if (!value || value === "N/A") {
        return "";
    }

    const trimmed = value.trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
        return trimmed;
    }

    const epoch = Date.parse(trimmed);
    if (!Number.isFinite(epoch)) {
        return "";
    }

    return new Date(epoch).toISOString().slice(0, 10);
}

export function resolveWikiSkinMap(index: WikiSkinDataIndex, championNameCandidates: string[]): Record<number, WikiSkinEntry> {
    for (const candidate of championNameCandidates) {
        const normalized = normalizeName(candidate ?? "");
        if (!normalized) {
            continue;
        }
        const resolved = index[normalized];
        if (resolved) {
            return resolved;
        }
    }
    return {};
}

function mapCDragonChroma(chroma: CDragonSkinChroma, patchVersion: string): Record<string, unknown> {
    return {
        name: chroma.name ?? "",
        id: chroma.id,
        chromaPath: toPluginAssetUrl(chroma.chromaPath ?? chroma.tilePath, patchVersion),
        colors: chroma.colors ?? [],
        descriptions: (chroma.descriptions ?? []).map((entry) => ({
            description: entry.description ?? "",
            region: entry.region ?? ""
        })),
        rarities: (chroma.rarities ?? []).map((entry) => ({
            rarity: Number(entry.rarity ?? 0),
            region: entry.region ?? ""
        }))
    };
}

export function mapSkinChromas(
    skin: CDragonChampionSkin,
    wikiSkin: WikiSkinEntry | undefined,
    championId: number,
    patchVersion: string
): Array<Record<string, unknown>> {
    const cdragonChromas = Array.isArray(skin.chromas) ? skin.chromas : [];
    const cdragonById = new Map<number, CDragonSkinChroma>();
    cdragonChromas.forEach((chroma) => {
        cdragonById.set(chroma.id, chroma);
    });

    const wikiChromas = toRecord(wikiSkin?.chromas);
    const wikiEntries = Object.entries(wikiChromas);

    if (wikiEntries.length === 0) {
        return cdragonChromas.map((chroma) => mapCDragonChroma(chroma, patchVersion));
    }

    const chromaPayload: Array<Record<string, unknown>> = [];
    for (const [chromaName, chromaValue] of wikiEntries) {
        const parsed = toRecord(chromaValue);
        if (String(parsed.availability ?? "") === "Canceled") {
            continue;
        }

        const wikiChromaLocalId = toNumber(parsed.id);
        if (!wikiChromaLocalId) {
            continue;
        }

        const fullChromaId = combineChampionAndSkinId(championId, wikiChromaLocalId);
        const cdragonChroma = cdragonById.get(fullChromaId);

        chromaPayload.push({
            name: chromaName,
            id: fullChromaId,
            chromaPath: toPluginAssetUrl(cdragonChroma?.chromaPath ?? cdragonChroma?.tilePath, patchVersion),
            colors: cdragonChroma?.colors ?? [],
            descriptions: (cdragonChroma?.descriptions ?? []).map((entry) => ({
                description: entry.description ?? "",
                region: entry.region ?? ""
            })),
            rarities: (cdragonChroma?.rarities ?? []).map((entry) => ({
                rarity: Number(entry.rarity ?? 0),
                region: entry.region ?? ""
            }))
        });
    }

    return chromaPayload;
}

export async function fetchWikiSkinDataIndex(): Promise<WikiSkinDataIndex> {
    try {
        const response = await fetch(WIKI_SKIN_DATA_URL, { headers: WIKI_SKIN_DATA_HEADERS });
        if (!response.ok) {
            return {};
        }

        const raw = await response.text();
        const parsed = parseWikiSkinData(raw);
        const index: WikiSkinDataIndex = {};

        Object.entries(parsed).forEach(([championName, championValue]) => {
            const championData = toRecord(championValue);
            const championId = toNumber(championData.id);
            if (!championId) {
                return;
            }

            const skins = toRecord(championData.skins);
            const bySkinId: Record<number, WikiSkinEntry> = {};

            Object.entries(skins).forEach(([skinName, skinValue]) => {
                const skinData = toRecord(skinValue);
                const skinLocalId = toNumber(skinData.id);
                if (skinLocalId === undefined || skinLocalId === null) {
                    return;
                }

                const skinId = combineChampionAndSkinId(championId, skinLocalId);
                bySkinId[skinId] = {
                    id: skinData.id as number | string | undefined,
                    availability: String(skinData.availability ?? "Available"),
                    cost: skinData.cost as number | string | undefined,
                    release: typeof skinData.release === "string" ? skinData.release : undefined,
                    looteligible: typeof skinData.looteligible === "boolean" ? skinData.looteligible : undefined,
                    formatname: typeof skinData.formatname === "string" ? skinData.formatname : skinName,
                    distribution: typeof skinData.distribution === "string" ? skinData.distribution : undefined,
                    set: toStringArray(skinData.set),
                    lore: typeof skinData.lore === "string" ? skinData.lore : undefined,
                    voiceactor: toStringArray(skinData.voiceactor),
                    splashartist: toStringArray(skinData.splashartist),
                    neweffects: Boolean(skinData.neweffects),
                    newanimations: Boolean(skinData.newanimations),
                    newrecall: Boolean(skinData.newrecall),
                    newvoice: Boolean(skinData.newvoice),
                    newquotes: Boolean(skinData.newquotes),
                    chromas: toRecord(skinData.chromas) as Record<string, WikiSkinChromaEntry>
                };
            });

            const normalizedChampion = normalizeName(championName);
            if (normalizedChampion) {
                index[normalizedChampion] = bySkinId;
            }
        });

        return index;
    } catch {
        return {};
    }
}
