import { createWrapperService } from "../factory.js";

async function main(): Promise<void> {
    const wrapper = createWrapperService();
    await wrapper.runScheduledCycle();
    wrapper.stop();
}

void main();
