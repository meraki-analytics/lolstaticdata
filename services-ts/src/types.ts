export type TriggerSource = "startup" | "scheduled";

export type PatchVersion = string;

export interface VersionState {
    version: string;
    lastUpdate: string;
    timestamp: number;
}

export interface GenerationContext {
    patchVersion: PatchVersion;
    source: TriggerSource;
    outputDir: string;
}

export interface GenerationResult {
    service: string;
    success: boolean;
    details?: string;
}
