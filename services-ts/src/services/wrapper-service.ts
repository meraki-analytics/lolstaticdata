import fs from "node:fs/promises";
import path from "node:path";
import { config } from "../config.js";
import type { GenerationService, PatchService, SchedulerService, VersionStateService } from "../contracts.js";
import type { TriggerSource } from "../types.js";
import { LockService } from "./lock-service.js";
import { ObservabilityService } from "./observability-service.js";

export class WrapperService {
    constructor(
        private readonly patchService: PatchService,
        private readonly versionStateService: VersionStateService,
        private readonly generationServices: GenerationService[],
        private readonly schedulerService: SchedulerService,
        private readonly lockService: LockService,
        private readonly logger: ObservabilityService
    ) { }

    async start(): Promise<void> {
        await this.runStartupCycle();
        this.schedulerService.start(async () => {
            await this.runScheduledCycle();
        });
        this.logger.info("WrapperService started: startup done, scheduler armed.");
    }

    stop(): void {
        this.schedulerService.stop();
        this.logger.info("WrapperService stopped.");
    }

    async runScheduledCycle(): Promise<void> {
        await this.lockService.runExclusive("scheduled-cycle", async () => {
            const latest = await this.patchService.getLatestPatch();
            const current = await this.versionStateService.load();

            if (current && current.version === latest) {
                this.logger.info(`No update required. Current patch ${current.version} is up to date.`);
                return;
            }

            this.logger.info(`Patch change detected (${current?.version ?? "none"} -> ${latest}). Triggering full generation.`);
            await this.generateAndCommit(latest, "scheduled");
        });
    }

    private async runStartupCycle(): Promise<void> {
        await this.lockService.runExclusive("startup-cycle", async () => {
            const latest = await this.patchService.getLatestPatch();
            this.logger.info(`Startup bootstrap generation for patch ${latest}.`);
            await this.generateAndCommit(latest, "startup");
        });
    }

    private async cleanupLegacyRootArtifacts(): Promise<void> {
        const legacyPaths = [
            path.join(config.outputDir, "champions"),
            path.join(config.outputDir, "champions.json"),
            path.join(config.outputDir, "champion-index.json"),
            path.join(config.outputDir, "items"),
            path.join(config.outputDir, "items.json")
        ];

        await Promise.all(
            legacyPaths.map((legacyPath) => fs.rm(legacyPath, { recursive: true, force: true }))
        );
    }

    private async generateAndCommit(latestPatch: string, source: TriggerSource): Promise<void> {
        await this.cleanupLegacyRootArtifacts();

        for (const locale of config.outputLocales) {
            const context = {
                patchVersion: latestPatch,
                source,
                rootOutputDir: config.outputDir,
                outputDir: path.join(config.outputDir, latestPatch, locale),
                locale
            };

            this.logger.info(`Starting generation for locale ${locale} at ${context.outputDir}.`);

            const generationResults = await Promise.all(this.generationServices.map(async (service) => {
                this.logger.info(`Starting generation for ${service.name} (${locale})...`);
                return await service.generate(context);
            }));

            generationResults.forEach(result => {
                if (result.success) {
                    this.logger.info(`Generation successful for ${result.service} (${locale}).`);
                }
            });

            if (generationResults.some(result => !result.success)) {
                this.logger.error(
                    `Generation failed for locale ${locale}. ${generationResults.filter(r => !r.success).map(r => `${r.service}: ${r.details ?? "unknown"}`).join("; ")}. Version file not updated.`
                );
                return;
            }
        }

        const saved = await this.versionStateService.save(latestPatch);
        this.logger.info(`Generation complete. Version committed to ${saved.version}.`);
    }

    // Future extension point (manual trigger) intentionally omitted from active behavior.
}
