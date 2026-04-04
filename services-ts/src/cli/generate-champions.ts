import { config } from "../config.js";
import { ChampionService } from "../services/champion-service.js";
import { DDragonPatchService } from "../services/patch-service.js";

async function main(): Promise<void> {
    const patchService = new DDragonPatchService();
    const patchVersion = await patchService.getLatestPatch();
    const result = await new ChampionService().generate({
        patchVersion,
        source: "scheduled",
        outputDir: config.outputDir
    });

    if (!result.success) {
        console.error(result.details ?? "Champion generation failed");
        process.exit(1);
    } else {
        console.log("Champion generation completed successfully.");
    }
}

void main();
