# services-ts

Phase 1 Bun + TypeScript module for wrapper-centric orchestration.

This module is intentionally separated from the legacy Python implementation.

## Commands

- `bun run wrapper:start`
  - Startup generation, then top-of-hour scheduled checks.
- `bun run wrapper:check-once`
  - One update check cycle.
- `bun run generate:champions`
  - Run champion generation service directly.
- `bun run generate:items`
  - Run item generation service directly.
- `bun run typecheck`
  - Strict TypeScript type check.

## Notes

- Manual retrigger is intentionally not enabled yet.
- WrapperService is the only orchestrator for check/generate/version commit order.
- ChampionService is now native TypeScript with CDragon ingestion (Phase 2).
- ItemService remains a legacy-command adapter and will be migrated to native TS in a later phase.
