import path from "node:path";

function resolveRepoRoot(): string {
    if (process.env.REPO_ROOT && process.env.REPO_ROOT.trim()) {
        return path.resolve(process.env.REPO_ROOT);
    }
    return path.resolve(process.cwd(), "..");
}

const repoRoot = resolveRepoRoot();

function resolveOutputLocales(): string[] {
    const raw = process.env.OUTPUT_LOCALES;
    if (!raw || !raw.trim()) {
        return ["en_US", "de_DE"];
    }

    const unique = new Set(
        raw
            .split(",")
            .map((value) => value.trim())
            .filter((value) => value.length > 0)
    );

    return unique.size > 0 ? Array.from(unique) : ["en_US", "de_DE"];
}

const outputLocales = resolveOutputLocales();

export const config = {
    repoRoot,
    cacheDir: process.env.CACHE_DIR
        ? path.resolve(process.env.CACHE_DIR)
        : path.join(repoRoot, "__cache__"),
    outputDir: process.env.OUTPUT_DIR
        ? path.resolve(process.env.OUTPUT_DIR)
        : path.join(repoRoot, "srv"),
    outputLocales,
    defaultLocale: outputLocales[0] ?? "en_US",
    versionFileName: "version.json",
    patchEndpoint: "https://ddragon.leagueoflegends.com/api/versions.json",
    pythonCommand: process.env.PYTHON_COMMAND || "python",
    scheduler: {
        intervalMs: 60 * 60 * 1000
    }
};
