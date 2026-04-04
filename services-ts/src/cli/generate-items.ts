import path from "node:path";
import { config } from "../config.js";
import { ItemService } from "../services/item-service.js";
import { DDragonPatchService } from "../services/patch-service.js";

async function main(): Promise<void> {
    const patchService = new DDragonPatchService();
    const patchVersion = await patchService.getLatestPatch();

    for (const locale of config.outputLocales) {
        const result = await new ItemService().generate({
            patchVersion,
            source: "scheduled",
            rootOutputDir: config.outputDir,
            outputDir: path.join(config.outputDir, patchVersion, locale),
            locale
        });

        if (!result.success) {
            console.error(result.details ?? `Item generation failed for ${locale}`);
            process.exit(1);
        }

        console.log(`Item generation completed successfully for ${locale}.`);
    }
}

void main();
