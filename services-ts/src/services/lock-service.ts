export class LockService {
    private locked = false;

    async runExclusive(actionName: string, action: () => Promise<void>): Promise<void> {
        if (this.locked) {
            console.log(`[LOCK] Skipping ${actionName}; another run is active.`);
            return;
        }

        this.locked = true;
        try {
            await action();
        } finally {
            this.locked = false;
        }
    }
}
