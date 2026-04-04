## Phase 0 Baseline Contract

Date locked: 2026-04-04
Scope: freeze current data and runtime behavior before TypeScript implementation.

## 1) Data Contract Baseline

### 1.1 Current artifact snapshot
- Aggregate champion artifact exists at `champions.json` in repository root.
- Per-champion artifacts exist in `champions/`.
- Current per-champion file count in `champions/`: 172 JSON files (snapshot value at lock time).
- Current `champions.json` size: 13,786,454 bytes (snapshot value at lock time).
- `items.json` is not currently present in repository root at lock time.
- Current external items snapshot source is available at `https://hexserve.dump-collector.de/latest/items.json`.
- External items endpoint verification at lock time: HTTP 200, `Content-Type: application/json; charset=utf-8`, `Content-Length: 3,223,462`.
- External items JSON appears to be object-keyed by item id strings (example starts with key `"1001"`).
- `srv/` is generated at runtime and is not present in repository root at lock time.

### 1.2 Champion canonical shape (locked)
Source of truth for field semantics:
- `lolstaticdata/champions/modelchampion.py` (`Champion`, `Stats`, `Ability`, `Skin`, enums)
- `lolstaticdata/champions/__main__.py` (field inclusion/exclusion behavior via CLI flags)

Locked top-level champion fields:
- id
- key
- name
- title
- fullName
- icon
- resource
- attackType
- adaptiveType
- stats
- positions
- roles
- attributeRatings
- abilities
- releaseDate
- releasePatch
- patchLastChanged
- price
- lore
- faction
- skins

Locked behavior:
- Champion aggregate output is keyed by champion key.
- Optional sections can be omitted via CLI flags (`stats`, `abilities`, `skins`, `lore`).
- Locale behavior in current implementation is effectively en_US/en_us hardcoded.

### 1.3 Item canonical shape (locked)
Source of truth for field semantics:
- `lolstaticdata/items/modelitem.py` (`Item`, `Stats`, `Passive`, `Active`, `Shop`)
- `lolstaticdata/items/__main__.py` (generation and export behavior)

Locked top-level item fields:
- name
- id
- tier
- rank
- buildsFrom
- buildsInto
- specialRecipe
- noEffects
- removed
- requiredChampion
- requiredAlly
- icon
- simpleDescription
- nicknames
- passives
- active
- stats
- shop
- iconOverlay

Note:
- Because `items.json` is not present in repository root at lock time, item output lock is based on model and generator behavior rather than a checked-in artifact snapshot.
- Additionally, the external items snapshot URL above is used as a practical reference artifact for manual local comparison during migration.

## 2) Runtime Contract Baseline

### 2.1 Current orchestration source of truth
- `lolstaticdata/check_and_update.py`
- `lolstaticdata/version_manager.py`
- `Dockerfile`
- `check_updates.sh`
- `docker-compose.yml`

### 2.2 Startup behavior (locked)
Container startup currently:
1. Generates champions.
2. Generates items.
3. Starts cron daemon.
4. Tails `/var/log/cron.log`.

### 2.3 Scheduled update behavior (locked)
- Cron schedule: top of each hour (`0 * * * *`).
- Scheduled script: `/app/check_updates.sh`.
- Scheduled action: run `python3 -m lolstaticdata.check_and_update`.

### 2.4 Update decision and commit behavior (locked)
Current check/update flow:
1. Read latest patch using `get_latest_patch_version()`.
2. Read current version from `srv/version.json` if present.
3. If versions match: no regeneration.
4. If versions differ or version file missing: generate champions and items.
5. Only after successful generation: update `srv/version.json`.

### 2.5 version.json contract (locked)
Fields:
- version (string)
- lastUpdate (UTC ISO timestamp with `Z` suffix)
- timestamp (unix seconds, integer)

Behavior:
- `version.json` write is post-generation commit, not pre-generation.
- Failures in generation must not commit a new version.

## 3) Phase 0 Acceptance (Completed)
- Data contract frozen from current models and existing champion artifact.
- Runtime contract frozen from current orchestration and container scheduler flow.
- Baseline document created for TS WrapperService implementation reference.

## 4) Phase 0 Carry-Forward Rules
- The new TS WrapperService must preserve orchestration order and version commit semantics.
- The new TS module may change internal implementation details but not external runtime contract behavior in initial rollout.
- Manual retrigger is deferred (architecture hook allowed, behavior disabled in first rollout).
