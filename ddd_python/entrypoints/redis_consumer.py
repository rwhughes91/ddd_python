import json
from datetime import datetime
from typing import Callable, Dict, Optional

from redis import Redis

from ddd_python.adapters import email, event_publisher, orm
from ddd_python.config import redis_host, redis_port
from ddd_python.domain import commands
from ddd_python.service_layer import unit_of_work
from ddd_python.service_layer.messagebus import MessageBus


class RedisMessage:
    channel: str
    type: str
    pattern: Optional[str]
    data: Dict[str, str]

    def __init__(self, channel: str, message_type: str, pattern: str, data: str):
        self.channel = channel
        self.type = message_type
        self.pattern = pattern
        self.data = json.loads(data)


# Products


def add_products(message: RedisMessage):
    uow = unit_of_work.SqlAlchemyUnitOfWork(
        email.FakeEmailAdapter(),
        event_publisher=event_publisher.RedisPublisherAdapter(
            host=redis_host, port=redis_port
        ),
    )
    messagebus = MessageBus(uow)
    messagebus.handle(commands.CreateProduct(message.data.get("sku", "")))


# Batches


def add_batch(message: RedisMessage):
    uow = unit_of_work.SqlAlchemyUnitOfWork(
        email.FakeEmailAdapter(),
        event_publisher=event_publisher.RedisPublisherAdapter(
            host=redis_host, port=redis_port
        ),
    )
    messagebus = MessageBus(uow)
    date = datetime.strptime(message.data.get("eta", ""), "%m/%d/%Y").date()
    messagebus.handle(
        commands.CreateBatch(
            message.data.get("ref", ""),
            message.data.get("sku", ""),
            int(message.data.get("qty", 0)),
            date,
        )
    )


def change_batch_quantity(message: RedisMessage):
    uow = unit_of_work.SqlAlchemyUnitOfWork(
        email.FakeEmailAdapter(),
        event_publisher=event_publisher.RedisPublisherAdapter(
            host=redis_host, port=redis_port
        ),
    )
    messagebus = MessageBus(uow)
    messagebus.handle(
        commands.ChangeBatchQuantity(
            message.data.get("ref", ""), int(message.data.get("qty", 0))
        )
    )


# Allocations


def allocate_endpoint(message: RedisMessage):
    uow = unit_of_work.SqlAlchemyUnitOfWork(
        email.FakeEmailAdapter(),
        event_publisher=event_publisher.RedisPublisherAdapter(
            host=redis_host, port=redis_port
        ),
    )
    messagebus = MessageBus(uow)
    messagebus.handle(
        commands.Allocate(
            message.data.get("orderid", ""),
            message.data.get("sku", ""),
            int(message.data.get("qty", 0)),
        )
    )


ENTRYPOINTS: Dict[str, Callable] = {
    "allocate": allocate_endpoint,
    "add_products": add_products,
    "add_batch": add_batch,
    "change_batch_quantity": change_batch_quantity,
}

if __name__ == "__main__":
    orm.start_mappers()
    r = Redis(host=redis_host, port=redis_port)
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(
        "allocate",
        "add_products",
        "add_batch",
        "change_batch_quantity",
    )

    for message in pubsub.listen():
        redis_message = RedisMessage(**message)
        entry_point = ENTRYPOINTS.get(message["channel"])
        if entry_point:
            entry_point(redis_message)
