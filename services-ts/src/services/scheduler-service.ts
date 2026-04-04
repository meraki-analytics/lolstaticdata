import { config } from "../config.js";
import type { SchedulerService } from "../contracts.js";

export class TopOfHourSchedulerService implements SchedulerService {
    private kickoffTimer: NodeJS.Timeout | null = null;
    private intervalTimer: NodeJS.Timeout | null = null;

    start(handler: () => Promise<void>): void {
        this.stop();

        const now = Date.now();
        const waitMs = config.scheduler.intervalMs - (now % config.scheduler.intervalMs);

        this.kickoffTimer = setTimeout(() => {
            void handler();
            this.intervalTimer = setInterval(() => {
                void handler();
            }, config.scheduler.intervalMs);
        }, waitMs);
    }

    stop(): void {
        if (this.kickoffTimer) {
            clearTimeout(this.kickoffTimer);
            this.kickoffTimer = null;
        }
        if (this.intervalTimer) {
            clearInterval(this.intervalTimer);
            this.intervalTimer = null;
        }
    }
}
