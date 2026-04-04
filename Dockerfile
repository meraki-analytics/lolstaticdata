FROM oven/bun:1.2

# Python remains available for the legacy ItemService adapter until native TS item generation is finished.
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /app

# Install Python dependencies used by legacy item generation.
COPY requirements.txt pyproject.toml ./
COPY lolstaticdata/ ./lolstaticdata/
RUN pip install --no-cache-dir -r requirements.txt

# Install Bun dependencies for the TypeScript services module.
COPY services-ts/package.json services-ts/bun.lock ./services-ts/
WORKDIR /app/services-ts
RUN bun install --frozen-lockfile

# Copy the TypeScript service sources.
COPY services-ts/ ./

# Wrapper defaults: output in /app/srv and cache in /app/__cache__.
ENV PYTHONPATH=/app
ENV REPO_ROOT=/app
ENV PYTHON_COMMAND=python

# Start wrapper service: startup generation + internal top-of-hour scheduler.
CMD ["bun", "run", "wrapper:start"]
