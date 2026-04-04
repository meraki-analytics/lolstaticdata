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
import { localizeAttackType, localizeDamageType, localizeResource } from "./champion/champion-i18n.js";
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

function dedupe(values: string[]): string[] {
    const seen = new Set<string>();
    const result: string[] = [];
    for (const value of values) {
        if (!value || seen.has(value)) {
            continue;
        }
        seen.add(value);
        result.push(value);
    }
    return result;
}

const DETAILED_ROLE_PARENT: Record<string, string> = {
    JUGGERNAUT: "FIGHTER",
    DIVER: "FIGHTER",
    SKIRMISHER: "FIGHTER",
    BURST: "MAGE",
    BATTLEMAGE: "MAGE",
    ARTILLERY: "MAGE",
    VANGUARD: "TANK",
    WARDEN: "TANK",
    ENCHANTER: "SUPPORT",
    CATCHER: "SUPPORT"
};

function resolveChampionRoles(
    metadataPrimaryType: string | undefined,
    metadataSecondaryType: string | undefined,
    ddragonTags: string[] | undefined,
    metadataRoles: string[] | undefined,
    fallbackRoles: string[] | undefined
): string[] {
    const metadataTypes = [metadataPrimaryType, metadataSecondaryType]
        .map((value) => String(value ?? "").trim().toUpperCase())
        .filter(Boolean);
    const ddragonBaseRoles = (ddragonTags ?? []).map((tag) => tag.trim().toUpperCase()).filter(Boolean);
    const baseRoles = dedupe([...metadataTypes, ...ddragonBaseRoles]);
    const detailedRoles = dedupe((metadataRoles ?? []).map((role) => role.trim().toUpperCase()).filter(Boolean));
    const fallback = dedupe((fallbackRoles ?? []).map((role) => role.trim().toUpperCase()).filter(Boolean));

    if (baseRoles.length === 0 && detailedRoles.length === 0) {
        return fallback;
    }

    const merged = [...baseRoles];
    for (const detailed of detailedRoles) {
        const parent = DETAILED_ROLE_PARENT[detailed];
        if (parent && merged.includes(parent)) {
            const parentIndex = merged.indexOf(parent);
            if (!merged.includes(detailed)) {
                merged.splice(parentIndex + 1, 0, detailed);
            }
            continue;
        }

        if (!merged.includes(detailed)) {
            merged.push(detailed);
        }
    }

    return dedupe(merged);
}

