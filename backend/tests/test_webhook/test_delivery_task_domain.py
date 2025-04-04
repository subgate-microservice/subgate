from datetime import timedelta

from backend.shared.utils.dt import get_current_datetime
from backend.webhook.domain.delivery_task import DeliveryTask, Message, SentErrorInfo

DELAYS = (0, 10, 30,)


def test_next_retry_delay(current_user):
    delivery = DeliveryTask(
        url="http://my-site.com",
        data=Message(type="event", event_code="any", occurred_at=get_current_datetime(), payload={}),
        retries=0,
        delays=DELAYS,
        partkey="Hello",
        auth_id=current_user.id,
    )
    dt = get_current_datetime().replace(microsecond=0)
    for retry in range(0, delivery.max_retries):
        assert delivery.next_retry_at.replace(microsecond=0) == dt + timedelta(seconds=DELAYS[delivery.retries])
        delivery = delivery.failed_sent(SentErrorInfo(status_code=500, detail="AnyErr"))
    assert delivery.retries == 3
    assert delivery.max_retries == 3
