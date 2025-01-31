from backend.shared.unit_of_work.uow import UnitOfWork


class Context:
    def __init__(
            self,
            uow: UnitOfWork,
    ):
        self.uow = uow
