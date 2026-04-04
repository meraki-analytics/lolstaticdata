import { createWrapperService } from "../factory.js";

async function main(): Promise<void> {
    const wrapper = createWrapperService();

    process.on("SIGINT", () => {
        wrapper.stop();
        process.exit(0);
    });

    process.on("SIGTERM", () => {
        wrapper.stop();
        process.exit(0);
    });

    await wrapper.start();
}

void main();
