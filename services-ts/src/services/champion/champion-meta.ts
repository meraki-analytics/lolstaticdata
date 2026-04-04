import luaparse from "luaparse";

const WIKI_CHAMPION_DATA_URL = "https://wiki.leagueoflegends.com/en-us/Module:ChampionData/data?action=raw";
const WIKI_CHAMPION_DATA_HEADERS = {
    Accept: "text/plain",
    "User-Agent": "lolstaticdata-meta-resolver/1.0"
};

const UNIVERSE_CHAMPION_BROWSE_URL = "https://universe-meeps.leagueoflegends.com/v1/en_us/champion-browse/index.json";

export interface ChampionMetadata {
    releaseDate: string;
    releasePatch: string;
    patchLastChanged: string;
    rp: number;
    blueEssence: number;
}

function normalizeChampionKey(value: string): string {
    return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function toRecord(value: unknown): Record<string, unknown> {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return {};
    }
    return value as Record<string, unknown>;
}

function toNumber(value: unknown): number {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
        return 0;
    }
    return parsed;
}

function normalizePatchValue(value: string): string {
    const trimmed = value.trim();
    if (!trimmed) {
        return "";
    }

    if (trimmed[0] === "V" || trimmed[0] === "v") {
        return trimmed.slice(1);
    }
    return trimmed;
}

function normalizeReleaseDate(value: string): string {
    const trimmed = value.trim();
    if (!trimmed || trimmed === "Upcoming") {
        return "";
    }

    if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
        return trimmed;
    }

    const epoch = Date.parse(trimmed);
    if (!Number.isFinite(epoch)) {
        return "";
    }

    return new Date(epoch).toISOString().slice(0, 10);
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

function parseWikiChampionData(raw: string): Record<string, unknown> {
    const ast = luaparse.parse(raw, { luaVersion: "5.3" });
    const returnStatement = ast.body.find((entry: any) => entry.type === "ReturnStatement") as any;
    const tableExpression = returnStatement?.arguments?.[0];
    return toRecord(evaluateLuaExpression(tableExpression));
}

export function resolveChampionMetadata(
    index: Record<string, ChampionMetadata>,
    championNameCandidates: string[]
): ChampionMetadata | undefined {
    for (const candidate of championNameCandidates) {
        const normalized = normalizeChampionKey(candidate ?? "");
        if (!normalized) {
            continue;
        }

        const resolved = index[normalized];
        if (resolved) {
            return resolved;
        }
    }
    return undefined;
}

export async function fetchChampionMetadataIndex(): Promise<Record<string, ChampionMetadata>> {
    try {
        const response = await fetch(WIKI_CHAMPION_DATA_URL, { headers: WIKI_CHAMPION_DATA_HEADERS });
        if (!response.ok) {
            return {};
        }

        const raw = await response.text();
        const parsed = parseWikiChampionData(raw);
        const index: Record<string, ChampionMetadata> = {};

        Object.entries(parsed).forEach(([championName, championValue]) => {
            const championData = toRecord(championValue);
            const apiname = String(championData.apiname ?? "").trim();
            const fullName = String(championData.fullname ?? "").trim();

            const metadata: ChampionMetadata = {
                releaseDate: normalizeReleaseDate(String(championData.date ?? "")),
                releasePatch: normalizePatchValue(String(championData.patch ?? "")),
                patchLastChanged: normalizePatchValue(String(championData.changes ?? "")),
                rp: toNumber(championData.rp),
                blueEssence: toNumber(championData.be)
            };

            const candidates = [championName, apiname, fullName];
            candidates.forEach((candidate) => {
                const normalized = normalizeChampionKey(candidate);
                if (!normalized || index[normalized]) {
                    return;
                }
                index[normalized] = metadata;
            });
        });

        return index;
    } catch {
        return {};
    }
}

export function resolveChampionFaction(
    factionBySlug: Record<string, string>,
    championNameCandidates: string[]
): string {
    for (const candidate of championNameCandidates) {
        const normalized = normalizeChampionKey(candidate ?? "");
        if (!normalized) {
            continue;
        }
        const faction = factionBySlug[normalized];
        if (typeof faction === "string" && faction.length > 0) {
            return faction;
        }
    }
    return "";
}

export async function fetchChampionFactionIndex(): Promise<Record<string, string>> {
    try {
        const response = await fetch(UNIVERSE_CHAMPION_BROWSE_URL);
        if (!response.ok) {
            return {};
        }

        const payload = await response.json() as { champions?: Array<{ slug?: string;[key: string]: unknown }> };
        const champions = Array.isArray(payload.champions) ? payload.champions : [];
        const index: Record<string, string> = {};

        champions.forEach((champion) => {
            const slug = String(champion.slug ?? "").trim();
            const faction = String(champion["associated-faction-slug"] ?? "").trim();
            const normalizedSlug = normalizeChampionKey(slug);
            if (!normalizedSlug || !faction) {
                return;
            }
            index[normalizedSlug] = faction;
        });

        return index;
    } catch {
        return {};
    }
}
