from loguru import logger

from backend.shared.utils import get_current_datetime
from backend.webhook.domain.delivery_task import DeliveryTask, Message, SentErrorInfo

DELAYS = (0, 10, 30, 180, 600, 1_800, 3_600, 7_200, 14_400, 28_800, 57_600, 86_400)


def test_next_retry_delay():
    delivery = DeliveryTask(
        url="http://my-site.com",
        data=Message(type="event", event_code="any", occurred_at=get_current_datetime(), payload={}),
        retries=0,
        delays=DELAYS,
    )
    logger.debug(f"First attempt: {delivery.next_retry_at}, retry={delivery.retries}")
    for retry in range(0, delivery.max_retries):
        delivery = delivery.failed_sent(SentErrorInfo(status_code=500, detail="AnyErr"))
        logger.debug(f"Next attempt: {delivery.next_retry_at}, retry={delivery.retries}")
