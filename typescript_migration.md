## Plan: Bun + TypeScript CDragon Rebuild with Auto-Update Runtime

Migrate from the current Python scraping pipeline to a Bun-run TypeScript CDragon-first pipeline while preserving the new operational behavior already added to the project: Dockerized long-running service, hourly patch checks, automatic full regeneration on new patch detection, and persisted version state.

**Steps**
1. Phase 0 - Lock Functional Baselines
Freeze two baseline contracts before migration:
- Data contract: current champions/items payload shapes and compatibility expectations.
- Runtime contract: current update loop semantics from check_and_update/version_manager and Docker startup+cron behavior.
Capture expected success/failure behavior (when version updates, when generation runs, and what happens on partial failures).

2. Phase 1 - Bun + TypeScript Foundation
Create a dedicated TypeScript package executed with Bun:
- bun scripts for build, typecheck, test, run.
- strict tsconfig and runtime schema validation.
- CLI commands replacing Python modules:
  - generate:champions
  - generate:items (can initially delegate to legacy Python)
  - check-and-update
  - version:status
Keep command UX aligned with existing operators so migration is operationally low-friction.

3. Phase 1 - Runtime Operations Module (New First-Class Scope)
Implement a dedicated operations layer in TypeScript for patch lifecycle automation:
- Patch detector using DDragon versions endpoint.
- Version state store compatible with existing srv/version.json fields (version, lastUpdate, timestamp).
- Update orchestrator that triggers full regeneration when latest patch differs from stored version.
- Commit protocol: only write new version.json after all required generators complete successfully.
- Locking protocol: prevent overlapping runs (cron overlap/manual trigger/startup race).

4. Phase 1 - Docker and Scheduler Migration
Preserve current container UX while moving internals to Bun:
- Maintain Docker service that writes data into shared volume path equivalent to current /app/srv behavior.
- Preserve startup semantics: initial generation on first run, then scheduled checks.
- Preserve hourly scheduling behavior (top-of-hour) either with in-container cron parity first, or a minimal Bun scheduler loop with equivalent cadence.
- Keep docker-compose volume contract stable for downstream containers (named shared data volume).
- Keep logging path/behavior predictable for operators currently tailing update logs.

5. Phase 2 - CDragon Ingestion for Champions (No Scraping)
Replace champion wiki scraping with CDragon JSON ingestion:
- champion metadata, stats, abilities, skins, assets from CDragon endpoints.
- deterministic URL construction (remove fuzzy icon guessing).
- retry/backoff, deterministic cache keys, and typed endpoint decoding.
- use CDragon json/bin.json representations first; defer raw bin parsing.

6. Phase 2 - Optional Bin Adapter
Add optional raw bin adapter only for champion edge mechanics not expressible from CDragon JSON exports. Keep adapter pluggable and champion-scoped to isolate complexity.

7. Phase 3 - Normalize to Current Champion Contract
Map CDragon raw data to current consumer-facing champion schema semantics:
- preserve existing stable field names where clients depend on them.
- preserve ability grouping structure and stat object semantics.
- convert exception logic into declarative rules rather than procedural branching.

8. Phase 3 - Localization Model
Apply localization only to champion detail artifacts:
- localized fields: champion text/name/title/lore/ability text.
- locale-neutral fields: ids, keys, stats, mechanics, assets.
Use deterministic fallback requested locale -> en_US -> explicit missing marker.

9. Phase 4 - Locale-Independent Summary Artifact
Publish a single champion-index.json that is locale-independent and list-focused.
Allowed fields: id/key/slug, icon URL, mechanical tags/roles, patch metadata.
No locale-dependent display text in this file.

10. Phase 4 - Export Layout and Patch Versioning
Publish immutable patch directories and a latest alias:
- patch-scoped localized champion details.
- locale-independent champion index at patch root.
- version.json reflects currently promoted patch after successful generation commit.
Use atomic file promotion to avoid partial publish states.

