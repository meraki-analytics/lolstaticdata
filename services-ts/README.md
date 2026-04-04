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

## Output Layout

- Root output directory remains `srv/` (configurable via `OUTPUT_DIR`).
- Version state stays at `srv/version.json` and now also includes a `history` list.
- Generated payloads are written under `srv/<patchVersion>/<locale>/...`.
  - Example: `srv/15.23.1/en_US/champions/Aatrox.json`
  - Example: `srv/15.23.1/de_DE/items/1001.json`

## Locale Configuration

- Locales are configured via `OUTPUT_LOCALES` (comma-separated).
- Default locales are `en_US,de_DE`.
