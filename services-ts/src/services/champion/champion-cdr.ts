import fs from "node:fs/promises";
import path from "node:path";
import { mapWithConcurrency } from "./champion-http.js";
import { resolveAbilitySlot, splitAbilityVariantNames } from "./champion-mapping.js";
import type { AbilitySlot, CDragonSpell } from "./champion-types.js";

const WIKI_TEMPLATE_BASE = "https://wiki.leagueoflegends.com/en-us/Template:Data_";
const WIKI_API_BASE = "https://wiki.leagueoflegends.com/en-us/api.php";
const WIKI_REQUEST_HEADERS = {
    Accept: "text/plain",
    "User-Agent": "lolstaticdata-cdr-resolver/1.0"
};

const WIKI_ABILITY_NAME_OVERRIDES: Record<string, string[]> = {
    "aphelios::weaponabilites": ["Weapon Queue System", "Weapon Abilities"],
    "jayce::mercurycannon": ["Transform Mercury Cannon", "Mercury Cannon"],
    "jayce::mercuryhammer": ["Transform Mercury Hammer", "Mercury Hammer"],
    "yunara::arcofjudgmentarcofruin": ["Arc of Judgment", "Arc of Ruin"],
    "yunara::kanmeisstepsuntouchableshadow": ["Kanmei's Steps", "Untouchable Shadow"]
};

interface WikiCacheFile {
    version: 1;
    entries: Record<string, { affectedByCdr: boolean; updatedAt: string }>;
}

interface WikiAllPagesResponse {
    query?: {
        allpages?: Array<{ title?: string }>;
    };
    continue?: {
        apcontinue?: string;
    };
}

export interface ChampionCooldownOverrides {
    bySlotIndex: Partial<Record<AbilitySlot, Record<number, boolean>>>;
    bySlotName: Partial<Record<AbilitySlot, Record<string, boolean>>>;
}

