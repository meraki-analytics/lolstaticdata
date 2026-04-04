import fs from "node:fs/promises";
import path from "node:path";
import type { GenerationService } from "../contracts.js";
import type { GenerationContext, GenerationResult } from "../types.js";
import {
    NativeAbilityMetadataResolver,
    resolveAbilityMetadata
} from "./champion/champion-ability-meta.js";
import {
    CDRAGON_BASE,
    CDRAGON_CHAMPION_SUMMARY_URL,
    resolveAbilityIconUrl,
    toPluginAssetUrl
} from "./champion/champion-assets.js";
import { type ChampionCooldownOverrides, WikiCooldownResolver } from "./champion/champion-cdr.js";
import {
    fetchFormAbilityVariantLookup,
    resolveFormVariantOverrides,
    resolvePrimaryAbilityOverride
} from "./champion/champion-forms.js";
import { fetchJson, mapWithConcurrency } from "./champion/champion-http.js";
import {
    buildAbility,
    buildLeveling,
    buildStats,
    clampValuesToMaxRank,
    fallbackCostUnitFromResource,
    mapAdaptiveType,
    mapAttackType,
    mapResource,
    normalizeArray,
    resolveAbilitySlot,
    resolveCostUnit,
    splitAbilityVariantNames
} from "./champion/champion-mapping.js";
import {
    fetchChampionFactionIndex,
    fetchChampionMetadataIndex,
    resolveChampionFaction,
    resolveChampionMetadata
} from "./champion/champion-meta.js";
import { fetchPassiveAbilityNumbers } from "./champion/champion-passive.js";
import {
    fetchWikiSkinDataIndex,
    mapSkinChromas,
    normalizeSkinReleaseDate,
    resolveWikiSkinMap,
    skinCostToString
} from "./champion/champion-skins.js";
import type {
    AbilityGroups,
    AbilitySlot,
    CDragonChampionDetail,
    CDragonChampionSummary,
    ChampionDetailWithPassive,
    DDragonChampionFull
} from "./champion/champion-types.js";

function renameGenericLevelingAttributes(
    leveling: Array<Record<string, unknown>>,
    calculationNames: string[]
): Array<Record<string, unknown>> {
    if (leveling.length === 0 || calculationNames.length === 0) {
        return leveling;
    }

    let nameIndex = 0;
    return leveling.map((entry) => {
        const attribute = String(entry.attribute ?? "");
        if (!/^effect\d+amount$/i.test(attribute)) {
            return entry;
        }
        const nextName = calculationNames[nameIndex];
        nameIndex += 1;
        if (!nextName) {
            return entry;
        }
        return {
            ...entry,
            attribute: nextName
        };
    });
}

function buildMaxRankBySlot(
    spells: Array<{ id?: string; maxrank?: number }> | undefined
): Partial<Record<AbilitySlot, number>> {
    const maxRankBySlot: Partial<Record<AbilitySlot, number>> = {};
    (spells ?? []).forEach((spell, index) => {
        const slot = resolveAbilitySlot(spell.id, index);
        const maxRank = Number(spell.maxrank);
        if (Number.isInteger(maxRank) && maxRank > 0) {
            maxRankBySlot[slot] = maxRank;
        }
    });
    return maxRankBySlot;
}

