import { ChampionService } from "./services/champion-service.js";
import { ItemService } from "./services/item-service.js";
import { LockService } from "./services/lock-service.js";
import { ObservabilityService } from "./services/observability-service.js";
import { DDragonPatchService } from "./services/patch-service.js";
import { TopOfHourSchedulerService } from "./services/scheduler-service.js";
import { JsonVersionStateService } from "./services/version-state-service.js";
import { WrapperService } from "./services/wrapper-service.js";

export function createWrapperService(): WrapperService {
    const logger = new ObservabilityService();
    return new WrapperService(
        new DDragonPatchService(),
        new JsonVersionStateService(),
        [new ChampionService(logger), new ItemService(logger)],
        new TopOfHourSchedulerService(),
        new LockService(),
        logger
    );
}
