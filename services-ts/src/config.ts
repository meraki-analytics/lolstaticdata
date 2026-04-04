import path from "node:path";

function resolveRepoRoot(): string {
    if (process.env.REPO_ROOT && process.env.REPO_ROOT.trim()) {
        return path.resolve(process.env.REPO_ROOT);
    }
    return path.resolve(process.cwd(), "..");
}

const repoRoot = resolveRepoRoot();

export const config = {
    repoRoot,
    outputDir: process.env.OUTPUT_DIR
        ? path.resolve(process.env.OUTPUT_DIR)
        : path.join(repoRoot, "srv"),
    versionFileName: "version.json",
    patchEndpoint: "https://ddragon.leagueoflegends.com/api/versions.json",
    pythonCommand: process.env.PYTHON_COMMAND || "python",
    scheduler: {
        intervalMs: 60 * 60 * 1000
    }
};
