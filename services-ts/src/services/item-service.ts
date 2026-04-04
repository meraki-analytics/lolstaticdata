import fs from "node:fs/promises";
import path from "node:path";
import { config } from "../config.js";
import type { GenerationService } from "../contracts.js";
import type { GenerationContext, GenerationResult } from "../types.js";
import { runCommand } from "./shared.js";

export class ItemService implements GenerationService {
    readonly name = "ItemService";

    async generate(context: GenerationContext): Promise<GenerationResult> {
        const cwd = config.repoRoot;
        try {
            await runCommand(config.pythonCommand, ["-m", "lolstaticdata.items"], cwd);

            const legacyOutputDir = path.join(config.repoRoot, "srv");
            const legacyItemsDir = path.join(legacyOutputDir, "items");
            const legacyItemsFile = path.join(legacyOutputDir, "items.json");

            const targetItemsDir = path.join(context.outputDir, "items");
            await fs.mkdir(targetItemsDir, { recursive: true });

            const existingTargetEntries = await fs.readdir(targetItemsDir);
            await Promise.all(
                existingTargetEntries
                    .filter((name) => name.endsWith(".json"))
                    .map((name) => fs.unlink(path.join(targetItemsDir, name)))
            );

            const generatedItemFiles = await fs.readdir(legacyItemsDir);
            await Promise.all(
                generatedItemFiles
                    .filter((name) => name.endsWith(".json"))
                    .map((name) => fs.copyFile(path.join(legacyItemsDir, name), path.join(targetItemsDir, name)))
            );

            await fs.mkdir(context.outputDir, { recursive: true });
            await fs.copyFile(legacyItemsFile, path.join(context.outputDir, "items.json"));

            if (path.resolve(context.outputDir) !== path.resolve(legacyOutputDir)) {
                await fs.rm(legacyItemsDir, { recursive: true, force: true });
                await fs.rm(legacyItemsFile, { force: true });
            }

            return {
                service: this.name,
                success: true,
                details: `Item generation completed via legacy adapter (${context.locale})`
            };
        } catch (error) {
            const msg = error instanceof Error ? error.message : String(error);
            return {
                service: this.name,
                success: false,
                details: `Item generation failed: ${msg}`
            };
        }
    }
}
