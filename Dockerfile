FROM oven/bun:1.2

WORKDIR /app

# Install Bun dependencies for the TypeScript services module.
COPY services-ts/package.json services-ts/bun.lock ./services-ts/
WORKDIR /app/services-ts
RUN bun install --frozen-lockfile

# Copy the TypeScript service sources.
COPY services-ts/ ./

# Wrapper defaults: output in /app/srv and cache in /app/__cache__.
ENV REPO_ROOT=/app

# Start wrapper service: startup generation + internal top-of-hour scheduler.
CMD ["bun", "run", "wrapper:start"]
