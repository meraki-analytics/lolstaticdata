# League of Legends Static Data - Automatic Updates

Automatic updates are now managed by the TypeScript `WrapperService` in `services-ts/`.

## How It Works

The wrapper automatically:
1. Runs a full generation on startup.
2. Checks for new patches every hour (top-of-hour cadence, internal scheduler).
3. Regenerates champion and item data when a patch change is detected.
4. Updates `srv/version.json` only after successful generation.

## Version File Format

The `srv/version.json` file keeps compatibility fields and includes history entries:

```json
{
  "version": "16.7.1",
  "lastUpdate": "2026-04-04T16:00:00Z",
  "timestamp": 1775318400,
  "history": [
    {
      "version": "16.7.1",
      "lastUpdate": "2026-04-04T16:00:00Z",
      "timestamp": 1775318400
    }
  ]
}
```

## Running Updates Manually

### Using Docker

```bash
# Trigger a single immediate update-check cycle
docker-compose exec lol-data-generator bun run wrapper:check-once

# View current version
docker-compose exec lol-data-generator cat /app/srv/version.json

# Stream wrapper logs
docker-compose logs -f lol-data-generator
```

### Running Locally

```bash
cd services-ts

# Start long-running wrapper (startup + scheduled checks)
bun run wrapper:start

# Run one update-check cycle
bun run wrapper:check-once
```

## Environment Variables

- `REPO_ROOT`: Base repository path. Default resolves to parent of `services-ts`.
- `OUTPUT_DIR`: Output root directory (default: `<REPO_ROOT>/srv`).
- `CACHE_DIR`: Cache root directory (default: `<REPO_ROOT>/__cache__`).
- `OUTPUT_LOCALES`: Comma-separated locales (default: `en_US,de_DE`).
- `PYTHON_COMMAND`: Python executable used by legacy item adapter (default: `python`).

## Notes

- Docker cron and cron helper scripts are no longer used.
- Scheduler behavior is owned by `WrapperService`, not container orchestration.
