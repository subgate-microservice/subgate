class ActiveStatusConflict(Exception):
    def __init__(self, subscriber_id: str):
        self.subscriber_id = subscriber_id

    def __str__(self):
        return f"Subscriber with ID '{self.subscriber_id}' already has active subscription"

    def to_json(self):
        return {"subscriber_id": self.subscriber_id}
