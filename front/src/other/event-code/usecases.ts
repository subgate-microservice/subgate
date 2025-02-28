import {EventCode} from "./domain.ts";

const ALL_DATA: EventCode[] = [
    EventCode.enum.SubscriptionCreated,
    EventCode.enum.SubscriptionUpdated,
    EventCode.enum.SubscriptionDeleted,
    EventCode.enum.SubscriptionExpired,
]

export async function getAllEventCodes(): Promise<EventCode[]> {
    return ALL_DATA
}