function resolveChampionPositions(
    metadataPositions: string[] | undefined
): string[] {
    return dedupe((metadataPositions ?? []).map((position) => position.trim().toUpperCase()).filter(Boolean));
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

async function fetchDDragonChampionFull(
    patchVersion: string,
    locale: string
): Promise<DDragonChampionFull> {
    const preferredLocale = locale || "en_US";
    const preferredUrl = `https://ddragon.leagueoflegends.com/cdn/${patchVersion}/data/${preferredLocale}/championFull.json`;
    try {
        return await fetchJson<DDragonChampionFull>(preferredUrl);
    } catch (error) {
        if (preferredLocale === "en_US") {
            throw error;
        }
        const fallbackUrl = `https://ddragon.leagueoflegends.com/cdn/${patchVersion}/data/en_US/championFull.json`;
        return await fetchJson<DDragonChampionFull>(fallbackUrl);
    }
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
                fetchDDragonChampionFull(context.patchVersion, context.locale)
            ]);

            const [wikiSkinDataIndex, championMetadataIndex, championFactionIndex] = await Promise.all([
                fetchWikiSkinDataIndex(),
                fetchChampionMetadataIndex(),
                fetchChampionFactionIndex()
            ]);

            const abilityMetadataResolver = await NativeAbilityMetadataResolver.create();
            const wikiCooldownResolver = await WikiCooldownResolver.create(
                path.resolve(context.rootOutputDir, "__cache__", "wiki-cdr-overrides.json")
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
                const localizedChampionName = ddragonChampion?.name?.trim() || detail.name;
                const localizedChampionTitle = ddragonChampion?.title?.trim() || detail.title;
                const localizedLore = (ddragonChampion?.lore ?? ddragonChampion?.blurb ?? detail.shortBio ?? "").trim();
                const localizedPassiveName = ddragonChampion?.passive?.name?.trim() || detail.passive?.name || "Passive";
                const localizedPassiveDescription =
                    (ddragonChampion?.passive?.description ?? detail.passive?.description ?? "").trim();

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
                    name: localizedPassiveName,
                    description: localizedPassiveDescription,
                    iconUrl: resolveAbilityIconUrl(key, "P", detail.passive?.abilityIconPath, context.patchVersion),
                    resource,
                    adaptiveType,
                    cooldown: item.passiveNumbers.cooldown,
                    affectedByCdr: false,
                    cost: item.passiveNumbers.cost,
                    costUnit: item.passiveNumbers.costUnit,
                    range: [],
                    leveling: [],
                    locale: context.locale,
                    metadata: passiveMetadata
                });
                const abilities: AbilityGroups = {
                    P: [passiveAbility],
                    Q: [],
                    W: [],
                    E: [],
                    R: []
                };

                const ddragonSkinNamesById = new Map<number, string>();
                for (const ddragonSkin of ddragonChampion?.skins ?? []) {
                    const id = Number(ddragonSkin.num);
                    const name = ddragonSkin.name?.trim();
                    if (Number.isInteger(id) && id >= 0 && name) {
                        ddragonSkinNamesById.set(id, name);
                    }
                }

                spells.forEach((spell, index) => {
                    const ddragonSpell = ddragonChampion?.spells?.[index];
                    const slot = resolveAbilitySlot(spell.spellKey, index);
                    const cdragonVariantNames = splitAbilityVariantNames(spell.name, slot);
                    const localizedSpellName = ddragonSpell?.name?.trim();
                    const variantNames = localizedSpellName
                        ? (cdragonVariantNames.length > 1
                            ? [localizedSpellName, ...cdragonVariantNames.slice(1)]
                            : splitAbilityVariantNames(localizedSpellName, slot))
                        : cdragonVariantNames;
                    const formVariantOverrides = resolveFormVariantOverrides(
                        spell.abilityIconPath,
                        slot,
                        variantNames.length,
                        item.formVariants
                    );
                    const primaryOverride = variantNames.length === 1
                        ? resolvePrimaryAbilityOverride(spell.abilityIconPath, slot, item.formVariants)
                        : undefined;
                    const description =
                        (ddragonSpell?.description ?? ddragonSpell?.tooltip ?? spell.description ?? spell.dynamicDescription ?? "").trim();
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
                            locale: context.locale,
                            metadata: abilityMetadata
                        }));
                    });
                });

                const wikiSkinMap = resolveWikiSkinMap(wikiSkinDataIndex, [detail.name, key, item.summary.alias]);
                const skins = (detail.skins ?? []).map((skin) => {
                    const localizedSkinName = ddragonSkinNamesById.get(skin.id) ?? skin.name;
                    const wikiSkin = wikiSkinMap[skin.id];
                    return {
                        name: localizedSkinName,
                        id: skin.id,
                        isBase: Boolean(skin.isBase),
                        availability: wikiSkin?.availability ?? "AVAILABLE",
                        formatName: wikiSkin?.formatname ?? localizedSkinName,
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
                const localizedAttackType = localizeAttackType(attackType, context.locale);
                const localizedResource = localizeResource(resource, context.locale);
                const localizedAdaptiveType = localizeDamageType(adaptiveType, context.locale);
                const icon = toPluginAssetUrl(detail.squarePortraitPath ?? item.summary.squarePortraitPath, context.patchVersion);
                const championMetadata = resolveChampionMetadata(championMetadataIndex, [
                    detail.name,
                    key,
                    item.summary.alias,
                    item.summary.name
                ]);
                const positions = resolveChampionPositions(championMetadata?.positions);
                const roles = resolveChampionRoles(
                    championMetadata?.primaryType,
                    championMetadata?.secondaryType,
                    ddragonChampion?.tags,
                    championMetadata?.roles,
                    detail.roles ?? item.summary.roles
                );
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
                    name: localizedChampionName,
                    title: localizedChampionTitle,
                    fullName: `${localizedChampionName}, ${localizedChampionTitle}`,
                    icon,
                    resource: localizedResource,
                    attackType: localizedAttackType,
                    adaptiveType: localizedAdaptiveType,
                    stats: buildStats(ddragonChampion),
                    positions,
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
                    lore: localizedLore,
                    faction,
                    skins
                };

                championPayloads[key] = payload;
                championIndex.push({
                    id: detail.id,
                    key,
                    name: localizedChampionName || item.summary.name || key,
                    slug: key.toLowerCase(),
                    iconUrl: icon,
                    attackType: localizedAttackType,
                    positions,
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
                locale: context.locale,
                generatedAt: new Date().toISOString(),
                totalChampions: championIndex.length,
                champions: championIndex
            }, null, 2), "utf8");

            await abilityMetadataResolver.save();
            await wikiCooldownResolver.save();

            const unresolvedCooldownKeys = wikiCooldownResolver.getUnresolvedKeys();
            const unresolvedReportPath = path.resolve(context.rootOutputDir, "__cache__", "wiki-cdr-unresolved.json");
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
