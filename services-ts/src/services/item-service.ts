import fs from "node:fs/promises";
import path from "node:path";
import type { GenerationService } from "../contracts.js";
import type { GenerationContext, GenerationResult } from "../types.js";
import { fetchItemPayload, fetchMapPayload } from "./item/item-http.js";
import { buildMapNameIndex, buildWrappedItem } from "./item/item-mapping.js";
import type { WrappedItem } from "./item/item-types.js";
import { ObservabilityService } from "./observability-service.js";

function toSlug(value: string): string {
    return value
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
}

export class ItemService implements GenerationService {
    readonly name = "ItemService";

    constructor(private readonly logger: ObservabilityService = new ObservabilityService()) { }

    async generate(context: GenerationContext): Promise<GenerationResult> {
        try {
            this.logger.info(`[items:${context.locale}] Starting DDragon item generation for patch ${context.patchVersion}.`);

            const targetItemsDir = path.join(context.outputDir, "items");
            await fs.mkdir(targetItemsDir, { recursive: true });

            const existingTargetEntries = await fs.readdir(targetItemsDir);
            await Promise.all(
                existingTargetEntries
                    .filter((name) => name.endsWith(".json"))
                    .map((name) => fs.unlink(path.join(targetItemsDir, name)))
            );

            const [payload, mapPayload] = await Promise.all([
                fetchItemPayload(context.patchVersion, context.locale),
                fetchMapPayload(context.patchVersion, context.locale)
            ]);
            const mapNames = buildMapNameIndex(mapPayload);
            const allItems = Object.entries(payload.data)
                .map(([id, item]) => ({ id: Number(id), item }))
                .filter(({ id }) => Number.isInteger(id));
            const inStoreItems = allItems.filter(({ item }) => item.inStore !== false);

            this.logger.info(
                `[items:${context.locale}] Filtered to ${inStoreItems.length}/${allItems.length} items (inStore != false).`
            );

            const wrapped: Record<string, WrappedItem> = {};
            const itemIndex: Array<Record<string, unknown>> = [];
            let written = 0;
            const progressStep = 50;

            for (const { id, item } of inStoreItems) {
                const mappedItem: WrappedItem = buildWrappedItem(context.patchVersion, id, item, mapNames);

                wrapped[String(id)] = mappedItem;
                itemIndex.push({
                    id,
                    key: String(id),
                    name: mappedItem.name,
                    slug: toSlug(mappedItem.name || String(id)),
                    iconUrl: mappedItem.icon.url,
                    totalPrice: mappedItem.gold.total,
                    purchasable: mappedItem.availability.purchasable,
                    tags: mappedItem.tags,
                    availableOn: mappedItem.availableOn
                });

                const filePath = path.join(targetItemsDir, `${id}.json`);
                await fs.writeFile(filePath, JSON.stringify(mappedItem, null, 2), "utf8");

                written += 1;
                if (written % progressStep === 0 || written === inStoreItems.length) {
                    this.logger.info(`[items:${context.locale}] Wrote item payloads ${written}/${inStoreItems.length}.`);
                }
            }

            const sorted = Object.fromEntries(
                Object.entries(wrapped).sort((a, b) => Number(a[0]) - Number(b[0]))
            );
            await fs.writeFile(path.join(context.outputDir, "items.json"), JSON.stringify(sorted, null, 2), "utf8");

            itemIndex.sort((a, b) => Number(a.id) - Number(b.id));
            await fs.writeFile(path.join(context.outputDir, "item-index.json"), JSON.stringify({
                version: context.patchVersion,
                locale: context.locale,
                generatedAt: new Date().toISOString(),
                totalItems: itemIndex.length,
                items: itemIndex
            }, null, 2), "utf8");

            const mapCoverage = new Set<string>();
            Object.values(sorted).forEach((item) => {
                item.availableOn.forEach((mode) => mapCoverage.add(mode));
            });

            return {
                service: this.name,
                success: true,
                details: `Item generation completed via DDragon wrapper (${context.locale}, ${inStoreItems.length} items, maps: ${Array.from(mapCoverage).sort().join(", ")})`
            };
        } catch (error) {
            const msg = error instanceof Error ? error.message : String(error);
            this.logger.error(`[items:${context.locale}] Generation failed: ${msg}`);
            return {
                service: this.name,
                success: false,
                details: `Item generation failed: ${msg}`
            };
        }
    }
}
