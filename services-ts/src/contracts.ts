import type { GenerationContext, GenerationResult, PatchVersion, VersionState } from "./types.js";

export interface GenerationService {
    readonly name: string;
    generate(context: GenerationContext): Promise<GenerationResult>;
}

export interface PatchService {
    getLatestPatch(): Promise<PatchVersion>;
}

export interface VersionStateService {
    load(): Promise<VersionState | null>;
    save(version: PatchVersion): Promise<VersionState>;
}

export interface SchedulerService {
    start(handler: () => Promise<void>): void;
    stop(): void;
}