11. Phase 5 - Python to TypeScript Migration Tracks (Expanded)
Track A: Contract extraction and golden fixtures from current outputs.
Track B: Model migration from Python dataclasses/enums to TS schemas/types.
Track C: Behavior migration for generator CLI flags and defaults.
Track D: Runtime migration for version manager + check-and-update orchestration.
Track E: Container migration from python:3.12-slim entry flow to Bun-based image while preserving docker-compose contracts.
Track F: Dual-run operation where scheduler can execute both pipelines and compare results (new pipeline shadow mode).
Track G: Cutover switch where check-and-update triggers Bun pipeline as primary; Python kept as rollback path for one patch window.
Track H: Decommission of legacy scraper modules and Python-only update scripts after rollback period.

12. Phase 5 - Verification and Reliability Gates
Add automated gates for both data and operations:
- Data parity: champion key set, critical fields, ability slots, item/champion artifact existence.
- Runtime parity: new patch detection behavior equals legacy for same version inputs.
- Version state integrity: version.json only changes on successful full generation.
- Concurrency safety: overlapping trigger attempts do not corrupt outputs.
- Determinism: same patch and config produce byte-stable artifacts.
- Container smoke tests: startup generation, hourly check run, manual retrigger command.

13. Phase 6 - Rollout and Observability
Roll out in stages:
- Stage 1: Bun check-and-update in dry-run mode.
- Stage 2: Bun generation in shadow mode with diff reports.
- Stage 3: Bun promoted to primary in container.
- Stage 4: Legacy Python removal.
Add metrics/logging for patch checks, generation duration, failure reasons, retrigger count, and last successful patch timestamp.

**Relevant files**
- lolstaticdata/Dockerfile - Current startup and cron behavior to preserve during migration.
- lolstaticdata/docker-compose.yml - Shared volume and long-running container contract to keep stable.
- lolstaticdata/check_updates.sh - Hourly scheduler entrypoint behavior reference.
- lolstaticdata/lolstaticdata/check_and_update.py - Current patch-check and full-regeneration orchestration semantics.
- lolstaticdata/lolstaticdata/version_manager.py - Current version.json lifecycle and update semantics.
- lolstaticdata/lolstaticdata/champions/__main__.py - Current champion generation CLI behavior to mirror.
- lolstaticdata/lolstaticdata/items/__main__.py - Current item generation path used by full retrigger flow.
- lolstaticdata/lolstaticdata/champions/pull_champions_wiki.py - Legacy scraping module targeted for removal.
- lolstaticdata/lolstaticdata/champions/pull_champions_dragons.py - Legacy fuzzy icon logic targeted for removal.
- lolstaticdata/champions.json - Golden compatibility dataset for migration diffing.

**Verification**
1. Confirm Bun check-and-update returns same decisions as Python for same version.json and mocked latest patch values.
2. Confirm no-update path leaves artifacts untouched and exits cleanly.
3. Confirm new-patch path regenerates all required artifacts and only then updates version.json.
4. Confirm scheduler-triggered and manual-triggered runs are lock-safe and non-overlapping.
5. Confirm champion-index.json remains locale-independent across all locale generation runs.
6. Confirm localized champion detail outputs vary only in translatable fields.
7. Confirm docker-compose consumers can read unchanged volume paths after migration.

**Decisions**
- Runtime and package manager: Bun.
- Data extraction source: CDragon JSON first; optional bin adapter for proven gaps.
- Summary artifact: one locale-independent champion-index.json.
- Localization scope: champion detail artifacts only.
- Operations scope now included in migration: Docker runtime, scheduler, version checks, auto-retrigger.
- Items migration strategy: keep item generation in full retrigger path; can remain legacy in first cut while champions move first.

**Further Considerations**
1. Scheduler implementation choice: keep in-container cron parity first or replace with Bun-native scheduler loop. Recommendation: keep cron parity first, then optionally simplify later.
2. Trigger granularity: full regeneration on patch change vs component-level regeneration. Recommendation: keep full regeneration parity first to avoid semantic drift.
3. Version source hardening: DDragon only vs DDragon plus secondary fallback source. Recommendation: DDragon primary with optional fallback for resilience.
