import { config } from "../config.js";
import { ItemService } from "../services/item-service.js";
import { DDragonPatchService } from "../services/patch-service.js";

async function main(): Promise<void> {
    const patchService = new DDragonPatchService();
    const patchVersion = await patchService.getLatestPatch();
    const result = await new ItemService().generate({
        patchVersion,
        source: "scheduled",
        outputDir: config.outputDir
    });

    if (!result.success) {
        console.error(result.details ?? "Item generation failed");
        process.exit(1);
    } else {
        console.log("Item generation completed successfully.");
    }
}

void main();
