from typing import Callable, Dict, List, Type

from ddd_python.domain import events


def handle(event: events.Event):
    for handler in HANDLERS[type(event)]:
        handler(event)


def send_out_of_stock_notification(event: events.OutOfStock):
    # email.send_mail(
    #     "stock@made.com",
    #     f"Out of stock for {event.sku}",
    # )
    return "Email Sent"


HANDLERS: Dict[Type[events.Event], List[Callable]] = {
    events.OutOfStock: [send_out_of_stock_notification],
}
