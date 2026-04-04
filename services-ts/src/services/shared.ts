import { spawn } from "node:child_process";


export function runCommand(command: string, args: string[], cwd: string): Promise<void> {
    return new Promise((resolve, reject) => {
        const child = spawn(command, args, {
            cwd,
            stdio: "inherit"
        });
        child.on("error", reject);
        child.on("exit", (code: number | null) => {
            if (code === 0) {
                resolve();
            } else {
                reject(new Error(`${command} exited with code ${code ?? "unknown"}`));
            }
        });
    });
}