from typing import Callable, Dict, List, Type

from ddd_python.domain import events

from . import handlers, unit_of_work


def handle(event: events.Event, uow: unit_of_work.AbstractUnitOfWork):
    results = []
    queue = [event]
    while queue:
        event = queue.pop(0)
        for handler in HANDLERS[type(event)]:
            results.append(handler(event, uow=uow))
            # uow.collect_new_events returns an iterator/generator
            # iterators are also iterables
            queue.extend(uow.collect_new_events())
    return results


HANDLERS: Dict[Type[events.Event], List[Callable]] = {
    events.AllocationRequired: [handlers.allocate],
    events.ProductsRequired: [handlers.list_products],
    events.ProductCreated: [handlers.add_product],
    events.BatchesRequired: [handlers.list_batches],
    events.BatchCreated: [handlers.add_batch],
    events.BatchEdited: [handlers.edit_batch],
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}
