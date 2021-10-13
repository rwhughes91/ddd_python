from ddd_python.adapters import email, event_publisher, orm
from ddd_python.config import redis_host, redis_port

from . import unit_of_work
from .messagebus import MessageBus


def bootstrap(
    start_orm=False,
    testing=False,
):
    if start_orm:
        orm.start_mappers()

    if testing:
        uow = unit_of_work.FakeUnitOfWork(
            email.FakeEmailAdapter(),
            event_publisher=event_publisher.FakePublisherAdapter(),
        )
    else:
        uow = unit_of_work.SqlAlchemyUnitOfWork(
            email.FakeEmailAdapter(),
            event_publisher=event_publisher.RedisPublisherAdapter(
                host=redis_host, port=redis_port
            ),
        )

    return MessageBus(uow)
