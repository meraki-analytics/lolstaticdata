import { config } from "../config.js";
import type { GenerationService } from "../contracts.js";
import type { GenerationContext, GenerationResult } from "../types.js";
import { runCommand } from "./shared.js";


export class ChampionService implements GenerationService {
    readonly name = "ChampionService";

    async generate(_context: GenerationContext): Promise<GenerationResult> {
        const cwd = config.repoRoot;
        try {
            await runCommand(config.pythonCommand, ["-m", "lolstaticdata.champions"], cwd);
            return {
                service: this.name,
                success: true,
                details: "Champion generation completed via legacy command adapter"
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
