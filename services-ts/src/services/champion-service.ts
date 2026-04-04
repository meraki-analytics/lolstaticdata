import fs from "node:fs/promises";
import path from "node:path";
import type { GenerationService } from "../contracts.js";
import type { GenerationContext, GenerationResult } from "../types.js";
import {
    CDRAGON_BASE,
    CDRAGON_CHAMPION_SUMMARY_URL,
    resolveAbilityIconUrl,
    toPluginAssetUrl
} from "./champion/champion-assets.js";
import { fetchJson, mapWithConcurrency } from "./champion/champion-http.js";
import {
    buildAbility,
    buildLeveling,
    buildStats,
    mapAdaptiveType,
    mapAttackType,
    mapResource,
    normalizeArray,
    resolveAbilitySlot,
    resolveCostUnit,
    splitAbilityVariantNames
} from "./champion/champion-mapping.js";
import { fetchPassiveAbilityNumbers } from "./champion/champion-passive.js";
import type {
    AbilityGroups,
    AbilitySlot,
    CDragonChampionDetail,
    CDragonChampionSummary,
    ChampionDetailWithPassive,
    DDragonChampionFull
} from "./champion/champion-types.js";

export class ChampionService implements GenerationService {
    readonly name = "ChampionService";

    async generate(context: GenerationContext): Promise<GenerationResult> {
        try {
            const championsDir = path.join(context.outputDir, "champions");
            await fs.mkdir(championsDir, { recursive: true });

            const existingChampionFiles = await fs.readdir(championsDir);
            await Promise.all(
                existingChampionFiles
                    .filter((name) => name.endsWith(".json"))
                    .map((name) => fs.unlink(path.join(championsDir, name)))
            );

            const [summary, ddragon] = await Promise.all([
                fetchJson<CDragonChampionSummary[]>(CDRAGON_CHAMPION_SUMMARY_URL),
                fetchJson<DDragonChampionFull>(`https://ddragon.leagueoflegends.com/cdn/${context.patchVersion}/data/en_US/championFull.json`)
            ]);

            const champions = summary.filter(
                (entry) => entry.id > 0 && entry.alias && entry.alias !== "None" && Boolean(ddragon.data[entry.alias])
            );

            const details = await mapWithConcurrency<CDragonChampionSummary, ChampionDetailWithPassive>(champions, 12, async (entry) => {
                const ddragonChampion = ddragon.data[entry.alias];
                const resource = mapResource(ddragonChampion?.partype);

                const detail = await fetchJson<CDragonChampionDetail>(`${CDRAGON_BASE}/v1/champions/${entry.id}.json`);
                const passiveNumbers = await fetchPassiveAbilityNumbers(
                    entry.alias,
                    context.patchVersion,
                    resource,
                    detail.passive?.name
                );

                return {
                    summary: entry,
                    detail,
                    passiveNumbers
                };
            });

            const championPayloads: Record<string, Record<string, unknown>> = {};
            const championIndex: Array<Record<string, unknown>> = [];

            for (const item of details) {
                const detail = item.detail;
                const key = detail.alias || item.summary.alias;
                const ddragonChampion = ddragon.data[key];

                const resource = mapResource(ddragonChampion?.partype);
                const adaptiveType = mapAdaptiveType(detail.tacticalInfo?.damageType);
                const ddragonCostTypeBySlot: Partial<Record<AbilitySlot, string>> = {};
                (ddragonChampion?.spells ?? []).forEach((spell, index) => {
                    const slot = resolveAbilitySlot(spell.id, index);
                    ddragonCostTypeBySlot[slot] = spell.costType ?? "";
                });

                const passiveAbility = buildAbility({
                    name: detail.passive?.name ?? "Passive",
                    description: detail.passive?.description ?? "",
                    iconUrl: resolveAbilityIconUrl(key, "P", detail.passive?.abilityIconPath, context.patchVersion),
                    resource,
                    adaptiveType,
                    cooldown: item.passiveNumbers.cooldown,
                    affectedByCdr: false,
                    cost: item.passiveNumbers.cost,
                    costUnit: item.passiveNumbers.costUnit,
                    range: [],
                    leveling: []
                });

                const spells = Array.isArray(detail.spells) ? detail.spells : [];
                const abilities: AbilityGroups = {
                    P: [passiveAbility],
                    Q: [],
                    W: [],
                    E: [],
                    R: []
                };

                spells.forEach((spell, index) => {
                    const slot = resolveAbilitySlot(spell.spellKey, index);
                    const variantNames = splitAbilityVariantNames(spell.name, slot);
                    const description = spell.description ?? spell.dynamicDescription ?? "";
                    const cooldown = normalizeArray(spell.cooldown).length > 0
                        ? normalizeArray(spell.cooldown)
                        : normalizeArray(spell.cooldownCoefficients);
                    const cost = normalizeArray(spell.cost).length > 0
                        ? normalizeArray(spell.cost)
                        : normalizeArray(spell.costCoefficients);
                    const costTypeRaw = ddragonCostTypeBySlot[slot] ?? "";
                    const costUnit = resolveCostUnit(costTypeRaw, resource);
                    const range = normalizeArray(spell.range);
                    const leveling = buildLeveling(spell.effectAmounts);

                    for (const variantName of variantNames) {
                        abilities[slot].push(buildAbility({
                            name: variantName,
                            description,
                            iconUrl: resolveAbilityIconUrl(key, slot, spell.abilityIconPath, context.patchVersion),
                            resource,
                            adaptiveType,
                            cooldown,
                            affectedByCdr: true,
                            cost,
                            costUnit,
                            range,
                            leveling
                        }));
                    }
                });

                const skins = (detail.skins ?? []).map((skin) => ({
                    name: skin.name,
                    id: skin.id,
                    isBase: Boolean(skin.isBase),
                    availability: "AVAILABLE",
                    formatName: skin.name,
                    lootEligible: true,
                    cost: "",
                    sale: 0,
                    distribution: "",
                    rarity: skin.skinClassification ?? "",
                    chromas: [],
                    lore: "",
                    release: 0,
                    set: [],
                    splashPath: toPluginAssetUrl(skin.splashPath, context.patchVersion),
                    uncenteredSplashPath: toPluginAssetUrl(skin.uncenteredSplashPath, context.patchVersion),
                    tilePath: toPluginAssetUrl(skin.tilePath, context.patchVersion),
                    loadScreenPath: toPluginAssetUrl(skin.loadScreenPath, context.patchVersion),
                    loadScreenVintagePath: "",
                    newEffects: false,
                    newAnimations: false,
                    newRecall: false,
                    newVoice: false,
                    newQuotes: false,
                    voiceActor: [],
                    splashArtist: []
                }));

                const attackType = mapAttackType(detail.tacticalInfo?.attackType);
                const roles = (detail.roles ?? item.summary.roles ?? []).map((role) => role.toUpperCase());
                const icon = toPluginAssetUrl(detail.squarePortraitPath ?? item.summary.squarePortraitPath, context.patchVersion);

                const payload: Record<string, unknown> = {
                    id: detail.id,
                    key,
                    name: detail.name,
                    title: detail.title,
                    fullName: `${detail.name}, ${detail.title}`,
                    icon,
                    resource,
                    attackType,
                    adaptiveType,
                    stats: buildStats(ddragonChampion),
                    positions: [],
                    roles,
                    attributeRatings: {
                        damage: detail.playstyleInfo?.damage ?? 0,
                        toughness: detail.playstyleInfo?.durability ?? 0,
                        control: detail.playstyleInfo?.crowdControl ?? 0,
                        mobility: detail.playstyleInfo?.mobility ?? 0,
                        utility: detail.playstyleInfo?.utility ?? 0,
                        abilityReliance: 0,
                        difficulty: detail.tacticalInfo?.difficulty ?? 0
                    },
                    abilities: {
                        P: abilities.P,
                        Q: abilities.Q,
                        W: abilities.W,
                        E: abilities.E,
                        R: abilities.R
                    },
                    releaseDate: "",
                    releasePatch: "",
                    patchLastChanged: context.patchVersion,
                    price: {
                        blueEssence: 0,
                        rp: 0,
                        saleRp: 0
                    },
                    lore: detail.shortBio ?? "",
                    faction: "",
                    skins
                };

                championPayloads[key] = payload;
                championIndex.push({
                    id: detail.id,
                    key,
                    name: detail.name || item.summary.name || key,
                    slug: key.toLowerCase(),
                    iconUrl: icon,
                    attackType,
                    roles
                });

                const filePath = path.join(championsDir, `${key}.json`);
                await fs.writeFile(filePath, JSON.stringify(payload, null, 2), "utf8");
            }

            const aggregatePath = path.join(context.outputDir, "champions.json");
            await fs.writeFile(aggregatePath, JSON.stringify(championPayloads, null, 2), "utf8");

            championIndex.sort((a, b) => Number(a.id) - Number(b.id));
            const indexPath = path.join(context.outputDir, "champion-index.json");
            await fs.writeFile(indexPath, JSON.stringify({
                version: context.patchVersion,
                generatedAt: new Date().toISOString(),
                totalChampions: championIndex.length,
                champions: championIndex
            }, null, 2), "utf8");

            return {
                service: this.name,
                success: true,
                details: `Champion generation completed with native CDragon pipeline (${championIndex.length} champions)`
            };
        } catch (error) {
            const msg = error instanceof Error ? error.message : String(error);
            return {
                service: this.name,
                success: false,
                details: `Champion generation failed: ${msg}`
            };
        }
    }
}
