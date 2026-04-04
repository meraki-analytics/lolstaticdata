import path from "node:path";
import { config } from "../config.js";
import { ItemService } from "../services/item-service.js";
import { DDragonPatchService } from "../services/patch-service.js";
import { ObservabilityService } from "../services/observability-service.js";

async function main(): Promise<void> {
    const patchService = new DDragonPatchService();
    const patchVersion = await patchService.getLatestPatch();
    const logger = new ObservabilityService();

    for (const locale of config.outputLocales) {
        const result = await new ItemService().generate({
            patchVersion,
            source: "scheduled",
            rootOutputDir: config.outputDir,
            outputDir: path.join(config.outputDir, patchVersion, locale),
            locale
        });

        if (!result.success) {
            logger.error(result.details ?? ` [items:${locale}] Item generation failed`);
            process.exit(1);
        }

        logger.info(`[items:${locale}] Item generation completed successfully.`);
    }
}

void main();
