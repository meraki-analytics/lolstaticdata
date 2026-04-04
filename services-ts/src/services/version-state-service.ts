import fs from "node:fs/promises";
import path from "node:path";
import { config } from "../config.js";
import type { VersionStateService } from "../contracts.js";
import type { VersionState } from "../types.js";

interface VersionStateWithHistory extends VersionState {
    history: VersionState[];
}

function toVersionState(value: unknown): VersionState | null {
    if (!value || typeof value !== "object") {
        return null;
    }

    const candidate = value as Partial<VersionState>;
    if (
        typeof candidate.version === "string" &&
        typeof candidate.lastUpdate === "string" &&
        typeof candidate.timestamp === "number"
    ) {
        return {
            version: candidate.version,
            lastUpdate: candidate.lastUpdate,
            timestamp: candidate.timestamp
        };
    }

    return null;
}

export class JsonVersionStateService implements VersionStateService {
    private get versionFilePath(): string {
        return path.join(config.outputDir, config.versionFileName);
    }

    private async loadVersionFile(): Promise<VersionStateWithHistory | null> {
        try {
            const content = await fs.readFile(this.versionFilePath, "utf8");
            const parsed = JSON.parse(content) as Record<string, unknown>;
            const current = toVersionState(parsed);
            if (!current) {
                return null;
            }

            const rawHistory = Array.isArray(parsed.history) ? parsed.history : [];
            const history = rawHistory
                .map((entry) => toVersionState(entry))
                .filter((entry): entry is VersionState => entry !== null);

            return {
                ...current,
                history
            };
        } catch {
            return null;
        }
    }

    async load(): Promise<VersionState | null> {
        const loaded = await this.loadVersionFile();
        if (!loaded) {
            return null;
        }
        return {
            version: loaded.version,
            lastUpdate: loaded.lastUpdate,
            timestamp: loaded.timestamp
        };
    }

    async save(version: string): Promise<VersionState> {
        await fs.mkdir(config.outputDir, { recursive: true });
        const existing = await this.loadVersionFile();

        const state: VersionState = {
            version,
            lastUpdate: new Date().toISOString(),
            timestamp: Math.floor(Date.now() / 1000)
        };

        const byVersion = new Map<string, VersionState>();
        for (const entry of existing?.history ?? []) {
            byVersion.set(entry.version, entry);
        }
        if (existing) {
            byVersion.set(existing.version, {
                version: existing.version,
                lastUpdate: existing.lastUpdate,
                timestamp: existing.timestamp
            });
        }
        byVersion.set(state.version, state);

        const history = Array.from(byVersion.values()).sort((a, b) => a.timestamp - b.timestamp);
        const payload: VersionStateWithHistory = {
            ...state,
            history
        };

        await fs.writeFile(this.versionFilePath, JSON.stringify(payload, null, 2), "utf8");
        return state;
    }
}
