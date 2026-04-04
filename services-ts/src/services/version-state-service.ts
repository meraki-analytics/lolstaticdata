import fs from "node:fs/promises";
import path from "node:path";
import { config } from "../config.js";
import type { VersionStateService } from "../contracts.js";
import type { VersionState } from "../types.js";

export class JsonVersionStateService implements VersionStateService {
    private get versionFilePath(): string {
        return path.join(config.outputDir, config.versionFileName);
    }

    async load(): Promise<VersionState | null> {
        try {
            const content = await fs.readFile(this.versionFilePath, "utf8");
            const parsed = JSON.parse(content) as Partial<VersionState>;
            if (
                typeof parsed.version === "string" &&
                typeof parsed.lastUpdate === "string" &&
                typeof parsed.timestamp === "number"
            ) {
                return {
                    version: parsed.version,
                    lastUpdate: parsed.lastUpdate,
                    timestamp: parsed.timestamp
                };
            }
            return null;
        } catch {
            return null;
        }
    }

    async save(version: string): Promise<VersionState> {
        await fs.mkdir(config.outputDir, { recursive: true });
        const state: VersionState = {
            version,
            lastUpdate: new Date().toISOString(),
            timestamp: Math.floor(Date.now() / 1000)
        };
        await fs.writeFile(this.versionFilePath, JSON.stringify(state, null, 2), "utf8");
        return state;
    }
}