function normalizeName(value: string): string {
    return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function toTemplateSegment(value: string): string {
    return encodeURIComponent(value.replace(/\s+/g, "_").trim());
}

function buildAbilityCandidates(abilityName: string): string[] {
    const base = abilityName.trim();
    const candidates = [
        base,
        base.replace(/[’']/g, ""),
        base.replace(/[!?.,:]/g, ""),
        base.replace(/&/g, "and"),
        base.replace(/\//g, "")
    ]
        .map((value) => value.trim())
        .filter(Boolean);

    return Array.from(new Set(candidates));
}

function isValidAbilityTemplate(raw: string): boolean {
    return /\|\s*skill\s*=/.test(raw);
}

function parseAffectedByCdr(raw: string): boolean | undefined {
    if (!isValidAbilityTemplate(raw)) {
        return undefined;
    }
    return !/^\|\s*static\s*=/mi.test(raw);
}

function extractAbilityFromTemplateTitle(title: string): string | undefined {
    const marker = "Template:Data";
    if (!title.startsWith(marker)) {
        return undefined;
    }

    const slashIndex = title.indexOf("/");
    if (slashIndex < 0 || slashIndex >= title.length - 1) {
        return undefined;
    }

    return title.slice(slashIndex + 1).trim();
}

async function fetchTemplateRaw(url: string): Promise<string | undefined> {
    const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

    async function fetchRawWithRetry(targetUrl: string): Promise<string | undefined> {
        for (let attempt = 0; attempt < 3; attempt += 1) {
            const response = await fetch(targetUrl, { headers: WIKI_REQUEST_HEADERS });
            if (!response.ok) {
                if (response.status === 429 || response.status >= 500) {
                    await sleep(500 * (attempt + 1));
                    continue;
                }
                return undefined;
            }

            const raw = await response.text();
            if (/just a moment|attention required|captcha|cloudflare/i.test(raw)) {
                await sleep(700 * (attempt + 1));
                continue;
            }
            return raw;
        }

        return undefined;
    }

    const raw = await fetchRawWithRetry(url);
    if (!raw) {
        return undefined;
    }

    const redirect = raw.match(/^#redirect\s+\[\[([^\]]+)\]\]/im);
    if (!redirect) {
        return raw;
    }

    const title = redirect[1].trim().replace(/\s+/g, "_");
    const redirectUrl = `https://wiki.leagueoflegends.com/en-us/${encodeURIComponent(title)}?action=raw`;
    return fetchRawWithRetry(redirectUrl);
}

export class WikiCooldownResolver {
    private readonly cachePath: string;
    private readonly entries: Record<string, { affectedByCdr: boolean; updatedAt: string }>;
    private readonly templateTitleIndex = new Map<string, Record<string, string>>();
    private readonly unresolvedKeys = new Set<string>();
    private dirty = false;

    private constructor(cachePath: string, entries: Record<string, { affectedByCdr: boolean; updatedAt: string }>) {
        this.cachePath = cachePath;
        this.entries = entries;
    }

    static async create(cachePath: string): Promise<WikiCooldownResolver> {
        try {
            const raw = await fs.readFile(cachePath, "utf8");
            const parsed = JSON.parse(raw) as WikiCacheFile;
            if (parsed.version === 1 && parsed.entries && typeof parsed.entries === "object") {
                return new WikiCooldownResolver(cachePath, parsed.entries);
            }
        } catch {
            // ignore cache load failures and rebuild lazily
        }

        return new WikiCooldownResolver(cachePath, {});
    }

    async save(): Promise<void> {
        if (!this.dirty) {
            return;
        }

        await fs.mkdir(path.dirname(this.cachePath), { recursive: true });
        const payload: WikiCacheFile = {
            version: 1,
            entries: this.entries
        };
        await fs.writeFile(this.cachePath, JSON.stringify(payload, null, 2), "utf8");
        this.dirty = false;
    }

    getUnresolvedKeys(): string[] {
        return Array.from(this.unresolvedKeys).sort();
    }

    async resolveChampion(
        championNameCandidates: string[],
        spells: CDragonSpell[]
    ): Promise<ChampionCooldownOverrides> {
        const bySlotIndex: Partial<Record<AbilitySlot, Record<number, boolean>>> = {};
        const bySlotName: Partial<Record<AbilitySlot, Record<string, boolean>>> = {};

        const abilityNames: string[] = [];
        spells.forEach((spell, index) => {
            const slot = resolveAbilitySlot(spell.spellKey, index);
            const names = splitAbilityVariantNames(spell.name, slot);
            names.forEach((name) => abilityNames.push(name));
        });

        const uniqueByNormalized = new Map<string, string>();
        abilityNames.forEach((name) => {
            const normalized = normalizeName(name);
            if (normalized && !uniqueByNormalized.has(normalized)) {
                uniqueByNormalized.set(normalized, name);
            }
        });

        const resolvedByName = new Map<string, boolean>();
        const uniqueNames = Array.from(uniqueByNormalized.values());
        const resolved = await mapWithConcurrency(uniqueNames, 1, async (abilityName) => ({
            abilityName,
            affectedByCdr: await this.resolveAbility(championNameCandidates, abilityName)
        }));
        resolved.forEach(({ abilityName, affectedByCdr }) => {
            if (typeof affectedByCdr === "boolean") {
                resolvedByName.set(normalizeName(abilityName), affectedByCdr);
            }
        });

        spells.forEach((spell, index) => {
            const slot = resolveAbilitySlot(spell.spellKey, index);
            const names = splitAbilityVariantNames(spell.name, slot);
            names.forEach((name, variantIndex) => {
                const normalized = normalizeName(name);
                const affectedByCdr = resolvedByName.get(normalized);
                if (typeof affectedByCdr !== "boolean") {
                    return;
                }

                if (!bySlotIndex[slot]) {
                    bySlotIndex[slot] = {};
                }
                bySlotIndex[slot]![variantIndex] = affectedByCdr;

                if (!bySlotName[slot]) {
                    bySlotName[slot] = {};
                }
                bySlotName[slot]![normalized] = affectedByCdr;
            });
        });

        return { bySlotIndex, bySlotName };
    }

    private async resolveAbility(championNameCandidates: string[], abilityName: string): Promise<boolean | undefined> {
        const normalizedChampion = normalizeName(championNameCandidates[0] ?? "");
        const normalizedAbility = normalizeName(abilityName);
        if (!normalizedChampion || !normalizedAbility) {
            return undefined;
        }

        const cacheKey = `${normalizedChampion}::${normalizedAbility}`;
        const cached = this.entries[cacheKey];
        if (cached) {
            this.unresolvedKeys.delete(cacheKey);
            return cached.affectedByCdr;
        }

        const championCandidates = Array.from(new Set(championNameCandidates.filter(Boolean)));
        const abilityCandidates = Array.from(new Set([
            ...buildAbilityCandidates(abilityName),
            ...(WIKI_ABILITY_NAME_OVERRIDES[cacheKey] ?? [])
        ]));

        for (const championName of championCandidates) {
            const championSegment = toTemplateSegment(championName);
            for (const candidateAbilityName of abilityCandidates) {
                const abilitySegment = toTemplateSegment(candidateAbilityName);
                const url = `${WIKI_TEMPLATE_BASE}${championSegment}/${abilitySegment}?action=raw`;
                const raw = await fetchTemplateRaw(url);
                if (!raw) {
                    continue;
                }

                const affectedByCdr = parseAffectedByCdr(raw);
                if (typeof affectedByCdr !== "boolean") {
                    continue;
                }

                this.entries[cacheKey] = {
                    affectedByCdr,
                    updatedAt: new Date().toISOString()
                };
                this.dirty = true;
                this.unresolvedKeys.delete(cacheKey);
                return affectedByCdr;
            }
        }

        for (const championName of championCandidates) {
            const titleIndex = await this.loadTemplateTitleIndex(championName);
            const seenTitles = new Set<string>();

            for (const candidateAbilityName of abilityCandidates) {
                const normalizedCandidate = normalizeName(candidateAbilityName);
                const title = titleIndex[normalizedCandidate];
                if (!title || seenTitles.has(title)) {
                    continue;
                }
                seenTitles.add(title);

                const url = `https://wiki.leagueoflegends.com/en-us/${encodeURIComponent(title)}?action=raw`;
                const raw = await fetchTemplateRaw(url);
                if (!raw) {
                    continue;
                }

                const affectedByCdr = parseAffectedByCdr(raw);
                if (typeof affectedByCdr !== "boolean") {
                    continue;
                }

                this.entries[cacheKey] = {
                    affectedByCdr,
                    updatedAt: new Date().toISOString()
                };
                this.dirty = true;
                this.unresolvedKeys.delete(cacheKey);
                return affectedByCdr;
            }
        }

        this.unresolvedKeys.add(cacheKey);
        return undefined;
    }

    private async loadTemplateTitleIndex(championName: string): Promise<Record<string, string>> {
        const normalizedChampion = normalizeName(championName);
        if (!normalizedChampion) {
            return {};
        }

        const cached = this.templateTitleIndex.get(normalizedChampion);
        if (cached) {
            return cached;
        }

        const index: Record<string, string> = {};
        const prefixes = [
            `Data ${championName.trim()}/`,
            `Data_${championName.trim()}/`
        ];

        for (const prefix of Array.from(new Set(prefixes))) {
            const titles = await this.fetchTemplateTitlesByPrefix(prefix);
            titles.forEach((title) => {
                const abilityName = extractAbilityFromTemplateTitle(title);
                if (!abilityName) {
                    return;
                }
                const normalizedAbilityName = normalizeName(abilityName);
                if (!normalizedAbilityName || index[normalizedAbilityName]) {
                    return;
                }
                index[normalizedAbilityName] = title;
            });
        }

        this.templateTitleIndex.set(normalizedChampion, index);
        return index;
    }

    private async fetchTemplateTitlesByPrefix(prefix: string): Promise<string[]> {
        const titles: string[] = [];
        let apcontinue: string | undefined;

        for (let page = 0; page < 5; page += 1) {
            const params = new URLSearchParams({
                action: "query",
                format: "json",
                list: "allpages",
                apnamespace: "10",
                aplimit: "500",
                apprefix: prefix
            });
            if (apcontinue) {
                params.set("apcontinue", apcontinue);
            }

            const response = await fetch(`${WIKI_API_BASE}?${params.toString()}`, {
                headers: WIKI_REQUEST_HEADERS
            });
            if (!response.ok) {
                break;
            }

            const parsed = (await response.json()) as WikiAllPagesResponse;
            const pageTitles = parsed.query?.allpages?.map((entry) => entry.title).filter(Boolean) as string[];
            titles.push(...pageTitles);

            apcontinue = parsed.continue?.apcontinue;
            if (!apcontinue) {
                break;
            }
        }

        return titles;
    }
}
