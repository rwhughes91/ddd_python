from typing import Callable, Dict, List, Type

from ddd_python.adapters.email import AbstractEmailAdapter
from ddd_python.domain import events


class MessageBus:
    email: AbstractEmailAdapter

    def __init__(self, email: AbstractEmailAdapter):
        self.email = email

        self.HANDLERS: Dict[Type[events.Event], List[Callable]] = {
            events.OutOfStock: [self.send_out_of_stock_notification],
        }

    def handle(self, event: events.Event):
        for handler in self.HANDLERS[type(event)]:
            handler(event)

    def send_out_of_stock_notification(self, event: events.OutOfStock):
        self.email.send_mail(
            "stock@made.com",
            f"Out of stock for {event.sku}",
        )
