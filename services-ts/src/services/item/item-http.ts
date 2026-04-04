import type { DDragonItemPayload, DDragonMapPayload } from "./item-types.js";

export async function fetchJson<T>(url: string): Promise<T> {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Request failed (${response.status}) for ${url}`);
    }
    return (await response.json()) as T;
}

export async function fetchItemPayload(patchVersion: string, locale: string): Promise<DDragonItemPayload> {
    const url = `https://ddragon.leagueoflegends.com/cdn/${patchVersion}/data/${locale}/item.json`;
    return await fetchJson<DDragonItemPayload>(url);
}

export async function fetchMapPayload(patchVersion: string, locale: string): Promise<DDragonMapPayload> {
    const url = `https://ddragon.leagueoflegends.com/cdn/${patchVersion}/data/${locale}/map.json`;
    return await fetchJson<DDragonMapPayload>(url);
}
