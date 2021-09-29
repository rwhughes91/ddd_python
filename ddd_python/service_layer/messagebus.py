from typing import Callable, Dict, List, Type

from ddd_python.domain import events

from . import handlers, unit_of_work


class AbstractMessageBus:
    HANDLERS: Dict[Type[events.Event], List[Callable]]
    uow: unit_of_work.AbstractUnitOfWork

    def __init__(self, uow: unit_of_work.AbstractUnitOfWork):
        self.uow = uow

    def handle(self, event: events.Event):
        results = []
        queue = [event]
        while queue:
            event = queue.pop(0)
            for handler in self.HANDLERS[type(event)]:
                results.append(handler(event, uow=self.uow))
                # uow.collect_new_events returns an iterator/generator
                # iterators are also iterables
                queue.extend(self.uow.collect_new_events())
        return results


class MessageBus(AbstractMessageBus):
    HANDLERS: Dict[Type[events.Event], List[Callable]] = {
        events.AllocationRequired: [handlers.allocate],
        events.ProductsRequired: [handlers.list_products],
        events.ProductCreated: [handlers.add_product],
        events.BatchesRequired: [handlers.list_batches],
        events.BatchCreated: [handlers.add_batch],
        events.BatchQuantityChanged: [handlers.change_batch_quantity],
        events.OutOfStock: [handlers.send_out_of_stock_notification],
    }


class Handler:
    def __getitem__(self, event):
        return [lambda e: self.events_published.append(e)]


class FakeMessageBus(AbstractMessageBus):
    events_published: List[events.Event]

    def __init__(self):
        super().__init__()
        self.events_published = []
        self.HANDLERS = Handler