function normalizeAbilityName(name: string): string {
    return name.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function resolveAffectedByCdr(
    overrides: ChampionCooldownOverrides,
    slot: AbilitySlot,
    variantIndex: number,
    variantName: string
): boolean {
    const byIndex = overrides.bySlotIndex[slot]?.[variantIndex];
    if (typeof byIndex === "boolean") {
        return byIndex;
    }

    const byName = overrides.bySlotName[slot]?.[normalizeAbilityName(variantName)];
    if (typeof byName === "boolean") {
        return byName;
    }

    return true;
}

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

            const [wikiSkinDataIndex, championMetadataIndex, championFactionIndex] = await Promise.all([
                fetchWikiSkinDataIndex(),
                fetchChampionMetadataIndex(),
                fetchChampionFactionIndex()
            ]);

            const abilityMetadataResolver = await NativeAbilityMetadataResolver.create();
            const wikiCooldownResolver = await WikiCooldownResolver.create(
                path.resolve(context.outputDir, "..", "__cache__", "wiki-cdr-overrides.json")
            );

            const champions = summary.filter(
                (entry) => entry.id > 0 && entry.alias && entry.alias !== "None" && Boolean(ddragon.data[entry.alias])
            );

            const details = await mapWithConcurrency<CDragonChampionSummary, ChampionDetailWithPassive>(champions, 12, async (entry) => {
                const ddragonChampion = ddragon.data[entry.alias];
                const resource = mapResource(ddragonChampion?.partype);
                const maxRankBySlot = buildMaxRankBySlot(ddragonChampion?.spells);

                const detail = await fetchJson<CDragonChampionDetail>(`${CDRAGON_BASE}/v1/champions/${entry.id}.json`);
                const [passiveNumbers, formVariants] = await Promise.all([
                    fetchPassiveAbilityNumbers(
                        entry.alias,
                        context.patchVersion,
                        resource,
                        detail.passive?.name
                    ),
                    fetchFormAbilityVariantLookup(
                        entry.alias,
                        context.patchVersion,
                        mapAdaptiveType(detail.tacticalInfo?.damageType),
                        resource,
                        maxRankBySlot
                    )
                ]);

                return {
                    summary: entry,
                    detail,
                    passiveNumbers,
                    formVariants
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
                const maxRankBySlot = buildMaxRankBySlot(ddragonChampion?.spells);
                (ddragonChampion?.spells ?? []).forEach((spell, index) => {
                    const slot = resolveAbilitySlot(spell.id, index);
                    ddragonCostTypeBySlot[slot] = spell.costType ?? "";
                });

                const spells = Array.isArray(detail.spells) ? detail.spells : [];
                const cooldownOverrides = await wikiCooldownResolver.resolveChampion(
                    [detail.name, key, item.summary.alias],
                    spells
                );
                const abilityMetadataOverrides = await abilityMetadataResolver.resolveChampion(
                    key,
                    context.patchVersion,
                    spells,
                    maxRankBySlot
                );
                const passiveMetadata = resolveAbilityMetadata(
                    abilityMetadataOverrides,
                    "P",
                    0,
                    detail.passive?.name ?? "Passive"
                );
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
                    leveling: [],
                    metadata: passiveMetadata
                });
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
                    const formVariantOverrides = resolveFormVariantOverrides(
                        spell.abilityIconPath,
                        slot,
                        variantNames.length,
                        item.formVariants
                    );
                    const primaryOverride = variantNames.length === 1
                        ? resolvePrimaryAbilityOverride(spell.abilityIconPath, slot, item.formVariants)
                        : undefined;
                    const description = spell.description ?? spell.dynamicDescription ?? "";
                    const maxRank = maxRankBySlot[slot];
                    const cooldown = normalizeArray(spell.cooldown).length > 0
                        ? clampValuesToMaxRank(normalizeArray(spell.cooldown), maxRank)
                        : clampValuesToMaxRank(normalizeArray(spell.cooldownCoefficients), maxRank);
                    const cost = normalizeArray(spell.cost).length > 0
                        ? clampValuesToMaxRank(normalizeArray(spell.cost), maxRank)
                        : clampValuesToMaxRank(normalizeArray(spell.costCoefficients), maxRank);
                    const costTypeRaw = ddragonCostTypeBySlot[slot] ?? "";
                    const costUnit = resolveCostUnit(costTypeRaw, resource);
                    const baseCostUnit = cost.length > 0
                        ? (costUnit || fallbackCostUnitFromResource(resource))
                        : "";
                    const range = clampValuesToMaxRank(normalizeArray(spell.range), maxRank);
                    const leveling = buildLeveling(spell.effectAmounts, adaptiveType, resource, maxRank);
                    const hasGenericLeveling = leveling.length > 0 && leveling.every((entry) => {
                        const attribute = String(entry.attribute ?? "");
                        return /^effect\d+amount$/i.test(attribute);
                    });
                    const renamedGenericLeveling = hasGenericLeveling && primaryOverride
                        ? renameGenericLevelingAttributes(leveling, primaryOverride.calculationNames)
                        : leveling;

                    variantNames.forEach((variantName, variantIndex) => {
                        const override = formVariantOverrides[variantIndex];
                        const fallbackOverride = override ?? primaryOverride;
                        const affectedByCdr = resolveAffectedByCdr(cooldownOverrides, slot, variantIndex, variantName);
                        const abilityMetadata = resolveAbilityMetadata(abilityMetadataOverrides, slot, variantIndex, variantName);
                        const variantIconPath = override?.iconPath ?? spell.abilityIconPath;
                        const variantCooldown = override
                            ? (override.hasCooldown ? override.cooldown : cooldown)
                            : (fallbackOverride?.hasCooldown && cooldown.length === 0 ? fallbackOverride.cooldown : cooldown);
                        const variantCost = override
                            ? (override.hasCost ? override.cost : [])
                            : (fallbackOverride?.hasCost && cost.length === 0 ? fallbackOverride.cost : cost);
                        const variantBaseCostUnit = variantCost.length > 0
                            ? (baseCostUnit || fallbackCostUnitFromResource(resource))
                            : "";
                        const variantCostUnit = override
                            ? (override.hasCost && override.cost.length > 0 ? variantBaseCostUnit : "")
                            : variantBaseCostUnit;
                        const variantRange = override
                            ? (override.hasRange ? override.range : range)
                            : (fallbackOverride?.hasRange && range.length === 0 ? fallbackOverride.range : range);
                        const variantLeveling = override
                            ? (override.hasLeveling ? override.leveling : [])
                            : (fallbackOverride?.hasLeveling && (leveling.length === 0 || hasGenericLeveling)
                                ? fallbackOverride.leveling
                                : renamedGenericLeveling);

                        abilities[slot].push(buildAbility({
                            name: variantName,
                            description,
                            iconUrl: resolveAbilityIconUrl(key, slot, variantIconPath, context.patchVersion),
                            resource,
                            adaptiveType,
                            cooldown: variantCooldown,
                            affectedByCdr,
                            cost: variantCost,
                            costUnit: variantCostUnit,
                            range: variantRange,
                            leveling: variantLeveling,
                            metadata: abilityMetadata
                        }));
                    });
                });

                const wikiSkinMap = resolveWikiSkinMap(wikiSkinDataIndex, [detail.name, key, item.summary.alias]);
                const skins = (detail.skins ?? []).map((skin) => {
                    const wikiSkin = wikiSkinMap[skin.id];
                    return {
                        name: skin.name,
                        id: skin.id,
                        isBase: Boolean(skin.isBase),
                        availability: wikiSkin?.availability ?? "AVAILABLE",
                        formatName: wikiSkin?.formatname ?? skin.name,
                        lootEligible: typeof wikiSkin?.looteligible === "boolean" ? wikiSkin.looteligible : true,
                        cost: skinCostToString(wikiSkin?.cost),
                        sale: 0,
                        distribution: wikiSkin?.distribution ?? "",
                        rarity: (skin.rarity ?? skin.skinClassification ?? "").replace(/^k/, ""),
                        chromas: mapSkinChromas(skin, wikiSkin, detail.id, context.patchVersion),
                        lore: wikiSkin?.lore ?? "",
                        release: normalizeSkinReleaseDate(wikiSkin?.release),
                        set: wikiSkin?.set ?? [],
                        splashPath: toPluginAssetUrl(skin.splashPath, context.patchVersion),
                        uncenteredSplashPath: toPluginAssetUrl(skin.uncenteredSplashPath, context.patchVersion),
                        tilePath: toPluginAssetUrl(skin.tilePath, context.patchVersion),
                        loadScreenPath: toPluginAssetUrl(skin.loadScreenPath, context.patchVersion),
                        loadScreenVintagePath: toPluginAssetUrl(skin.loadScreenVintagePath, context.patchVersion),
                        newEffects: Boolean(wikiSkin?.neweffects),
                        newAnimations: Boolean(wikiSkin?.newanimations),
                        newRecall: Boolean(wikiSkin?.newrecall),
                        newVoice: Boolean(wikiSkin?.newvoice),
                        newQuotes: Boolean(wikiSkin?.newquotes),
                        voiceActor: wikiSkin?.voiceactor ?? [],
                        splashArtist: wikiSkin?.splashartist ?? []
                    };
                });

                const attackType = mapAttackType(detail.tacticalInfo?.attackType);
                const roles = (detail.roles ?? item.summary.roles ?? []).map((role) => role.toUpperCase());
                const icon = toPluginAssetUrl(detail.squarePortraitPath ?? item.summary.squarePortraitPath, context.patchVersion);
                const championMetadata = resolveChampionMetadata(championMetadataIndex, [
                    detail.name,
                    key,
                    item.summary.alias,
                    item.summary.name
                ]);
                const faction = resolveChampionFaction(championFactionIndex, [
                    key,
                    detail.name,
                    item.summary.alias,
                    item.summary.name,
                    detail.title
                ]);

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
                    releaseDate: championMetadata?.releaseDate ?? "",
                    releasePatch: championMetadata?.releasePatch ?? "",
                    patchLastChanged: championMetadata?.patchLastChanged ?? context.patchVersion,
                    price: {
                        blueEssence: championMetadata?.blueEssence ?? 0,
                        rp: championMetadata?.rp ?? 0,
                        saleRp: 0
                    },
                    lore: detail.shortBio ?? "",
                    faction,
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

            await abilityMetadataResolver.save();
            await wikiCooldownResolver.save();

            const unresolvedCooldownKeys = wikiCooldownResolver.getUnresolvedKeys();
            const unresolvedReportPath = path.resolve(context.outputDir, "..", "__cache__", "wiki-cdr-unresolved.json");
            if (unresolvedCooldownKeys.length > 0) {
                await fs.mkdir(path.dirname(unresolvedReportPath), { recursive: true });
                await fs.writeFile(unresolvedReportPath, JSON.stringify({
                    version: 1,
                    generatedAt: new Date().toISOString(),
                    patchVersion: context.patchVersion,
                    unresolvedKeys: unresolvedCooldownKeys
                }, null, 2), "utf8");
            } else {
                await fs.rm(unresolvedReportPath, { force: true });
            }

            return {
                service: this.name,
                success: true,
                details: `Champion generation completed with native CDragon pipeline (${championIndex.length} champions, ${unresolvedCooldownKeys.length} unresolved wiki cooldown mappings)`
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
