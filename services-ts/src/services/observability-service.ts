export class ObservabilityService {
    info(message: string): void {
        console.log(`[INFO] ${new Date().toISOString()} ${message}`);
    }

    warn(message: string): void {
        console.warn(`[WARN] ${new Date().toISOString()} ${message}`);
    }

    error(message: string): void {
        console.error(`[ERROR] ${new Date().toISOString()} ${message}`);
    }
}
