import path from "node:path";
import { config } from "../config.js";
import { ChampionService } from "../services/champion-service.js";
import { ObservabilityService } from "../services/observability-service.js";
import { DDragonPatchService } from "../services/patch-service.js";

async function main(): Promise<void> {
    const patchService = new DDragonPatchService();
    const patchVersion = await patchService.getLatestPatch();
    const logger = new ObservabilityService();

    for (const locale of config.outputLocales) {
        const result = await new ChampionService(logger).generate({
            patchVersion,
            source: "scheduled",
            rootOutputDir: config.outputDir,
            outputDir: path.join(config.outputDir, patchVersion, locale),
            locale
        });

        if (!result.success) {
            logger.error(result.details ?? ` [champions:${locale}] Champion generation failed`);
            process.exit(1);
        }

        logger.info(`[champions:${locale}] Champion generation completed successfully.`);
    }
}

void main();
