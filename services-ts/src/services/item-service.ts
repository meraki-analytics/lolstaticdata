import { config } from "../config.js";
import type { GenerationService } from "../contracts.js";
import type { GenerationContext, GenerationResult } from "../types.js";
import { runCommand } from "./shared.js";



export class ItemService implements GenerationService {
    readonly name = "ItemService";

    async generate(_context: GenerationContext): Promise<GenerationResult> {
        const cwd = config.repoRoot;
        try {
            await runCommand(config.pythonCommand, ["-m", "lolstaticdata.items"], cwd);
            return {
                service: this.name,
                success: true,
                details: "Item generation completed via legacy command adapter"
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
