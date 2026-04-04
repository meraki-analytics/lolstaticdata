## Plan: Bun TypeScript Service-Oriented Migration

Keep the legacy Python implementation in the repository and add a new Bun TypeScript module in a separate folder. The TS module contains multiple small, independent services and one wrapper service that fully orchestrates startup generation, periodic update checks, patch comparison, full regeneration on patch changes, and version state commits.

## Architecture Direction

Use one TS module (one package, one deployable) in a separate folder, for example `services-ts/`, with internal service boundaries rather than one large replacement script.

### Core service topology

- WrapperService (control plane)
  - Owns lifecycle: startup bootstrap, scheduled checks, full regeneration orchestration, version commit flow, and run locking.
  - Exposes a future extension point for manual retrigger, but does not enable manual retrigger in the initial rollout.
  - Delegates generation work to ChampionService and ItemService.
  - Delegates patch/version state checks to PatchService and VersionStateService.
- PatchService
  - Reads latest patch from DDragon (primary) and optional fallback source.
  - Normalizes and validates patch identifiers.
- VersionStateService
  - Reads/writes srv/version.json.
  - Preserves compatibility fields: version, lastUpdate, timestamp.
  - Only commits after successful full generation.
- ChampionService
  - CDragon ingestion, normalization, locale overlay (detail files), and champion export.
  - Produces locale-independent champion-index.json.
- ItemService
  - Item generation pipeline implemented natively in TypeScript.
- SchedulerService
  - Provides top-of-hour trigger semantics (cron parity first).
- LockService
  - Prevents concurrent runs from startup and scheduled triggers.
  - Supports a future manual-trigger source without changing lock semantics.
- ExportService
  - Atomic writes/promotions for patch outputs and latest alias.
- ObservabilityService
  - Structured logs, run metrics, and failure classification.

## Service Contracts

Define explicit interfaces so each service is replaceable without affecting others.

- GenerationService contract
  - generate(context): Promise<Result>
  - validate(context): Promise<ValidationResult>
- UpdateCheck contract
  - getLatestPatch(): Promise<PatchVersion>
  - isUpdateRequired(current, latest): boolean
- VersionState contract
  - load(): Promise<VersionState | null>
  - save(next): Promise<void>
- Scheduler contract
  - start(handler): void
  - stop(): void

## Migration Plan

Phase 0 baseline artifact:
- `phase0_baseline.md` (locked data/runtime baseline for implementation)

1. Phase 0 - Lock Baselines
- Freeze data contract baselines from current outputs (champions/items).
- Freeze runtime contract baselines from current update behavior:
  - startup full generation
  - hourly checks
  - regenerate both domains on new patch
  - update version.json only on success

2. Phase 1 - Create TS module shell (Bun)
- Create a separate folder for the new implementation (for example `services-ts/`).
- Initialize one package with Bun scripts for run/typecheck/build.
- Add strict tsconfig, linting, runtime schema validation.
- Add command entrypoints:
  - bun run wrapper:start
  - bun run wrapper:check-once
  - bun run generate:champions
  - bun run generate:items

3. Phase 1 - Implement wrapper and runtime services first
- Implement WrapperService, PatchService, VersionStateService, SchedulerService, and LockService.
- Ensure WrapperService is the single orchestrator for update checks, generation delegation, and version.json commit sequencing.
- Validate behavior manually in local runs against the Python output and runtime behavior.

4. Phase 2 - Migrate ChampionService to CDragon
- Replace wiki scraping with CDragon JSON ingestion.
- Keep locale model where only detailed champion files are localized.
- Generate one locale-independent champion-index.json.
- Keep deterministic cache, retries, and typed decoding.

5. Phase 2 - ItemService strategy
- Implement ItemService in TypeScript with the same service contracts used by ChampionService.
- Keep WrapperService orchestration unchanged while item internals are developed and hardened.

6. Phase 3 - Export and publish consistency
- Implement ExportService atomic publishing for patch folders and latest alias.
- Maintain current volume compatibility for docker-compose consumers.

7. Phase 4 - Container migration
- Move Docker runtime from python image to bun image while preserving external behavior:
  - same data volume layout
  - same scheduler cadence
  - wrapper-driven orchestration for startup and scheduled runs only (manual retrigger deferred)
  - same version.json compatibility

8. Phase 5 - Local validation and cutover
- Run exhaustive local validation manually (fixture comparisons and container smoke checks) before production promotion.
- Promote TS WrapperService as primary after local gates pass and a final pre-production verification run is clean.
- Use artifact snapshot rollback (previous generated patch artifacts) rather than maintaining a dual runtime.

9. Phase 6
- Keep service interfaces stable so future data-source changes are isolated.

## Data and Localization Rules

- Champion detail files: localized fields (name/title/lore/ability text) only.
- Mechanical fields (stats, ids, keys, tags, assets): locale-neutral.
- champion-index.json: locale-independent and list-focused.
- Fallback policy: requested locale -> en_US -> explicit missing marker for required text.

## Verification Gates (Manual)

1. Runtime parity gate
- TS WrapperService makes same update/no-update decisions as current Python flow for identical version inputs.

2. Version integrity gate
- version.json changes only after successful generation of all required services.

3. Concurrency gate
- overlapping triggers do not run concurrently and do not corrupt outputs.

4. Data parity gate
- champion key coverage, required field parity, ability slot coverage, and item/champion artifact existence.

5. Summary gate
- champion-index.json remains identical regardless of locale generation sequence.

6. Container gate
- startup run, hourly schedule, and volume access all work with the TS wrapper runtime.
- architecture keeps a future manual-trigger hook without enabling it now.

## Operational Decisions

- One TS module, many internal services.
- TS module is built in a separate folder from the Python codebase (for example `services-ts/`).
- WrapperService is the only component aware of cross-domain orchestration.
- WrapperService is the only component allowed to orchestrate checks, generation, and version commit order.
- Services remain independently verifiable and replaceable.
- Keep cron parity first; optional switch to Bun-native scheduler later.
- Keep full regeneration on patch changes first to avoid behavioral drift.
- No automated tests are required for this migration phase; validation is done through repeated local execution and output comparison.
- Manual retriggers are intentionally omitted in the initial rollout but reserved as a future extension.

## Relevant current files (reference)

- lolstaticdata/Dockerfile
- lolstaticdata/docker-compose.yml
- lolstaticdata/check_updates.sh
- lolstaticdata/lolstaticdata/check_and_update.py
- lolstaticdata/lolstaticdata/version_manager.py
- lolstaticdata/lolstaticdata/champions/__main__.py
- lolstaticdata/lolstaticdata/items/__main__.py
- lolstaticdata/lolstaticdata/champions/pull_champions_wiki.py
- lolstaticdata/lolstaticdata/champions/pull_champions_dragons.py
- lolstaticdata/champions.json
