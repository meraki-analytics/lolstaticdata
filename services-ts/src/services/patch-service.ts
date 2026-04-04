import { config } from "../config.js";
import type { PatchService } from "../contracts.js";

function comparePatchVersions(a: string, b: string): number {
    const av = a.split(".").map((x) => Number.parseInt(x, 10));
    const bv = b.split(".").map((x) => Number.parseInt(x, 10));
    const maxLen = Math.max(av.length, bv.length);

    for (let i = 0; i < maxLen; i += 1) {
        const left = av[i] ?? 0;
        const right = bv[i] ?? 0;
        if (left > right) {
            return 1;
        }
        if (left < right) {
            return -1;
        }
    }

    return 0;
}

export class DDragonPatchService implements PatchService {
    async getLatestPatch(): Promise<string> {
        const response = await fetch(config.patchEndpoint);
        if (!response.ok) {
            throw new Error(`Patch endpoint request failed: ${response.status}`);
        }

        const payload = (await response.json()) as unknown;
        if (!Array.isArray(payload)) {
            throw new Error("Patch endpoint returned unexpected payload");
        }

        const stableVersions = payload
            .filter((v): v is string => typeof v === "string")
            .filter((v) => !v.includes("_"));

        if (stableVersions.length === 0) {
            throw new Error("No stable patch versions found");
        }

        stableVersions.sort(comparePatchVersions);
        return stableVersions[stableVersions.length - 1];
    }
}
