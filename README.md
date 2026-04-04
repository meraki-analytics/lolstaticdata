# League of Legends Static Data

This repository provides code to generate accurate champion and item data. First, a big thanks goes out to the people who work hard to maintain the League of Legends Wiki. We pull champion ability information from them because it is the only accurate source of champion data.

If you use this data, please give a shoutout to the League of Legends Wiki.

**Features:**
- Accurate champion and item data from League of Legends Wiki
- Automatic patch version detection and updates
- Bun wrapper runtime with internal hourly scheduling

## Goals of the Project
Until now, accurate champion data that developers can use to create apps has not been reliably available. Our goal is to provide high quality champion and item data so that you can create awesome applications.


In this project, we aim to strike a balance between data that is accurate and simple enough to be understandable and parsable. Having accurate data for champion abilities in particular will open up a new use-case for League of Legends apps by allowing ability damages to be calculated accurately. For example, this data may allow for quick and automated calculations of a champion's power from one patch to another (you'll need to keep track of the changes). This has never before been possible due to the inaccuracy of the available data and, therefore, the manual work required to update that data each patch.
Data other than that for champions and items should be covered by the data that Riot provides, or by the CDragon project.

Note that it is impossible to represent the enormous complexity of League of Legends data in a simple JSON format, so special cases exist that need to be handled on a case-by-case basis. This is left up to you, as the developer, to create the complex interactions that are needed by your app.

## Running the Code

### Using Docker (Recommended)

Generate the static data files in a Docker volume that can be accessed by other containers. The container will automatically check for new patch versions every hour and regenerate the data when a new patch is released:

```bash
# Build and start the service (runs in background)
docker-compose up -d

# The container will:
# 1. Generate initial data on first run
# 2. WrapperService checks for new patch versions every hour
# 3. Automatically regenerate data when a new patch is detected
# 4. Store version info in srv/version.json
```

**Version Information:**

The service creates a `version.json` file in the srv directory containing compatibility fields and history:
```json
{
  "version": "14.23.1",
  "lastUpdate": "2026-01-13T10:30:00Z",
  "timestamp": 1736765400,
  "history": [
    {
      "version": "14.23.1",
      "lastUpdate": "2026-01-13T10:30:00Z",
      "timestamp": 1736765400
    }
  ]
}
```

**Environment Variables**

The Docker setup works with defaults, but you can override behavior with these environment variables:

- `REPO_ROOT`
  - Base repository path used by the TypeScript services.
  - Docker default: `/app`.
- `OUTPUT_DIR`
  - Output directory for generated artifacts and `version.json`.
  - Default: `<REPO_ROOT>/srv`.
- `CACHE_DIR`
  - Cache directory for non-public intermediate files.
  - Default: `<REPO_ROOT>/__cache__`.
- `OUTPUT_LOCALES`
  - Comma-separated locales to generate.
  - Default: `en_US,de_DE`.

Example override in `docker-compose.yml`:

```yaml
services:
  lol-data-generator:
    environment:
      - REPO_ROOT=/app
      - OUTPUT_DIR=/app/srv
      - CACHE_DIR=/app/__cache__
      - OUTPUT_LOCALES=en_US,de_DE
```

**Using the Volume in Other Containers:**

The generated data is stored in a named Docker volume called `lol-static-data`. You can mount this volume in other containers to access the JSON files:

```yaml
# In another docker-compose.yml
services:
  your-app:
    image: your-image
    volumes:
      - lol-static-data:/data/lol:ro  # Mount as read-only
      
volumes:
  lol-static-data:
    external: true  # Use the volume created by lolstaticdata
```

**Common Docker Commands:**
```bash
# View the logs (including update checks)
docker-compose logs -f lol-data-generator

# Trigger a single immediate update-check cycle
docker-compose exec lol-data-generator bun run wrapper:check-once

# Check current version
docker-compose exec lol-data-generator cat /app/srv/version.json

# Inspect the volume contents
docker run --rm -v lol-static-data:/data alpine ls -la /data

# Copy files from volume to host (if needed)
docker run --rm -v lol-static-data:/data -v $(pwd)/output:/output alpine cp -r /data/. /output

# Stop the service
docker-compose down

# Remove the volume (warning: deletes all generated data)
docker-compose down -v
```

The service runs continuously and the internal wrapper scheduler checks for updates every hour at the top of the hour (e.g., 1:00, 2:00, 3:00).

### Running Locally

```bash
git clone https://github.com/meraki-analytics/lolstaticdata.git
cd lolstaticdata
cd services-ts
bun install
bun run wrapper:start
```

Local prerequisites:

- `bun` for the wrapper and TypeScript services.

Useful local commands:

```bash
# Run one update-check cycle
bun run wrapper:check-once

# Run domains directly
bun run generate:champions
bun run generate:items
```

### Serving the Files Locally

After generating the data locally, you can serve the files with any static file server.

Example with Bun:

```bash
cd srv
bunx serve . -p 8080
```

Then access the data at `http://localhost:8080/champions.json`.

## Automatic Updates

The application supports automatic version checking and data regeneration when new patches are released. See [UPDATES.md](UPDATES.md) for detailed information on:
- How automatic updates work
- WrapperService internal scheduling behavior
- Version file format
- Manual update commands

