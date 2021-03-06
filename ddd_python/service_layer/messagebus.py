from typing import Callable, Dict, List, Type, Union

from retry import retry

from ddd_python.domain import commands, events

from . import handlers, unit_of_work

Message = Union[commands.Command, events.Event]


class AbstractMessageBus:
    EVENT_HANDLERS: Dict[Type[events.Event], List[Callable]]
    COMMAND_HANDLERS: Dict[Type[commands.Command], Callable]
    uow: unit_of_work.AbstractUnitOfWork
    queue: List[Message]

    def __init__(self, uow: unit_of_work.AbstractUnitOfWork):
        self.uow = uow
        self.queue = []

    def _handle_event(self, event: events.Event):
        for handler in self.EVENT_HANDLERS[type(event)]:
            try:

                @retry(tries=3, delay=2, backoff=1)
                def run():
                    handler(event, uow=self.uow, queue=self.queue)
                    self.queue.extend(self.uow.collect_new_events())

                run()

            except Exception:
                continue

    def _handle_command(
        self,
        command: commands.Command,
    ):
        try:
            handler = self.COMMAND_HANDLERS[type(command)]
            result = handler(command, uow=self.uow)
            self.queue.extend(self.uow.collect_new_events())
            return result
        except Exception:
            raise

    def handle(self, message: Message):
        results = []
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, events.Event):
                self._handle_event(message)
            elif isinstance(message, commands.Command):
                cmd_result = self._handle_command(message)
                results.append(cmd_result)
            else:
                raise Exception(f"{message} was not an Event or Command")
        return results


class MessageBus(AbstractMessageBus):
    COMMAND_HANDLERS: Dict[Type[commands.Command], Callable] = {
        commands.CreateProduct: handlers.add_product,
        commands.CreateBatch: handlers.add_batch,
        commands.ChangeBatchQuantity: handlers.change_batch_quantity,
        commands.Allocate: handlers.allocate,
        commands.Deallocate: handlers.deallocate,
    }
    EVENT_HANDLERS: Dict[Type[events.Event], List[Callable]] = {
        events.Allocated: [
            handlers.publish_allocated_event,
            handlers.add_allocation_to_read_model,
        ],
        events.Deallocated: [
            handlers.publish_deallocated_event,
            handlers.remove_allocation_from_read_model,
        ],
        events.ProductCreated: [
            handlers.publish_product_created_event,
            handlers.add_product_to_read_model,
        ],
        events.BatchCreated: [
            handlers.publish_batch_created_event,
            handlers.add_batch_to_read_model,
        ],
        events.BatchQuantityChanged: [
            handlers.publish_batch_quantity_changed,
            handlers.edit_batch_qty_to_read_model,
        ],
        events.OutOfStock: [handlers.send_out_of_stock_notification],
    }


class EventHandler:
    def __getitem__(self, event):
        return [lambda e: self.events_published.append(e)]


class CommandHandler:
    def __getitem__(self, event):
        return lambda e: self.commands_published.append(e)


class FakeMessageBus(AbstractMessageBus):
    events_published: List[events.Event]
    commands_published: List[commands.Command]

    def __init__(self):
        super().__init__()
        self.events_published = []
        self.commands_published = []
        self.EVENT_HANDLERS = EventHandler
        self.COMMAND_HANDLERS = CommandHandler
