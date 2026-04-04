import type { AbilitySlot } from "./champion-types.js";

export const CDRAGON_BASE = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default";
export const CDRAGON_CHAMPION_SUMMARY_URL = `${CDRAGON_BASE}/v1/champion-summary.json`;
export const RAW_CDRAGON_BASE = "https://raw.communitydragon.org";
const CDRAGON_PLUGIN_PATH = "plugins/rcp-be-lol-game-data/global/default";

export function toPatchChannel(patchVersion: string): string {
    const parts = patchVersion
        .split(".")
        .map((value) => value.trim())
        .filter(Boolean);
    if (parts.length >= 2) {
        return `${parts[0]}.${parts[1]}`;
    }
    return patchVersion || "latest";
}

export function toPluginAssetUrl(assetPath: string | undefined, patchVersion: string): string {
    if (!assetPath) {
        return "";
    }
    if (assetPath.startsWith("http://") || assetPath.startsWith("https://")) {
        return assetPath;
    }

    const normalized = assetPath.replace(/\\/g, "/");
    const normalizedLower = normalized.toLowerCase();
    const pluginBase = `${RAW_CDRAGON_BASE}/${toPatchChannel(patchVersion)}/${CDRAGON_PLUGIN_PATH}`;

    if (normalizedLower.startsWith("/lol-game-data/assets/")) {
        const tail = normalizedLower.slice("/lol-game-data/assets/".length);
        return `${pluginBase}/${tail}`;
    }

    if (normalizedLower.startsWith("/")) {
        return `${pluginBase}${normalizedLower}`;
    }

    return `${pluginBase}/${normalizedLower}`;
}

function toPatchGameAssetUrl(assetPath: string, patchVersion: string): string {
    if (assetPath.startsWith("http://") || assetPath.startsWith("https://")) {
        return assetPath;
    }

    const normalized = assetPath.replace(/\\/g, "/");
    const normalizedLower = normalized.toLowerCase();
    const patchChannel = toPatchChannel(patchVersion);

    if (normalizedLower.startsWith("/lol-game-data/assets/")) {
        let tail = normalizedLower.slice("/lol-game-data/assets/".length);
        if (tail.startsWith("assets/")) {
            tail = tail.slice("assets/".length);
        }
        return `${RAW_CDRAGON_BASE}/${patchChannel}/game/assets/${tail}`;
    }

    if (normalizedLower.startsWith("/")) {
        return `${RAW_CDRAGON_BASE}/${patchChannel}${normalizedLower}`;
    }

    return `${RAW_CDRAGON_BASE}/${patchChannel}/${normalizedLower}`;
}

function buildFallbackAbilityIconUrl(championKey: string, slot: AbilitySlot, patchVersion: string): string {
    const patchChannel = toPatchChannel(patchVersion);
    const championKeyLower = championKey.toLowerCase();
    const suffix = slot === "P" ? "passive" : slot.toLowerCase();
    return `${RAW_CDRAGON_BASE}/${patchChannel}/game/assets/characters/${championKeyLower}/hud/icons2d/${championKeyLower}_${suffix}.png`;
}

export function resolveAbilityIconUrl(
    championKey: string,
    slot: AbilitySlot,
    iconPath: string | undefined,
    patchVersion: string
): string {
    if (iconPath && iconPath.trim()) {
        return toPatchGameAssetUrl(iconPath, patchVersion);
    }
    return buildFallbackAbilityIconUrl(championKey, slot, patchVersion);
}
